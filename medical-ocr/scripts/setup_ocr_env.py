#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医学文档OCR环境配置脚本
自动检测系统环境并安装所需依赖
"""
import os
import sys
import subprocess
import platform

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, description=""):
    """执行命令并返回结果"""
    print(f"\n{'='*50}")
    print(f"正在: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*50)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print(f"✓ {description} 成功")
            if result.stdout:
                print(result.stdout[:500])
            return True
        else:
            print(f"✗ {description} 失败")
            print(f"错误: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ {description} 超时")
        return False
    except Exception as e:
        print(f"✗ {description} 异常: {e}")
        return False

def check_python():
    """检查Python版本"""
    print("\n检查Python环境...")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("✓ Python版本满足要求 (>=3.7)")
        return True
    else:
        print("✗ Python版本过低，需要Python 3.7或更高版本")
        return False

def get_pip_install_cmd():
    """获取pip安装命令"""
    return [sys.executable, "-m", "pip", "install"]

def install_paddleocr():
    """安装PaddleOCR及相关依赖"""
    print("\n" + "="*60)
    print("安装 PaddleOCR (推荐用于中文医学文档)")
    print("="*60)

    packages = [
        "paddlepaddle",      # PaddlePaddle核心
        "paddleocr",         # PaddleOCR
        "paddlepaddle-gpu" if platform.system() == "Windows" else "paddlepaddle-gpu",  # GPU版本可选
        "opencv-python",     # 图像处理
        "Pillow",            # PIL图像库
        "numpy",             # 数值计算
        "scikit-image",      # 图像处理
        "pyyaml",            # 配置文件
        "shapely",           # 几何计算
        "scipy",             # 科学计算
    ]

    # 先安装CPU版本
    cmd = get_pip_install_cmd() + ["--upgrade", "pip"]
    run_command(cmd, "升级pip")

    # 安装paddlepaddle CPU版本
    cmd = get_pip_install_cmd() + ["paddlepaddle"]
    success = run_command(cmd, "安装paddlepaddle")

    if not success:
        print("尝试安装paddlepaddle CPU版本...")
        cmd = get_pip_install_cmd() + ["paddlepaddle", "-i", "https://mirror.baidu.com/pypi/simple"]
        success = run_command(cmd, "安装paddlepaddle (百度镜像)")

    if success:
        # 安装其他依赖
        for pkg in packages[1:]:
            if pkg != "paddlepaddle":
                cmd = get_pip_install_cmd() + [pkg]
                run_command(cmd, f"安装 {pkg}")

    return success

def install_tesseract():
    """安装Tesseract OCR"""
    print("\n" + "="*60)
    print("安装 Tesseract OCR")
    print("="*60)

    if platform.system() == "Windows":
        print("Windows系统: 请手动下载安装Tesseract")
        print("下载地址: https://github.com/UB-Mannheim/tesseract/wiki")
        print("\n安装时请勾选以下选项:")
        print("  - Chinese Simplified (chi_sim)")
        print("  - Chinese Traditional (chi_tra)")
        print("  - English")
        print("\n安装完成后，请将Tesseract路径添加到系统PATH环境变量")

        # 尝试安装Python包装器
        cmd = get_pip_install_cmd() + ["pytesseract"]
        run_command(cmd, "安装pytesseract Python包装器")

        return False  # 需要手动安装

    elif platform.system() == "Darwin":  # macOS
        cmd = ["brew", "install", "tesseract", "tesseract-lang"]
        success = run_command(cmd, "安装Tesseract (Homebrew)")
        if success:
            cmd = get_pip_install_cmd() + ["pytesseract"]
            run_command(cmd, "安装pytesseract Python包装器")
        return success

    else:  # Linux
        cmd = ["sudo", "apt-get", "install", "tesseract-ocr", "tesseract-ocr-chi-sim"]
        success = run_command(cmd, "安装Tesseract (apt)")
        if success:
            cmd = get_pip_install_cmd() + ["pytesseract"]
            run_command(cmd, "安装pytesseract Python包装器")
        return success

def install_easyocr():
    """安装EasyOCR"""
    print("\n" + "="*60)
    print("安装 EasyOCR")
    print("="*60)

    packages = [
        "easyocr",
        "torch",          # PyTorch核心
        "torchvision",
    ]

    cmd = get_pip_install_cmd() + packages
    return run_command(cmd, "安装EasyOCR及PyTorch")

def install_pdf_dependencies():
    """安装PDF处理依赖"""
    print("\n" + "="*60)
    print("安装 PDF处理依赖")
    print("="*60)

    packages = [
        "pdf2image",      # PDF转图片
        "pypdf2",         # PDF读取
        "pymupdf",        # PyMuPDF (Fitz)
        "pdfplumber",     # PDF表格提取
    ]

    success = True
    for pkg in packages:
        cmd = get_pip_install_cmd() + [pkg]
        if not run_command(cmd, f"安装 {pkg}"):
            success = False

    return success

def verify_installation():
    """验证安装"""
    print("\n" + "="*60)
    print("验证OCR安装")
    print("="*60)

    # 验证PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("✓ PaddleOCR 导入成功")
        # 尝试初始化（下载模型）
        print("  尝试初始化PaddleOCR（首次会下载模型）...")
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        print("✓ PaddleOCR 初始化成功")
    except ImportError:
        print("✗ PaddleOCR 未安装")
    except Exception as e:
        print(f"✗ PaddleOCR 初始化失败: {e}")

    # 验证Tesseract
    try:
        import pytesseract
        print("✓ pytesseract 导入成功")
        # 检查tesseract是否可用
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract 版本: {version}")
        except Exception as e:
            print(f"⚠ Tesseract 可能未正确安装: {e}")
    except ImportError:
        print("✗ pytesseract 未安装")

    # 验证EasyOCR
    try:
        import easyocr
        print("✓ EasyOCR 导入成功")
    except ImportError:
        print("✗ EasyOCR 未安装")

    # 验证PDF
    try:
        import fitz  # PyMuPDF
        print("✓ PyMuPDF 导入成功")
    except ImportError:
        print("✗ PyMuPDF 未安装")

    try:
        import pdfplumber
        print("✓ pdfplumber 导入成功")
    except ImportError:
        print("✗ pdfplumber 未安装")

def print_usage():
    """打印使用说明"""
    print("""
