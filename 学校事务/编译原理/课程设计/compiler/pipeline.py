from pathlib import Path
from typing import List, Optional

from .assembly import function_params_from_ast, quads_to_masm16
from .cfg_dag import analyze_control_flow
from .interpreter import interpret_quads
from .ir import format_quads, generate_quads
from .lexer import Lexer
from .llvm_ir import quads_to_llvm_ir
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
    target_code_text = quads_to_target_code(quads) if quads else ""
    assembly_text = quads_to_masm16(quads, function_params_from_ast(ast)) if quads else ""
    optimized_target_code_text = quads_to_target_code(optimized_quads) if optimized_quads else ""
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
    lines = [f"{diagnostic.line} {diagnostic.code}" for diagnostic in diagnostics if diagnostic.phase == "semantic"]
    return "\n".join(lines) + ("\n" if lines else "")


def format_symbols(symbols: List[SymbolInfo], kind: str) -> str:
    if kind == "function":
        lines = [
            f"{symbol.get('type', 'unknown')} {symbol.get('name', '')}({', '.join(symbol.get('params', []) or ['void'])})"
            for symbol in symbols
        ]
    else:
        lines = [f"{symbol.get('type', 'unknown')} {symbol.get('name', '')}" for symbol in symbols]
    return "\n".join(lines) + ("\n" if lines else "")


def write_outputs(result: PipelineResult, output_dir=Path("outputs")) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for key, filename in OUTPUT_NAMES.items():
        (output_path / filename).write_text(result.texts[key], encoding="utf-8")
