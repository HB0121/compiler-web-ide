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


def main() -> int:
    checks = []

    lexical = assert_no_diagnostics("01_lexical/lexical_all_tokens.c")
    checks.append(("lexical tokens", len(lexical.tokens) > 20))
    assert_diagnostic_codes("01_lexical/lexical_errors.c", {"L003", "L004"})

    syntax = assert_no_diagnostics("02_syntax/syntax_control_flow.c")
    assert_contains(syntax.texts["ast"], "ForStmt", "syntax AST")
    assert_diagnostic_codes("02_syntax/syntax_errors.c", {"P001", "P002"})

    semantic = assert_no_diagnostics("03_semantic/semantic_symbols_ok.c")
    assert_contains(semantic.texts["function"], "int inc(int)", "semantic function symbols")
    assert_diagnostic_codes("03_semantic/semantic_errors.c", {"301", "302", "305", "309"})

    factorial = assert_no_diagnostics("04_ir_interpreter/interpreter_loop_factorial.c")
    assert_contains(factorial.texts["interpreter"], "builtin write(120)", "interpreter factorial")
    branch = assert_no_diagnostics("04_ir_interpreter/interpreter_branch_function.c")
    assert_contains(branch.texts["interpreter"], "builtin write(7)", "interpreter branch function")
    runtime = assert_no_diagnostics("04_ir_interpreter/interpreter_runtime_warning.c")
    assert_contains(runtime.texts["interpreter"], "runtime warning: division by zero", "runtime warning")
    assert_contains(runtime.texts["interpreter"], "runtime warning: modulo by zero", "runtime warning")

    assembly = assert_no_diagnostics("05_assembly_masm16/assembly_basic_masm16.c")
    assert_contains(assembly.texts["assembly"], "assume cs:code,ds:data,ss:stack,es:extended", "masm segments")
    assert_contains(assembly.texts["assembly"], "main:", "masm main")
    assert_contains(assembly.texts["assembly"], "add:", "masm function")
    read_write = assert_no_diagnostics("05_assembly_masm16/assembly_read_write.c")
    assert_contains(read_write.texts["assembly"], "CALL read", "masm read")
    assert_contains(read_write.texts["assembly"], "CALL write", "masm write")
    assert_contains(read_write.texts["assembly"], "read proc near", "masm read proc")
    assert_contains(read_write.texts["assembly"], "write proc near", "masm write proc")

    log_text = read_case("06_log_regex_automata/log_sample.log")
    ip_result = analyze_log_with_regex(log_text, r"(?:\d{1,3}\.){3}\d{1,3}")
    if len(ip_result.matches) != 3:
        raise AssertionError(f"log regex: expected 3 IP matches, got {len(ip_result.matches)}")
    assert_contains(ip_result.nfa_text, "NFA Graph for regex", "log nfa")
    assert_contains(ip_result.dfa_text, "DFA Graph from subset construction", "log dfa")
    no_match = analyze_log_with_regex(read_case("06_log_regex_automata/no_match.log"), r"\d{4}-\d{2}-\d{2}")
    if no_match.matches:
        raise AssertionError("log no-match: expected zero matches")

    llvm = assert_no_diagnostics("07_llvm_ir/llvm_branch_call.c")
    assert_contains(llvm.texts["llvm_ir"], "define i32 @main", "llvm main")
    assert_contains(llvm.texts["llvm_ir"], "alloca i32", "llvm stack slots")
    assert_contains(llvm.texts["llvm_ir"], "br i1", "llvm branch")
    assert_contains(llvm.texts["llvm_ir"], "ret i32", "llvm return")

    cfg = assert_no_diagnostics("08_cfg_dag_optimization/cfg_if_else.c")
    assert_contains(cfg.texts["basic_blocks"], "Basic Blocks", "cfg blocks")
    assert_contains(cfg.texts["cfg"], "Control Flow Graph", "cfg graph")
    assert_contains(cfg.texts["cfg"], "->", "cfg edges")
    dag = assert_no_diagnostics("08_cfg_dag_optimization/dag_common_subexpr.c")
    assert_contains(dag.texts["dag"], "reuse", "dag common subexpr")
    assert_contains(dag.texts["dag_optimized_quads"], "DAG optimized quadruples", "dag optimized quads")

    assert_diagnostic_codes("09_gui_editor_features/gui_realtime_errors.c", {"P002", "302"})
    gui_format = assert_no_diagnostics("09_gui_editor_features/gui_format_highlight.c")
    assert_contains(gui_format.texts["tokens"], "while", "gui keyword token")

    for label, ok in checks:
        if not ok:
            raise AssertionError(label)

    print("system tests: PASS")
    print("covered: lexical, syntax, semantic, IR/interpreter, MASM16, log regex NFA/DFA, LLVM IR, CFG/DAG, GUI editor inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
