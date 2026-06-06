from dataclasses import dataclass
from pathlib import Path

from .pipeline import PipelineResult, run_pipeline


@dataclass
class SubmissionCase:
    stem: str
    source_path: Path
    txt_path: Path
    int_path: Path
    doc_path: Path


def generate_submission_package(input_dir: Path | str, output_dir: Path | str) -> list[SubmissionCase]:
    source_root = Path(input_dir)
    target_root = Path(output_dir)
    target_root.mkdir(parents=True, exist_ok=True)

    generated: list[SubmissionCase] = []
    for source_path in sorted(source_root.rglob("test*.txt")):
        source = read_source_text(source_path)
        result = run_pipeline(source)
        stem = source_path.stem
        txt_path = target_root / f"{stem}.txt"
        int_path = target_root / f"{stem}.int"
        doc_path = target_root / f"{stem}.doc"

        txt_path.write_text(source, encoding="utf-8")
        int_path.write_text(build_int_text(stem, source, result), encoding="utf-8")
        doc_path.write_text(build_doc_rtf(stem, source, result), encoding="utf-8")

        generated.append(
            SubmissionCase(
                stem=stem,
                source_path=source_path,
                txt_path=txt_path,
                int_path=int_path,
                doc_path=doc_path,
            )
        )
    return generated


def read_source_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def build_int_text(stem: str, source: str, result: PipelineResult) -> str:
    diagnostics = format_diagnostics(result)
    sections = [
        ("测试用例", stem),
        ("源程序", source.rstrip()),
        ("TOKEN 序列", result.texts.get("tokens", "").rstrip()),
        ("AST", result.texts.get("ast", "").rstrip()),
        ("中间代码（四元式）", result.texts.get("quads", "").rstrip()),
        ("MASM16 汇编程序代码", result.texts.get("assembly", "").rstrip()),
        ("编译诊断", diagnostics.rstrip()),
    ]
    output: list[str] = []
    for title, content in sections:
        output.append(f"========== {title} ==========")
        output.append(content or "-")
        output.append("")
    return "\n".join(output)


def format_diagnostics(result: PipelineResult) -> str:
    if not result.diagnostics:
        return "No diagnostics"
    lines = ["Line | Phase | Code | Message", "--- | --- | --- | ---"]
    for diagnostic in result.diagnostics:
        lines.append(f"{diagnostic.line} | {diagnostic.phase} | {diagnostic.code} | {diagnostic.message}")
    return "\n".join(lines)


def build_doc_rtf(stem: str, source: str, result: PipelineResult) -> str:
    return "{\\rtf1\\ansi\\deff0\n" + "\n".join(
        [
            rtf_heading(f"{stem} 运行结果输出"),
            rtf_paragraph(f"测试用例：{stem}"),
            rtf_paragraph(f"Token 数量：{len(result.tokens)}"),
            rtf_paragraph(f"诊断数量：{len(result.diagnostics)}"),
            rtf_paragraph(f"四元式数量：{len(result.quads)}"),
            rtf_paragraph("运行界面说明：在 GUI 左侧打开源程序后点击“运行”，右侧 Results 区域展示 Tokens、AST、中间代码、Interpreter、Assembly 等结果；下方 Diagnostics 区域展示错误提示。"),
            rtf_heading("源程序"),
            rtf_pre(source),
            rtf_heading("执行结果摘要"),
            rtf_pre(result.texts.get("interpreter", "").strip() or "No interpreter output"),
            rtf_heading("诊断信息"),
            rtf_pre(format_diagnostics(result)),
        ]
    ) + "\n}"


def rtf_heading(text: str) -> str:
    return r"\pard\b " + rtf_escape(text) + r"\b0\par"


def rtf_paragraph(text: str) -> str:
    return r"\pard " + rtf_escape(text) + r"\par"


def rtf_pre(text: str) -> str:
    lines = text.splitlines() or [""]
    escaped_lines = [rtf_escape(line) for line in lines]
    return r"\pard\f1 " + r"\par ".join(escaped_lines) + r"\par"


def rtf_escape(text: str) -> str:
    parts: list[str] = []
    for char in text:
        code = ord(char)
        if char in ("\\", "{", "}"):
            parts.append("\\" + char)
        elif char == "\t":
            parts.append(r"\tab ")
        elif char == "\n":
            parts.append(r"\par ")
        elif code < 128:
            parts.append(char)
        else:
            signed = code if code <= 32767 else code - 65536
            parts.append(f"\\u{signed}?")
    return "".join(parts)
