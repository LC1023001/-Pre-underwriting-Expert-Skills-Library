# Medical OCR Assets

此目录包含医学文档OCR识别相关的资源文件。

## 资源文件说明

### templates/
OCR识别结果输出模板

- `result_template.md`: 标准Markdown输出模板
- `result_template.json`: 结构化JSON输出模板
- `result_summary.md`: 结果摘要模板

### examples/
示例文件和测试数据

- `sample_report.png`: 示例医学检验报告图像
- `sample_prescription.jpg`: 示例处方图像
- `sample_health_check.pdf`: 示例体检报告PDF

### fonts/
OCR识别优化的字体文件（可选）

- `NotoSansCJK-Regular.ttc`: 思源黑体（中英文）
- 用于OCR训练和测试

### config/
配置文件

- `tesseract_config.txt`: Tesseract配置文件
- `preprocess_config.json`: 图像预处理配置
- `output_config.json`: 输出格式配置

## 使用方法

### 使用模板

```python
# 加载模板
with open('templates/result_template.md', 'r', encoding='utf-8') as f:
    template = f.read()

# 填充数据
filled_template = template.replace('{{patient_name}}', '张三')
filled_template = filled_template.replace('{{test_date}}', '2026-04-05')

# 保存结果
with open('result.md', 'w', encoding='utf-8') as f:
    f.write(filled_template)
```

### 使用示例

示例文件可用于：
- 测试OCR识别效果
- 验证预处理流程
- 演示功能使用

### 使用配置

```python
# 加载配置
import json

with open('config/tesseract_config.txt', 'r') as f:
    tesseract_config = f.read()

with open('config/preprocess_config.json', 'r') as f:
    preprocess_config = json.load(f)

# 应用配置
ocr_result = pytesseract.image_to_string(
    image,
    config=tesseract_config
)
```

## 添加自定义资源

如需添加自定义资源：

1. **自定义模板**: 放入`templates/`目录
2. **自定义示例**: 放入`examples/`目录
3. **自定义配置**: 放入`config/`目录
4. **自定义字体**: 放入`fonts/`目录

## 注意事项

- 示例文件中的患者信息已脱敏处理
- 字体文件仅供OCR训练使用，不用于商业用途
- 配置文件可根据实际需求调整
