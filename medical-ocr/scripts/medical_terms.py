#!/usr/bin/env python3
"""
医学术语后处理模块
用于OCR识别结果的术语校验和标准化
"""

import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass


@dataclass
class TermCorrection:
    """术语修正结果"""
    original: str
    corrected: str
    reason: str


class MedicalTermProcessor:
    """
    医学术语处理器

    功能：
    - 术语标准化
    - 单位换算
    - 异常值检测
    - 格式规范化

    使用示例：
    ```python
    processor = MedicalTermProcessor()
    result = processor.correct_term("血唐", "血糖检测")
    print(result.corrected)  # "血糖"
    ```
    """

    def __init__(self):
        """初始化医学术语处理器"""
        self._init_term_dict()
        self._init_unit_dict()

    def _init_term_dict(self):
        """初始化术语词典"""
        # 常见错误映射
        self.term_corrections: Dict[str, str] = {
            # 血常规
            "血唐": "血糖",
            "血溏": "血糖",
            "红细胸": "红细胞",
            "白细胸": "白细胞",
            "血小扳": "血小板",
            "中性籲": "中性粒",
            "中性籲细胸": "中性粒细胞",
            "淋巴细胸": "淋巴细胞",

            # 肝功能
            "谷丙专氨酶": "谷丙转氨酶",
            "谷草专氨酶": "谷草转氨酶",
            "总胆红素": "总胆红素",
            "碱性磷酸晦": "碱性磷酸酶",
            "Y-谷氨酰转肽晦": "γ-谷氨酰转肽酶",
            "r-谷氨酰转肽晦": "γ-谷氨酰转肽酶",

            # 肾功能
            "肌酉": "肌酐",
            "尿素氮": "尿素氮",

            # 血脂
            "胆固醉": "胆固醇",
            "甘油三酯": "甘油三酯",
            "高密度脂蛋白": "高密度脂蛋白",
            "低密度脂蛋白": "低密度脂蛋白",

            # 常见医学词汇
            "住院": "住院",
            "出院": "出院",
            "病历": "病历",
            "诊断": "诊断",
            "治疗": "治疗",
            "检查": "检查",
            "报告": "报告",
            "结果": "结果",

            # 单位混淆
            "mmol/L": "mmol/L",
            "mg/dL": "mg/dL",
            "μmol/L": "μmol/L",
            "g/L": "g/L",
        }

        # 医学术语同义词
        self.synonyms: Dict[str, str] = {
            "ALT": "谷丙转氨酶",
            "AST": "谷草转氨酶",
            "ALP": "碱性磷酸酶",
            "GGT": "γ-谷氨酰转肽酶",
            "TBIL": "总胆红素",
            "DBIL": "直接胆红素",
            "Cr": "肌酐",
            "BUN": "尿素氮",
            "UA": "尿酸",
            "TC": "总胆固醇",
            "TG": "甘油三酯",
            "HDL": "高密度脂蛋白",
            "LDL": "低密度脂蛋白",
            "FPG": "空腹血糖",
            "2hPBG": "餐后2小时血糖",
            "HbA1c": "糖化血红蛋白",
            "RBC": "红细胞计数",
            "WBC": "白细胞计数",
            "PLT": "血小板计数",
            "HGB": "血红蛋白",
        }

    def _init_unit_dict(self):
        """初始化单位字典"""
        # 正常值范围
        self.reference_ranges: Dict[str, Tuple[str, str, str]] = {
            # 血糖 (mmol/L)
            "空腹血糖": ("3.9", "6.1", "mmol/L"),
            "餐后2小时血糖": ("3.9", "7.8", "mmol/L"),
            "血糖": ("3.9", "6.1", "mmol/L"),

            # 肝功能
            "谷丙转氨酶": ("0", "40", "U/L"),
            "谷草转氨酶": ("0", "40", "U/L"),
            "碱性磷酸酶": ("40", "150", "U/L"),
            "γ-谷氨酰转肽酶": ("0", "50", "U/L"),

            # 肾功能
            "肌酐": ("44", "133", "μmol/L"),
            "尿素氮": ("2.6", "7.5", "mmol/L"),
            "尿酸": ("150", "440", "μmol/L"),

            # 血脂
            "总胆固醇": ("0", "5.2", "mmol/L"),
            "甘油三酯": ("0", "1.7", "mmol/L"),
            "高密度脂蛋白": ("1.0", "∞", "mmol/L"),
            "低密度脂蛋白": ("0", "3.4", "mmol/L"),

            # 血常规
            "血红蛋白": ("110", "160", "g/L"),
            "红细胞计数": ("3.5", "5.5", "10^12/L"),
            "白细胞计数": ("4.0", "10.0", "10^9/L"),
            "血小板计数": ("100", "300", "10^9/L"),
        }

    def correct_term(self, text: str, context: str = "") -> TermCorrection:
        """
        修正术语

        Args:
            text: 原始文本
            context: 上下文

        Returns:
            TermCorrection: 修正结果
        """
        # 检查是否需要修正
        if text in self.term_corrections:
            return TermCorrection(
                original=text,
                corrected=self.term_corrections[text],
                reason="术语标准化"
            )

        # 检查同义词
        if text.upper() in self.synonyms:
            return TermCorrection(
                original=text,
                corrected=self.synonyms[text.upper()],
                reason="缩写展开"
            )

        return TermCorrection(
            original=text,
            corrected=text,
            reason=""
        )

    def process_text(self, text: str) -> str:
        """
        处理整段文本

        Args:
            text: 原始文本

        Returns:
            str: 处理后的文本
        """
        result = text

        # 修正术语
        for wrong, correct in self.term_corrections.items():
            result = result.replace(wrong, correct)

        # 展开缩写
        for abbr, full in self.synonyms.items():
            # 保持大小写一致
            pattern = re.compile(re.escape(abbr), re.IGNORECASE)
            result = pattern.sub(full, result)

        # 规范化单位格式
        result = self._normalize_units(result)

        return result

    def _normalize_units(self, text: str) -> str:
        """规范化单位格式"""
        # 统一μ符号
        text = text.replace("u", "μ")

        # 统一百分比格式
        text = text.replace("％", "%")

        # 统一上下标
        text = text.replace("²", "^2")
        text = text.replace("³", "^3")

        return text

    def extract_values(self, text: str) -> List[Dict[str, str]]:
        """
        提取数值

        Args:
            text: 文本

        Returns:
            List[Dict]: 提取的数值列表
        """
        results = []

        # 模式: 指标名 + 数值 + 单位
        pattern = r'([\u4e00-\u9fa5A-Za-z]+)[:：]?\s*([<>]?\s*\d+\.?\d*)\s*([A-Za-z/μ^²³%]+)?'

        matches = re.finditer(pattern, text)

        for match in matches:
            indicator = match.group(1).strip()
            value = match.group(2).strip()
            unit = match.group(3).strip() if match.group(3) else ""

            results.append({
                "indicator": indicator,
                "value": value,
                "unit": unit,
                "raw": match.group(0)
            })

        return results

    def check_abnormal(self, indicator: str, value: float) -> Tuple[bool, str]:
        """
        检查数值是否异常

        Args:
            indicator: 指标名
            value: 数值

        Returns:
            (is_abnormal, status): 是否异常, 状态描述
        """
        # 查找参考范围
        for key in self.reference_ranges:
            if key in indicator:
                low, high, unit = self.reference_ranges[key]

                low_val = float(low) if low != "0" else float('-inf')
                high_val = float(high) if high != "∞" else float('inf')

                if value < low_val:
                    return True, "偏低"
                elif value > high_val:
                    return True, "偏高"
                else:
                    return False, "正常"

        return False, "范围未知"


