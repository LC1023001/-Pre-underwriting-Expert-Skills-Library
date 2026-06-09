---
name: wechat-underwriting-intake
description: >
  WeChat 核保接单预处理技能 v3.0。处理来自微信群/文件传输助手的多种格式输入：
  文字描述、聊天记录截图、体检报告图片、PDF文件、压缩包。
  支持自动文件监控（wechat-auto-system）、PyMuPDF文字型PDF提取和 PaddleOCR 本地识别引擎。
  支持多次体检报告对比分析。自动识别格式 → 提取医学信息 → 结构化异常标记 → 输出预核保评估请求。
  author: 路畅 + 山竹
  version: 3.0.0
  agent_created: true
---

# WeChat 核保接单预处理技能

## 触发场景

用户说以下任一情况即触发：
- "帮我处理一下这个微信发来的资料"
- "这是客户发来的体检报告/病历"
- 直接粘贴微信聊天记录（含图片/文件）
- 提到"文件传输助手"、"微信群"、处理客户资料

---

## 输入格式识别与处理策略

### 格式一：纯文字描述

**特征：** 用户直接粘贴或描述病情/体检异常

**处理方式：**
1. 提取所有医学实体（疾病、症状、检验指标、数值）
2. 结构化输出：
```
【医学信息提取结果】
- 诊断/异常：甲状腺结节 TI-RADS 3级
- 检验指标：AST 48 U/L（偏高）
- 病史时间：高血压 3年，服药控制可
- 年龄/性别：（如提及）
```
3. 直接调用预核保评估逻辑输出结论

---

### 格式二：聊天记录截图（含图片）

**特征：** 用户发送微信聊天截图，图片中含文字

**处理方式：**
1. 使用 OCR 识别截图中的文字（优先用 `medical-ocr` 技能）
2. 区分：聊天对话 vs 报告内容
3. 提取医学信息后按格式一处理

**工具调用顺序：**
- 先调用 `medical-ocr` 技能识别图片文字
- 如 `medical-ocr` 不可用，降级使用 `ocr-local` 或 `ocr-space`

---

### 格式三：体检报告/病历图片（单张或多张）

**特征：** 直接发送报告照片/扫描件，非聊天截图

**处理方式：**
1. 使用 `medical-ocr` 技能识别（专为医疗文档优化）
2. 提取关键字段：
   - 基本信息：姓名、年龄、性别
   - 检验指标：项目名、结果、参考范围、异常标记
   - 影像学结论：超声、CT、MRI描述
   - 诊断意见
3. 输出结构化摘要，供核保评估使用

---

### 格式四：PDF文件

**特征：** 发送 `.pdf` 文件（体检报告、病历等）

**处理方式（v3.0 优化）：**

**第一步：判断PDF类型**
- 文字型PDF（可选中文字）→ 优先使用 PyMuPDF (fitz) 提取
- 扫描件PDF（图片型）→ 使用 OCR 识别

**第二步：文字型PDF提取（推荐方案）**

使用 PyMuPDF (fitz) 直接提取文字，速度极快、准确率高、无需API：

```python
import fitz  # PyMuPDF

doc = fitz.open("体检报告.pdf")
for i, page in enumerate(doc):
    text = page.get_text()
    # 跳过纯影像附件页（无实质文字内容）
    if text.strip() and not text.strip().startswith("影像附件"):
        print(f"--- Page {i+1} ---")
        print(text)
doc.close()
```

**安装命令（仅需一次）：**
```bash
/c/Users/lucha/.workbuddy/binaries/python/versions/3.14.3/python.exe -m pip install PyMuPDF
```

**第三步：扫描件PDF提取**
- 使用 `pdf-ocr` 或 `pdf-ocr-layout` 技能
- 如PDF为扫描件（图片型）：用 PaddleOCR 或 `medical-ocr` 识别

**第四步：结构化提取**

按照「体检报告结构化提取模板」章节提取关键信息。

**多份PDF对比（v3.0 新增）：**

当用户提供同一人多次体检报告时，自动执行对比分析：
1. 按时间排序所有报告
2. 对比相同指标的变化趋势（正常→异常、异常→恶化/好转）
3. 识别新发异常（前次正常本次异常）
4. 识别消失异常（前次异常本次正常）
5. 输出「异常指标趋势对比表」（见输出规范章节）

**实战案例参考：** 张瑜案例（2025-01-18 vs 2026-01-02），两份瑞慈体检报告PDF，
PyMuPDF提取后成功识别：乳腺增生→BI-RADS 3类进展、TC 5.45→6.30恶化、
HPV16/18阳性、先心术后新告知等关键核保风险变化。

---

### 格式五：压缩包（.zip / .rar / .7z）

**特征：** 发送压缩文件，内含多份报告

