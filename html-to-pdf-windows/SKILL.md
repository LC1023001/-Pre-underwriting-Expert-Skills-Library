---
name: html-to-pdf-windows
description: >
  Windows 环境 HTML/报告转 PDF 生成方案。基于 fpdf2 + fontTools（TTC→TTF 字体提取），
  纯 Python 实现，零系统依赖，完美支持中文。
  解决 WeasyPrint（缺GTK）、xhtml2pdf（安装失败）、Playwright（不兼容Py3.14）在 Windows 上的兼容性问题。
  适用于：预核保评估报告 PDF 输出、体检报告 PDF 生成、核保意见书 PDF 输出、任意中文结构化报告转 PDF。
  agent_created: true
  version: 1.0.0
  created: 2026-06-09
---

# HTML-to-PDF Windows — fpdf2 + fontTools 中文 PDF 生成

## 技能用途

在 Windows 环境下将结构化报告/HTML 转换为中文 PDF，纯 Python 实现，零系统依赖。

## 适用场景

- 预核保评估报告 PDF 输出
- 体检报告解读 PDF
- 核保意见书 PDF 生成
- 任意中文结构化报告转 PDF
- 微信发送场景（无需用户安装任何软件即可生成 PDF）

## 为什么用 fpdf2 + fontTools？

在 Windows 上尝试过的方案：

| 方案 | 结果 | 原因 |
|------|------|------|
| WeasyPrint | ❌ 失败 | 缺失 GTK3 系统库，Windows 安装极困难 |
| xhtml2pdf | ❌ 失败 | 依赖链复杂，pip 安装常中断 |
| Playwright (Py) | ❌ 失败 | 不支持 Python 3.14 |
| Puppeteer (Node) | ❌ 失败 | Chromium 下载超时/权限问题 |
| **fpdf2 + fontTools** | ✅ **成功** | 纯 Python，零系统依赖，中文完美 |

## 核心技术要点

### 1. TTC → TTF 字体提取

Windows 系统中文矢量字体（如微软雅黑 `msyh.ttc`）为 **TrueType Collection** 格式，fpdf2 不直接支持。
需先用 `fontTools` 提取单字体 TTF：

```python
from fontTools.ttLib import TTCollection

# 打开 TTC（Contains 2 fonts: Regular + Bold）
ttc = TTCollection("C:/Windows/Fonts/msyh.ttc")

# 提取第 0 个字体（Regular 变体）
ttc.fonts[0].save("./fonts/msyh.ttf")
```

### 2. fpdf2 中文 PDF 生成框架

```python
from fpdf import FPDF

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.add_font("YaHei", "", "./fonts/msyh.ttf")
        self.add_font("YaHei", "B", "./fonts/msyh.ttf")
        self.set_auto_page_break(True, 15)
    
    def header(self):
        # 公司/报告名称
        self.set_font("YaHei", "B", 16)
        self.cell(0, 10, "报告名称", align="C")
    
    def footer(self):
        self.set_y(-15)
        self.set_font("YaHei", "", 7)
        self.cell(0, 10, f"第 {self.page_no()} 页", align="C")
```

### 3. Emoji / 特殊字符处理

Windows 中文字体（微软雅黑/黑体/宋体）**不包含 Emoji 字形**。
报告中的 ✓ ✗ ⚠ 等符号需替换为纯文字标记：

| 原符号 | 替换 |
|--------|------|
| ✓ / ✅ | [OK] |
| ✗ / ❌ | [NO] |
| ⚠ / 🔴 | [WARN] |
| → | > |
| ← | < |

## 完整工作流程

```
1. 识别需求：用户要求 HTML/报告 → PDF
       ↓
2. 检查环境：Windows？→ 跳过 WeasyPrint/xhtml2pdf/Playwright
       ↓
3. 检查字体：C:/Windows/Fonts/msyh.ttc 是否存在？
       ├── 存在 → fontTools 提取 TTF
       └── 不存在 → 下载开源中文字体（思源黑体 etc.）
       ↓
4. 安装依赖（仅一次）：
   pip install fpdf2 fontTools
       ↓
5. 编写 ReportPDF 类（基于模板 references/generate_pdf_template.py）
       ↓
6. 填充数据 → 生成 PDF
       ↓
7. 输出到目标路径
```

