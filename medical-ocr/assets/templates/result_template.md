# 医学文档OCR识别结果

## 基本信息

- **报告类型**: {{report_type}}
- **识别日期**: {{recognition_date}}
- **源文件**: {{source_file}}

---

## 患者信息

- **姓名**: {{patient_name}}
- **性别**: {{patient_gender}}
- **年龄**: {{patient_age}}
- **检查日期**: {{test_date}}

---

## 检验结果

### 检验指标

| 指标 | 指标名称 | 检验结果 | 单位 | 参考范围 | 提示 |
|------|---------|---------|------|---------|------|
{{#each test_results}}
| {{indicator}} | {{indicator_cn}} | {{value}} | {{unit}} | {{reference_range}} | {{status}} |
{{/each}}

---

## 异常指标

{{#if has_abnormal}}

以下指标超出正常范围：

| 指标 | 检验结果 | 参考范围 | 异常类型 |
|------|---------|---------|---------|
{{#each abnormal_results}}
| {{indicator}} | {{value}} {{unit}} | {{reference_range}} | {{abnormal_type}} |
{{/each}}

{{else}}
所有检验指标均在正常范围内。

{{/if}}

---

## 诊断结论

{{#if diagnoses}}

{{#each diagnoses}}
{{@index}}. {{this}}
{{/each}}

{{else}}
{{diagnosis_text}}

{{/if}}

---

## 医师建议

{{#if physician_notes}}

{{#each physician_notes}}
{{@index}}. {{this}}
{{/each}}

{{else}}
{{physician_notes_text}}

{{/if}}

---

## 原始识别文字

```
{{raw_ocr_text}}
```

---

## 处理信息

- **OCR引擎**: {{ocr_engine}}
- **识别准确率**: {{accuracy}}%
- **处理时间**: {{processing_time}}秒
- **预处理**: {{preprocessing_used}}
- **配置**: {{tesseract_config}}

---

**注意**:
1. OCR识别结果可能存在误差，重要医学信息请人工核对
2. 参考范围可能因实验室和仪器不同而有所差异
3. 本识别结果仅供参考，不能替代医师诊断
4. 如有疑问，请咨询专业医师

---

*生成于: {{generation_datetime}}*