**处理方式：**
1. 解压到临时目录
2. 遍历所有文件，按格式一~四分别处理
3. 汇总所有报告的医学信息
4. 输出合并后的结构化摘要

**解压工具（Windows）：**
```powershell
# ZIP
Expand-Archive -Path "file.zip" -DestinationPath "tmp_dir"

# RAR（需安装 7-Zip）
& "C:\Program Files\7-Zip\7z.exe" x "file.rar" -o"tmp_dir"

# 如未安装 7-Zip，提示用户手动解压或安装
```

---

## 体检报告结构化提取模板（v3.0 新增）

体检报告PDF提取文字后，按以下模板结构化提取。该模板基于瑞慈、美年大健康、爱康国宾、
慈铭等主流体检机构报告格式优化，涵盖中国体检报告常见结构。

### 提取字段清单

```python
EXTRACTION_TEMPLATE = {
    "基本信息": {
        "姓名": None, "性别": None, "年龄": None,
        "身高_cm": None, "体重_kg": None, "BMI": None,
        "收缩压_mmHg": None, "舒张压_mmHg": None,
        "体检日期": None, "体检编号": None, "工作单位": None,
    },
    "健康问卷": {
        "既往史": None, "手术史": None, "外伤史": None, "过敏史": None,
    },
    "体格检查": {
        "营养": None, "心率_次分": None, "心律": None,
        "心音": None, "心脏杂音": None, "肺部": None,
        "腹部": None, "肝脏": None, "脾脏": None,
        "甲状腺": None, "乳房": None, "浅表淋巴结": None,
        "皮肤": None, "脊柱": None, "四肢关节": None,
    },
    "妇科（女性）": {
        "外阴": None, "阴道": None, "宫颈": None,
        "宫体": None, "附件": None,
        "TCT": None, "HPV": None,
    },
    "检验指标": {
        # 血常规
        "WBC": {"value": None, "unit": None, "ref": None, "flag": None},
        "RBC": {"value": None, "unit": None, "ref": None, "flag": None},
        "Hb": {"value": None, "unit": None, "ref": None, "flag": None},
        "PLT": {"value": None, "unit": None, "ref": None, "flag": None},
        # 肝功
        "ALT": {"value": None, "unit": None, "ref": None, "flag": None},
        "AST": {"value": None, "unit": None, "ref": None, "flag": None},
        "GGT": {"value": None, "unit": None, "ref": None, "flag": None},
        # 肾功
        "BUN": {"value": None, "unit": None, "ref": None, "flag": None},
        "Cr": {"value": None, "unit": None, "ref": None, "flag": None},
        "UA": {"value": None, "unit": None, "ref": None, "flag": None},
        # 血脂
        "TC": {"value": None, "unit": None, "ref": None, "flag": None},
        "TG": {"value": None, "unit": None, "ref": None, "flag": None},
        "HDL_C": {"value": None, "unit": None, "ref": None, "flag": None},
        "LDL_C": {"value": None, "unit": None, "ref": None, "flag": None},
        # 血糖
        "FPG": {"value": None, "unit": None, "ref": None, "flag": None},
        # 甲功
        "TSH": {"value": None, "unit": None, "ref": None, "flag": None},
        "FT3": {"value": None, "unit": None, "ref": None, "flag": None},
        "FT4": {"value": None, "unit": None, "ref": None, "flag": None},
        # 肿瘤标志物
        "AFP": {"value": None, "unit": None, "ref": None, "flag": None},
        "CEA": {"value": None, "unit": None, "ref": None, "flag": None},
        "CA125": {"value": None, "unit": None, "ref": None, "flag": None},
        "CA15_3": {"value": None, "unit": None, "ref": None, "flag": None},
        "CA19_9": {"value": None, "unit": None, "ref": None, "flag": None},
    },
    "影像检查": {
        "超声结论": [],   # 列表，每项含"部位+结论"
        "CT结论": [],     # 列表
        "X线结论": [],    # 列表
        "MRI结论": [],    # 列表
    },
    "心电图": {
        "心率": None, "结论": None,
    },
    "终检结论": [],      # 体检报告终检总结（最重要）
}
```

### 异常标记自动识别规则

从PDF提取的文字中自动识别异常指标，以下规则按优先级排列：

