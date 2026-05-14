from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compiler.log_automata import analyze_log_with_regex
from compiler.pipeline import run_pipeline


BASE = Path(__file__).resolve().parent


def read_case(relative: str) -> str:
    return (BASE / relative).read_text(encoding="utf-8")


def assert_contains(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label}: expected to contain {needle!r}")


def assert_diagnostic_codes(relative: str, expected_codes: set[str]) -> None:
    result = run_pipeline(read_case(relative))
    codes = {diagnostic.code for diagnostic in result.diagnostics}
    missing = expected_codes - codes
    if missing:
        raise AssertionError(f"{relative}: missing diagnostics {sorted(missing)}, got {sorted(codes)}")


def assert_no_diagnostics(relative: str):
    result = run_pipeline(read_case(relative))
    if result.diagnostics:
        diagnostics = [(d.line, d.phase, d.code) for d in result.diagnostics]
        raise AssertionError(f"{relative}: expected no diagnostics, got {diagnostics}")
    return result


def target_code_row_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if " | " in line and not line.startswith(("Line |", "---")))


def main() -> int:
    checks = []

    lexical = assert_no_diagnostics("01_词法分析/lexical_all_tokens.c")
    checks.append(("lexical tokens", len(lexical.tokens) > 20))
    assert_diagnostic_codes("01_词法分析/lexical_errors.c", {"L003", "L004"})
    lexical_text = assert_no_diagnostics("01_词法分析/lexical_comments_strings.c")
    assert_contains(lexical_text.texts["tokens"], "' * '", "single quoted output literal")
    assert_contains(lexical_text.texts["tokens"], '"done"', "string literal")

    syntax = assert_no_diagnostics("02_语法分析/syntax_control_flow.c")
    assert_contains(syntax.texts["ast"], "ForStmt", "syntax AST")
    assert_diagnostic_codes("02_语法分析/syntax_errors.c", {"P001", "P002"})
    nested = assert_no_diagnostics("02_语法分析/syntax_nested_loops.c")
    assert_contains(nested.texts["ast"], "WhileStmt", "nested while AST")
    assert_contains(nested.texts["ast"], "ForStmt", "nested for AST")

    semantic = assert_no_diagnostics("03_语义分析/semantic_symbols_ok.c")
    assert_contains(semantic.texts["function"], "Name | Return Type | Parameters", "semantic function symbols")
    assert_contains(semantic.texts["function"], "inc | int | int", "semantic function symbols")
    assert_diagnostic_codes("03_语义分析/semantic_errors.c", {"301", "302", "305", "309"})
    assert_diagnostic_codes("03_语义分析/semantic_return_type_error.c", {"307", "310"})

    factorial = assert_no_diagnostics("04_中间代码与解释执行/interpreter_loop_factorial.c")
    assert_contains(factorial.texts["interpreter"], "builtin write(120)", "interpreter factorial")
    branch = assert_no_diagnostics("04_中间代码与解释执行/interpreter_branch_function.c")
    assert_contains(branch.texts["interpreter"], "builtin write(7)", "interpreter branch function")
    runtime = assert_no_diagnostics("04_中间代码与解释执行/interpreter_runtime_warning.c")
    assert_contains(runtime.texts["interpreter"], "runtime warning: division by zero", "runtime warning")
    assert_contains(runtime.texts["interpreter"], "runtime warning: modulo by zero", "runtime warning")
    array_sum = assert_no_diagnostics("04_中间代码与解释执行/interpreter_array_sum.c")
    assert_contains(array_sum.texts["quads"], "[]=", "array store quads")
    assert_contains(array_sum.texts["quads"], "=[]", "array load quads")
    assert_contains(array_sum.texts["interpreter"], "builtin write(10)", "array sum interpreter")

    assembly = assert_no_diagnostics("05_MASM16汇编生成/assembly_basic_masm16.c")
    assert_contains(assembly.texts["assembly"], "assume cs:code,ds:data,ss:stack,es:extended", "masm segments")
    assert_contains(assembly.texts["assembly"], "main:", "masm main")
    assert_contains(assembly.texts["assembly"], "add:", "masm function")
    read_write = assert_no_diagnostics("05_MASM16汇编生成/assembly_read_write.c")
    assert_contains(read_write.texts["assembly"], "CALL read", "masm read")
    assert_contains(read_write.texts["assembly"], "CALL write", "masm write")
    assert_contains(read_write.texts["assembly"], "read proc near", "masm read proc")
    assert_contains(read_write.texts["assembly"], "write proc near", "masm write proc")
    recursive_asm = assert_no_diagnostics("05_MASM16汇编生成/assembly_recursive_factor.c")
    assert_contains(recursive_asm.texts["assembly"], "factor:", "recursive factor label")
    assert_contains(recursive_asm.texts["assembly"], "CALL factor", "recursive factor call")
    assert_contains(recursive_asm.texts["assembly"], "ss:[bp+4]", "stack parameter access")

    log_text = read_case("06_日志正则自动机/log_sample.log")
    ip_result = analyze_log_with_regex(log_text, r"(?:\d{1,3}\.){3}\d{1,3}")
    if len(ip_result.matches) != 3:
        raise AssertionError(f"log regex: expected 3 IP matches, got {len(ip_result.matches)}")
    assert_contains(ip_result.nfa_text, "NFA Graph for regex", "log nfa")
    assert_contains(ip_result.dfa_text, "DFA Graph from subset construction", "log dfa")
    no_match = analyze_log_with_regex(read_case("06_日志正则自动机/no_match.log"), r"\d{4}-\d{2}-\d{2}")
    if no_match.matches:
        raise AssertionError("log no-match: expected zero matches")
    mixed_log = read_case("06_日志正则自动机/log_mixed_formats.log")
    status_result = analyze_log_with_regex(mixed_log, r"status=\d{3}|STATUS:\s*\d{3}")
    if len(status_result.matches) != 3:
        raise AssertionError(f"log regex: expected 3 status matches, got {len(status_result.matches)}")
    assert_contains(status_result.format_matches(), "Line | Column | Kind | Value", "log coordinate header")

    llvm = assert_no_diagnostics("07_LLVM_IR生成/llvm_branch_call.c")
    assert_contains(llvm.texts["llvm_ir"], "define i32 @main", "llvm main")
    assert_contains(llvm.texts["llvm_ir"], "alloca i32", "llvm stack slots")
    assert_contains(llvm.texts["llvm_ir"], "br i1", "llvm branch")
    assert_contains(llvm.texts["llvm_ir"], "ret i32", "llvm return")
    assert_contains(llvm.texts["llvm_verify"], "Internal verifier: PASS", "llvm internal verifier")
    assert_contains(llvm.texts["llvm_verify"], "External tools:", "llvm external verifier")
    llvm_mod = assert_no_diagnostics("07_LLVM_IR生成/llvm_modulo_loop.c")
    assert_contains(llvm_mod.texts["llvm_ir"], "srem i32", "llvm modulo")
    assert_contains(llvm_mod.texts["llvm_ir"], "br i1", "llvm loop branch")

    cfg = assert_no_diagnostics("08_CFG与DAG优化/cfg_if_else.c")
    assert_contains(cfg.texts["basic_blocks"], "Basic Blocks", "cfg blocks")
    assert_contains(cfg.texts["cfg"], "Control Flow Graph", "cfg graph")
    assert_contains(cfg.texts["cfg"], "Successors", "cfg edges")
    dag = assert_no_diagnostics("08_CFG与DAG优化/dag_common_subexpr.c")
    assert_contains(dag.texts["dag"], "reuse", "dag common subexpr")
    assert_contains(dag.texts["dag_optimized_quads"], "DAG optimized quadruples", "dag optimized quads")
    complex_cfg_dag = assert_no_diagnostics("08_CFG与DAG优化/cfg_dag_complex.c")
    assert_contains(complex_cfg_dag.texts["basic_blocks"], "Leaders", "complex leaders")
    assert_contains(complex_cfg_dag.texts["cfg"], "Predecessors", "complex cfg predecessor")
    assert_contains(complex_cfg_dag.texts["dag"], "common:", "complex dag common subexpr")
    assert_contains(complex_cfg_dag.texts["dag_optimized_quads"], "Optimized instruction count", "complex optimized count")
    if target_code_row_count(complex_cfg_dag.texts["optimized_target_code"]) >= target_code_row_count(complex_cfg_dag.texts["target_code"]):
        raise AssertionError("complex optimized target code: expected fewer rows than original target code")
    assert_contains(complex_cfg_dag.texts["optimized_target_code"], "MOV x, 225", "complex optimized target folded expression")

    assert_diagnostic_codes("09_GUI编辑器功能/gui_realtime_errors.c", {"P002", "302"})
    gui_format = assert_no_diagnostics("09_GUI编辑器功能/gui_format_highlight.c")
    assert_contains(gui_format.texts["tokens"], "while", "gui keyword token")

    for label, ok in checks:
        if not ok:
            raise AssertionError(label)

    print("system tests: PASS")
    print("covered: lexical, syntax, semantic, IR/interpreter, MASM16, log regex NFA/DFA, LLVM IR, CFG/DAG, GUI editor inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
