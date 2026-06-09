---
name: medical-ocr
description: >
  专门OCR识别医疗检查报告、体检报告和医学文档 v2.0。支持扫描件、PDF、图片等多种格式，
  智能识别医疗术语、诊断结果、检验指标、处方信息等医学内容。
  v2.0新增：PyMuPDF文字型PDF首选提取、异常标记自动识别（↑↓△H L阳性）、
  多次报告对比分析、体检报告结构化提取模板、核保风险分级输出。
  支持本地化部署，无需依赖云服务API。
  agent_created: true
  version: 2.1.0
  updated: 2026-06-09
---

# Medical OCR - 医学文档OCR识别技能 v2.0

## 技能用途

本技能专门用于识别医疗检查报告、体检报告和医学文档中的文字内容。支持从扫描件、PDF、图片等多种格式中提取医学信息，包括但不限于：

- **医疗检查报告**: 血液检查、尿液检查、影像学检查报告等
- **体检报告**: 全面体检、专项体检报告
- **医学文档**: 病历、处方、医嘱、诊断证明等
- **检验报告**: 生化指标、免疫指标、微生物检验等
- **医学影像报告**: X光、CT、MRI、超声检查结果

## 核心能力

1. **多格式支持**: 处理图片(JPG、PNG、GIF)、PDF（文字型+扫描件）
2. **PyMuPDF首选提取**: 文字型PDF毫秒级提取，零API调用（v2.0新增）
3. **异常标记自动识别**: 自动识别↑↓△H L阳性等异常标志（v2.0新增）
4. **结构化提取**: 按体检报告标准模板组织数据
5. **多次报告对比**: 支持同一被保人多次体检趋势分析（v2.0新增）
6. **核保风险分级**: A/B/C三级异常分类，直接衔接核保评估（v2.0新增）
7. **本地化部署**: 完全本地运行，保护患者隐私，无需云端API
8. **中文优化**: 针对中文医学文档优化，支持简体中文和医学术语

## 使用场景

当用户提出以下需求时，应使用本技能：

- "识别这份体检报告"
- "提取PDF中的文字内容"
- "OCR识别这张化验单"
- "扫描件转文字"
- "医学文档识别"
- "检查报告文字提取"
- "病历资料OCR"
- "检验报告识别"
- "对比两次体检报告"（v2.0新增）

## 工作流程

### 步骤1: 识别输入类型与PDF类型判断

判断用户提供的是：
- **PDF文件** → 进一步判断文字型 vs 扫描件
- **图片文件**（JPG、PNG、GIF等）→ OCR识别
- **多份文件** → 逐份提取后对比分析

**PDF类型判断方法：**
```python
import fitz
doc = fitz.open("file.pdf")
# 尝试提取第一页文字
first_page_text = doc[0].get_text().strip()
if len(first_page_text) > 50:
    # 文字型PDF，使用PyMuPDF提取
    method = "pymupdf"
else:
    # 扫描件PDF，需要OCR
    method = "ocr"
doc.close()
```

### 步骤2: 选择提取方法（v2.0 优化）

按优先级选择提取引擎：

| 优先级 | 输入类型 | 提取方法 | 说明 |
|--------|---------|---------|------|
| 1 | 文字型PDF | **PyMuPDF (fitz)** | 速度最快、准确率最高、零API |
| 2 | 扫描件PDF | PaddleOCR → pdf-ocr-layout → Tesseract | 按可用性降级 |
| 3 | 图片 | medical-ocr → ocr-space → ocr-local | 按可用性降级 |

### 步骤3: 执行提取

#### 方案A：PyMuPDF 文字型PDF提取（首选）

```python
import fitz

def extract_medical_pdf(pdf_path):
    """提取体检报告PDF文字，自动跳过影像附件页"""
    doc = fitz.open(pdf_path)
    text_pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        stripped = text.strip()
        # 跳过空白页和纯影像附件页
        if stripped and not stripped.startswith("影像附件"):
            text_pages.append({
                "page": i + 1,
                "text": stripped
            })
    doc.close()
    return text_pages
```

