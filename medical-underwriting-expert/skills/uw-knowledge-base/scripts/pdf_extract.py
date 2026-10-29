#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf_extract.py — 核保材料 PDF 稳健提取链（v1.1，2026-10-29）

背景：workbuddy-pdf CLI 0.1.0 (2026.10.13) 在 Windows 上处理含扫描页的 PDF 时
会在文本提取路径（md/txt/md-plain/structure/table）发生原生崩溃
（NTSTATUS 0xC0000409，Git Bash 显示为退出码 127，无任何 stderr 输出），
被误报为「PDF CLI 不可用（退出码 127）」。纯文本 PDF 不受影响。

本脚本的策略（分级降级，永不因 CLI 崩溃而中断）：
  1. 先用 pymupdf 做页级体检（每页文本量/图片数）；
  2. 纯文本 PDF → 优先调 workbuddy-pdf CLI（-f md-plain，版面归组更好），
     30 秒超时 + 产物校验；CLI 任何异常（含原生崩溃）→ 立即改用 pymupdf 提取；
  3. 含扫描页（无文本层）→ 完全跳过 CLI（已知必崩），pymupdf 提取文本页，
     扫描页渲染为 PNG（默认 150 dpi），有 OCR 引擎则自动 OCR 合入，无则输出
     图片路径交给会话的视觉能力读取；
  4. 输出统一产物：<out>/content.md、<out>/images/page-XXXX.png、<out>/report.json。

OCR 引擎（v1.1，2026-10-29 接入 PaddleOCR v3+）：
  - 优先级：paddleocr（中文医学文档最佳）→ tesseract（降级）。
  - PaddleOCR v3+ 适配要点（与 v2 断裂式差异，勿用旧 API）：
    初始化 `PaddleOCR(lang='ch')`，识别用 `ocr.predict(img)`；
    `use_angle_cls`/`show_log`/`cls` 参数已移除，传入直接报错；
    结果取 `res['rec_texts']` / `res['rec_scores']`（list[OCRResult]）。
  - **Windows 铁律**：paddlepaddle 3.x 的 oneDNN 路径在本机 CPU 上会抛
    `NotImplementedError: ConvertPirAttribute2RuntimeAttribute ... onednn_instruction`
    ——必须 `enable_mkldnn=False`，否则引擎整体不可用（2026-10-29 实测）。
  - 批量识别在单子进程内完成（模型只加载一次），结果经临时 JSON 回传，
    避免逐页重启引擎与 stdout 混入横幅日志。

退出码语义：
  0 成功（含部分页降级）；2 用法错误；3 输入文件不存在；
  4 PDF 无法解析/加密；5 无任何可提取内容。

依赖：pymupdf（必需，纯 Python 安装无原生依赖冲突）；OCR 引擎（可选，
推荐 `pip install paddlepaddle paddleocr`，CPU 版即可）。

用法：
  python pdf_extract.py <input.pdf> [output_dir] [--dpi 150] [--no-ocr] [--no-cli]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

EXIT_OK, EXIT_USAGE, EXIT_NOFILE, EXIT_BADPDF, EXIT_EMPTY = 0, 2, 3, 4, 5

# 一页视为「有文本层」的最低非空白字符数（低于此值且含图片 → 判为扫描页）
TEXT_PAGE_MIN_CHARS = 20
CLI_TIMEOUT_SECONDS = 30


def log(msg: str) -> None:
    print(f"[pdf_extract] {msg}", flush=True)