| 标记类型 | 识别规则 | 示例 |
|---------|---------|------|
| 符号标记 | `↑` `↓` `△` `*` `H` `L` 后缀 | `5.45 ↑`、`3.36 H` |
| 参考值越界 | 结果值超出参考范围 | LDL-C 4.21 vs 参考<3.37 |
| 关键词标记 | "偏高"、"偏低"、"异常"、"阳性"、"可疑" | "阳性(+)"、"偏高" |
| 分级标记 | TI-RADS/BI-RADS/Lung-RADS ≥3 | "BI-RADS 3类" |
| 阳性/阴性 | HPV、乙肝五项、幽门螺杆菌等 | "HPV16型/18型 阳性(+)" |
| 临界值 | 结果值在参考范围边缘±5% | FPG 5.18（上限6.1的85%） |
| 新发vs既往 | 与前次报告对比，新出现的异常 | 2025无结节→2026 BI-RADS 3类 |

**异常严重度分级：**
- **A类（核保关键）**：肿瘤标志物升高、分级≥3的结节、HPV高危阳性、ASC-US及以上、心电图ST-T改变
- **B类（核保关注）**：血脂/血糖/血压超标、BMI过低/过高、肝功异常、肺结节<5mm
- **C类（建议关注）**：轻度增生、颈椎曲度变直、维生素C微量等

### 多次报告对比分析流程（v3.0 新增）

当收到同一被保人的多次体检报告时：

**Step 1: 按时间排序**
```
报告1: 2025-01-18 (早期)
报告2: 2026-01-02 (近期)
```

**Step 2: 关键指标趋势对比**

输出格式：
```
| 指标 | 报告1日期 | 报告1值 | 报告2日期 | 报告2值 | 参考值 | 趋势 |
|------|----------|---------|----------|---------|--------|------|
| TC   | 2025-01  | 5.45 ↑  | 2026-01  | 6.30 ↑  | <5.18  | ⬆恶化 |
| LDL-C| 2025-01  | 3.36    | 2026-01  | 4.21 ↑  | <3.37  | ⬆恶化 |
| TSH  | 2025-01  | 4.15    | 2026-01  | 2.631   | 正常范围| ✅正常 |
```

**Step 3: 疾病/异常进展对比**

输出格式：
```
| 疾病/异常 | 报告1 | 报告2 | 变化 |
|----------|-------|-------|------|
| 乳腺 | 双侧小叶增生 | 左乳结节BI-RADS 3类 | ⬆进展 |
| HPV | 未检测 | 未检测 | 需关注 |
| 先心 | 未告知 | 动脉导管修补术30年 | 新告知 |
```

**Step 4: 识别核保风险变化**
- 新发异常 → 新增核保风险因子
- 恶化趋势 → 风险等级上调
- 好转/消失 → 可能缩小除外范围
- 新告知既往史 → 需补充评估

---

## 输出规范

无论输入格式如何，最终输出统一为：

### 单次报告输出

```
【预核保评估资料摘要】
客户：XXX（男/女，XX岁）
资料类型：体检报告 / 门诊病历 / 住院小结 / 混合
体检日期：YYYY-MM-DD
体检机构：XXX

■ 基本信息
  身高：XXX cm  体重：XXX kg  BMI：XXX（正常/偏高/偏低）
  血压：XXX/XXX mmHg

■ A类异常（核保关键）
  01 [乳腺] 左乳结节 BI-RADS 3类，7×3mm
  02 [宫颈] HPV16/18型阳性 + TCT ASC-US
  03 [肺] 两肺多发微小结节，最大4mm

■ B类异常（核保关注）
  04 [血脂] TC 6.30↑ LDL-C 4.21↑
  05 [心血管] 先心PDA修补术后30年
  06 [体重] BMI 17.8（过低）

■ C类异常（建议关注）
  07 [颈椎] 生理曲度变直
  08 [乳腺] 双侧结构不良，增生考虑

■ 需要核保评估的病种
  - 乳腺结节（BI-RADS 3类）
  - HPV16/18感染 + ASC-US
  - 肺结节（多发）
  - 高脂血症
  - 先心术后

■ 资料完整度：□完整 □部分缺失（说明：______）

【建议处理方式】
- 可直接评估：是/否
- 需补充资料：______
```

### 多次报告对比输出（v3.0 新增）

```
【预核保评估资料摘要 — 多次对比】
客户：XXX（男/女，XX岁）
资料类型：体检报告 × N份
报告期间：YYYY-MM-DD ~ YYYY-MM-DD

■ 异常指标趋势对比
| 指标 | 报告1 | 报告2 | 参考值 | 趋势 |
|------|-------|-------|--------|------|
| ... |

■ 疾病/异常进展对比
| 疾病 | 报告1 | 报告2 | 变化 |
|------|-------|-------|------|
| ... |

■ 新发风险（本次新增）
  - [乳腺] 增生→结节BI-RADS 3类（进展）
  - [心血管] 先心术后新告知

■ 恶化风险（较前次加重）
  - [血脂] TC +15.6%, LDL-C +25.3%

■ 好转/稳定（较前次改善）
  - [甲功] TSH 4.15→2.631（正常范围）

■ 综合核保风险等级：低 / 中 / 高
■ 建议优先投保：[险种] / [保险公司推荐]
```