class BloodTestParser:
    """
    血液检查报告解析器

    专门用于解析血常规、生化检查等报告
    """

    def __init__(self):
        self.processor = MedicalTermProcessor()

    def parse_report(self, text: str) -> Dict:
        """
        解析血液检查报告

        Args:
            text: OCR识别的报告文本

        Returns:
            Dict: 结构化的报告数据
        """
        result = {
            "patient_info": {},
            "test_items": [],
            "summary": {}
        }

        # 提取患者信息
        result["patient_info"] = self._extract_patient_info(text)

        # 提取检测项目
        result["test_items"] = self.processor.extract_values(text)

        # 异常值汇总
        abnormal_items = []
        for item in result["test_items"]:
            try:
                value = float(item["value"])
                is_abnormal, status = self.processor.check_abnormal(
                    item["indicator"], value
                )
                if is_abnormal:
                    abnormal_items.append({
                        **item,
                        "status": status
                    })
            except ValueError:
                pass

        result["summary"]["abnormal_items"] = abnormal_items
        result["summary"]["total_items"] = len(result["test_items"])
        result["summary"]["abnormal_count"] = len(abnormal_items)

        return result

    def _extract_patient_info(self, text: str) -> Dict:
        """提取患者基本信息"""
        info = {}

        # 姓名
        name_match = re.search(r'姓名[：:]\s*([^\n]+)', text)
        if name_match:
            info["name"] = name_match.group(1).strip()

        # 性别
        gender_match = re.search(r'性别[：:]\s*([男女])', text)
        if gender_match:
            info["gender"] = gender_match.group(1)

        # 年龄
        age_match = re.search(r'年龄[：:]\s*(\d+)', text)
        if age_match:
            info["age"] = int(age_match.group(1))

        # 日期
        date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)', text)
        if date_match:
            info["date"] = date_match.group(1)

        return info


def main():
    """命令行测试"""
    processor = MedicalTermProcessor()

    # 测试术语修正
    print("术语修正测试:")
    test_terms = ["血唐", "谷丙专氨酶", "ALT", "GGT", "肌酉"]
    for term in test_terms:
        result = processor.correct_term(term)
        print(f"  {result.original} -> {result.corrected} ({result.reason})")

    # 测试文本处理
    print("\n文本处理测试:")
    test_text = "血唐检测结果：5.6 mmol/L，ALT 25 U/L，GGT 35 U/L"
    processed = processor.process_text(test_text)
    print(f"  原文: {test_text}")
    print(f"  处理: {processed}")

    # 测试数值提取
    print("\n数值提取测试:")
    values = processor.extract_values(processed)
    for v in values:
        print(f"  {v}")

    # 测试异常值检测
    print("\n异常值检测:")
    for v in values:
        try:
            is_abnormal, status = processor.check_abnormal(v["indicator"], float(v["value"]))
            print(f"  {v['indicator']}: {v['value']} -> {status}")
        except ValueError:
            pass


if __name__ == "__main__":
    main()
