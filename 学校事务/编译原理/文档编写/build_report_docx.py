from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "编译原理实验报告_语义与中间代码生成.docx"

PARTS = [
    ("第一部分：语义", ROOT / "编译原理实验报告_语义分析_v2.pdf"),
    ("第二部分：中间代码生成", ROOT / "中间代码生成.pdf"),
]


def set_east_asian_font(run, font_name):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)


def set_cell_shading(paragraph, fill):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)
    set_east_asian_font(run, "宋体")
    run.font.size = Pt(9)


def clean_line(line):
    return line.rstrip()


def extract_pdf_pages(path):
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout") or ""
        pages.append([clean_line(line) for line in text.splitlines()])
    return pages


def classify(line):
    stripped = line.strip()
    if not stripped:
        return "blank"
    if stripped.startswith("《编译原理》实验报告"):
        return "pdf_title"
    if stripped.startswith("学号：") or stripped.startswith("学号： "):
        return "meta"
    if re.match(r"^[1-5]\s+.+", stripped):
        return "h2"
    if re.match(r"^3\.[12]\s+.+", stripped):
        return "h3"
    if re.search(r"\s{4,}", line) or stripped.startswith(("测试场景", "维度", "场景类", "作用域", "跳转指令", "延迟判定")):
        return "layout"
    return "body"


def add_styled_line(doc, line):
    kind = classify(line)
    stripped = line.strip()

    if kind == "blank":
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = Pt(4)
        return

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = Pt(15)

    if kind == "pdf_title":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(10)
        run = p.add_run(stripped)
        set_east_asian_font(run, "黑体")
        run.font.size = Pt(16)
        run.bold = True
        return

    if kind == "meta":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(12)
        run = p.add_run(re.sub(r"\s+", "    ", stripped))
        set_east_asian_font(run, "宋体")
        run.font.size = Pt(10.5)
        return

    if kind == "h2":
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(stripped)
        set_east_asian_font(run, "黑体")
        run.font.size = Pt(12.5)
        run.bold = True
        return

    if kind == "h3":
        p.paragraph_format.space_before = Pt(5)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(stripped)
        set_east_asian_font(run, "黑体")
        run.font.size = Pt(11)
        run.bold = True
        return

    if kind == "layout":
        p.paragraph_format.line_spacing = Pt(12)
        p.paragraph_format.space_after = Pt(1)
        run = p.add_run(line)
        set_east_asian_font(run, "宋体")
        run.font.name = "Consolas"
        run.font.size = Pt(8.2)
        return

    p.paragraph_format.first_line_indent = Cm(0.74)
    run = p.add_run(stripped)
    set_east_asian_font(run, "宋体")
    run.font.size = Pt(10.5)


def add_part_heading(doc, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run(title)
    set_east_asian_font(run, "黑体")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(31, 78, 121)

    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    line.paragraph_format.space_after = Pt(18)
    r = line.add_run("—" * 20)
    set_east_asian_font(r, "宋体")
    r.font.color.rgb = RGBColor(31, 78, 121)


def build():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.25)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.35)
    section.right_margin = Cm(2.35)
    add_page_number(section)

    styles = doc.styles
    styles["Normal"].font.name = "宋体"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    styles["Normal"].font.size = Pt(10.5)

    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(120)
    cover.paragraph_format.space_after = Pt(20)
    run = cover.add_run("《编译原理》实验报告")
    set_east_asian_font(run, "黑体")
    run.bold = True
    run.font.size = Pt(24)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(80)
    run = subtitle.add_run("语义分析与中间代码生成")
    set_east_asian_font(run, "宋体")
    run.font.size = Pt(16)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run("学号：12303070250    姓名：黄彬    时间：2026年5月")
    set_east_asian_font(run, "宋体")
    run.font.size = Pt(12)

    doc.add_page_break()

    for part_index, (part_title, pdf_path) in enumerate(PARTS):
        if part_index:
            doc.add_page_break()
        add_part_heading(doc, part_title)
        pages = extract_pdf_pages(pdf_path)
        for page_index, lines in enumerate(pages):
            if page_index:
                doc.add_page_break()
            for line in lines:
                add_styled_line(doc, line)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
