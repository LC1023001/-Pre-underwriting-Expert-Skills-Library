# Medical OCR Scripts

此目录包含医学文档OCR识别相关的可执行脚本。

## 脚本说明

### medical_pdf_ocr.py
专门处理医学PDF文档的OCR识别，支持：
- 多页PDF文档批处理
- 自动裁剪页眉页脚
- 保留医学图表和插图
- 结构化输出检验数据

### medical_image_preprocess.py
医学图像预处理脚本，提高OCR识别率：
- 图像降噪
- 对比度增强
- 文字区域检测
- 倾斜校正

### extract_medical_entities.py
从OCR识别结果中提取医学实体：
- 检验指标名称
- 检验数值
- 参考范围
- 诊断术语
- 药品名称

## 使用方法

```bash
# OCR识别医学PDF
python medical_pdf_ocr.py input.pdf output.md

# 预处理医学图像
python medical_image_preprocess.py input.jpg output.jpg

# 提取医学实体
python extract_medical_entities.py ocr_result.md entities.json
```

## 注意事项

- 确保已安装必要的依赖：`pip install -r requirements.txt`
- Tesseract需要单独安装并配置路径
- 处理包含患者隐私的文档时，请遵守相关法律法规
