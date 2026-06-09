# OCR识别最佳实践指南

## 图像预处理

### 1. 图像质量评估

在执行OCR前，先评估图像质量：

- **分辨率**: 建议至少300 DPI
- **对比度**: 文字与背景对比度应足够高
- **清晰度**: 文字边缘清晰，无严重模糊
- **倾斜度**: 尽量保持水平，倾斜角度<5度

### 2. 图像增强技术

**对比度增强**:
```python
from PIL import Image, ImageEnhance

img = Image.open('input.jpg')
enhancer = ImageEnhance.Contrast(img)
enhanced_img = enhancer.enhance(2.0)  # 增强2倍
```

**亮度调整**:
```python
enhancer = ImageEnhance.Brightness(img)
adjusted_img = enhancer.enhance(1.2)  # 增加20%亮度
```

**锐化处理**:
```python
from PIL import ImageFilter
sharpened_img = img.filter(ImageFilter.SHARPEN)
```

**去噪**:
```python
denoised_img = img.filter(ImageFilter.MedianFilter(size=3))
```

### 3. 二值化处理

对于扫描文档，二值化可以显著提高OCR准确率：

```python
from PIL import Image

gray = img.convert('L')
threshold = 128  # 可调整阈值
binary = gray.point(lambda x: 0 if x < threshold else 255, '1')
```

**自适应阈值**（适用于光照不均匀的图像）:
```python
import cv2

gray = cv2.imread('input.jpg', cv2.IMREAD_GRAYSCALE)
binary = cv2.adaptiveThreshold(
    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 11, 2
)
```

### 4. 倾斜校正

检测并校正图像倾斜：

```python
import cv2
import numpy as np

# 边缘检测
edges = cv2.Canny(gray, 50, 150, apertureSize=3)

# 霍夫变换检测直线
lines = cv2.HoughLines(edges, 1, np.pi/180, 100)

# 计算平均角度并旋转
if lines is not None:
    angles = [np.degrees(theta) - 90 for rho, theta in lines]
    median_angle = np.median(angles)
    # 旋转图像...
```

## Tesseract参数调优

### 1. 语言设置

根据文档语言选择合适的语言包：

- 中文简体: `chi_sim`
- 中文繁体: `chi_tra`
- 英文: `eng`
- 中英混合: `chi_sim+eng`

```python
text = pytesseract.image_to_string(
    img,
    lang='chi_sim+eng',  # 中文+英文
    config='--psm 6'
)
```

### 2. 页面分割模式（PSM）

选择合适的PSM参数：

| PSM值 | 说明 | 适用场景 |
|-------|------|---------|
| 3 | 全自动页面分割 | 一般文档 |
| 4 | 单列文本 | 标准文章 |
| 5 | 单块垂直文本 | 竖排文字 |
| 6 | 单块文本 | 表格、单段文字 |
| 7 | 单行文本 | 单行文字 |
| 11 | 稀疏文本 | 少量文字 |
| 12 | 带OSD的稀疏文本 | 稀疏文字带方向 |

**推荐配置**:
- 医学报告表格: `--psm 6`
- 标准文档: `--psm 3`
- 手写文字: `--psm 11`

### 3. OCR引擎模式（OEM）

| OEM值 | 说明 |
|-------|------|
| 0 | 传统引擎（仅限LSTM） |
| 1 | LSTM神经网络引擎（推荐） |
| 2 | Legacy + LSTM混合 |
| 3 | 默认（自动选择） |

```python
config = '--psm 6 --oem 3'
```

### 4. 高级参数

**提高准确率**:
```python
config = '''
--psm 6
--oem 3
-c tessedit_char_whitelist=0123456789.+-×÷%
--textord_force_make_prop_words=false
'''
```

**处理数字和单位**:
```python
# 限制字符集，提高数字识别准确率
config = '--psm 7 -c tessedit_char_whitelist=0123456789.×10⁹/L'
```

## 医学文档特殊处理

### 1. 表格识别

医学检验报告通常包含表格，需要特殊处理：

**方法1: 使用表格分割模式**
```python
# 先检测表格结构
import cv2

# 使用OpenCV的表格检测（需要训练模型）
# 或使用专门的表格识别库如camelot
```

