from pathlib import Path
from typing import List, Optional

from .assembly import function_params_from_ast, quads_to_masm16
from .cfg_dag import analyze_control_flow
from .interpreter import interpret_quads
from .ir import format_quads, generate_quads
from .lexer import Lexer
from .llvm_ir import quads_to_llvm_ir, verify_llvm_ir
from .models import ASTNode, Diagnostic, OutputTexts, PipelineResult, SymbolInfo, Token, format_ast
from .optimizer import optimize_quads
from .parser import Parser
from .semantic import SemanticAnalyzer
from .target_code import quads_to_target_code


OUTPUT_NAMES = {
    "tokens": "tokens.txt",
    "ast": "ast.txt",
    "semantic_errors": "semantic_errors.txt",
    "const": "const.txt",
    "var": "var.txt",
    "function": "function.txt",
    "quads": "quads.txt",
    "optimized_quads": "optimized_quads.txt",
    "basic_blocks": "basic_blocks.txt",
    "cfg": "cfg.txt",
    "dag": "dag.txt",
    "dag_optimized_quads": "dag_optimized_quads.txt",
    "interpreter": "interpreter.txt",
    "llvm_ir": "llvm_ir.txt",
    "llvm_verify": "llvm_verify.txt",
    "target_code": "target_code.txt",
    "assembly": "assembly.asm",
    "optimized_target_code": "optimized_target_code.txt",
}


def run_pipeline(source: str) -> PipelineResult:
    tokens, lexer_diagnostics = Lexer().tokenize(source)

    ast: Optional[ASTNode] = None
    parser_diagnostics: List[Diagnostic] = []
    if tokens:
        ast, parser_diagnostics = Parser(tokens).parse()

    semantic_diagnostics: List[Diagnostic] = []
    const_symbols: List[SymbolInfo] = []
    var_symbols: List[SymbolInfo] = []
    function_symbols: List[SymbolInfo] = []
    if ast is not None:
        analyzer = SemanticAnalyzer().analyze_program(ast)
        semantic_diagnostics = analyzer.diagnostics
        const_symbols = analyzer.history_symbols["const"]
        var_symbols = analyzer.history_symbols["var"]
        function_symbols = analyzer.history_symbols["func"]

    quads = generate_quads(ast) if ast is not None else []
    optimized_quads = optimize_quads(quads) if quads else []
    control_flow = analyze_control_flow(quads) if quads else None
    interpreter_text = interpret_quads(quads).format() if quads else ""
    llvm_ir_text = quads_to_llvm_ir(quads) if quads else ""
    llvm_verify_text = verify_llvm_ir(llvm_ir_text) if llvm_ir_text else ""
    target_code_text = explain_target_code(quads_to_target_code(quads)) if quads else ""
    assembly_text = quads_to_masm16(quads, function_params_from_ast(ast)) if quads else ""
    target_optimized_quads = optimize_quads(control_flow.optimized_quads) if control_flow else optimized_quads
    optimized_target_code_text = explain_target_code(quads_to_target_code(target_optimized_quads)) if target_optimized_quads else ""
    diagnostics = lexer_diagnostics + parser_diagnostics + semantic_diagnostics
    texts = build_texts(
        tokens,
        ast,
        semantic_diagnostics,
        const_symbols,
        var_symbols,
        function_symbols,
        quads,
        optimized_quads,
        control_flow.basic_blocks_text if control_flow else "",
        control_flow.cfg_text if control_flow else "",
        control_flow.dag_text if control_flow else "",
        control_flow.dag_optimized_quads_text if control_flow else "",
        interpreter_text,
        llvm_ir_text,
        llvm_verify_text,
        target_code_text,
        assembly_text,
        optimized_target_code_text,
    )

    return PipelineResult(
        tokens=tokens,
        ast=ast,
        diagnostics=diagnostics,
        const_symbols=const_symbols,
        var_symbols=var_symbols,
        function_symbols=function_symbols,
        quads=quads,
        texts=texts,
    )


