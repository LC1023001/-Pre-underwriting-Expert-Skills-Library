#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从OCR识别结果中提取医学实体
提取检验指标、数值、参考范围等关键信息
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


# 常见医学检验指标字典
MEDICAL_INDICATORS = {
    # 血常规
    'WBC': '白细胞',
    'RBC': '红细胞',
    'HGB': '血红蛋白',
    'HCT': '红细胞压积',
    'MCV': '平均红细胞体积',
    'MCH': '平均红细胞血红蛋白',
    'MCHC': '平均红细胞血红蛋白浓度',
    'PLT': '血小板',
    'NEUT': '中性粒细胞',
    'LYM': '淋巴细胞',
    'MON': '单核细胞',
    'EOS': '嗜酸性粒细胞',
    'BAS': '嗜碱性粒细胞',

    # 生化指标
    'GLU': '血糖',
    'ALT': '丙氨酸转氨酶',
    'AST': '天门冬氨酸转氨酶',
    'ALP': '碱性磷酸酶',
    'GGT': '谷氨酰转肽酶',
    'TP': '总蛋白',
    'ALB': '白蛋白',
    'GLO': '球蛋白',
    'TC': '总胆固醇',
    'TG': '甘油三酯',
    'HDL': '高密度脂蛋白',
    'LDL': '低密度脂蛋白',
    'BUN': '尿素氮',
    'CRE': '肌酐',
    'UA': '尿酸',
    'Ca': '钙',
    'P': '磷',
    'K': '钾',
    'Na': '钠',
    'Cl': '氯',

    # 凝血功能
    'PT': '凝血酶原时间',
    'APTT': '活化部分凝血活酶时间',
    'TT': '凝血酶时间',
    'FIB': '纤维蛋白原',

    # 心血管指标
    'SBP': '收缩压',
    'DBP': '舒张压',
    'HR': '心率',
    'TC': '总胆固醇',
    'LDL-C': '低密度脂蛋白胆固醇',
    'HDL-C': '高密度脂蛋白胆固醇',
}