**方法2: 分块处理**
```python
# 将表格分割成小块，分别OCR
# 然后重新组合结果
```

**方法3: 使用pdf-ocr-layout**
```bash
use_skill "pdf-ocr-layout"
```

### 2. 医学符号和单位

医学文档中常见特殊字符和单位：

- 希腊字母: α、β、γ、μ等
- 上标/下标: 10⁹、mol/L等
- 特殊符号: ×、÷、±、↑、↓等
- 医学单位: mmHg、mmol/L、U/L等

**处理方法**:
```python
# 使用字符白名单确保正确识别
config = '-c tessedit_char_whitelist=0123456789.+-×÷%↑↓±μmolLUg/'
```

### 3. 手写识别

手写医学文档（如处方、医嘱）的OCR准确率较低：

**建议**:
- 使用专门的手写OCR引擎（如Google Cloud Vision API）
- 先进行图像预处理提高清晰度
- 考虑人工校对

```python
# Tesseract对手写文字支持有限
# 如需识别手写，建议使用云端API
```

### 4. 多语言混合

中文医学报告常混合英文指标名称：

```python
# 同时加载中文和英文语言包
lang = 'chi_sim+eng'

# 如果遇到繁体中文
lang = 'chi_tra+eng'
```

## 错误校正

### 1. 医学术语校正

OCR识别后，使用医学术语字典进行校正：

```python
# 从references/medical_terminology.md加载术语表
with open('medical_terminology.md', 'r') as f:
    terminology = parse_medical_terms(f)

# 校正识别结果
for i, result in enumerate(ocr_results):
    corrected = correct_medical_term(result, terminology)
    ocr_results[i] = corrected
```

### 2. 数值范围验证

根据医学术语表中的正常范围验证识别的数值：

```python
def validate_value(indicator, value, unit):
    """验证检验数值是否在合理范围内"""
    normal_range = get_normal_range(indicator)
    if normal_range:
        min_val, max_val = normal_range
        if not (min_val <= value <= max_val):
            print(f"警告: {indicator}的值{value}{unit}超出正常范围")
            return False
    return True
```

### 3. 格式标准化

统一输出格式：

```python
# 统一单位
unit_mapping = {
    'u/l': 'U/L',
    'mmol/l': 'mmol/L',
    'umol/l': 'μmol/L',
}

# 统一数字格式
# 1,234.56 -> 1234.56
def normalize_number(s):
    return s.replace(',', '')
```

## 性能优化

### 1. 批处理

对于多页文档，使用批处理提高效率：

```python
from pdf2image import convert_from_path

# 批量转换PDF页面
images = convert_from_path('report.pdf', dpi=300)

# 并行OCR识别（需要多线程）
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(ocr_image, images))
```

### 2. 内存管理

处理大文件时注意内存使用：

```python
# 逐页处理，避免一次性加载所有页面
for i, image in enumerate(images):
    # 处理当前页
    result = ocr_image(image)
    save_result(result, f'page_{i+1}.txt')
    # 及时释放内存
    del image
```

### 3. GPU加速（可选）

如果有GPU，可以使用GPU加速的OCR引擎：

```python
# 使用EasyOCR（支持CUDA）
import easyocr

reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
result = reader.readtext('image.jpg')
```

## 质量评估

### 1. OCR准确率评估

使用人工标注的ground truth评估：

```python
from difflib import SequenceMatcher

def calculate_accuracy(ocr_text, ground_truth):
    """计算OCR准确率"""
    similarity = SequenceMatcher(None, ocr_text, ground_truth).ratio()
    return similarity * 100
```

### 2. 关键信息提取率

评估关键医学信息的提取率：

```python
def evaluate_extraction(extracted, ground_truth):
    """评估医学实体提取准确率"""
    metrics = {
        'indicator_accuracy': 0,
        'value_accuracy': 0,
        'diagnosis_accuracy': 0,
    }
    # 计算各项指标...
    return metrics
```

## 注意事项

1. **隐私保护**: 医疗文档包含敏感信息，确保本地处理，不上传云端
2. **法律合规**: 遵守医疗数据保护相关法律法规
3. **人工校对**: 重要医学信息建议人工核对
4. **持续优化**: 根据使用反馈不断优化预处理和OCR参数
5. **备份原始数据**: 保留原始文档，便于重新处理