def build_texts(
    tokens: List[Token],
    ast: Optional[ASTNode],
    semantic_diagnostics: List[Diagnostic],
    const_symbols: List[SymbolInfo],
    var_symbols: List[SymbolInfo],
    function_symbols: List[SymbolInfo],
    quads,
    optimized_quads,
    basic_blocks_text: str,
    cfg_text: str,
    dag_text: str,
    dag_optimized_quads_text: str,
    interpreter_text: str,
    llvm_ir_text: str,
    llvm_verify_text: str,
    target_code_text: str,
    assembly_text: str,
    optimized_target_code_text: str,
) -> OutputTexts:
    return {
        "tokens": format_tokens(tokens),
        "ast": format_ast(ast),
        "semantic_errors": format_semantic_errors(semantic_diagnostics),
        "const": format_symbols(const_symbols, "const"),
        "var": format_symbols(var_symbols, "var"),
        "function": format_symbols(function_symbols, "function"),
        "quads": format_quads(quads),
        "optimized_quads": format_optimized_quads(optimized_quads),
        "basic_blocks": basic_blocks_text,
        "cfg": cfg_text,
        "dag": dag_text,
        "dag_optimized_quads": dag_optimized_quads_text,
        "interpreter": interpreter_text,
        "llvm_ir": llvm_ir_text,
        "llvm_verify": llvm_verify_text,
        "target_code": target_code_text,
        "assembly": assembly_text,
        "optimized_target_code": optimized_target_code_text,
    }


def format_tokens(tokens: List[Token]) -> str:
    lines = [f"{token.text} {token.code} {token.line}" for token in tokens]
    return "\n".join(lines) + ("\n" if lines else "")


def format_optimized_quads(quads) -> str:
    if not quads:
        return ""
    return "optimized quadruples\n" + format_quads(quads)


def format_semantic_errors(diagnostics: List[Diagnostic]) -> str:
    semantic_diagnostics = [diagnostic for diagnostic in diagnostics if diagnostic.phase == "semantic"]
    if not semantic_diagnostics:
        return "Line | Phase | Code | Message\n--- | --- | --- | ---\n"
    lines = ["Line | Phase | Code | Message", "--- | --- | --- | ---"]
    for diagnostic in semantic_diagnostics:
        lines.append(f"{diagnostic.line} | {diagnostic.phase} | {diagnostic.code} | {diagnostic.message}")
    return "\n".join(lines) + ("\n" if lines else "")


def format_symbols(symbols: List[SymbolInfo], kind: str) -> str:
    if kind == "function":
        lines = ["Name | Return Type | Parameters", "--- | --- | ---"]
        for symbol in symbols:
            params = ", ".join(symbol.get("params", []) or ["void"])
            lines.append(f"{symbol.get('name', '')} | {symbol.get('type', 'unknown')} | {params}")
    else:
        title = "Const" if kind == "const" else "Variable"
        lines = [f"{title} Name | Type", "--- | ---"]
        for symbol in symbols:
            lines.append(f"{symbol.get('name', '')} | {symbol.get('type', 'unknown')}")
    return "\n".join(lines) + ("\n" if lines else "")


def number_lines(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    width = len(str(len(lines)))
    return "\n".join(f"{index:>{width}} | {line}" for index, line in enumerate(lines, start=1)) + "\n"


def explain_target_code(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    output = ["Line | Target Code | Meaning", "--- | --- | ---"]
    for index, line in enumerate(lines, start=1):
        output.append(f"{index} | {line} | {explain_target_instruction(line)}")
    return "\n".join(output) + "\n"


def explain_target_instruction(line: str) -> str:
    instruction = line.strip()
    if not instruction:
        return ""
    if instruction.endswith(":"):
        return f"label {instruction[:-1]}: jump target"
    if instruction.startswith(";"):
        return "comment or skipped helper instruction"

    parts = instruction.split(None, 1)
    op = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    args = [item.strip() for item in rest.split(",")] if rest else []

    if op == "FUNC" and args:
        return f"enter function {args[0]}"
    if op == "MOV" and len(args) == 2:
        return f"{args[0]} = {args[1]}"
    if op == "LOAD" and len(args) == 2:
        return f"load {args[1]} into register {args[0]}"
    if op in {"ADD", "SUB", "MUL", "DIV", "MOD"} and len(args) == 2:
        symbols = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/", "MOD": "%"}
        return f"{args[0]} = {args[0]} {symbols[op]} {args[1]}"
    if op == "STORE" and len(args) == 2:
        return f"{args[0]} = {args[1]}"
    if op in {"JG", "JL", "JGE", "JLE", "JE", "JNE"} and len(args) == 3:
        signs = {"JG": ">", "JL": "<", "JGE": ">=", "JLE": "<=", "JE": "==", "JNE": "!="}
        return f"if {args[0]} {signs[op]} {args[1]}, jump to {args[2]}"
    if op == "JMP" and args:
        return f"jump to {args[0]}"
    if op == "RET" and args:
        return f"return {args[0]}"
    if op == "END":
        return "program end"
    return "target instruction"


def write_outputs(result: PipelineResult, output_dir=Path("outputs")) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for key, filename in OUTPUT_NAMES.items():
        (output_path / filename).write_text(result.texts[key], encoding="utf-8")
    (output_path / "llvm_ir.ll").write_text(result.texts["llvm_ir"], encoding="utf-8")