class MedicalEntityExtractor:
    """医学实体提取器"""

    def __init__(self):
        self.indicators = MEDICAL_INDICATORS

    def extract_test_results(self, text: str) -> List[Dict[str, Any]]:
        """
        提取检验结果

        Args:
            text: OCR识别的文本

        Returns:
            检验结果列表
        """
        results = []

        # 匹配模式：指标名称 + 数值 + 单位
        # 支持中文和英文指标名称
        pattern = r'([A-Z]{2,4}|[\u4e00-\u9fa5]{2,6})\s*[:：]?\s*(\d+\.?\d*)\s*([a-zA-Z%/μL×10⁹/L]+)'

        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            indicator = match.group(1)
            value = float(match.group(2))
            unit = match.group(3)

            # 查找对应的中文指标名称
            indicator_cn = self.indicators.get(indicator.upper(), indicator)

            results.append({
                'indicator': indicator,
                'indicator_cn': indicator_cn,
                'value': value,
                'unit': unit,
                'context': text[max(0, match.start()-20):match.end()+20]
            })

        return results

    def extract_reference_ranges(self, text: str) -> List[Dict[str, str]]:
        """
        提取参考范围

        Args:
            text: OCR识别的文本

        Returns:
            参考范围列表
        """
        ranges = []

        # 匹配参考范围模式
        patterns = [
            r'参考范围\s*[:：]\s*([\d.]+[-~－到至][\d.]+)',
            r'正常值\s*[:：]\s*([\d.]+[-~－到至][\d.]+)',
            r'Reference\s*[:：]\s*([\d.]+[-~－to][\d.]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                range_str = match.group(1)
                ranges.append({
                    'range': range_str,
                    'context': text[max(0, match.start()-30):match.end()+30]
                })

        return ranges

    def extract_diagnosis(self, text: str) -> List[str]:
        """
        提取诊断结论

        Args:
            text: OCR识别的文本

        Returns:
            诊断列表
        """
        diagnoses = []

        # 常见诊断关键词
        keywords = ['诊断', '结论', '意见', '建议', 'impression', 'diagnosis', 'conclusion']

        for keyword in keywords:
            # 查找关键词后的内容
            pattern = rf'{keyword}\s*[:：]?\s*(.*?)(?:\n|$)'
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                diagnosis = match.group(1).strip()
                if diagnosis and len(diagnosis) > 2:
                    diagnoses.append(diagnosis)

        return diagnoses

    def extract_patient_info(self, text: str) -> Dict[str, str]:
        """
        提取患者信息

        Args:
            text: OCR识别的文本

        Returns:
            患者信息字典
        """
        info = {}

        # 姓名模式
        name_patterns = [
            r'姓名\s*[:：]\s*([\u4e00-\u9fa5]{2,4})',
            r'Name\s*[:：]\s*([A-Za-z\s]+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                info['name'] = match.group(1).strip()
                break

        # 性别模式
        gender_patterns = [
            r'性别\s*[:：]\s*(男|女|Male|Female|M|F)',
            r'Sex\s*[:：]\s*(男|女|Male|Female|M|F)',
        ]
        for pattern in gender_patterns:
            match = re.search(pattern, text)
            if match:
                info['gender'] = match.group(1).strip()
                break

        # 年龄模式
        age_patterns = [
            r'年龄\s*[:：]\s*(\d+)\s*(岁|years?|y)',
            r'Age\s*[:：]\s*(\d+)\s*(岁|years?|y)',
        ]
        for pattern in age_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['age'] = match.group(1) + '岁'
                break

        return info

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        提取所有医学实体

        Args:
            text: OCR识别的文本

        Returns:
            所有提取的实体
        """
        return {
            'patient_info': self.extract_patient_info(text),
            'test_results': self.extract_test_results(text),
            'reference_ranges': self.extract_reference_ranges(text),
            'diagnoses': self.extract_diagnosis(text),
        }


def save_to_json(entities: Dict[str, Any], output_path: str):
    """将提取的实体保存为JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)


def save_to_markdown(entities: Dict[str, Any], output_path: str):
    """将提取的实体保存为Markdown"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 医学实体提取结果\n\n")

        # 患者信息
        patient_info = entities.get('patient_info', {})
        if patient_info:
            f.write("## 患者信息\n\n")
            for key, value in patient_info.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n")

        # 检验结果
        test_results = entities.get('test_results', [])
        if test_results:
            f.write("## 检验结果\n\n")
            f.write("| 指标 | 指标名称 | 数值 | 单位 |\n")
            f.write("|------|---------|------|------|\n")
            for result in test_results:
                f.write(f"| {result['indicator']} | {result['indicator_cn']} | {result['value']} | {result['unit']} |\n")
            f.write("\n")

        # 参考范围
        reference_ranges = entities.get('reference_ranges', [])
        if reference_ranges:
            f.write("## 参考范围\n\n")
            for i, r in enumerate(reference_ranges, 1):
                f.write(f"{i}. {r['range']}\n")
                f.write(f"   上下文: {r['context']}\n\n")

        # 诊断结论
        diagnoses = entities.get('diagnoses', [])
        if diagnoses:
            f.write("## 诊断结论\n\n")
            for i, diagnosis in enumerate(diagnoses, 1):
                f.write(f"{i}. {diagnosis}\n")


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python extract_medical_entities.py <输入Markdown> <输出文件> [格式]")
        print()
        print("格式:")
        print("  json  - JSON格式（默认）")
        print("  md    - Markdown格式")
        print()
        print("示例:")
        print("  python extract_medical_entities.py ocr_result.md entities.json")
        print("  python extract_medical_entities.py ocr_result.md entities.md md")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else 'json'

    # 检查输入文件
    if not Path(input_path).exists():
        print(f"✗ 文件不存在: {input_path}")
        sys.exit(1)

    # 读取OCR结果
    print(f"正在读取: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 提取医学实体
    print("正在提取医学实体...")
    extractor = MedicalEntityExtractor()
    entities = extractor.extract_all(text)

    # 统计
    print(f"  患者信息字段: {len(entities['patient_info'])}")
    print(f"  检验指标: {len(entities['test_results'])}")
    print(f"  参考范围: {len(entities['reference_ranges'])}")
    print(f"  诊断结论: {len(entities['diagnoses'])}")

    # 保存结果
    print(f"正在保存到: {output_path}")
    if output_format == 'md':
        save_to_markdown(entities, output_path)
    else:
        save_to_json(entities, output_path)

    print("✓ 医学实体提取完成!")


if __name__ == '__main__':
    main()
