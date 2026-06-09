#!/usr/bin/env python3
"""
医学文档图片OCR识别模块
支持多种OCR引擎，本地化处理
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple, Union
from enum import Enum

# 尝试导入各种OCR引擎
OCR_ENGINES = {}

try:
    from paddleocr import PaddleOCR
    OCR_ENGINES['paddleocr'] = True
except ImportError:
    OCR_ENGINES['paddleocr'] = False

try:
    import pytesseract
    OCR_ENGINES['tesseract'] = True
except ImportError:
    OCR_ENGINES['tesseract'] = False

try:
    import easyocr
    OCR_ENGINES['easyocr'] = True
except ImportError:
    OCR_ENGINES['easyocr'] = False

try:
    from PIL import Image
    OCR_ENGINES['pil'] = True
except ImportError:
    OCR_ENGINES['pil'] = False


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float
    boxes: List[Tuple[List[Tuple[int, int]], str, float]] = None  # [(box, text, confidence), ...]
    engine: str = ""
    language: str = ""

    def __str__(self):
        return f"OCRResult(text={self.text[:100]}..., confidence={self.confidence:.2f})"


class OCREngine(Enum):
    """支持的OCR引擎"""
    PADDLEOCR = "paddleocr"
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


class OCRProcessor:
    """
    医学文档图片OCR处理器

    支持的引擎：
    - PaddleOCR (推荐): 中文识别效果最好
    - Tesseract: 通用OCR引擎
    - EasyOCR: 多语言支持

    使用示例：
    ```python
    processor = OCRProcessor(engine='paddleocr')
    result = processor.recognize('medical_report.jpg')
    print(result.text)
    ```
    """

    def __init__(
        self,
        engine: str = 'paddleocr',
        lang: str = 'ch',
        use_gpu: bool = False,
        show_log: bool = False
    ):
        """
        初始化OCR处理器

        Args:
            engine: OCR引擎类型 ('paddleocr', 'tesseract', 'easyocr')
            lang: 语言 ('ch' - 中文, 'en' - 英文, 'ch_en' - 中英文混合)
            use_gpu: 是否使用GPU加速
            show_log: 是否显示日志
        """
        self.engine = engine.lower()
        self.lang = lang
        self.use_gpu = use_gpu
        self.show_log = show_log

        # 验证引擎可用性
        if self.engine not in OCR_ENGINES or not OCR_ENGINES[self.engine]:
            available = [k for k, v in OCR_ENGINES.items() if v]
            raise ValueError(
                f"OCR引擎 '{self.engine}' 不可用。"
                f"可用引擎: {available}"
            )

        # 初始化引擎
        self._ocr_engine = None
        self._init_engine()

    def _init_engine(self):
        """初始化OCR引擎"""
        if self.engine == 'paddleocr':
            self._init_paddleocr()
        elif self.engine == 'tesseract':
            self._init_tesseract()
        elif self.engine == 'easyocr':
            self._init_easyocr()

    def _init_paddleocr(self):
        """初始化PaddleOCR"""
        lang_map = {
            'ch': 'ch',
            'en': 'en',
            'ch_en': 'ch'
        }
        paddle_lang = lang_map.get(self.lang, 'ch')

        self._ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang=paddle_lang,
            use_gpu=self.use_gpu,
            show_log=self.show_log
        )
        print(f"PaddleOCR 初始化完成 (语言: {paddle_lang})")

    def _init_tesseract(self):
        """初始化Tesseract"""
        # Tesseract不需要额外初始化，pytesseract直接使用
        print("Tesseract 初始化完成")

    def _init_easyocr(self):
        """初始化EasyOCR"""
        lang_map = {
            'ch': ['ch_sim', 'en'],
            'en': ['en'],
            'ch_en': ['ch_sim', 'en']
        }
        languages = lang_map.get(self.lang, ['ch_sim', 'en'])

        self._ocr_engine = easyocr.Reader(
            languages,
            gpu=self.use_gpu,
            verbose=False
        )
        print(f"EasyOCR 初始化完成 (语言: {languages})")

    def recognize(
        self,
        image_path: str,
        with_confidence: bool = False
    ) -> OCRResult:
        """
        识别单张图片

        Args:
            image_path: 图片路径
            with_confidence: 是否返回详细信息（文本框位置等）

        Returns:
            OCRResult: 识别结果
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        if self.engine == 'paddleocr':
            return self._recognize_paddle(image_path, with_confidence)
        elif self.engine == 'tesseract':
            return self._recognize_tesseract(image_path, with_confidence)
        elif self.engine == 'easyocr':
            return self._recognize_easyocr(image_path, with_confidence)

    def _recognize_paddle(
        self,
        image_path: str,
        with_confidence: bool
    ) -> OCRResult:
        """使用PaddleOCR识别"""
        result = self._ocr_engine.ocr(image_path, cls=True)

        if not result or not result[0]:
            return OCRResult(text="", confidence=0.0, engine=self.engine)

        lines = []
        boxes = []
        total_conf = 0.0
        count = 0

        for line in result[0]:
            if line:
                box = line[0]
                text = line[1][0]
                conf = line[1][1]
                lines.append(text)
                boxes.append((box, text, conf))
                total_conf += conf
                count += 1

        avg_conf = total_conf / count if count > 0 else 0.0
        full_text = '\n'.join(lines)

        return OCRResult(
            text=full_text,
            confidence=avg_conf,
            boxes=boxes if with_confidence else None,
            engine=self.engine,
            language=self.lang
        )

    def _recognize_tesseract(
        self,
        image_path: str,
        with_confidence: bool
    ) -> OCRResult:
        """使用Tesseract识别"""
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)

        # 语言配置
        lang_map = {
            'ch': 'chi_sim',
            'en': 'eng',
            'ch_en': 'chi_sim+eng'
        }
        tesseract_lang = lang_map.get(self.lang, 'chi_sim')

        # OCR配置
        config = '--oem 3 --psm 6'

        if with_confidence:
            data = pytesseract.image_to_data(
                img,
                lang=tesseract_lang,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            # 处理详细结果
            lines = []
            boxes = []
            confs = []
            for i, text in enumerate(data['text']):
                if text.strip():
                    conf = float(data['conf'][i])
                    if conf > 0:
                        x, y, w, h = (
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        )
                        box = [(x, y), (x+w, y), (x+w, y+h), (x, y+h)]
                        lines.append(text)
                        boxes.append((box, text, conf/100))
                        confs.append(conf/100)

            full_text = '\n'.join(lines)
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            return OCRResult(
                text=full_text,
                confidence=avg_conf,
                boxes=boxes,
                engine=self.engine,
                language=self.lang
            )
        else:
            text = pytesseract.image_to_string(
                img,
                lang=tesseract_lang,
                config=config
            )
            return OCRResult(
                text=text.strip(),
                confidence=0.85,  # Tesseract不直接返回置信度
                engine=self.engine,
                language=self.lang
            )

    def _recognize_easyocr(
        self,
        image_path: str,
        with_confidence: bool
    ) -> OCRResult:
        """使用EasyOCR识别"""
        result = self._ocr_engine.readtext(image_path)

        lines = []
        boxes = []
        confs = []

        for detection in result:
            box, text, conf = detection
            lines.append(text)
            confs.append(conf)
            if with_confidence:
                boxes.append((box, text, conf))

        full_text = '\n'.join(lines)
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        return OCRResult(
            text=full_text,
            confidence=avg_conf,
            boxes=boxes if with_confidence else None,
            engine=self.engine,
            language=self.lang
        )

    def recognize_batch(
        self,
        image_paths: List[str],
        with_confidence: bool = False
    ) -> List[OCRResult]:
        """
        批量识别图片

        Args:
            image_paths: 图片路径列表
            with_confidence: 是否返回详细信息

        Returns:
            List[OCRResult]: 识别结果列表
        """
        results = []
        for path in image_paths:
            try:
                result = self.recognize(path, with_confidence)
                results.append(result)
            except Exception as e:
                print(f"识别失败 {path}: {e}")
                results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    engine=self.engine,
                    language=self.lang
                ))
        return results

    @staticmethod
    def list_available_engines() -> dict:
        """列出可用的OCR引擎"""
        return OCR_ENGINES.copy()


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='医学文档图片OCR识别')
    parser.add_argument('image', help='图片文件路径')
    parser.add_argument(
        '-e', '--engine',
        default='paddleocr',
        choices=['paddleocr', 'tesseract', 'easyocr'],
        help='OCR引擎 (默认: paddleocr)'
    )
    parser.add_argument(
        '-l', '--lang',
        default='ch',
        choices=['ch', 'en', 'ch_en'],
        help='语言 (默认: ch)'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细信息'
    )

    args = parser.parse_args()

    # 显示可用引擎
    print("\n可用OCR引擎:")
    for engine, available in OCR_ENGINE.items():
        status = "可用" if available else "不可用"
        print(f"  {engine}: {status}")

    # 执行识别
    print(f"\n使用引擎: {args.engine}")
    print(f"图片文件: {args.image}")

    processor = OCRProcessor(
        engine=args.engine,
        lang=args.lang
    )

    result = processor.recognize(args.image, with_confidence=args.verbose)

    print(f"\n识别置信度: {result.confidence:.2%}")
    print("\n识别结果:")
    print("-" * 60)
    print(result.text)
    print("-" * 60)

    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result.text)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
