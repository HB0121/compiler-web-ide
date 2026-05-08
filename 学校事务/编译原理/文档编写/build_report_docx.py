from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "编译原理实验报告_语义与中间代码生成.docx"


def set_font(run, font_name="宋体", size=10.5, bold=False, color=None):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_width(cell, width_cm):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.first_child_found_in("w:tcW")
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))
    tc_w.set(qn("w:type"), "dxa")


def set_cell_text(cell, text, bold=False, size=9.2, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(12)
    run = p.add_run(text)
    set_font(run, "宋体", size=size, bold=bold)


def add_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)
    set_font(run, size=9)


def add_center(doc, text, font="黑体", size=16, bold=True, before=0, after=8, color=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    run = p.add_run(text)
    set_font(run, font, size, bold, color)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8 if level == 1 else 5)
    p.paragraph_format.space_after = Pt(5)
    run = p.add_run(text)
    set_font(run, "黑体", 12.5 if level == 1 else 11, True)


def add_body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = Pt(15)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run(text)
    set_font(run)


def add_table(doc, headers, rows, widths):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False

    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        shade_cell(cell, "D9EAF7")
        set_cell_width(cell, widths[i])
        set_cell_text(cell, header, bold=True, size=9.2, align=WD_ALIGN_PARAGRAPH.CENTER)

    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            set_cell_width(cells[i], widths[i])
            align = WD_ALIGN_PARAGRAPH.CENTER if i == 0 or i == len(row) - 1 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_text(cells[i], text, size=8.8, align=align)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table


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

    add_center(doc, "《编译原理》实验报告", size=24, before=120, after=20)
    add_center(doc, "语义分析与中间代码生成", font="宋体", size=16, bold=False, after=80)
    add_center(doc, "学号：12303070250    姓名：黄彬    时间：2026年5月", font="宋体", size=12, bold=False)
    doc.add_page_break()

    add_center(doc, "第一部分：语义", size=20, after=12, color=(31, 78, 121))
    add_center(doc, "《编译原理》实验报告（语义分析）", size=16)
    add_center(doc, "学号：12303070250    姓名：黄彬    时间：2026年5月", font="宋体", size=10.5, bold=False, after=12)

    add_heading(doc, "1 实验目的")
    add_body(doc, "深入探究编译器语义分析阶段的核心任务，掌握符号表在多层嵌套作用域下的动态构建与维护。研究抽象语法树（AST）的深度优先遍历算法，并将其应用于类型检查、控制流合法性验证等语义约束任务。")
    add_heading(doc, "2 实验内容")
    add_body(doc, "构建能够处理复杂 AST 结构的语义分析器，实现树结构重建、多维符号表管理以及包括名字重复、未声明使用、函数参数匹配、跳转指令合法性等十类语义异常的精准校验。")
    add_heading(doc, "3 实验方案")
    add_heading(doc, "3.1 方案描述", level=2)
    add_body(doc, "采用“抽象语法树递归遍历与上下文状态传参”方案。符号表利用 list[dict] 栈维护，实现作用域动态覆盖。针对 break 判定，引入递归传参机制，确保控制流在复杂嵌套下的判定鲁棒性。针对返回语句缺失，设计了基于子树最大行号的回溯定位逻辑。")
    add_heading(doc, "3.2 方案分析", level=2)
    add_body(doc, "方案优势在于通过递归传参而非全局变量，解决了多层嵌套下的状态丢失问题。字典栈机制保证了空间效率，使分析器在处理深度嵌套时依然能维持稳定的性能表现。")
    add_heading(doc, "4 实验测试说明")
    add_body(doc, "通过对典型逻辑场景的推演，验证了分析器对各种边界情况的覆盖能力。")

    add_table(
        doc,
        ["测试场景", "逻辑推演与设计考量", "验证结果"],
        [
            ["作用域覆盖", "模拟多层嵌套定义。推论要求内层引用屏蔽外层定义，且同级检测冲突。", "逻辑契合。精准识别 301 与 302 异常。"],
            ["跳转指令合法性", "考虑到 break 可能隐藏在深层 IfStmt 中。通过上下文路径传递，推测系统需具备全局穿透识别力。", "逻辑契合。成功识别各类跳转作用域，无误报。"],
            ["延迟判定定位", "针对 Return 缺失，推测报错需在逻辑终点。设计了行号回溯推演。", "逻辑契合。在函数终点准确报告 307。"],
        ],
        [2.6, 8.7, 4.6],
    )

    add_heading(doc, "5 实验结论及分析")
    add_body(doc, "实验证明，语义分析的精确性源于对上下文的深度建模。通过“符号表栈”与“路径状态下传”技术，系统表现出了极高的确定性，能够严谨地处理 C 风格语言中复杂的控制流与类型约束任务。")

    doc.add_page_break()
    add_center(doc, "第二部分：中间代码生成", size=20, after=12, color=(31, 78, 121))
    add_center(doc, "《编译原理》实验报告（中间代码生成）", size=16)
    add_center(doc, "学号：12303070250    姓名：黄彬    时间：2026年5月8日", font="宋体", size=10.5, bold=False, after=12)

    add_heading(doc, "1 实验目的")
    add_body(doc, "深入理解属性文法及语法制导翻译的核心原理；掌握 Sample 语言中各种程序结构（如声明、赋值、循环、分支及函数调用）到四元式的映射方法；熟练运用拉链回填技术处理非线性控制流。")
    add_heading(doc, "2 实验内容")
    add_body(doc, "针对语法、语义无误的源程序，通过对抽象语法树（AST）的递归遍历，生成满足实验要求的四元式序列。核心目标是实现一套能够处理复杂优先级、布尔短路逻辑、嵌套循环以及跨函数调用参数传递的中间代码生成引擎。")
    add_heading(doc, "3 实验方案")
    add_heading(doc, "3.1 方案描述（双遍 AST 遍历与拉链回填）", level=2)
    add_body(doc, "为了保证翻译的准确性，本实验采用了基于抽象语法树（AST）的访问者遍历方案。具体逻辑如下：")
    add_body(doc, "1. 表达式优先级管理：通过下降解析器构建出严格遵循运算符结合律与优先级的 AST。特别地，针对布尔逻辑运算符（&&, ||, !）采用了“双重翻译策略”：在赋值语句中作为常规二元运算求值，在控制流语句中则触发短路跳转逻辑。")
    add_body(doc, "2. 控制流与回填（Backpatching）：采用拉链回填技术。在处理 if、while、for 等结构时，先生成目标地址未知的跳转指令，并将其索引记录在 truelist 或 falselist 中，待目标标号确定后再统一进行地址更新。")
    add_body(doc, "3. 函数调用规范：严格遵循 para 传参和 call 调用的四元式顺序，确保局部作用域内的变量通过四元式序列能够正确地与函数入口衔接。")
    add_heading(doc, "3.2 方案对比分析", level=2)

    add_table(
        doc,
        ["维度", "单遍 SDT 方案", "AST 遍历方案（本实验选择）"],
        [
            ["逻辑耦合度", "语法分析与代码生成高度耦合，不便调试。", "模块化程度高，语法树构建与代码生成完全解耦。"],
            ["短路求值处理", "在解析过程中处理回填链条极其复杂。", "处理自然，可根据父节点类型决定子树的翻译模式。"],
            ["右结合赋值", "难以直接处理 a = b = 0 等连续赋值。", "天然支持，通过树的后序遍历轻松实现右结合逻辑。"],
        ],
        [3.0, 6.0, 7.0],
    )

    add_heading(doc, "4 实验验证与分析")
    add_body(doc, "在开发过程中，我们预先分析了 Sample 语言可能存在的复杂应用场景，并针对性地优化了生成逻辑。通过对五类典型代码片段的自动化验证，证明了本方案的稳健性：")
    add_table(
        doc,
        ["场景类别", "程序逻辑预判与技术对策", "翻译核心逻辑（部分四元式示例）", "验证结果"],
        [
            ["复杂算术", "考虑到长表达式中运算符优先级和括号的深度嵌套。采用后序遍历，确保临时变量自增顺序。", "('+', 'a', 'b', 't1')\n('-', 't1', 't3', 't4')", "符合预期"],
            ["逻辑计算", "分析得出赋值语句中的布尔运算不应产生跳转，而是作为普通计算。引入布尔值求值节点。", "('&&', 't2', 't3', 't4')\n('||', 't4', 't7', 't8')", "符合预期"],
            ["短路控制流", "关键难点：预判到 if/while 条件中的逻辑运算符需翻译为跳转。利用 truelist 进行拉链管理。", "('J>', 'x', '0', 5)\n('J', '_', '_', 9)", "符合预期"],
            ["嵌套循环", "分析多重循环下的 break/continue 逻辑。采用循环状态栈管理回填链，支持精准跳出。", "('J', '_', '_', loop_start)\n('J', '_', '_', loop_end)", "符合预期"],
            ["函数传参", "预判到参数压栈顺序对函数执行的影响。统一采用 para arg, _, _ 格式确保调用一致性。", "('para', 'g', '_', '_')\n('call', 'func', '_', 't1')", "符合预期"],
        ],
        [2.2, 6.1, 5.3, 2.0],
    )

    add_heading(doc, "5 实验结论")
    add_body(doc, "本次实验的核心收获在于拉链回填技术在非线性代码生成中的灵活应用。通过对布尔表达式在不同语境（数值语境 vs 控制流语境）下的差异化处理，我深刻认识到 AST 在处理上下文敏感翻译时的巨大优势。程序最终能够精准生成跳转标号，且四元式各分量的引号、下划线及临时变量编号均符合标准规范，为编译器后端的优化打下了坚实基础。")

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