================================================================================
医学文档OCR环境配置完成！

快速开始使用：
================================================================================

1. 图片OCR识别示例：
   ```python
   from scripts.ocr_image import OCRProcessor

   processor = OCRProcessor(engine='paddleocr')
   result = processor.recognize('medical_report.jpg')
   print(result.text)
   ```

2. PDF OCR识别示例：
   ```python
   from scripts.ocr_pdf import PDFOCRProcessor

   processor = PDFOCRProcessor(engine='paddleocr')
   result = processor.recognize('medical_report.pdf')
   print(result.text)
   ```

3. 摄像头拍照识别：
   ```python
   from scripts.ocr_camera import CameraOCR

   camera = CameraOCR(engine='paddleocr')
   result = camera.capture_and_recognize()
   print(result.text)
   ```

================================================================================
如需测试OCR功能，请运行：
   python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='ch'); print('PaddleOCR安装成功！')"
================================================================================
""")

def main():
    """主函数"""
    print("="*60)
    print("医学文档OCR环境配置脚本")
    print("="*60)

    # 检查Python版本
    if not check_python():
        print("\n✗ Python版本不满足要求")
        return 1

    # 询问安装选项
    print("\n请选择要安装的OCR引擎:")
    print("1. PaddleOCR (推荐 - 中文识别效果最好)")
    print("2. Tesseract (通用OCR引擎)")
    print("3. EasyOCR (多语言支持)")
    print("4. 全部安装")
    print("5. 仅安装PDF处理依赖")

    choice = input("\n请输入选择 (1-5, 默认1): ").strip() or "1"

    if choice == "1":
        install_paddleocr()
        install_pdf_dependencies()
    elif choice == "2":
        install_tesseract()
        install_pdf_dependencies()
    elif choice == "3":
        install_easyocr()
        install_pdf_dependencies()
    elif choice == "4":
        install_paddleocr()
        install_tesseract()
        install_easyocr()
        install_pdf_dependencies()
    elif choice == "5":
        install_pdf_dependencies()
    else:
        print("无效选择")

    # 验证安装
    verify_installation()

    # 打印使用说明
    print_usage()

    return 0

if __name__ == "__main__":
    sys.exit(main())
