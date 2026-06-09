#!/usr/bin/env python3
"""
医学文档摄像头/拍照OCR识别模块
支持实时拍照或图片文件识别
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional, List, Union
from dataclasses import dataclass

# 尝试导入图像处理库
IMAGE_LIBRARIES = {}

try:
    from PIL import Image
    IMAGE_LIBRARIES['pil'] = True
except ImportError:
    IMAGE_LIBRARIES['pil'] = False

try:
    import cv2
    IMAGE_LIBRARIES['cv2'] = True
except ImportError:
    IMAGE_LIBRARIES['cv2'] = False


@dataclass
class CameraOCRResult:
    """摄像头OCR识别结果"""
    text: str
    confidence: float
    image_path: str = ""
    engine: str = ""

    def __str__(self):
        return f"CameraOCRResult(text={self.text[:50]}..., confidence={self.confidence:.2f})"


class CameraOCR:
    """
    摄像头拍照OCR识别器

    功能：
    - 摄像头实时预览和拍照
    - 照片文件OCR识别
    - 图片预处理优化

    使用示例：
    ```python
    camera = CameraOCR(engine='paddleocr')
    result = camera.capture_and_recognize()
    print(result.text)
    ```
    """

    def __init__(
        self,
        engine: str = 'paddleocr',
        lang: str = 'ch',
        use_gpu: bool = False,
        camera_index: int = 0
    ):
        """
        初始化摄像头OCR识别器

        Args:
            engine: OCR引擎类型
            lang: 语言
            use_gpu: 是否使用GPU
            camera_index: 摄像头索引 (默认0)
        """
        self.engine = engine.lower()
        self.lang = lang
        self.use_gpu = use_gpu
        self.camera_index = camera_index

        # 初始化OCR处理器
        self._ocr_processor = None
        self._init_ocr()

    def _init_ocr(self):
        """初始化OCR处理器"""
        if self.engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                self._ocr_processor = PaddleOCR(
                    use_angle_cls=True,
                    lang='ch' if self.lang != 'en' else 'en',
                    use_gpu=self.use_gpu,
                    show_log=False
                )
            except ImportError:
                raise ImportError("PaddleOCR未安装")

        elif self.engine == 'tesseract':
            try:
                import pytesseract
                self._ocr_processor = None  # Tesseract直接使用
            except ImportError:
                raise ImportError("pytesseract未安装")

        elif self.engine == 'easyocr':
            try:
                import easyocr
                lang_map = {
                    'ch': ['ch_sim', 'en'],
                    'en': ['en'],
                    'ch_en': ['ch_sim', 'en']
                }
                self._ocr_processor = easyocr.Reader(
                    lang_map.get(self.lang, ['ch_sim', 'en']),
                    gpu=self.use_gpu,
                    verbose=False
                )
            except ImportError:
                raise ImportError("EasyOCR未安装")

    def recognize_from_file(
        self,
        image_path: str,
        preprocess: bool = True
    ) -> CameraOCRResult:
        """
        识别已有图片文件

        Args:
            image_path: 图片文件路径
            preprocess: 是否进行预处理

        Returns:
            CameraOCRResult: 识别结果
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        # 图片预处理
        if preprocess:
            processed_image = self._preprocess_image(image_path)
        else:
            processed_image = image_path

        # OCR识别
        text = self._ocr_image(processed_image)
        confidence = 0.85  # 默认置信度

        return CameraOCRResult(
            text=text,
            confidence=confidence,
            image_path=image_path,
            engine=self.engine
        )

    def capture_and_recognize(
        self,
        save_capture: bool = False,
        output_dir: Optional[str] = None
    ) -> CameraOCRResult:
        """
        摄像头拍照并识别

        Args:
            save_capture: 是否保存拍摄的照片
            output_dir: 保存目录，None则使用临时目录

        Returns:
            CameraOCRResult: 识别结果
        """
        if not IMAGE_LIBRARIES.get('cv2'):
            raise ImportError("OpenCV未安装，请运行: pip install opencv-python")

        import cv2

        # 打开摄像头
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            raise RuntimeError("无法打开摄像头")

        print("\n摄像头已打开")
        print("按 's' 键拍照并识别")
        print("按 'q' 键退出")

        result = None

        while True:
            # 读取帧
            ret, frame = cap.read()

            if not ret:
                print("无法读取摄像头画面")
                break

            # 显示画面
            cv2.imshow('Medical OCR - Press s to capture, q to quit', frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('s'):
                # 拍照
                print("\n正在处理...")

                # 保存或使用临时文件
                if save_capture:
                    if output_dir is None:
                        output_dir = tempfile.gettempdir()
                    image_path = os.path.join(output_dir, 'capture.jpg')
                else:
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                        image_path = f.name

                # 保存图片
                cv2.imwrite(image_path, frame)
                print(f"图片已保存: {image_path}")

                # 预处理和识别
                processed = self._preprocess_image(image_path)
                text = self._ocr_image(processed)
                confidence = 0.85

                result = CameraOCRResult(
                    text=text,
                    confidence=confidence,
                    image_path=image_path,
                    engine=self.engine
                )

                print(f"\n识别置信度: {confidence:.2%}")
                print("\n识别结果:")
                print("-" * 50)
                print(text if text else "(未识别到文字)")
                print("-" * 50)

                # 如果不需要保存，删除临时文件
                if not save_capture:
                    pass  # 保留文件供后续使用

                break

            elif key == ord('q'):
                print("\n退出")
                break

        # 清理
        cap.release()
        cv2.destroyAllWindows()

        if result is None:
            raise RuntimeError("未进行拍照识别")

        return result

    def _preprocess_image(
        self,
        image_path: str
    ) -> str:
        """
        图像预处理

        包括：灰度化、对比度增强、去噪等

        Args:
            image_path: 原始图片路径

        Returns:
            str: 处理后的图片路径
        """
        if not IMAGE_LIBRARIES.get('cv2'):
            return image_path

        import cv2
        import numpy as np

        # 读取图片
        img = cv2.imread(image_path)

        # 转换为灰度图
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 自适应直方图均衡化 - 增强对比度
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 中值滤波去噪
        denoised = cv2.medianBlur(enhanced, 3)

        # 二值化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 保存处理后的图片
        processed_path = image_path.replace('.jpg', '_processed.jpg')
        cv2.imwrite(processed_path, binary)

        return processed_path

    def _ocr_image(self, image_path: str) -> str:
        """对图片进行OCR识别"""
        from PIL import Image

        if self.engine == 'paddleocr':
            result = self._ocr_processor.ocr(image_path, cls=True)
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
                image_path,
                lang=lang_map.get(self.lang, 'chi_sim'),
                config='--oem 3 --psm 6'
            )

        elif self.engine == 'easyocr':
            result = self._ocr_processor.readtext(image_path)
            return ' '.join([item[1] for item in result])

        return ""

    def recognize_batch(
        self,
        image_paths: List[str],
        preprocess: bool = True
    ) -> List[CameraOCRResult]:
        """
        批量识别图片

        Args:
            image_paths: 图片路径列表
            preprocess: 是否预处理

        Returns:
            List[CameraOCRResult]: 识别结果列表
        """
        results = []
        for path in image_paths:
            try:
                result = self.recognize_from_file(path, preprocess)
                results.append(result)
            except Exception as e:
                print(f"识别失败 {path}: {e}")
                results.append(CameraOCRResult(
                    text="",
                    confidence=0.0,
                    image_path=path,
                    engine=self.engine
                ))
        return results


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='医学文档摄像头OCR识别')
    parser.add_argument(
        'image',
        nargs='?',
        help='图片文件路径（不指定则启动摄像头）'
    )
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
        '-c', '--camera',
        type=int,
        default=0,
        help='摄像头索引 (默认: 0)'
    )
    parser.add_argument(
        '-o', '--output',
        help='输出文件路径'
    )
    parser.add_argument(
        '-s', '--save',
        action='store_true',
        help='保存拍摄的照片'
    )
    parser.add_argument(
        '--no-preprocess',
        action='store_true',
        help='不进行图像预处理'
    )

    args = parser.parse_args()

    # 显示可用库
    print("\n可用图像处理库:")
    for lib, available in IMAGE_LIBRARIES.items():
        status = "可用" if available else "不可用"
        print(f"  {lib}: {status}")

    camera = CameraOCR(
        engine=args.engine,
        lang=args.lang,
        camera_index=args.camera
    )

    if args.image:
        # 识别已有图片
        print(f"\n识别图片: {args.image}")
        result = camera.recognize_from_file(args.image, not args.no_preprocess)
    else:
        # 摄像头拍照识别
        print("\n启动摄像头拍照识别...")
        result = camera.capture_and_recognize(save_capture=args.save)

    print(f"\n识别置信度: {result.confidence:.2%}")
    print(f"图片路径: {result.image_path}")

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result.text)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
