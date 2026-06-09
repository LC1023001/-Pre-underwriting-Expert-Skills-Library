#!/usr/bin/env python3
"""从 TTC 提取 TTF 字体，然后用 fpdf2 生成预核保评估报告 PDF"""
import sys, os

# Step 1: Extract TTF from TTC
from fontTools.ttLib import TTCollection
ttc = TTCollection("C:/Windows/Fonts/msyh.ttc")
ttf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msyh.ttf")
ttc.fonts[0].save(ttf_path)
print(f"TTF extracted: {ttf_path}")

# Step 2: Generate PDF
from fpdf import FPDF

class UWReport(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.add_font("YaHei", "", ttf_path)
        self.add_font("YaHei", "B", ttf_path)  # fpdf2 uses same TTF for bold
        self.set_auto_page_break(True, 15)
    
    def header(self):
        if self.page_no() == 1:
            self.set_fill_color(26, 79, 138)
            self.rect(0, 0, 210, 28, "F")
            self.set_font("YaHei", "B", 20)
            self.set_text_color(255, 255, 255)
            self.set_y(6)
            self.cell(0, 10, "预 核 保 评 估 报 告", align="C")
            self.set_font("YaHei", "", 9)
            self.set_y(18)
            self.cell(0, 6, "健康险核保评估 · 上分预核保系统", align="C")
        else:
            self.set_font("YaHei", "", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 6, f"预核保评估报告 - 张先生 | 第{self.page_no()}页", align="R")
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("YaHei", "", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"第 {self.page_no()} 页 | 评估专家：路畅（核保15年） | 报告生成：2026-06-09", align="C")
    
    def section_title(self, title, color=(26, 79, 138)):
        self.set_font("YaHei", "B", 13)
        self.set_text_color(*color)
        self.set_fill_color(240, 244, 252)
        self.cell(0, 9, f"  {title}", fill=True, ln=True)
        self.ln(3)
        self.set_text_color(34, 34, 34)
    
    def normal_text(self, text, size=10):
        self.set_font("YaHei", "", size)
        self.multi_cell(0, 5.5, text)
    
    def bold_text(self, text, size=10):
        self.set_font("YaHei", "B", size)
        self.multi_cell(0, 5.5, text)
    
    def key_value(self, key, value, w_key=40):
        self.set_font("YaHei", "", 9)
        self.cell(w_key, 6, key)
        self.set_font("YaHei", "B", 9)
        self.cell(0, 6, value, ln=True)
    
    def table_row(self, cells, widths, bold=False, fill=None, header=False):
        if fill:
            self.set_fill_color(*fill)
        if header:
            self.set_font("YaHei", "B", 8.5)
            self.set_text_color(26, 79, 138)
        else:
            self.set_font("YaHei", "", 8.5)
            self.set_text_color(34, 34, 34)
        if bold and not header:
            self.set_font("YaHei", "B", 8.5)
        
        for i, (c, w) in enumerate(zip(cells, widths)):
            if fill:
                self.cell(w, 7, f" {c}", border=0, fill=True)
            else:
                self.cell(w, 7, f" {c}", border=0)
        self.ln()
    
    def alert_box(self, text):
        self.set_fill_color(255, 247, 237)
        self.set_draw_color(254, 215, 170)
        self.set_font("YaHei", "", 9)
        x = self.get_x()
        y = self.get_y()
        self.rect(x, y, 190, 5)
        self.set_xy(x + 3, y + 1)
        self.multi_cell(184, 5, text)
        self.ln(3)

pdf = UWReport()
pdf.set_margins(10, 10, 10)

# Page 1: Header info + Verdict + Basic Info
pdf.add_page()

# Verdict bar
pdf.set_y(32)
pdf.set_fill_color(255, 251, 235)
pdf.set_draw_color(245, 158, 11)
pdf.set_line_width(0.8)
pdf.rect(10, 32, 190, 16, "DF")
pdf.set_draw_color(245, 158, 11)
pdf.line(10, 32, 10, 48)
pdf.set_line_width(0.2)

pdf.set_font("YaHei", "", 10)
pdf.set_text_color(100, 100, 100)
pdf.set_xy(16, 33)
pdf.cell(30, 6, "综合核保结论：")
pdf.set_font("YaHei", "B", 14)
pdf.set_text_color(26, 79, 138)
pdf.cell(100, 6, "大概率标准体 — 甲状腺需核实")

# Risk badge
pdf.set_fill_color(254, 243, 199)
pdf.set_text_color(180, 83, 9)
pdf.set_font("YaHei", "B", 10)
pdf.set_xy(162, 34)
pdf.cell(34, 8, "  中低风险  ", fill=True)
pdf.set_text_color(34, 34, 34)

# Basic info
pdf.set_y(54)
pdf.section_title("基本信息")
info = [
    ("被保人", "张 *（已脱敏）", "性别/年龄", "男 / 28岁"),
    ("身高", "171 cm", "体重", "79.2 kg（理想 66 kg）"),
    ("BMI", "27.1 kg/m\u00b2（超重）", "血压", "116/63 mmHg（正常）"),
    ("体检日期", "2025-12-19", "体检机构", "上海美张门诊部"),
]
for a, b, c, d in info:
    pdf.set_font("YaHei", "", 9)
    pdf.cell(22, 6, a)
    pdf.set_font("YaHei", "B", 9)
    bw = 38
    pdf.cell(bw, 6, b)
    pdf.set_font("YaHei", "", 9)
    pdf.cell(22, 6, c)
    pdf.set_font("YaHei", "B", 9)
    pdf.cell(0, 6, d, ln=True)

pdf.ln(4)

# Abnormal summary table
pdf.section_title("异常指标汇总（核保分级）", (180, 30, 30))

cols = ["级别", "异常项目", "结果值", "参考范围", "核保影响"]
widths = [22, 60, 45, 35, 28]
pdf.table_row(cols, widths, header=True, fill=(238, 243, 251))

rows = [
    ("A 核保关键", "甲状腺右叶未见显影", "CT发现", "--", "需核实"),
    ("B 核保关注", "血尿酸(UA)升高", "469 \u03bcmol/L \u2191", "208~428", "无症状多标准体"),
    ("B 核保关注", "BMI 超重", "27.1 kg/m\u00b2", "18.5~23.9", "代谢风险因子"),
    ("B 核保关注", "轻度脂肪肝", "超声+CT均见", "--", "肝功全正常"),
    ("B 核保关注", "肝内钙化灶", "超声+CT均见", "--", "良性不影响"),
    ("C 建议关注", "窦性心律不齐", "HR 80次/分", "--", "生理性无影响"),
    ("C 建议关注", "左下肺钙化灶", "边界尚清", "--", "陈旧性良性"),
    ("C 建议关注", "总胆固醇(TC)", "5.09 mmol/L", "\u22645.2", "正常范围"),
]
for r in rows:
    fill_color = (255, 237, 237) if "A" in r[0] else ((255, 247, 237) if "B" in r[0] else ((224, 242, 254) if "C" in r[0] else None))
    pdf.table_row(r, widths, bold=("A" in r[0]), fill=fill_color)

pdf.ln(4)

# 甲状腺专题
pdf.section_title("核保重点 — 甲状腺右叶未见显影", (180, 30, 30))

pdf.set_fill_color(255, 247, 237)
pdf.set_font("YaHei", "", 9)
pdf.set_text_color(124, 45, 18)
pdf.set_x(10)
alert_text = (
    "影像与触诊存在矛盾：\n"
    "  \u2022 CT报告：甲状腺右叶未见显影，请结合临床病史\n"
    "  \u2022 外科触诊：甲状腺未见明显异常\n\n"
    "可能原因：\n"
    "  1. 先天性单叶甲状腺（一侧缺如）\u2014 最常见，无临床意义\n"
    "  2. 既往甲状腺手术切除史\n"
    "  3. 右叶萎缩或功能减退\n\n"
    "关键缺失：本次体检未做甲状腺功能（TSH/FT4/FT3），这是核保决策的核心依据！"
)
y0 = pdf.get_y()
pdf.multi_cell(190, 5, alert_text, fill=True)
pdf.ln(2)

pdf.set_fill_color(240, 249, 255)
pdf.set_text_color(12, 74, 110)
pdf.set_font("YaHei", "B", 9)
pdf.cell(0, 5, "  核保预估结论（按情景）：", fill=True, ln=True)
pdf.set_font("YaHei", "", 9)
conclusions = [
    "\u2022 甲功正常 + 无手术史 \u2192 绝大多数公司 标准体",
    "\u2022 甲功正常 + 有手术史 \u2192 重疾可能 除外甲状腺相关",
    "\u2022 甲功异常(TSH\u2191) \u2192 可能 延期或加费",
]
for c in conclusions:
    pdf.set_fill_color(240, 249, 255)
    pdf.cell(0, 5, f"  {c}", fill=True, ln=True)

# 投保前行动
pdf.set_font("YaHei", "B", 9)
pdf.set_text_color(2, 105, 161)
pdf.cell(0, 7, "  行动建议：投保前先做甲功五项 + 甲状腺超声，结合报告预核保", ln=True)
pdf.set_text_color(34, 34, 34)
pdf.ln(2)

# 正常指标
pdf.section_title("正常指标确认", (34, 139, 34))

pdf.set_font("YaHei", "", 8.5)
normal_items = [
    ("空腹血糖 4.78", "ALT 12.4", "AST 16.0", "GGT 13.4"),
    ("TG 1.18", "LDL-C 3.11", "HDL-C 1.23", "Cr 82.1"),
    ("T-BIL 13.7", "EF 63%", "血压 116/63", "Hb 147"),
    ("血常规 全正常", "尿常规 全正常", "心脏彩超 正常", "头颅CT 正常"),
]
cols_n = [47.5, 47.5, 47.5, 47.5]
for row in normal_items:
    for val, w in zip(row, cols_n):
        pdf.set_fill_color(240, 253, 244)
        pdf.set_text_color(22, 101, 52)
        pdf.cell(w, 6, f"  OK {val}", fill=True)
    pdf.ln()

pdf.ln(4)

# 产品推荐
pdf.section_title("各产品类型投保建议")

pcols = ["产品类型", "投保建议", "预估承保条件", "备注"]
pwidths = [30, 22, 65, 73]
pdf.table_row(pcols, pwidths, header=True, fill=(238, 243, 251))

products = [
    ("重大疾病险", "[OK] 可投保", "甲功正常>标准体；手术史>除外甲状腺", "需核实甲状腺右叶缺失原因"),
    ("百万医疗险", "[OK] 可投保", "智核大概率通过", "推荐先做智核测试"),
    ("定期寿险", "[OK] 标准体", "标准费率，无障碍", "28岁男性，保费极低"),
    ("防癌险", "[OK] 标准体", "无影响因素", "适合即刻投保"),
    ("长期护理险", "[OK] 标准体", "年龄优势，标准费率", "适合投保"),
]
for r in products:
    pdf.table_row(r, pwidths)

pdf.ln(4)

# 保险公司匹配
pdf.section_title("主要保险公司预估结论")

companies = [
    "平安人寿  [OK] 标准体（甲功正常前提）",
    "太平人寿  [OK] 标准体（甲功正常前提）",
    "友邦AIA  [OK] 标准体（建议预核保确认）",
    "泰康人寿  [OK] 标准体",
    "中国人寿  [OK] 标准体",
    "昆仑健康  [OK] 标准体",
    "阳光人寿  [OK] 标准体",
    "水滴保  [OK] 标准体（互联网智核首选）",
]

for i, c in enumerate(companies):
    x = 10 + (i % 2) * 95
    y = pdf.get_y() + (i // 2) * 10
    if i % 2 == 0 and i > 0:
        pass
    pdf.set_font("YaHei", "", 9)
    pdf.set_xy(x, pdf.get_y() if i % 2 == 0 else pdf.get_y())
    pdf.set_fill_color(250, 251, 252)
    pdf.set_draw_color(229, 233, 240)
    pdf.rect(x, pdf.get_y() if i % 2 == 0 else pdf.get_y() - 10, 93, 8, "DF")
    pdf.set_xy(x + 2, (pdf.get_y() if i % 2 == 0 else pdf.get_y() - 8))
    pdf.cell(90, 6, c)
    if i % 2 == 1:
        pdf.ln(10)
    elif i == len(companies) - 1:
        pdf.ln(10)

pdf.ln(4)

# 关键告知清单
pdf.section_title("投保关键告知清单")
items = [
    ("\u2460 甲状腺右叶未见显影", 
     "需告知是否有甲状腺手术史；建议投保前完善甲功五项+甲状腺超声。若无手术史、甲功正常，先天性单叶绝大多数公司标准体。"),
    ("\u2461 血尿酸偏高（469 \u03bcmol/L）",
     "需告知是否有痛风发作史/肾结石史。无症状性高尿酸血症通常不影响承保。"),
    ("\u2462 轻度脂肪肝",
     "需提供肝功能检查结果（ALT 12.4、AST 16.0均正常）。轻度脂肪肝+肝功正常，主流公司均可标准体。"),
]
for title, desc in items:
    pdf.set_font("YaHei", "B", 9)
    pdf.set_text_color(26, 79, 138)
    pdf.cell(0, 6, title, ln=True)
    pdf.set_font("YaHei", "", 8.5)
    pdf.set_text_color(80, 80, 80)
    pdf.set_x(14)
    pdf.multi_cell(184, 5, desc)
    pdf.ln(1)
pdf.set_text_color(34, 34, 34)

pdf.ln(2)

# 行动建议
pdf.section_title("投保行动建议")
steps = [
    "立即可投保：定期寿险、防癌险 \u2014 无需任何补充检查",
    "补充检查后再投保重疾/百万医疗：先完成甲功五项+甲状腺超声",
    "智核测试：通过水滴保/微保等平台做智能核保预测试",
    "预核保申请：重疾险建议选择支持预核保的公司（友邦、太平）",
    "如实告知：甲状腺右叶缺失情况必须如实告知，切勿隐瞒",
    "生活干预：控制饮食+有氧运动降BMI和尿酸，半年后复查",
]
for s in steps:
    pdf.set_font("YaHei", "", 9)
    pdf.cell(0, 6, f"  \u2022  {s}", ln=True)

pdf.ln(4)

# Disclaimer
pdf.set_font("YaHei", "", 7)
pdf.set_text_color(156, 163, 175)
disclaimer = (
    "免责声明：本评估为AI辅助参考意见，不构成正式核保结论。实际投保结果以保险公司正式核保为准。"
    "评估报告已脱敏处理，不含原始身份信息。投保时务必如实告知健康状况，避免因未如实告知导致理赔纠纷。"
    "本系统仅供专业人士参考使用。"
)
pdf.multi_cell(0, 4, disclaimer)
pdf.ln(1)
pdf.set_font("YaHei", "", 7)
pdf.cell(0, 4, "评估基于：2025年12月19日上海美张门诊部体检报告（共18页） | 生成：2026-06-09 | 评估专家：路畅", ln=True)

# Output
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "预核保评估报告_张先生.pdf")
pdf.output(output_path)
print(f"\nPDF 生成完成: {output_path}")