## 依赖安装

```bash
# 使用项目 Python 3.14
/c/Users/lucha/.workbuddy/binaries/python/versions/3.14.3/python.exe \
  -m pip install fpdf2 fontTools
```

- `fpdf2`：纯 Python PDF 生成库（~500KB）
- `fontTools`：字体工具库，用于 TTC→TTF 提取

## 常用 API 速查

### 文本操作

```python
pdf.set_font("YaHei", "", 10)       # 常规
pdf.set_font("YaHei", "B", 12)      # 加粗（用同一个TTF）
pdf.cell(w, h, "文本")              # 单行
pdf.multi_cell(w, h, "多行文本")    # 自动换行
```

### 颜色

```python
pdf.set_text_color(r, g, b)          # 文字颜色
pdf.set_fill_color(r, g, b)          # 填充颜色
pdf.set_draw_color(r, g, b)          # 描边颜色
pdf.set_line_width(0.5)              # 线宽
```

### 图形

```python
pdf.rect(x, y, w, h, "DF")          # 矩形（D=描边, F=填充）
pdf.line(x1, y1, x2, y2)            # 直线
```

### 布局

```python
pdf.set_margins(left, top, right)    # 页边距
pdf.ln(h)                            # 换行
pdf.set_xy(x, y)                    # 绝对定位
pdf.get_x() / pdf.get_y()           # 当前位置
pdf.page_no()                        # 当前页码
```

## 设计规范（预核保报告专用）

### 配色方案

| 用途 | 颜色 | RGB |
|------|------|-----|
| 报告页头 | 深蓝 | (26, 79, 138) |
| 核保结论栏 | 琥珀 | (255, 251, 235) 底 / (245, 158, 11) 边 |
| A类异常（关键） | 浅红 | (255, 237, 237) |
| B类异常（关注） | 浅橙 | (255, 247, 237) |
| C类异常（建议） | 浅蓝 | (224, 242, 254) |
| 正常指标 | 浅绿 | (240, 253, 244) |
| 表格表头 | 浅灰蓝 | (238, 243, 251) |
| 免责声明 | 灰色 | (156, 163, 175) |

### 字号规范

| 层级 | 字号 | 粗细 |
|------|------|------|
| 报告标题 | 20pt | Bold |
| 副标题 | 9pt | Regular |
| 章节标题 | 13pt | Bold |
| 正文 | 9-10pt | Regular |
| 表格内容 | 8.5pt | Regular |
| 表格表头 | 8.5pt | Bold |
| 免责声明 | 7pt | Regular |

## 参考模板

完整可运行的 PDF 生成模板见：
- `references/generate_pdf_template.py` — 预核保评估报告 PDF 生成完整示例

## 注意事项

1. **TTC 字体**：`msyh.ttc` 含 2 个字体变体（Regular + Bold），fpdf2 用同一个 TTF 文件即可设置 Regular 和 Bold 两种样式
2. **Emoji 陷阱**：中文字体不含 Emoji，写报告时避免使用 ✓✗⚠ 等符号
3. **页码计算**：`multi_cell` 后的位置不确定，多页布局建议用 `set_xy` 绝对定位
4. **内存问题**：大报告（>20页）建议分章节生成后拼接
5. **Python 版本**：fpdf2 和 fontTools 均支持 Python 3.8-3.14，无版本兼容问题

## 技能边界

本技能专注 **程序化中文 PDF 生成**（从结构化数据直接构建 PDF），不处理：
- 复杂 HTML/CSS 渲染 → 需 WeasyPrint 或浏览器方案
- 扫描件 OCR → 见 `medical-ocr` 技能
- Word/DOCX 转 PDF → 需 python-docx + 本技能