---

## 注意事项

1. **隐私保护：** 处理后及时删除临时文件，不在日志中保留客户姓名等敏感信息
2. **中文医学术语：** 识别时注意简写（如"甲亢"="甲状腺功能亢进症"）
3. **数值提取：** 检验指标必须提取数值 + 单位 + 参考范围，用于精确评估
4. **图片方向：** 如OCR识别结果乱码，尝试旋转图片后重新识别
5. **压缩包密码：** 如遇到加密压缩包，提示用户另发密码

---

## 与核保系统的衔接

资料摘要输出后，自动衔接：
1. 匹配《重疾险智能核保问卷v1》对应病种
2. 输出每道题的核保结论（标体/除外/加费/拒保）
3. 生成正式评估报告（使用 `预核保评估报告模板.md`）

---

## 自动处理模式（v2.0 新增）

### 微信文件自动监控

自动化系统路径：`{项目根目录}/wechat-auto-system/`

**启动自动监控：**
```bash
# 启动文件监控（守护模式）
python auto_process.py monitor

# 处理单个文件
python auto_process.py once <文件路径>

# 查看系统状态
python auto_process.py status

# 运行自检
python auto_process.py test
```

**监控机制：**
- 轮询监控 `D:\Users\lucha\Documents\xwechat_files\drlucifer_7f1d\msg\file\` 目录
- 检测到新 PDF/图片文件 → 自动触发 OCR → 生成评估报告
- 已处理文件记录在 `.processed_files.json`，避免重复处理
- 报告输出到 `reports/` 目录，通知输出到 `notifications/` 目录

**文件处理管道：**
```
微信文件目录 ──(检测)──> monitor.py ──(OCR)──> ocr_engine.py (PaddleOCR)
                                    ──(评估)──> pipeline.py
                                    ──(发送)──> send_report.py → 通知/邮件
```

### 报告自动发送

报告发送策略（按优先级）：
1. **本地通知**：在 `notifications/` 目录生成待审核通知
2. **邮件发送**：如配置 SMTP 环境变量，自动发送报告附件
3. **手动发送**：报告生成后，在微信中手动转发给客户

---

## 技能依赖

OCR / 提取引擎（按效果和使用场景排序）：

### 文字型PDF提取（首选）
- **PyMuPDF (fitz)**（v3.0 推荐，文字型PDF速度最快、准确率最高）
  - 安装：`/c/Users/lucha/.workbuddy/binaries/python/versions/3.14.3/python.exe -m pip install PyMuPDF`
  - 用法：`import fitz; doc = fitz.open("file.pdf"); text = page.get_text()`
  - 适用：瑞慈、美年、爱康、慈铭等体检机构生成的电子PDF
  - 优势：毫秒级提取、零API调用、保留完整中文医学文本
  - 注意：扫描件PDF无法提取文字，需降级到OCR方案

### 扫描件/图片OCR识别
- **PaddleOCR**（推荐，本地部署，中文医学文档效果最佳）
  - 路径：`~/.workbuddy/binaries/python/envs/paddleocr/`
  - Python 3.12 虚拟环境
  - 通过 `wechat-auto-system/ocr_engine.py` 调用
- `pdf-ocr-layout` —— GLM-OCR多模态分析（需智谱API Key）
- `medical-ocr` / `ocr-local` —— Tesseract.js 本地OCR（备选）

### 不可用时的降级方案
1. 文字型PDF → PyMuPDF (fitz) 直接提取
2. 扫描件PDF → pdf-ocr-layout (GLM-OCR) → PaddleOCR → Tesseract
3. 图片 → medical-ocr → ocr-space → ocr-local
4. 如以上均不可用，提示用户手动提供文字版资料

### 已知问题与规避方案（v3.0 新增）
| 问题 | 场景 | 规避方案 |
|------|------|---------|
| markitdown安装依赖冲突 | Python 3.13 pip install markitdown[pdf] | 改用PyMuPDF直接提取 |
| pdfplumber安装超时 | Windows Python 3.14 pip install | 改用PyMuPDF，安装更轻量 |
| 影像附件页无实质内容 | 体检报告PDF后10-20页为影像图 | 跳过`text.strip().startswith("影像附件")`的页面 |
| 检验项目跨页断裂 | 血常规表格被分页符切断 | 逐页提取后按"项目名称/结果/参考值"模式拼接 |
| 参考值含性别条件 | "男:9-50U/L 女:7-40U/L" | 根据被保人性别匹配对应参考范围 |
| TSH参考值含孕期 | 正常/孕早/孕中/孕晚分段 | 使用"正常人群"参考范围，除非已知怀孕 |