**安装命令（仅需一次）：**
```bash
/c/Users/lucha/.workbuddy/binaries/python/versions/3.14.3/python.exe -m pip install PyMuPDF
```

**优势：**
- 毫秒级提取，无需等待OCR处理
- 中文医学文本完整保留（如BI-RADS、TI-RADS、ASC-US等）
- 保留检验指标数值、参考范围、异常标记符号
- 无API调用，完全本地化

#### 方案B：扫描件/图片OCR识别

降级使用以下引擎（按优先级）：
1. **PaddleOCR**（中文医学文档效果最佳）
2. **pdf-ocr-layout**（GLM-OCR多模态分析，需智谱API Key）
3. **medical-ocr / ocr-local**（Tesseract.js，本地OCR备选）

### 步骤4: 异常标记自动识别（v2.0 新增）

从提取的文字中自动识别异常指标：

```python
def detect_abnormal_markers(text, gender="女"):
    """从体检报告文字中识别异常标记"""
    abnormalities = []

    # 1. 符号标记识别
    # ↑ ↓ △ * H L 后缀 → 异常
    symbol_patterns = [
        r'(\d+\.?\d*)\s*↑',   # 数值后跟↑
        r'(\d+\.?\d*)\s*↓',   # 数值后跟↓
        r'(\d+\.?\d*)\s*△',   # 数值后跟△（轻度异常）
        r'阳性\(\+\)',          # 阳性标记
    ]

    # 2. 关键词标记
    keyword_markers = ["偏高", "偏低", "异常", "阳性", "可疑", "增大"]

    # 3. 分级标记
    grade_patterns = [
        r'BI-RADS\s*(\d)\s*类',
        r'TI-RADS\s*(\d)\s*级',
        r'Lung-RADS\s*(\d)',
    ]

    # 4. 参考值越界检测
    # 需要提取结果值和参考范围，对比判断

    return abnormalities
```

**异常严重度分级：**
- **A类（核保关键）**：肿瘤标志物升高、分级≥3的结节、HPV高危阳性、ASC-US及以上
- **B类（核保关注）**：血脂/血糖/血压超标、BMI过低/过高、肝功异常、肺结节<5mm
- **C类（建议关注）**：轻度增生、颈椎曲度变直、维生素C微量等

### 步骤5: 结构化提取

按照 `wechat-underwriting-intake` 技能中的「体检报告结构化提取模板」提取关键字段：
- 基本信息（姓名、性别、年龄、身高、体重、BMI、血压）
- 健康问卷（既往史、手术史、过敏史）
- 体格检查（各系统查体结果）
- 检验指标（血常规、肝肾功能、血脂血糖、甲功、肿瘤标志物）
- 影像检查（超声/CT/MRI/X线结论）
- 心电图
- 终检结论（最重要的核保评估依据）

### 步骤6: 多次报告对比（如适用）

当存在多份报告时：
1. 按时间排序
2. 关键指标趋势对比（数值+方向）
3. 疾病/异常进展对比（新发/恶化/好转/消失）
4. 输出趋势对比表

### 步骤7: 保存结果

将识别结果保存为Markdown文件：
- 默认路径: 当前工作目录
- 文件命名: `ocr_result_[姓名]_[日期].md`
- 内容格式: 结构化Markdown，包含表格、列表等

**v2.1 新增 — PDF 输出（Windows）**：
如需将提取结果生成 PDF 报告，使用 `html-to-pdf-windows` 技能（fpdf2 + fontTools）。
方案选择：Windows 上 WeasyPrint（缺 GTK）、xhtml2pdf（安装困难）、Playwright（不兼容 Py3.14）均不可用，
**fpdf2 + fontTools 是唯一纯 Python 零系统依赖的可靠方案**。

## 输出格式

### 单次报告输出

