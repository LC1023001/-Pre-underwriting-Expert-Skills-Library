#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kb_tool.py — 核保知识库检索 / 统计 / 指纹工具

用法:
    python kb_tool.py search "甲状腺结节"
    python kb_tool.py search "额外死亡率" --context 3
    python kb_tool.py stats
    python kb_tool.py list
    python kb_tool.py fingerprint          # 生成所有规则条的指纹，供增量去重
    python kb_tool.py snapshot             # 生成本次运行快照到 references/.versions/

设计原则:
    - 零第三方依赖（仅标准库），Windows 环境可直接运行
    - UTF-8 全链路，兼容中文路径
"""
import argparse
import hashlib
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_DIR = SKILL_DIR / "references"
VERSIONS_DIR = REF_DIR / ".versions"
CHANGELOG = SKILL_DIR / "CHANGELOG.md"


def iter_md_files():
    """返回 references 目录下的规则 md 文件（不含 .versions 子目录）。"""
    if not REF_DIR.exists():
        return []
    return sorted(
        p for p in REF_DIR.glob("*.md") if p.is_file()
    )


def read_text(path):
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


# ---------------------------------------------------------------- search

def cmd_search(args):
    pattern = args.query
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        rx = re.compile(re.escape(pattern), re.IGNORECASE)

    total = 0
    for path in iter_md_files():
        lines = read_text(path).splitlines()
        hits = [i for i, ln in enumerate(lines) if rx.search(ln)]
        if not hits:
            continue
        print(f"\n{'=' * 70}")
        print(f"  {path.name}   命中 {len(hits)} 处")
        print(f"{'=' * 70}")
        shown = 0
        for i in hits:
            if shown >= args.max_per_file:
                print(f"  ... 还有 {len(hits) - shown} 处命中（用 --max-per-file 调整）")
                break
            lo = max(0, i - args.context)
            hi = min(len(lines), i + args.context + 1)
            for j in range(lo, hi):
                mark = ">>" if j == i else "  "
                print(f"{mark} {j + 1:5d} | {lines[j]}")
            print()
            shown += 1
        total += len(hits)

    print(f"\n合计命中 {total} 处（{pattern}）")
    if total == 0:
        print("提示：可尝试更短的关键词，或用 `list` 查看文件清单。")
    return 0


# ---------------------------------------------------------------- stats

def cmd_stats(args):
    files = iter_md_files()
    print("\n核保知识库统计")
    print("=" * 74)
    print(f"{'文件':<46}{'行数':>8}{'字数':>10}{'表格':>8}")
    print("-" * 74)

    t_lines = t_chars = t_tables = 0
    for p in files:
        txt = read_text(p)
        lines = txt.count("\n") + 1
        chars = len(txt)
        tables = len(re.findall(r"^\|.*\|$", txt, re.M))
        t_lines += lines
        t_chars += chars
        t_tables += tables
        name = p.name
        if len(name) > 44:
            name = name[:41] + "..."
        print(f"{name:<46}{lines:>8}{chars:>10}{tables:>8}")

    print("-" * 74)
    print(f"{'合计 ' + str(len(files)) + ' 个文件':<46}{t_lines:>8}{t_chars:>10}{t_tables:>8}")

    # 可信度分布
    conf = {"A": 0, "B": 0, "C": 0, "D": 0}
    for p in files:
        for m in re.finditer(r"可信度\s*\*{0,2}([ABCD])\*{0,2}", read_text(p)):
            conf[m.group(1)] += 1
    print("\n可信度标注分布（条目级）")
    print(f"  A 权威 : {conf['A']}")
    print(f"  B 可靠 : {conf['B']}")
    print(f"  C 参考 : {conf['C']}")
    print(f"  D 待核 : {conf['D']}")

    # 待核实条目
    if CHANGELOG.exists():
        cl = read_text(CHANGELOG)
        pending = len(re.findall(r"\*\*T-\d+\*\*", cl))
        print(f"\nCHANGELOG 待核实条目：{pending} 条")
    print()
    return 0


# ---------------------------------------------------------------- list

def cmd_list(args):
    print("\nreferences/ 规则文件：")
    for p in iter_md_files():
        print(f"  - {p.name}")
    print("\n其他：")
    print(f"  - {SKILL_DIR.name}/SKILL.md")
    print(f"  - {SKILL_DIR.name}/CHANGELOG.md")
    print(f"  - {SKILL_DIR.name}/scripts/{Path(__file__).name}\n")
    return 0


# ---------------------------------------------------------------- fingerprint

FINGERPRINT_SKIP = re.compile(r"^\s*[#>\-\s]*$")


def _fingerprints():
    """对每个 md 中的表格数据行与加粗要点行生成指纹。"""
    fps = {}
    for p in iter_md_files():
        for ln in read_text(p).splitlines():
            s = ln.strip()
            if not s or FINGERPRINT_SKIP.match(s):
                continue
            # 表格数据行（含中文或数字，且不是分隔行）
            is_table = s.startswith("|") and "---" not in s
            # 加粗要点
            is_bullet = bool(re.match(r"^[-*]\s|^\*\*", s))
            if not (is_table or is_bullet):
                continue
            key = re.sub(r"\s+", "", s)
            if len(key) < 12:
                continue
            fp = hashlib.md5(key.encode("utf-8")).hexdigest()[:10]
            fps.setdefault(fp, []).append((p.name, s[:100]))
    return fps


def cmd_fingerprint(args):
    fps = _fingerprints()
    print(f"\n共生成 {len(fps)} 个唯一指纹\n")
    out = REF_DIR / ".fingerprints.txt"
    with out.open("w", encoding="utf-8") as f:
        for fp, items in sorted(fps.items()):
            name, sample = items[0]
            f.write(f"{fp}\t{name}\t{sample}\n")
    print(f"已写入：{out}")
    print("用途：下次巡检时对比新内容的指纹，命中的即为已存在条目（丢弃），未命中的为新增候选。\n")
    return 0


# ---------------------------------------------------------------- snapshot

def cmd_snapshot(args):
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    dest = VERSIONS_DIR / f"{today}.md"

    lines = [
        f"# 核保知识库快照 · {today}",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 文件清单",
        "",
    ]
    for p in iter_md_files():
        txt = read_text(p)
        lines.append(
            f"- `{p.name}` — {txt.count(chr(10)) + 1} 行 / {len(txt)} 字"
            f" / md5={hashlib.md5(txt.encode('utf-8')).hexdigest()[:12]}"
        )
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n快照已生成：{dest}\n")
    return 0


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="核保知识库检索 / 统计 / 指纹工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd")

    p1 = sub.add_parser("search", help="全文检索")
    p1.add_argument("query", help="检索关键词（支持正则）")
    p1.add_argument("--context", type=int, default=1, help="上下文行数，默认 1")
    p1.add_argument("--max-per-file", type=int, default=12, help="每文件最多显示命中数")
    p1.set_defaults(func=cmd_search)

    p2 = sub.add_parser("stats", help="知识库统计")
    p2.set_defaults(func=cmd_stats)

    p3 = sub.add_parser("list", help="列出文件")
    p3.set_defaults(func=cmd_list)

    p4 = sub.add_parser("fingerprint", help="生成条目指纹（增量去重用）")
    p4.set_defaults(func=cmd_fingerprint)

    p5 = sub.add_parser("snapshot", help="生成版本快照")
    p5.set_defaults(func=cmd_snapshot)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
