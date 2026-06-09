# Medical OCR Skill 测试示例

## 测试场景1: 图片OCR识别

用户请求:
```
"识别这份血液检查报告图片"
```

预期流程:
1. 接收图片文件（如 blood_test.jpg）
2. 使用 `OCR - Local (No API Key)` 技能
3. 提取医学实体（WBC、RBC、HGB等）
4. 生成结构化Markdown结果

预期输出格式:
```markdown
# 医学文档OCR识别结果

## 基本信息
- 报告类型: 血液检查报告
- 识别日期: 2026-04-05
- 源文件: blood_test.jpg

## 患者信息
- 姓名: ***
- 性别: ***
- 年龄: ***

## 检验结果

| 指标 | 指标名称 | 检验结果 | 单位 | 参考范围 | 提示 |
|------|---------|---------|------|---------|------|
| WBC | 白细胞 | 6.5 | ×10⁹/L | 4.0-10.0 | 正常 |
| RBC | 红细胞 | 4.8 | ×10¹²/L | 4.0-5.5 | 正常 |
| HGB | 血红蛋白 | 145 | g/L | 120-160 | 正常 |
| PLT | 血小板 | 220 | ×10⁹/L | 100-300 | 正常 |
```

---

## 测试场景2: PDF文档OCR

用户请求:
```
"提取这份体检报告PDF的文字"
```

预期流程:
1. 使用 `Ocr Document` 技能
2. 逐页OCR识别
3. 提取检验指标和数值
4. 组织为表格格式

---

## 测试场景3: 医学实体提取

用户请求:
```
"从OCR结果中提取检验指标和数值"
```

预期流程:
1. 读取OCR识别结果
2. 使用 `extract_medical_entities.py` 脚本
3. 提取检验指标、数值、单位
4. 生成JSON或Markdown格式输出

---

## 测试场景4: 图像预处理

用户请求:
```
"这张扫描件比较模糊，先优化一下再识别"
```

预期流程:
1. 使用 `medical_image_preprocess.py` 脚本
2. 应用对比度增强、去噪、锐化
3. 倾斜校正（如需要）
4. 保存预处理后的图像
5. 执行OCR识别

---

## 实际使用示例

### 完整工作流程

```bash
# 步骤1: 预处理图像（如果需要）
python scripts/medical_image_preprocess.py \
    input/blood_test.jpg \
    preprocessed/blood_test_clean.jpg

# 步骤2: 执行OCR识别
# 使用Skill内部调用OCR技能
# 或直接使用脚本
python scripts/medical_pdf_ocr.py \
    preprocessed/blood_test_clean.jpg \
    output/ocr_result.md

# 步骤3: 提取医学实体
python scripts/extract_medical_entities.py \
    output/ocr_result.md \
    output/entities.json
```

---

## 验证检查清单

- [ ] Skill能正确识别用户意图
- [ ] 能选择合适的OCR技能（图片/PDF/深度分析）
- [ ] OCR识别结果准确
- [ ] 医学术语识别正确
- [ ] 数值和单位提取准确
- [ ] 输出格式符合规范
- [ ] 文件命名正确（ocr_result_YYYYMMDD_HHMMSS.md）
- [ ] 保护患者隐私（敏感信息脱敏）
- [ ] 错误处理得当（文件不存在、格式不支持等）

---

## 常见问题

### Q1: OCR识别准确率低
A: 尝试以下方法：
1. 使用图像预处理脚本优化图像质量
2. 调整Tesseract参数（PSM、OEM等）
3. 选择更合适的OCR技能（如pdf-ocr-layout）

### Q2: 医学术语识别错误
A: 参考以下资源：
1. `references/medical_terminology.md` - 术语对照表
2. 使用医学术语校正功能
3. 人工核对重要术语

### Q3: 表格识别效果差
A: 建议：
1. 使用 `pdf-ocr-layout` 技能（支持智能内容检测）
2. 尝试不同的PSM参数（psm 6适用于表格）
3. 手动调整表格结构

### Q4: 如何保护患者隐私
A: 遵循以下原则：
1. 使用本地OCR引擎
2. 不上传医疗文档到云端
3. 敏感信息脱敏（姓名、身份证号等）
4. 参考 `references/data_protection.md`

---

## 性能指标

- 图片OCR识别时间: < 5秒（单页）
- PDF文档处理速度: ~2秒/页
- 医学实体提取准确率: > 90%（清晰文档）
- 医学术语识别准确率: > 85%

---

## 后续改进方向

1. **智能纠错**: 基于上下文的OCR错误自动校正
2. **医学知识图谱**: 关联检验指标与疾病知识
3. **异常检测**: 自动标记异常检验结果
4. **多语言支持**: 扩展到更多语言（英文、日文等）
5. **模板识别**: 自动识别不同类型的医学报告模板
6. **云端备份**: 可选的加密云端备份功能
