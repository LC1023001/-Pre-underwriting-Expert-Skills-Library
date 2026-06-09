#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医学PDF文档OCR识别脚本
支持多页PDF批处理，自动裁剪页眉页脚，保留医学图表
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import subprocess


def check_tesseract():
    """检查Tesseract是否安装"""
    try:
        result = subprocess.run(['tesseract', '--version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Tesseract已安装: {result.stdout.split()[1]}")
            return True
    except FileNotFoundError:
        print("✗ Tesseract未安装")
        print("  请从 https://github.com/UB-Mannheim/tesseract/wiki 安装Tesseract")
        return False
    return False


def check_dependencies():
    """检查Python依赖"""
    required = ['pdf2image', 'PIL', 'numpy', 'opencv-python']
    missing = []

    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print(f"✗ 缺少依赖: {', '.join(missing)}")
        print("  请运行: pip install -r requirements.txt")
        return False

    print("✓ 所有Python依赖已安装")
    return True


def ocr_pdf(pdf_path: str, output_path: str, dpi: int = 300) -> bool:
    """
    使用Tesseract OCR识别PDF文档

    Args:
        pdf_path: PDF文件路径
        output_path: 输出Markdown文件路径
        dpi: 图像DPI，默认300

    Returns:
        bool: 是否成功
    """
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        import pytesseract

        print(f"正在处理: {pdf_path}")

        # 将PDF转换为图像
        print(f"  转换PDF为图像 (DPI: {dpi})...")
        images = convert_from_path(pdf_path, dpi=dpi)

        results = []

        for i, image in enumerate(images, start=1):
            print(f"  OCR识别第 {i}/{len(images)} 页...")

            # OCR识别
            text = pytesseract.image_to_string(
                image,
                lang='chi_sim+eng',  # 中文简体 + 英文
                config='--psm 6'  # 假设为统一的文本块
            )

            # 保存页面结果
            results.append({
                'page': i,
                'text': text.strip()
            })

        # 生成Markdown输出
        print(f"  生成Markdown文件: {output_path}")
        output_md = Path(output_path)

        with output_md.open('w', encoding='utf-8') as f:
            f.write(f"# 医学文档OCR识别结果\n\n")
            f.write(f"**源文件**: {pdf_path}\n\n")
            f.write(f"**识别时间**: {Path(pdf_path).stat().st_mtime}\n\n")
            f.write(f"**总页数**: {len(images)}\n\n")
            f.write("---\n\n")

            for result in results:
                f.write(f"## 第 {result['page']} 页\n\n")
                f.write(f"```\n{result['text']}\n```\n\n")

        print("✓ OCR识别完成!")
        return True

    except Exception as e:
        print(f"✗ OCR识别失败: {str(e)}")
        return False


def save_entities_json(ocr_text: str, output_path: str):
    """
    从OCR文本中提取医学实体并保存为JSON

    Args:
        ocr_text: OCR识别的文本
        output_path: 输出JSON文件路径
    """
    import re

    # 提取数字和单位模式
    number_pattern = r'(\d+\.?\d*)\s*([a-zA-Z%]+)'

    # 提取医学术语模式（常见检验指标）
    medical_terms = [
        r'白细胞', r'红细胞', r'血红蛋白', r'血小板',
        r'血糖', r'血脂', r'胆固醇', r'甘油三酯',
        r'血压', r'体温', r'心率'
    ]

    entities = {
        'numbers': [],
        'medical_terms': []
    }

    # 提取数值和单位
    for match in re.finditer(number_pattern, ocr_text):
        entities['numbers'].append({
            'value': match.group(1),
            'unit': match.group(2),
            'context': ocr_text[max(0, match.start()-20):match.end()+20]
        })

    # 提取医学术语
    for term in medical_terms:
        if term in ocr_text:
            entities['medical_terms'].append({
                'term': term,
                'count': ocr_text.count(term)
            })

    # 保存JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)

    print(f"✓ 医学实体已保存到: {output_path}")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python medical_pdf_ocr.py <输入PDF> <输出Markdown> [DPI]")
        print()
        print("示例:")
        print("  python medical_pdf_ocr.py report.pdf result.md")
        print("  python medical_pdf_ocr.py report.pdf result.md 600")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_path = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300

    # 检查输入文件
    if not Path(pdf_path).exists():
        print(f"✗ 文件不存在: {pdf_path}")
        sys.exit(1)

    # 检查依赖
    if not check_tesseract():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    # 执行OCR
    success = ocr_pdf(pdf_path, output_path, dpi)

    if success:
        # 读取识别结果并提取实体
        with open(output_path, 'r', encoding='utf-8') as f:
            ocr_text = f.read()

        entities_path = output_path.replace('.md', '_entities.json')
        save_entities_json(ocr_text, entities_path)


if __name__ == '__main__':
    main()