```markdown
# [报告标题]

## 基本信息
- 报告类型: [体检报告/检验报告/病历等]
- 检查日期: [YYYY-MM-DD]
- 患者信息: [姓名、性别、年龄等，如适用]
- 体检机构: [机构名]

## 检验指标（含异常标记）

| 项目名称 | 检验结果 | 单位 | 参考范围 | 异常标记 | 严重度 |
|---------|---------|------|---------|---------|--------|
| 总胆固醇 | 6.30 | mmol/L | <5.18 | ↑ | B |
| LDL-C | 4.21 | mmol/L | <3.37 | ↑ | B |

## 影像结论
- [超声] 双侧乳腺结构不良，增生考虑；左乳结节 BI-RADS 3类
- [CT] 两肺多发微小结节，建议随诊复查

## 终检结论（核保评估核心依据）
1. [结论1]
2. [结论2]

## 异常汇总（核保分级）
- A类异常：[列表]
- B类异常：[列表]
- C类异常：[列表]
```

### 多次报告对比输出

```markdown
# 多次体检报告对比分析

## 异常指标趋势对比
| 指标 | 报告1(日期) | 报告2(日期) | 参考值 | 趋势 |
|------|-----------|-----------|--------|------|
| TC | 5.45↑ | 6.30↑ | <5.18 | ⬆恶化 |
| LDL-C | 3.36 | 4.21↑ | <3.37 | ⬆恶化 |

## 疾病进展对比
| 疾病 | 报告1 | 报告2 | 变化 |
|------|-------|-------|------|
| 乳腺 | 小叶增生 | 结节BI-RADS 3类 | ⬆进展 |

## 核保风险变化
- 新发风险：[列表]
- 恶化风险：[列表]
- 好转风险：[列表]
```

## 最佳实践

1. **优先PyMuPDF**: 文字型PDF务必用PyMuPDF提取，不用OCR，速度快且更准确
2. **跳过影像页**: 体检报告PDF后10-20页常为影像附件，无文字价值，应自动跳过
3. **参考值性别区分**: 部分检验项目参考值分男女（如ALT: 男9-50/女7-40），需根据被保人性别匹配
4. **TSH参考值**: 部分体检机构TSH参考值包含孕期分段，应使用"正常人群"范围
5. **隐私保护**: 医疗文档包含敏感信息，本地化OCR确保数据不离开用户设备
6. **质量控制**: 对于重要医学信息，建议人工核对OCR识别结果
7. **终检结论优先**: 体检报告末尾的"终检结论"是最重要的核保评估依据，必须完整提取
8. **多报告对比**: 同一被保人多次报告对比是核保风险评估的关键输入

## 注意事项

1. **PDF类型判断**: 务必先判断文字型vs扫描件，文字型用PyMuPDF，扫描件用OCR
2. **OCR准确率**: 手写文档、扫描质量差的文档OCR准确率可能降低
3. **医学术语**: 罕见医学术语可能需要人工校对
4. **格式复杂**: 复杂表格和图形可能需要额外处理
5. **法律合规**: 使用OCR识别的医疗文档需遵守相关法律法规，保护患者隐私
6. **跨页表格**: 检验项目表可能跨页，需逐页提取后拼接
7. **markitdown依赖冲突**: 不推荐使用markitdown，依赖链过重且Windows环境安装常失败

## 技能依赖

### 提取引擎（按优先级）
- **PyMuPDF (fitz)**（v2.0 首选，文字型PDF）
  - 安装：`pip install PyMuPDF`
  - 无额外依赖，轻量级
- **PaddleOCR**（扫描件/图片首选）
  - 路径：`~/.workbuddy/binaries/python/envs/paddleocr/`
- **pdf-ocr-layout**（GLM-OCR多模态深度分析，需智谱API Key）
- **medical-ocr / ocr-local**（Tesseract.js备选）
- **ocr-space**（免费API备选）

### PDF 输出（v2.1 新增）
- **html-to-pdf-windows**（fpdf2 + fontTools）：Windows 中文 PDF 生成，纯 Python 零系统依赖
  - 安装：`pip install fpdf2 fontTools`
  - 解决 WeasyPrint（缺 GTK）、xhtml2pdf、Playwright 在 Windows 上的兼容性问题

### 不推荐
- `markitdown[pdf]`：依赖链重（onnxruntime/magika等），Windows安装常失败
- `pdfplumber`：安装超时问题，PyMuPDF已完全覆盖其功能
