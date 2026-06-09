# Medical OCR - 医学文档OCR识别技能

专门用于识别医疗检查报告、体检报告和医学文档的OCR识别技能。

## 功能特点

- ✅ **多格式支持**: 图片（JPG、PNG、GIF）、PDF扫描件等
- ✅ **医学术语识别**: 智能识别专业医学术语和检验指标
- ✅ **结构化提取**: 自动组织为表格、列表等结构化格式
- ✅ **本地化部署**: 完全本地运行，保护患者隐私
- ✅ **中文优化**: 针对中文医学文档优化识别效果

## 适用场景

当用户需要以下操作时，使用本技能：

- 医学检查报告识别
- 体检报告文字提取
- 病历资料OCR
- 检验报告识别
- 图片转文字（医学文档）
- 扫描件识别
- PDF文字提取

## 技能结构

```
medical-ocr/
├── SKILL.md                  # 技能主文件
├── README.md                 # 本文件
├── scripts/                  # 可执行脚本
│   ├── README.md
│   ├── medical_pdf_ocr.py    # PDF文档OCR识别
│   ├── medical_image_preprocess.py  # 图像预处理
│   ├── extract_medical_entities.py  # 医学实体提取
│   └── requirements.txt      # Python依赖
├── references/               # 参考资料
│   ├── README.md
│   ├── medical_terminology.md  # 医学术语对照表
│   ├── ocr_best_practices.md    # OCR最佳实践
│   └── data_protection.md       # 数据隐私保护指南
└── assets/                   # 资源文件
    ├── README.md
    ├── templates/             # 输出模板
    │   ├── result_template.md
    │   └── result_template.json
    └── config/               # 配置文件
        ├── tesseract_config.txt
        └── preprocess_config.json
```

## 核心工作流程

### 1. 识别输入类型
判断用户提供的是图片、PDF还是扫描件

### 2. 选择OCR方法
- **图片**: 使用 `OCR - Local (No API Key)` 或 `OCR Local V2`
- **PDF**: 使用 `Ocr Document` 或 `Pdf Ocr Tool`
- **深度分析**: 使用 `pdf-ocr-layout`

### 3. 执行OCR识别
调用相应的OCR技能进行文字识别

### 4. 结果处理与优化
- 文字校对
- 结构化组织
- 医学术语验证
- 数值提取
- 格式化输出

### 5. 保存结果
生成Markdown格式的结构化识别结果

## 依赖的OCR技能

本技能依赖以下OCR技能（需要预先安装）：

- `OCR - Local (No API Key)`: 基于Tesseract.js的本地OCR
- `OCR Local V2`: 基于Tesseract.js的本地OCR
- `Ocr Document`: PDF和图片OCR提取
- `Pdf Ocr Tool`: 基于Ollama GLM-OCR的智能PDF/图片转Markdown
- `pdf-ocr-layout`: 基于Zhipu GLM-OCR的多模态文档深度分析

## 使用示例

### 示例1: 识别体检报告图片

用户请求:
```
"识别这份体检报告"
```

技能响应:
1. 接收用户上传的图片文件
2. 使用 `OCR - Local (No API Key)` 技能进行OCR识别
3. 提取医学实体（检验指标、数值、参考范围等）
4. 生成结构化Markdown结果
5. 保存为 `ocr_result_YYYYMMDD_HHMMSS.md`

### 示例2: 提取PDF检验报告

用户请求:
```
"提取这份PDF检验报告中的文字"
```

技能响应:
1. 使用 `Ocr Document` 技能处理PDF
2. 逐页进行OCR识别
3. 提取检验指标和数值
4. 组织为表格格式
5. 生成Markdown输出

### 示例3: 深度分析医学文档

用户请求:
```
"深度分析这份医学文档"
```

技能响应:
1. 使用 `pdf-ocr-layout` 技能进行智能内容检测
2. 识别文本、表格、图形等不同类型内容
3. 生成包含完整布局信息的Markdown
4. 保存结果

## 输出格式

识别结果采用标准化的Markdown格式：

```markdown
# 医学文档OCR识别结果

## 基本信息
- 报告类型: 体检报告
- 识别日期: 2026-04-05
- 源文件: health_check.pdf

## 患者信息
- 姓名: ***
- 性别: ***
- 年龄: ***

## 检验结果

| 指标 | 指标名称 | 检验结果 | 单位 | 参考范围 | 提示 |
|------|---------|---------|------|---------|------|
| WBC | 白细胞 | 6.5 | ×10⁹/L | 4.0-10.0 | 正常 |

## 诊断结论
...

## 医师建议
...
```

## 最佳实践

### 1. 隐私保护
- ✅ 本地化OCR，数据不离开用户设备
- ✅ 遵守医疗数据保护法律法规
- ✅ 不上传敏感医疗信息到云端

### 2. 质量控制
- ✅ 重要医学信息建议人工核对
- ✅ 使用图像预处理提高识别准确率
- ✅ 选择合适的OCR参数和语言包

### 3. 格式标准化
- ✅ 统一使用Markdown格式输出
- ✅ 参考医学术语对照表
- ✅ 标准化单位和数值格式

## 注意事项

### OCR准确率
- 手写文档准确率可能较低
- 扫描质量差的文档准确率降低
- 罕见医学术语可能需要人工校对

### 格式复杂度
- 复杂表格可能需要额外处理
- 图形和图表内容提取有限
- 混合排版文档需要智能处理

### 法律合规
- 处理医疗文档需遵守相关法律法规
- 保护患者隐私和个人信息
- 重要医学决策不应仅依赖OCR结果

## 环境要求

### 必需
- Python 3.7+
- Tesseract OCR引擎
- 相关Python依赖（见 `scripts/requirements.txt`）

### 可选
- OpenCV（用于高级图像处理）
- GPU加速（用于大规模处理）

## 安装Tesseract

### Windows
1. 下载Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装到默认路径或自定义路径
3. 将安装路径添加到系统PATH
4. 下载中文语言包并放置到 `tessdata` 目录

### macOS
```bash
brew install tesseract
brew install tesseract-lang  # 包含中文语言包
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-chi-sim  # 中文简体
sudo apt-get install tesseract-ocr-chi-tra  # 中文繁体
```

## 安装Python依赖

```bash
cd scripts/
pip install -r requirements.txt
```

## 使用脚本

### PDF文档OCR
```bash
python medical_pdf_ocr.py input.pdf output.md
python medical_pdf_ocr.py input.pdf output.md 600  # 指定DPI
```

### 图像预处理
```bash
python medical_image_preprocess.py input.jpg output.jpg
python medical_image_preprocess.py input.jpg output.jpg binary  # 二值化
python medical_image_preprocess.py input.jpg output.jpg deskew  # 倾斜校正
```

### 提取医学实体
```bash
python extract_medical_entities.py ocr_result.md entities.json
python extract_medical_entities.py ocr_result.md entities.md md  # Markdown格式
```

## 技术支持

如有问题或建议，请参考：
- `references/ocr_best_practices.md` - OCR最佳实践
- `references/medical_terminology.md` - 医学术语对照
- `references/data_protection.md` - 数据隐私保护

## 许可证

本技能遵循WorkBuddy技能开发规范。

## 更新日志

### v1.0.0 (2026-04-05)
- 初始版本发布
- 支持图片和PDF文档OCR识别
- 包含医学术语对照表
- 提供完整的脚本和配置文件
