from pathlib import Path
from typing import List, Optional

from .ir import format_quads, generate_quads
from .lexer import Lexer
from .models import ASTNode, Diagnostic, OutputTexts, PipelineResult, SymbolInfo, Token, format_ast
from .parser import Parser
from .semantic import SemanticAnalyzer


OUTPUT_NAMES = {
    "tokens": "tokens.txt",
    "ast": "ast.txt",
    "semantic_errors": "semantic_errors.txt",
    "const": "const.txt",
    "var": "var.txt",
    "function": "function.txt",
    "quads": "quads.txt",
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
    diagnostics = lexer_diagnostics + parser_diagnostics + semantic_diagnostics
    texts = build_texts(tokens, ast, semantic_diagnostics, const_symbols, var_symbols, function_symbols, quads)

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
) -> OutputTexts:
    return {
        "tokens": format_tokens(tokens),
        "ast": format_ast(ast),
        "semantic_errors": format_semantic_errors(semantic_diagnostics),
        "const": format_symbols(const_symbols, "const"),
        "var": format_symbols(var_symbols, "var"),
        "function": format_symbols(function_symbols, "function"),
        "quads": format_quads(quads),
    }


def format_tokens(tokens: List[Token]) -> str:
    lines = [f"{token.text} {token.code} {token.line}" for token in tokens]
    return "\n".join(lines) + ("\n" if lines else "")


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
