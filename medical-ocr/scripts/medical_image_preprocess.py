#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医学图像预处理脚本
提高OCR识别准确率
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(input_path: str, output_path: str):
    """
    预处理医学图像以提高OCR准确率

    Args:
        input_path: 输入图像路径
        output_path: 输出图像路径
    """
    try:
        print(f"正在处理: {input_path}")

        # 加载图像
        img = Image.open(input_path)

        # 转换为RGB模式（如果是RGBA或其他模式）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        print("  应用图像增强...")

        # 1. 对比度增强
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)  # 对比度增强2倍

        # 2. 亮度调整
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.2)  # 亮度增加20%

        # 3. 锐化
        img = img.filter(ImageFilter.SHARPEN)

        # 4. 去噪
        img = img.filter(ImageFilter.MedianFilter(size=3))

        print(f"  保存到: {output_path}")
        img.save(output_path, quality=95)

        print("✓ 图像预处理完成!")
        return True

    except Exception as e:
        print(f"✗ 图像预处理失败: {str(e)}")
        return False


def binarize_image(input_path: str, output_path: str, threshold: int = 128):
    """
    二值化图像（转换为黑白）

    Args:
        input_path: 输入图像路径
        output_path: 输出图像路径
        threshold: 二值化阈值 (0-255)
    """
    try:
        print(f"正在二值化: {input_path}")

        img = Image.open(input_path)

        # 转换为灰度图
        gray = img.convert('L')

        # 二值化
        binary = gray.point(lambda x: 0 if x < threshold else 255, '1')

        binary.save(output_path)

        print(f"✓ 二值化完成: {output_path}")
        return True

    except Exception as e:
        print(f"✗ 二值化失败: {str(e)}")
        return False


def deskew_image(input_path: str, output_path: str):
    """
    校正图像倾斜

    Args:
        input_path: 输入图像路径
        output_path: 输出图像路径
    """
    try:
        print(f"正在校正倾斜: {input_path}")

        import cv2

        # 使用OpenCV检测倾斜角度
        img = cv2.imread(input_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # 霍夫变换检测直线
        lines = cv2.HoughLines(edges, 1, np.pi/180, 100)

        if lines is not None:
            # 计算平均角度
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                angles.append(angle)

            # 使用中位数作为倾斜角度
            median_angle = np.median(angles)

            print(f"  检测到倾斜角度: {median_angle:.2f}°")

            # 旋转图像
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h),
                                      flags=cv2.INTER_CUBIC,
                                      borderMode=cv2.BORDER_REPLICATE)

            cv2.imwrite(output_path, rotated)
            print(f"✓ 倾斜校正完成: {output_path}")
            return True
        else:
            print("  未检测到明显的倾斜，跳过校正")
            return False

    except ImportError:
        print("  未安装OpenCV，跳过倾斜校正")
        print("  可选安装: pip install opencv-python")
        return False
    except Exception as e:
        print(f"✗ 倾斜校正失败: {str(e)}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法:")
        print("  python medical_image_preprocess.py <输入图像> <输出图像> [模式]")
        print()
        print("模式:")
        print("  enhance  - 图像增强（默认）")
        print("  binary   - 二值化")
        print("  deskew   - 倾斜校正")
        print()
        print("示例:")
        print("  python medical_image_preprocess.py input.jpg output.jpg")
        print("  python medical_image_preprocess.py input.jpg output.jpg binary")
        print("  python medical_image_preprocess.py input.jpg output.jpg deskew")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'enhance'

    # 检查输入文件
    if not Path(input_path).exists():
        print(f"✗ 文件不存在: {input_path}")
        sys.exit(1)

    # 根据模式执行处理
    if mode == 'enhance':
        success = preprocess_image(input_path, output_path)
    elif mode == 'binary':
        success = binarize_image(input_path, output_path)
    elif mode == 'deskew':
        success = deskew_image(input_path, output_path)
    else:
        print(f"✗ 未知模式: {mode}")
        sys.exit(1)

    if success:
        print(f"\n✓ 处理完成!")
        print(f"  输入: {input_path}")
        print(f"  输出: {output_path}")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
