#!/usr/bin/env python3
"""
医学文档PDF OCR识别模块
支持扫描版PDF和文本PDF的文字提取
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from PIL import Image

# 尝试导入PDF处理库
PDF_LIBRARIES = {}

try:
    import fitz  # PyMuPDF
    PDF_LIBRARIES['pymupdf'] = True
except ImportError:
    PDF_LIBRARIES['pymupdf'] = False

try:
    import pdfplumber
    PDF_LIBRARIES['pdfplumber'] = True
except ImportError:
    PDF_LIBRARIES['pdfplumber'] = False

try:
    from pdf2image import convert_from_path
    PDF_LIBRARIES['pdf2image'] = True
except ImportError:
    PDF_LIBRARIES['pdf2image'] = False


@dataclass
class PDFOCRResult:
    """PDF OCR识别结果"""
    text: str
    confidence: float
    page_count: int
    pages: List[str] = None  # 每页的文本
    tables: List[List[List[str]]] = None  # 提取的表格
    engine: str = ""
    is_scanned: bool = False

    def __str__(self):
        return f"PDFOCRResult(pages={self.page_count}, text_len={len(self.text)}, scanned={self.is_scanned})"


class PDFOCRProcessor:
    """
    医学文档PDF OCR处理器

    功能：
    - 文本PDF直接提取文字
    - 扫描版PDF转图片后OCR
    - 表格提取
    - 批量处理

    使用示例：
    ```python
    processor = PDFOCRProcessor(engine='paddleocr')
    result = processor.recognize('medical_report.pdf')
    print(result.text)
    ```
    """

    def __init__(
        self,
        engine: str = 'paddleocr',
        lang: str = 'ch',
        dpi: int = 300,
        use_gpu: bool = False
    ):
        """
        初始化PDF OCR处理器

        Args:
            engine: OCR引擎类型 ('paddleocr', 'tesseract', 'easyocr')
            lang: 语言 ('ch' - 中文, 'en' - 英文, 'ch_en' - 中英文混合)
            dpi: PDF转图片的分辨率 (默认300)
            use_gpu: 是否使用GPU加速
        """
        self.engine = engine.lower()
        self.lang = lang
        self.dpi = dpi
        self.use_gpu = use_gpu

        # 导入OCR处理器
        self._ocr = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化OCR处理器"""
        if self.engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch' if self.lang != 'en' else 'en',
                    use_gpu=self.use_gpu,
                    show_log=False
                )
            except ImportError:
                raise ImportError("PaddleOCR未安装，请运行: pip install paddlepaddle paddleocr")

        elif self.engine == 'tesseract':
            try:
                import pytesseract
                self._ocr = None  # Tesseract直接使用
            except ImportError:
                raise ImportError("pytesseract未安装，请运行: pip install pytesseract")

        elif self.engine == 'easyocr':
            try:
                import easyocr
                lang_map = {
                    'ch': ['ch_sim', 'en'],
                    'en': ['en'],
                    'ch_en': ['ch_sim', 'en']
                }
                self._ocr = easyocr.Reader(
                    lang_map.get(self.lang, ['ch_sim', 'en']),
                    gpu=self.use_gpu,
                    verbose=False
                )
            except ImportError:
                raise ImportError("EasyOCR未安装，请运行: pip install easyocr")

    def recognize(
        self,
        pdf_path: str,
        extract_tables: bool = True,
        page_range: Optional[Tuple[int, int]] = None
    ) -> PDFOCRResult:
        """
        识别PDF文档

        Args:
            pdf_path: PDF文件路径
            extract_tables: 是否提取表格
            page_range: 页码范围 (起始页, 结束页)，None表示全部

        Returns:
            PDFOCRResult: 识别结果
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 检查PDF库
        if not any(PDF_LIBRARIES.values()):
            raise ImportError("未安装PDF处理库，请运行: pip install pymupdf pdfplumber pdf2image")

        # 尝试直接提取文本
        text, is_scanned = self._extract_text(pdf_path, page_range)

        if not text.strip() or is_scanned:
            # 如果没有文本或确定是扫描版，进行OCR
            text, pages = self._ocr_pdf(pdf_path, page_range)
            is_scanned = True
        else:
            # 提取每页文本
            pages = self._get_pages_text(pdf_path, page_range)

        # 提取表格
        tables = []
        if extract_tables and PDF_LIBRARIES.get('pdfplumber'):
            tables = self._extract_tables(pdf_path, page_range)

        return PDFOCRResult(
            text=text,
            confidence=0.9 if not is_scanned else 0.85,
            page_count=len(pages),
            pages=pages,
            tables=tables,
            engine=self.engine,
            is_scanned=is_scanned
        )

    def _extract_text(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]]
    ) -> Tuple[str, bool]:
        """
        尝试直接提取PDF文本

        Returns:
            (text, is_scanned): 文本内容，是否为扫描版
        """
        if not PDF_LIBRARIES.get('pymupdf'):
            return "", False

        import fitz

        doc = fitz.open(pdf_path)
        all_text = []
        is_scanned = True  # 假设是扫描版

        start, end = page_range if page_range else (0, len(doc))
        end = min(end, len(doc))

        for page_num in range(start, end):
            page = doc[page_num]
            text = page.get_text()

            if text and len(text.strip()) > 50:
                # 有实质性文本内容，说明不是扫描版
                is_scanned = False
                all_text.append(text)
            else:
                all_text.append("")

        doc.close()
        return "\n\n".join(all_text), is_scanned

    def _get_pages_text(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]]
    ) -> List[str]:
        """获取每页文本"""
        if not PDF_LIBRARIES.get('pymupdf'):
            return []

        import fitz

        doc = fitz.open(pdf_path)
        pages = []

        start, end = page_range if page_range else (0, len(doc))
        end = min(end, len(doc))

        for page_num in range(start, end):
            page = doc[page_num]
            pages.append(page.get_text())

        doc.close()
        return pages

    def _ocr_pdf(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]]
    ) -> Tuple[str, List[str]]:
        """
        对PDF进行OCR识别

        Returns:
            (full_text, pages_text): 完整文本，每页文本列表
        """
        # 将PDF转换为图片
        images = self._pdf_to_images(pdf_path, page_range)

        if not images:
            return "", []

        # 对每张图片进行OCR
        full_text = []
        for img in images:
            text = self._ocr_image(img)
            full_text.append(text)

        return "\n\n".join(full_text), full_text

    def _pdf_to_images(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]]
    ) -> List[Image.Image]:
        """将PDF页面转换为图片"""
        if PDF_LIBRARIES.get('pdf2image'):
            # 使用pdf2image
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=page_range[0] + 1 if page_range else None,
                last_page=page_range[1] if page_range else None
            )
            return images

        elif PDF_LIBRARIES.get('pymupdf'):
            # 使用PyMuPDF
            import fitz
            doc = fitz.open(pdf_path)
            images = []

            start, end = page_range if page_range else (0, len(doc))
            end = min(end, len(doc))

            for page_num in range(start, end):
                page = doc[page_num]
                # 渲染为图片
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)

            doc.close()
            return images

        return []

    def _ocr_image(self, image: Image.Image) -> str:
        """对单张图片进行OCR"""
        if self.engine == 'paddleocr':
            result = self._ocr.ocr(image, cls=True)
            if result and result[0]:
                lines = [line[1][0] for line in result[0] if line]
                return '\n'.join(lines)
            return ""

        elif self.engine == 'tesseract':
            import pytesseract
            lang_map = {
                'ch': 'chi_sim',
                'en': 'eng',
                'ch_en': 'chi_sim+eng'
            }
            return pytesseract.image_to_string(
                image,
                lang=lang_map.get(self.lang, 'chi_sim'),
                config='--oem 3 --psm 6'
            )

        elif self.engine == 'easyocr':
            result = self._ocr.readtext(image)
            return ' '.join([item[1] for item in result])

        return ""

    def _extract_tables(
        self,
        pdf_path: str,
        page_range: Optional[Tuple[int, int]]
    ) -> List[List[List[str]]]:
        """提取PDF中的表格"""
        if not PDF_LIBRARIES.get('pdfplumber'):
            return []

        import pdfplumber

        all_tables = []
        with pdfplumber.open(pdf_path) as pdf:
            start, end = page_range if page_range else (0, len(pdf.pages))
            end = min(end, len(pdf.pages))

            for page_num in range(start, end):
                page = pdf.pages[page_num]
                tables = page.extract_tables()

                if tables:
                    all_tables.extend(tables)

        return all_tables

    def convert_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        image_format: str = 'png'
    ) -> List[str]:
        """
        将PDF转换为图片文件

        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            image_format: 图片格式 ('png', 'jpg')

        Returns:
            List[str]: 生成的图片路径列表
        """
        os.makedirs(output_dir, exist_ok=True)

        if not PDF_LIBRARIES.get('pymupdf'):
            raise ImportError("PyMuPDF未安装，请运行: pip install pymupdf")

        import fitz
        doc = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            output_path = os.path.join(
                output_dir,
                f"page_{page_num + 1:03d}.{image_format}"
            )
            pix.save(output_path)
            image_paths.append(output_path)

        doc.close()
        return image_paths


# 添加缺失的导入
import io


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='医学文档PDF OCR识别')
    parser.add_argument('pdf', help='PDF文件路径')
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
        '-d', '--dpi',
        type=int,
        default=300,
        help='PDF转图片分辨率 (默认: 300)'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径'
    )
    parser.add_argument(
        '--no-tables',
        action='store_true',
        help='不提取表格'
    )

    args = parser.parse_args()

    # 显示可用库
    print("\n可用PDF处理库:")
    for lib, available in PDF_LIBRARIES.items():
        status = "可用" if available else "不可用"
        print(f"  {lib}: {status}")

    # 执行识别
    print(f"\n使用引擎: {args.engine}")
    print(f"PDF文件: {args.pdf}")

    processor = PDFOCRProcessor(
        engine=args.engine,
        lang=args.lang,
        dpi=args.dpi
    )

    result = processor.recognize(
        args.pdf,
        extract_tables=not args.no_tables
    )

    print(f"\n页数: {result.page_count}")
    print(f"是否为扫描版: {'是' if result.is_scanned else '否'}")
    print(f"识别置信度: {result.confidence:.2%}")

    if result.tables:
        print(f"发现 {len(result.tables)} 个表格")

    print("\n识别结果:")
    print("-" * 60)
    print(result.text[:2000] if len(result.text) > 2000 else result.text)
    if len(result.text) > 2000:
        print(f"\n... (共 {len(result.text)} 字符)")
    print("-" * 60)

    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result.text)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
