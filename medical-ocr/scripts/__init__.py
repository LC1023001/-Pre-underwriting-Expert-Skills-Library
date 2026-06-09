"""
Medical OCR Scripts Package
医学文档OCR识别脚本包

主要模块：
- ocr_image: 图片OCR识别
- ocr_pdf: PDF文档OCR识别
- ocr_camera: 摄像头拍照OCR
- medical_terms: 医学术语处理
- setup_ocr_env: 环境配置
"""

from .ocr_image import OCRProcessor, OCRResult
from .ocr_pdf import PDFOCRProcessor, PDFOCRResult
from .ocr_camera import CameraOCR, CameraOCRResult
from .medical_terms import MedicalTermProcessor, BloodTestParser

__all__ = [
    'OCRProcessor',
    'OCRResult',
    'PDFOCRProcessor',
    'PDFOCRResult',
    'CameraOCR',
    'CameraOCRResult',
    'MedicalTermProcessor',
    'BloodTestParser',
]