# ---------------------------------------------------------------- CLI 定位
def locate_cli():
    """按序查找 workbuddy-pdf CLI：WORKBUDDY_PDF → 默认安装位 → PATH。找不到返回 None。"""
    env = os.environ.get("WORKBUDDY_PDF")
    candidates = []
    if env:
        candidates.append(env)
    home = os.path.expanduser("~")
    candidates.append(os.path.join(home, ".workbuddy", "external-packages", "pdf-cli", "workbuddy-pdf.exe"))
    candidates.append(os.path.join(home, ".workbuddy", "external-packages", "pdf-cli", "workbuddy-pdf"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return shutil.which("workbuddy-pdf")


def try_cli(cli, pdf_path, out_md):
    """对纯文本 PDF 尝试 CLI 的 md-plain 提取。成功返回 True（产物已校验）。"""
    if not cli:
        return False
    try:
        proc = subprocess.run(
            [cli, pdf_path, out_md, "-f", "md-plain"],
            capture_output=True, text=True, timeout=CLI_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        log(f"CLI 调用异常（{type(exc).__name__}），改用 pymupdf 提取")
        return False
    # Windows 原生崩溃：returncode 为负数（如 -1073740940 = 0xC0000409）；
    # 127 是 Git Bash 对崩溃码的显示值，不应误判为「命令不存在」。
    if proc.returncode != 0:
        log(f"CLI 退出码 {proc.returncode}（负数=原生崩溃，非命令缺失），改用 pymupdf 提取")
        return False
    if not os.path.isfile(out_md) or os.path.getsize(out_md) == 0:
        log("CLI 报成功但产物为空，改用 pymupdf 提取")
        return False
    return True


# ---------------------------------------------------------------- OCR 引擎
def detect_ocr():
    """探测可用 OCR 引擎。返回 (kind, exe_or_none)。kind ∈ {paddle, tesseract, none}。

    优先级：paddleocr（中文医学文档识别最佳，选型结论 2026-06）→ tesseract（降级）。
    paddleocr 可用 PDF2DOCX_PADDLE_PYTHON 指定装了该包的解释器，否则探测当前解释器。
    """
    # 1) PaddleOCR：环境变量指定解释器优先，其次当前解释器可导入
    paddle_py = os.environ.get("PDF2DOCX_PADDLE_PYTHON")
    if paddle_py and os.path.isfile(paddle_py):
        return "paddle", paddle_py
    try:
        import paddleocr  # noqa: F401
        return "paddle", None
    except ImportError:
        pass
    # 2) tesseract：环境变量指定或 PATH
    t = os.environ.get("PDF2DOCX_TESSERACT") or shutil.which("tesseract")
    if t and os.path.isfile(t):
        return "tesseract", t
    return "none", None


# PaddleOCR v3+ 批量子进程代码：单进程加载一次模型，逐页 predict，
# 结果写临时 JSON 回传（规避 stdout 横幅日志污染与逐页重启开销）。
# 铁律：Windows 上必须 enable_mkldnn=False（paddlepaddle 3.x oneDNN 路径
# 会抛 NotImplementedError，2026-10-29 实测）；勿传 v2 已废弃参数。
_PADDLE_BATCH_CODE = r"""
import json, sys
out_path, paths = sys.argv[1], sys.argv[2:]
result = {}
try:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(lang="ch", enable_mkldnn=False)
    for p in paths:
        try:
            r = ocr.predict(p)[0]
            texts = list(r.get("rec_texts", []))
            scores = list(r.get("rec_scores", []))
            result[p] = {
                "text": "\n".join(texts),
                "lines": len(texts),
                "conf": round(sum(scores) / len(scores), 3) if scores else 0.0,
            }
        except Exception as e:
            result[p] = {"text": "", "lines": 0, "conf": 0.0, "error": str(e)[:200]}
except Exception as e:
    result["__engine_error__"] = str(e)[:300]
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(result, fh, ensure_ascii=False)
"""


def ocr_images_batch(kind, engine, png_paths):
    """批量 OCR。返回 dict[png_path -> text]；引擎整体不可用返回 None（不抛异常）。"""
    if kind == "paddle":
        py = engine or sys.executable
        tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        out_json = tf.name
        tf.close()
        try:
            # 初始化约 15~60s（含模型加载），CPU 上每页约 3~10s
            timeout = min(3600, 600 + 150 * len(png_paths))
            # PYTHONIOENCODING：Windows 下 paddle 子进程默认 GBK 输出会让父进程
            # UTF-8 读取线程抛 UnicodeDecodeError；显式容错双保险（结果走 JSON 文件）
            proc = subprocess.run(
                [py, "-c", _PADDLE_BATCH_CODE, out_json] + list(png_paths),
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            if proc.returncode != 0 or not os.path.isfile(out_json):
                log(f"PaddleOCR 批量子进程失败（rc={proc.returncode}），保留 PNG 供视觉读取")
                return None
            with open(out_json, encoding="utf-8") as fh:
                data = json.load(fh)
            if "__engine_error__" in data:
                log(f"PaddleOCR 引擎错误：{data['__engine_error__']}")
                return None
            return {p: (data.get(p) or {}).get("text", "") for p in png_paths}
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
            log(f"PaddleOCR 进程异常（{type(exc).__name__}），保留 PNG 供视觉读取")
            return None
        finally:
            try:
                os.remove(out_json)
            except OSError:
                pass
    if kind == "tesseract":
        out = {}
        for png_path in png_paths:
            txt = ""
            for lang in ("chi_sim+eng", "eng"):
                try:
                    proc = subprocess.run(
                        [engine, png_path, "stdout", "-l", lang],
                        capture_output=True, text=True, timeout=120,
                    )
                    if proc.returncode == 0 and proc.stdout.strip():
                        txt = proc.stdout.strip()
                        break
                except (subprocess.TimeoutExpired, OSError):
                    break
            out[png_path] = txt
        return out
    return None


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description="核保材料 PDF 稳健提取链")
    ap.add_argument("input", help="输入 PDF 路径")
    ap.add_argument("output_dir", nargs="?", help="输出目录（默认：输入旁建 <stem>_extract）")
    ap.add_argument("--dpi", type=int, default=150, help="扫描页渲染 dpi（默认 150）")
    ap.add_argument("--no-ocr", action="store_true", help="跳过 OCR（只渲染图片）")
    ap.add_argument("--no-cli", action="store_true", help="完全跳过 workbuddy-pdf CLI")
    args = ap.parse_args()

    pdf_path = os.path.abspath(args.input)
    if not os.path.isfile(pdf_path):
        log(f"输入文件不存在: {pdf_path}")
        return EXIT_NOFILE

    out_dir = os.path.abspath(args.output_dir) if args.output_dir else \
        os.path.join(os.path.dirname(pdf_path), re.sub(r"\.pdf$", "", os.path.basename(pdf_path), flags=re.I) + "_extract")
    os.makedirs(out_dir, exist_ok=True)
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf  # 兼容旧包名
        except ImportError:
            log("pymupdf 未安装（pip install pymupdf）")
            return EXIT_BADPDF

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        log(f"PDF 无法解析: {exc}")
        return EXIT_BADPDF
    if doc.is_encrypted:
        try:
            doc.authenticate("")
        except Exception:
            pass
        if doc.is_encrypted:
            log("PDF 已加密且空口令无法解锁")
            return EXIT_BADPDF

    # ---- 页级体检
    page_stats = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        n_img = len(page.get_images())
        page_stats.append({
            "page": i + 1,
            "text_chars": len(text),
            "images": n_img,
            "is_scan": len(text) < TEXT_PAGE_MIN_CHARS and n_img > 0,
        })
    n_pages = len(page_stats)
    scan_pages = [p["page"] for p in page_stats if p["is_scan"]]
    text_pages = [p["page"] for p in page_stats if not p["is_scan"]]
    log(f"体检完成：共 {n_pages} 页，文本页 {len(text_pages)}，扫描页 {len(scan_pages)}"
        + (f"（第 {', '.join(map(str, scan_pages[:20]))}{'…' if len(scan_pages) > 20 else ''} 页）" if scan_pages else ""))

    method = "pymupdf"
    md_path = os.path.join(out_dir, "content.md")
    cli_md = os.path.join(out_dir, "_cli_content.md")

    # ---- 纯文本 PDF：先试 CLI（版面/表格归组更好）
    if not scan_pages and not args.no_cli and text_pages:
        cli = locate_cli()
        if cli and try_cli(cli, pdf_path, cli_md):
            try:
                os.replace(cli_md, md_path)
                method = "workbuddy-pdf CLI (md-plain)"
            except OSError:
                method = "pymupdf"
        elif os.path.isfile(cli_md):
            os.remove(cli_md)

    # ---- CLI 未用/失败 → pymupdf 全量提取
    if method == "pymupdf":
        parts = []
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            parts.append(f"<!-- Page {i + 1} -->\n")
            if text:
                parts.append(text + "\n")
            if page_stats[i]["is_scan"]:
                png = os.path.join(img_dir, f"page-{i + 1:04d}.png")
                try:
                    pix = page.get_pixmap(dpi=args.dpi)
                    pix.save(png)
                    parts.append(f"（扫描页，已渲染：images/page-{i + 1:04d}.png）\n")
                except Exception as exc:
                    parts.append(f"（扫描页渲染失败: {exc}）\n")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(parts))

    # ---- OCR（可选）：对渲染出的扫描页批量跑引擎，结果合入 content.md
    ocr_engine_kind = "none"
    ocr_done = 0
    rendered = sorted(os.listdir(img_dir)) if os.path.isdir(img_dir) else []
    if rendered and not args.no_ocr:
        ocr_engine_kind, engine = detect_ocr()
        if ocr_engine_kind == "none":
            log("未发现 OCR 引擎。扫描页保留为 PNG，请用视觉能力直接读取 images/page-*.png "
                "提取医学信息（如需自动化：pip install paddlepaddle paddleocr，CPU 版即可）")
        else:
            png_paths = [os.path.join(img_dir, n) for n in rendered]
            log(f"OCR 引擎: {ocr_engine_kind}，开始批量识别 {len(rendered)} 张扫描页…")
            batch = ocr_images_batch(ocr_engine_kind, engine, png_paths)
            if batch is None:
                log("OCR 引擎运行失败，扫描页保留为 PNG 供视觉读取")
            else:
                with open(md_path, "a", encoding="utf-8") as fh:
                    fh.write("\n\n## OCR 识别结果（扫描页）\n")
                    for png_name, png_path in zip(rendered, png_paths):
                        page_no = re.sub(r"\D", "", png_name)
                        txt = (batch.get(png_path) or "").strip()
                        if txt:
                            fh.write(f"\n### 第 {page_no} 页\n\n{txt}\n")
                            ocr_done += 1
                        else:
                            fh.write(f"\n### 第 {page_no} 页\n\n（OCR 未识别出文本，请用视觉能力读取 images/{png_name}）\n")

    # ---- 报告
    md_size = os.path.getsize(md_path) if os.path.isfile(md_path) else 0
    if md_size == 0 and not rendered:
        log("未提取到任何内容（无文本、无图片）")
        return EXIT_EMPTY

    report = {
        "input": pdf_path,
        "pages": n_pages,
        "text_pages": text_pages,
        "scan_pages": scan_pages,
        "method": method,
        "ocr_engine": ocr_engine_kind,
        "ocr_pages_done": ocr_done,
        "dpi": args.dpi,
        "output": {
            "markdown": md_path,
            "images": [os.path.join(img_dir, n) for n in rendered],
        },
    }
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    log(f"完成：{md_path}（{md_size} 字节）"
        + (f"；扫描页图片 {len(rendered)} 张 → {img_dir}" if rendered else ""))
    print(json.dumps(report, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
