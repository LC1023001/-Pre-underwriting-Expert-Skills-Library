#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gen Re CLUE 疾病核保评点搜索工具
用法:
  python search_disease.py --query "心房颤动"
  python search_disease.py --query "心房颤动" --system "循环系统"
  python search_disease.py --query "I49.8"   # ICD代码搜索
  python search_disease.py --list             # 列出所有疾病名
"""
import sys
import io
import re
import argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

KNOWLEDGE_DIR = Path(r"c:\Users\lucha\WorkBuddy\20260423214913\genre_knowledge")

# 知识库文件与系统映射
SYSTEM_FILES = {
    "循环系统": "循环系统.md",
    "肿瘤": "肿瘤.md",
    "神经系统": "神经系统.md",
    "精神和行为障碍": "精神和行为障碍.md",
    "内分泌系统和新陈代谢": "内分泌系统和新陈代谢.md",
    "消化系统": "消化系统.md",
    "泌尿生殖系统": "泌尿生殖系统.md",
    "血液和免疫系统": "血液和免疫系统.md",
    "呼吸系统": "呼吸系统.md",
    "传染性和寄生性疾病": "传染性和寄生性疾病.md",
    "肌肉骨骼系统和结缔组织": "肌肉骨骼系统和结缔组织.md",
    "皮肤和皮下组织": "皮肤和皮下组织.md",
    "损伤中毒和外部原因": "损伤_中毒和外部原因.md",
    "妊娠和分娩": "妊娠和分娩.md",
    "眼": "眼.md",
    "耳": "耳.md",
    "先天性畸形和染色体异常": "先天性畸形和染色体异常.md",
    "症状体征和异常发现": "症状_体征和异常发现.md",
    "业余爱好和嗜好": "业余爱好和嗜好.md",
    "旅行与居住地": "旅行与居住地.md",
    "职业核保": "职业核保.md",
    "财务核保": "财务核保.md",
    "ICD-10分类": "ICD-10分类.md",
    "罕见疾病": "罕见疾病.md",
    "影响健康状况的因素": "影响健康状况的因素.md",
    "其他": "其他.md",
}


def clean_nav_text(text: str) -> str:
    """清理导航文字（面包屑）— 保留核心评点内容"""
    nav_markers = [
        "首页\n医学核保\n评点",
        "首页\n计算器\n医学核保",
        "计算器\n医学核保",
    ]
    for marker in nav_markers:
        idx = text.find(marker)
        if idx != -1:
            # 找到导航结束的位置（通常是评点表/一般信息后，实际内容开始）
            end_nav = text.find("评点表\n", idx)
            if end_nav == -1:
                end_nav = text.find("一般信息\n", idx)
            if end_nav != -1:
                # 跳过导航区域，找下一个疾病名重复出现的位置
                after_nav = text[end_nav:]
                lines = after_nav.split("\n")
                # 跳过"评点表"行和重复标题行
                content_start = 0
                for i, line in enumerate(lines):
                    if i > 2 and line.strip() and not line.strip().startswith("首页"):
                        content_start = i
                        break
                text = "\n".join(lines[content_start:])
                break
    return text


def extract_sections(filepath: Path) -> list[dict]:
    """从md文件中提取各个疾病条目"""
    content = filepath.read_text(encoding="utf-8", errors="replace")
    sections = []

    # 按 ## 标题分割
    parts = re.split(r"\n## ", content)
    for part in parts[1:]:  # 跳过文件头
        lines = part.strip().split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:])
        # 清理导航文字
        body_clean = clean_nav_text(body)
        sections.append({"title": title, "body": body_clean, "raw_body": body})
    return sections


def search_in_file(filepath: Path, query: str, max_results: int = 5) -> list[dict]:
    """在单个文件中搜索"""
    results = []
    sections = extract_sections(filepath)
    query_lower = query.lower()

    for sec in sections:
        title_lower = sec["title"].lower()
        body_lower = sec["body"].lower()

        # 计算相关性得分
        score = 0
        if query_lower in title_lower:
            score += 10
            if title_lower.startswith(query_lower):
                score += 5
        if query_lower in body_lower:
            score += 3
            # ICD代码匹配
            if re.search(r"[A-Z]\d{2}", query, re.I) and query_lower in body_lower:
                score += 5

        if score > 0:
            results.append(
                {
                    "file": filepath.name,
                    "title": sec["title"],
                    "score": score,
                    "body": sec["body"],
                }
            )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def search_all(query: str, system: str = None, max_results: int = 8) -> list[dict]:
    """全库搜索"""
    all_results = []

    if system:
        # 指定系统搜索
        fname = SYSTEM_FILES.get(system)
        if fname:
            fp = KNOWLEDGE_DIR / fname
            if fp.exists():
                all_results = search_in_file(fp, query, max_results)
        if not all_results:
            print(f"[提示] 在 '{system}' 中未找到结果，切换到全库搜索...")
            system = None

    if not system:
        for sys_name, fname in SYSTEM_FILES.items():
            fp = KNOWLEDGE_DIR / fname
            if fp.exists():
                results = search_in_file(fp, query, max_results=3)
                for r in results:
                    r["system"] = sys_name
                all_results.extend(results)

        all_results.sort(key=lambda x: x["score"], reverse=True)
        all_results = all_results[:max_results]

    return all_results


def format_result(result: dict, show_full: bool = False) -> str:
    """格式化单个搜索结果"""
    lines = []
    system_info = f" [{result.get('system', result.get('file', ''))}]" if result.get("system") else ""
    lines.append(f"\n{'='*60}")
    lines.append(f"## {result['title']}{system_info}  (相关度: {result['score']})")
    lines.append("=" * 60)

    body = result["body"]
    # 提取核心内容
    if not show_full:
        # 找关键段落：核保要求、寿险、收入保障、健康险
        key_sections = []
        for keyword in ["核保要求", "寿险", "收入保障", "健康险", "末次更新", "Last updated", "预后", "治疗", "诊断"]:
            idx = body.find(keyword)
            if idx != -1:
                start = max(0, idx - 20)
                excerpt = body[start: idx + 500].strip()
                if excerpt not in " ".join(key_sections):
                    key_sections.append(excerpt[:500])

        if key_sections:
            lines.append("\n".join(key_sections[:6]))
        else:
            lines.append(body[:1000])
    else:
        lines.append(body)

    return "\n".join(lines)


def list_all_diseases() -> None:
    """列出所有疾病名称"""
    total = 0
    for sys_name, fname in SYSTEM_FILES.items():
        fp = KNOWLEDGE_DIR / fname
        if fp.exists():
            sections = extract_sections(fp)
            if sections:
                print(f"\n【{sys_name}】({len(sections)}条)")
                for s in sections:
                    title = s["title"]
                    if not title.startswith("20") and len(title) < 60:
                        print(f"  - {title}")
                        total += 1
    print(f"\n共计 {total} 个疾病/条目")


def main():
    parser = argparse.ArgumentParser(
        description="Gen Re CLUE 核保评点搜索",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python search_disease.py --query "心房颤动"
  python search_disease.py --query "糖尿病" --system "内分泌系统和新陈代谢"
  python search_disease.py --query "I49.8"
  python search_disease.py --query "乳腺癌" --full
  python search_disease.py --list
        """,
    )
    parser.add_argument("--query", "-q", type=str, help="搜索疾病名称或ICD代码")
    parser.add_argument("--system", "-s", type=str, help="限定系统（如：循环系统、肿瘤、神经系统）")
    parser.add_argument("--full", "-f", action="store_true", help="显示完整内容")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有疾病名称")
    parser.add_argument("--max", "-n", type=int, default=5, help="最多显示结果数（默认5）")

    args = parser.parse_args()

    if args.list:
        list_all_diseases()
        return

    if not args.query:
        parser.print_help()
        return

    print(f"\n🔍 Gen Re CLUE 核保手册搜索")
    print(f"   查询: {args.query}")
    if args.system:
        print(f"   系统: {args.system}")
    print(f"   知识库: {KNOWLEDGE_DIR}")

    results = search_all(args.query, system=args.system, max_results=args.max)

    if not results:
        print(f"\n❌ 未找到与 '{args.query}' 相关的核保评点。")
        print("建议：")
        print("  1. 尝试中文同义词（如：房颤→心房颤动）")
        print("  2. 使用 --list 查看所有可用疾病名")
        print("  3. 搜索ICD代码（如：I48）")
        return

    print(f"\n找到 {len(results)} 个相关结果：\n")
    for result in results:
        print(format_result(result, show_full=args.full))

    print(f"\n{'='*60}")
    print(f"数据来源：Gen Re CLUE 核保手册（截止2026年3月）")
    print(f"注意：仅供内部学习参考，不得对外传播")


if __name__ == "__main__":
    main()
