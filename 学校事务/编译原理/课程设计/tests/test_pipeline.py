import tempfile
import unittest
from pathlib import Path


SAMPLE_SOURCE = """
const int limit = 3;

int add(int a, int b) {
    int c = a + b;
    return c;
}

int main() {
    int i = 0;
    int total = 0;
    while (i < limit) {
        total = add(total, i);
        i = i + 1;
    }
    return total;
}
"""


class PipelineSmokeTests(unittest.TestCase):
    def test_pipeline_outputs_expected_sections(self):
        from compiler.pipeline import run_pipeline

        result = run_pipeline(SAMPLE_SOURCE)

        self.assertIn("const", result.texts["tokens"])
        self.assertIn("FunctionDef(int main)", result.texts["ast"])
        self.assertIn("Const Name | Type", result.texts["const"])
        self.assertIn("limit | int", result.texts["const"])
        self.assertIn("Variable Name | Type", result.texts["var"])
        self.assertIn("total | int", result.texts["var"])
        self.assertIn("Name | Return Type | Parameters", result.texts["function"])
        self.assertIn("add | int | int, int", result.texts["function"])
        self.assertIn("call", result.texts["quads"])
        self.assertIn("return_value", result.texts["interpreter"])
        self.assertIn("define i32 @main()", result.texts["llvm_ir"])
        self.assertIn("Internal verifier: PASS", result.texts["llvm_verify"])
        self.assertIn("FUNC main", result.texts["target_code"])
        self.assertIn("Line | Target Code | Meaning", result.texts["target_code"])
        self.assertIn("enter function main", result.texts["target_code"])
        self.assertIn("assume cs:code,ds:data,ss:stack,es:extended", result.texts["assembly"])
        self.assertIn("main:", result.texts["assembly"])
        self.assertIn("optimized", result.texts["optimized_quads"])
        self.assertIn("FUNC main", result.texts["optimized_target_code"])
        self.assertIn("Line | Target Code | Meaning", result.texts["optimized_target_code"])
        self.assertIn("Basic Blocks", result.texts["basic_blocks"])
        self.assertIn("Control Flow Graph", result.texts["cfg"])
        self.assertIn("DAG", result.texts["dag"])
        self.assertIn("DAG optimized quadruples", result.texts["dag_optimized_quads"])

    def test_pipeline_writes_output_files(self):
        from compiler.pipeline import run_pipeline, write_outputs

        result = run_pipeline(SAMPLE_SOURCE)
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_outputs(result, out_dir)
            self.assertTrue((out_dir / "tokens.txt").exists())
            self.assertTrue((out_dir / "ast.txt").exists())
            self.assertTrue((out_dir / "semantic_errors.txt").exists())
            self.assertTrue((out_dir / "quads.txt").exists())
            self.assertTrue((out_dir / "interpreter.txt").exists())
            self.assertTrue((out_dir / "llvm_ir.txt").exists())
            self.assertTrue((out_dir / "llvm_ir.ll").exists())
            self.assertTrue((out_dir / "llvm_verify.txt").exists())
            self.assertTrue((out_dir / "target_code.txt").exists())
            self.assertTrue((out_dir / "assembly.asm").exists())
            self.assertTrue((out_dir / "optimized_quads.txt").exists())
            self.assertTrue((out_dir / "optimized_target_code.txt").exists())
            self.assertTrue((out_dir / "basic_blocks.txt").exists())
            self.assertTrue((out_dir / "cfg.txt").exists())
            self.assertTrue((out_dir / "dag.txt").exists())
            self.assertTrue((out_dir / "dag_optimized_quads.txt").exists())
            self.assertIn("main", (out_dir / "tokens.txt").read_text(encoding="utf-8"))
            self.assertIn("FunctionDef(int main)", (out_dir / "ast.txt").read_text(encoding="utf-8"))
            self.assertIn("sys", (out_dir / "quads.txt").read_text(encoding="utf-8"))
            self.assertIn("return_value", (out_dir / "interpreter.txt").read_text(encoding="utf-8"))
            self.assertIn("define i32 @main()", (out_dir / "llvm_ir.txt").read_text(encoding="utf-8"))
            self.assertIn("Internal verifier: PASS", (out_dir / "llvm_verify.txt").read_text(encoding="utf-8"))
            self.assertIn("FUNC main", (out_dir / "target_code.txt").read_text(encoding="utf-8"))
            self.assertIn("assume cs:code,ds:data,ss:stack,es:extended", (out_dir / "assembly.asm").read_text(encoding="utf-8"))
            self.assertIn("optimized", (out_dir / "optimized_quads.txt").read_text(encoding="utf-8"))
            self.assertIn("FUNC main", (out_dir / "optimized_target_code.txt").read_text(encoding="utf-8"))
            self.assertIn("Basic Blocks", (out_dir / "basic_blocks.txt").read_text(encoding="utf-8"))
            self.assertIn("Control Flow Graph", (out_dir / "cfg.txt").read_text(encoding="utf-8"))
            self.assertIn("DAG", (out_dir / "dag.txt").read_text(encoding="utf-8"))
            self.assertIn("DAG optimized quadruples", (out_dir / "dag_optimized_quads.txt").read_text(encoding="utf-8"))

    def test_pipeline_returns_parser_diagnostic_for_missing_logical_rhs(self):
        from compiler.pipeline import run_pipeline

        result = run_pipeline("int main(){int a;if(a &&){return 1;}return 0;}")

        self.assertIn("parser", [diagnostic.phase for diagnostic in result.diagnostics])

    def test_pipeline_accepts_course_style_main_string_write_and_modulo(self):
        from compiler.pipeline import run_pipeline

        source = 'main(){int x;x=10%3;write("ok");return x;}'
        result = run_pipeline(source)

        self.assertEqual([], result.diagnostics)
        self.assertIn("('%'", result.texts["quads"])
        self.assertIn("builtin write(ok)", result.texts["interpreter"])
        self.assertIn("return_value | 1", result.texts["interpreter"])

    def test_pipeline_accepts_course_style_arrays(self):
        from compiler.pipeline import run_pipeline

        source = "int a[5]; main(){int i;i=2;a[0]=1;a[1]=1;a[i]=a[i-1]+a[i-2];write(a[i]);}"
        result = run_pipeline(source)

        self.assertEqual([], result.diagnostics)
        self.assertIn("('[]=', '1', '0', 'a')", result.texts["quads"])
        self.assertIn("('=[]', 'a'", result.texts["quads"])
        self.assertIn("builtin write(2)", result.texts["interpreter"])


class LexerTests(unittest.TestCase):
    def test_lexer_recognizes_comments_operators_and_lines(self):
        from compiler.lexer import Lexer

        source = "int main() {\n  // comment\n  int x = 1;\n  x = x + 2;\n}\n"
        tokens, diagnostics = Lexer().tokenize(source)
        texts = [token.text for token in tokens]

        self.assertEqual([], diagnostics)
        self.assertEqual(
            ["int", "main", "(", ")", "{", "int", "x", "=", "1", ";", "x", "=", "x", "+", "2", ";", "}"],
            texts,
        )
        self.assertEqual(101, tokens[0].code)
        self.assertEqual(700, tokens[1].code)
        self.assertEqual(401, tokens[8].code)
        self.assertEqual(3, tokens[5].line)

    def test_lexer_recognizes_escaped_char_literals(self):
        from compiler.lexer import Lexer

        tokens, diagnostics = Lexer().tokenize("char a = 'x'; char n = '\\n'; char t = '\\t'; char r = '\\r'; char z = '\\0'; char q = '\\''; char b = '\\\\';")
        char_literals = [token for token in tokens if token.code == 403]

        self.assertEqual([], diagnostics)
        self.assertEqual(["'x'", "'\\n'", "'\\t'", "'\\r'", "'\\0'", "'\\''", "'\\\\'"], [token.text for token in char_literals])
        self.assertEqual([403, 403, 403, 403, 403, 403, 403], [token.code for token in char_literals])

    def test_lexer_rejects_empty_and_accepts_course_text_literals(self):
        from compiler.lexer import Lexer

        tokens, diagnostics = Lexer().tokenize("char empty = ''; char multi = 'ab';")

        self.assertEqual(["'ab'"], [token.text for token in tokens if token.code == 403])
        self.assertEqual(1, len(diagnostics))
        self.assertTrue(all(diagnostic.phase == "lexer" for diagnostic in diagnostics))


class ParserTests(unittest.TestCase):
    def parse_source(self, source):
        from compiler.lexer import Lexer
        from compiler.parser import Parser

        tokens, lexer_diagnostics = Lexer().tokenize(source)
        ast, parser_diagnostics = Parser(tokens).parse()

        self.assertEqual([], lexer_diagnostics)
        self.assertEqual([], parser_diagnostics)
        return ast

    def main_compound(self, source):
        ast = self.parse_source(source)
        function = ast.children[0]
        return function.children[-1]

    def test_for_statement_preserves_declaration_initializer(self):
        compound = self.main_compound("int main(){for(int i=0;i<3;i=i+1){break;}}")
        for_node = compound.children[0]

        self.assertEqual("ForStmt", for_node.name)
        self.assertEqual("VarDecl", for_node.children[0].name)
        self.assertEqual("int i", for_node.children[0].value)
        self.assertEqual("0", for_node.children[0].children[0].name)
        self.assertEqual("<", for_node.children[1].name)
        self.assertEqual("=", for_node.children[2].name)
        self.assertEqual("Compound", for_node.children[3].name)
        self.assertEqual("BreakStmt", for_node.children[3].children[0].name)

    def test_grouped_assignment_expr_parses_recursively(self):
        compound = self.main_compound("int main(){int x;int y;x=(y=1);}")
        assign = compound.children[2].children[0]

        self.assertEqual("=", assign.name)
        self.assertEqual("x", assign.children[0].name)
        self.assertEqual("=", assign.children[1].name)
        self.assertEqual("y", assign.children[1].children[0].name)
        self.assertEqual("1", assign.children[1].children[1].name)

    def test_if_condition_accepts_assignment_expression(self):
        compound = self.main_compound("int main(){int x;if(x=2){break;}}")
        if_node = compound.children[1]

        self.assertEqual("IfStmt", if_node.name)
        self.assertEqual("=", if_node.children[0].name)
        self.assertEqual("x", if_node.children[0].children[0].name)
        self.assertEqual("2", if_node.children[0].children[1].name)
        self.assertEqual("Compound", if_node.children[1].name)

    def test_for_statement_preserves_omitted_init_position(self):
        compound = self.main_compound("int main(){int i=0;for(;i<3;i=i+1){continue;}}")
        for_node = compound.children[1]

        self.assertEqual("ForStmt", for_node.name)
        self.assertEqual("Empty", for_node.children[0].name)
        self.assertEqual("<", for_node.children[1].name)
        self.assertEqual("=", for_node.children[2].name)
        self.assertEqual("Compound", for_node.children[3].name)


class SemanticTests(unittest.TestCase):
    def analyze_source(self, source):
        from compiler.lexer import Lexer
        from compiler.parser import Parser
        from compiler.semantic import SemanticAnalyzer

        tokens, lexer_diagnostics = Lexer().tokenize(source)
        ast, parser_diagnostics = Parser(tokens).parse()

        self.assertEqual([], lexer_diagnostics)
        self.assertEqual([], parser_diagnostics)
        return SemanticAnalyzer().analyze_program(ast)

    def test_reports_undeclared_identifier_assignment(self):
        analyzer = self.analyze_source("int main() { x = 1; return 0; }")

        self.assertIn("302", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_for_decl_scope_allows_break_and_records_loop_var(self):
        analyzer = self.analyze_source("int main(){for(int i=0;i<2;i=i+1){break;} return 0;}")
        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]
        var_names = [row["name"] for row in analyzer.history_symbols["var"]]

        self.assertNotIn("308", codes)
        self.assertIn("i", var_names)

    def test_for_bare_identifier_condition_reports_undeclared_identifier(self):
        analyzer = self.analyze_source("int main(){for(int i=0;x;i=i+1){break;} return 0;}")
        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]

        self.assertIn("302", codes)
        self.assertNotIn("308", codes)

    def test_mismatched_prototype_definition_reports_duplicate_function(self):
        analyzer = self.analyze_source("int f(int a); float f(float b){return b;} int main(){return 0;}")

        self.assertIn("303", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_declared_only_function_call_reports_undefined_function(self):
        analyzer = self.analyze_source("int f(); int main(){return f();}")

        self.assertIn("304", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_builtin_read_write_declarations_are_allowed(self):
        analyzer = self.analyze_source("int read(); void write(int a); void main(){int n;n=read();write(n);}")

        self.assertNotIn("304", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_course_style_read_argument_is_accepted(self):
        analyzer = self.analyze_source("main(){int n;read(n);write(n);}")

        self.assertNotIn("305", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_course_style_write_accepts_single_quoted_text(self):
        analyzer = self.analyze_source("main(){write(' * ');write('\\n');}")

        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]
        self.assertNotIn("L004", codes)
        self.assertNotIn("305", codes)

    def test_course_style_void_return_value_is_accepted(self):
        analyzer = self.analyze_source("void f(){return 0;} main(){f();}")

        self.assertNotIn("307", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_forward_declared_later_defined_function_call_is_allowed(self):
        analyzer = self.analyze_source("int f(); int main(){return f();} int f(){return 1;}")

        self.assertNotIn("304", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_for_omitted_init_uses_declared_condition_identifier(self):
        analyzer = self.analyze_source("int main(){int i=0;for(;i<3;i=i+1){continue;} return i;}")
        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]

        self.assertNotIn("302", codes)
        self.assertNotIn("308", codes)

    def test_mixed_relational_operands_report_expression_type_mismatch(self):
        analyzer = self.analyze_source("int main(){int a; char c; if(a<c){return 1;} return 0;}")

        self.assertIn("310", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_unary_minus_preserves_literal_type_for_initializers_and_returns(self):
        int_analyzer = self.analyze_source("int main(){int x=-1; return x;}")
        int_codes = [diagnostic.code for diagnostic in int_analyzer.diagnostics]
        float_analyzer = self.analyze_source("float main(){return -1;}")

        self.assertNotIn("310", int_codes)
        self.assertNotIn("307", int_codes)
        self.assertIn("307", [diagnostic.code for diagnostic in float_analyzer.diagnostics])

    def test_unary_not_returns_int_type(self):
        int_analyzer = self.analyze_source("int main(){int x=!1.0; return x;}")
        float_analyzer = self.analyze_source("float main(){return !1.0;}")

        self.assertNotIn("310", [diagnostic.code for diagnostic in int_analyzer.diagnostics])
        self.assertIn("307", [diagnostic.code for diagnostic in float_analyzer.diagnostics])

    def test_if_bare_identifier_condition_reports_undeclared_identifier(self):
        analyzer = self.analyze_source("int main(){if(x){return 1;} return 0;}")

        self.assertIn("302", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_while_bare_identifier_condition_reports_undeclared_identifier(self):
        analyzer = self.analyze_source("int main(){while(x){break;} return 0;}")
        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]

        self.assertIn("302", codes)
        self.assertNotIn("308", codes)

    def test_do_while_bare_identifier_condition_reports_undeclared_identifier(self):
        analyzer = self.analyze_source("int main(){do{break;}while(x); return 0;}")
        codes = [diagnostic.code for diagnostic in analyzer.diagnostics]

        self.assertIn("302", codes)
        self.assertNotIn("308", codes)


class IRTests(unittest.TestCase):
    def parse_source(self, source):
        from compiler.lexer import Lexer
        from compiler.parser import Parser

        tokens, lexer_diagnostics = Lexer().tokenize(source)
        ast, parser_diagnostics = Parser(tokens).parse()

        self.assertEqual([], lexer_diagnostics)
        self.assertEqual([], parser_diagnostics)
        return ast

    def assert_no_unresolved_jumps(self, quads):
        unresolved = [quad for quad in quads if str(quad[0]).startswith("J") and quad[3] == "_"]

        self.assertEqual([], unresolved)

    def test_generates_basic_assignment_arithmetic_return_and_sys(self):
        from compiler.ir import format_quads, generate_quads

        ast = self.parse_source("int main(){int x=1; x=x+2; return x;}")
        formatted = format_quads(generate_quads(ast))

        self.assertIn("main", formatted)
        self.assertIn("'='", formatted)
        self.assertIn("'+'", formatted)
        self.assertIn("'ret'", formatted)
        self.assertIn("'sys'", formatted)

    def test_generates_while_relational_and_unconditional_jumps(self):
        from compiler.ir import generate_quads

        ast = self.parse_source("int main(){int i=0; while(i<3){i=i+1;} return i;}")
        quads = generate_quads(ast)
        ops = [quad[0] for quad in quads]

        self.assertIn("J<", ops)
        self.assertIn("J", ops)
        self.assert_no_unresolved_jumps(quads)

    def test_generates_for_continue_without_crashing(self):
        from compiler.ir import generate_quads

        ast = self.parse_source("int main(){for(int i=0;i<2;i=i+1){continue;} return 0;}")
        quads = generate_quads(ast)
        ops = [quad[0] for quad in quads]
        step_index = ops.index("+")
        jumps_to_step = [quad for quad in quads if quad[0] == "J" and quad[3] == step_index]

        self.assertIn("J<", ops)
        self.assertIn("J", ops)
        self.assertGreaterEqual(len(jumps_to_step), 2)
        self.assert_no_unresolved_jumps(quads)

    def test_generates_for_with_omitted_init_condition_jump(self):
        from compiler.ir import generate_quads

        ast = self.parse_source("int main(){int i=0;for(;i<3;i=i+1){continue;} return i;}")
        quads = generate_quads(ast)
        ops = [quad[0] for quad in quads]

        self.assertIn("J<", ops)
        self.assert_no_unresolved_jumps(quads)

    def test_partial_return_non_main_false_branch_targets_implicit_ret(self):
        from compiler.ir import generate_quads

        ast = self.parse_source("int f(int x){if(x)return 1;} int main(){return 0;}")
        quads = generate_quads(ast)
        false_jump = quads[2]
        false_target = false_jump[3]

        self.assertEqual("J", false_jump[0])
        self.assertIsInstance(false_target, int)
        self.assertEqual("ret", quads[false_target][0])
        self.assertNotEqual("main", quads[false_target][0])
        self.assert_no_unresolved_jumps(quads)


class InterpreterTests(unittest.TestCase):
    def test_interpreter_handles_builtin_read_and_write(self):
        from compiler.interpreter import interpret_quads

        quads = [
            ("main", "_", "_", "_"),
            ("call", "read", "_", "t1"),
            ("=", "t1", "_", "n"),
            ("para", "n", "_", "_"),
            ("call", "write", "_", "_"),
            ("sys", "_", "_", "_"),
        ]
        result = interpret_quads(quads)

        self.assertEqual(0, result.variables["n"])
        self.assertIn("builtin read() -> 0", result.trace)
        self.assertIn("builtin write(0)", result.trace)

    def test_interpreter_does_not_crash_on_division_by_zero(self):
        from compiler.interpreter import interpret_quads

        quads = [
            ("main", "_", "_", "_"),
            ("/", 1, 0, "t1"),
            ("%", 1, 0, "t2"),
            ("sys", "_", "_", "_"),
        ]
        result = interpret_quads(quads)

        self.assertEqual(0, result.variables["t1"])
        self.assertEqual(0, result.variables["t2"])
        self.assertIn("runtime warning: division by zero, result forced to 0", result.trace)
        self.assertIn("runtime warning: modulo by zero, result forced to 0", result.trace)

    def test_interpreter_does_not_crash_on_invalid_jump_target(self):
        from compiler.interpreter import interpret_quads

        quads = [
            ("main", "_", "_", "_"),
            ("J", "_", "_", "_"),
            ("sys", "_", "_", "_"),
        ]
        result = interpret_quads(quads)

        self.assertIn("runtime warning: invalid jump target _, continuing", result.trace)

    def test_interprets_assignment_arithmetic_loop_and_return(self):
        from compiler.interpreter import interpret_quads
        from compiler.ir import generate_quads

        ast = IRTests().parse_source("int main(){int i=0; int sum=0; while(i<3){sum=sum+i; i=i+1;} return sum;}")
        result = interpret_quads(generate_quads(ast))

        self.assertEqual(3, result.return_value)
        self.assertEqual(3, result.variables["i"])
        self.assertEqual(3, result.variables["sum"])
        formatted = result.format()
        self.assertIn("Execution Result", formatted)
        self.assertIn("Variables", formatted)
        self.assertIn("Execution Trace", formatted)
        self.assertIn("return_value | 3", formatted)
        self.assertIn("sum | 3", formatted)
        self.assertIn("程序最终返回值", formatted)

    def test_interpreter_applies_global_initializers_before_main(self):
        from compiler.interpreter import interpret_quads

        quads = [
            ("=", "3", "_", "limit"),
            ("main", "_", "_", "_"),
            ("=", "0", "_", "i"),
            ("J<", "i", "limit", 5),
            ("J", "_", "_", 8),
            ("+", "i", "1", "t1"),
            ("=", "t1", "_", "i"),
            ("J", "_", "_", 3),
            ("ret", "_", "_", "i"),
            ("sys", "_", "_", "_"),
        ]
        result = interpret_quads(quads)

        self.assertEqual(3, result.return_value)
        self.assertEqual(3, result.variables["limit"])

    def test_interpreter_executes_simple_function_call(self):
        from compiler.interpreter import interpret_quads

        quads = [
            ("add", "_", "_", "_"),
            ("+", "a", "b", "t1"),
            ("ret", "_", "_", "t1"),
            ("ret", "_", "_", "_"),
            ("main", "_", "_", "_"),
            ("=", "1", "_", "x"),
            ("=", "2", "_", "y"),
            ("para", "x", "_", "_"),
            ("para", "y", "_", "_"),
            ("call", "add", "_", "t2"),
            ("ret", "_", "_", "t2"),
            ("sys", "_", "_", "_"),
        ]
        result = interpret_quads(quads)

        self.assertEqual(3, result.return_value)
        self.assertEqual(3, result.variables["t2"])


class LLVMIRTests(unittest.TestCase):
    def test_converts_assignment_arithmetic_and_return(self):
        from compiler.llvm_ir import quads_to_llvm_ir

        quads = [
            ("=", "10", "_", "a"),
            ("=", "20", "_", "b"),
            ("+", "a", "b", "t1"),
            ("=", "t1", "_", "c"),
            ("ret", "_", "_", "c"),
        ]
        llvm = quads_to_llvm_ir(quads)

        self.assertIn("define i32 @main()", llvm)
        self.assertIn("%a = alloca i32", llvm)
        self.assertIn("store i32 10, i32* %a", llvm)
        self.assertIn("%t1 = add i32", llvm)
        self.assertIn("store i32 %t1, i32* %c", llvm)
        self.assertIn("ret i32", llvm)

    def test_converts_conditional_jumps_to_cmp_and_br(self):
        from compiler.llvm_ir import quads_to_llvm_ir

        quads = [
            ("=", "10", "_", "a"),
            ("=", "20", "_", "b"),
            ("J>", "a", "b", 4),
            ("J", "_", "_", 6),
            ("=", "a", "_", "max"),
            ("J", "_", "_", 7),
            ("=", "b", "_", "max"),
            ("ret", "_", "_", "max"),
        ]
        llvm = quads_to_llvm_ir(quads)

        self.assertIn("icmp sgt i32", llvm)
        self.assertIn("br i1", llvm)
        self.assertIn("label %L4", llvm)
        self.assertIn("L6:", llvm)
        self.assertNotRegex(llvm, r"store i32 [^\n]+\nL\d+:")

    def test_llvm_conversion_uses_main_region_when_function_labels_exist(self):
        from compiler.llvm_ir import quads_to_llvm_ir

        quads = [
            ("helper", "_", "_", "_"),
            ("ret", "_", "_", "1"),
            ("ret", "_", "_", "_"),
            ("main", "_", "_", "_"),
            ("=", "2", "_", "x"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]
        llvm = quads_to_llvm_ir(quads)

        self.assertNotIn("ret i32 1", llvm)
        self.assertIn("store i32 2, i32* %x", llvm)

    def test_llvm_conversion_keeps_call_temps_defined(self):
        from compiler.llvm_ir import quads_to_llvm_ir

        quads = [
            ("main", "_", "_", "_"),
            ("para", "x", "_", "_"),
            ("call", "add", "_", "t1"),
            ("=", "t1", "_", "x"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]
        llvm = quads_to_llvm_ir(quads)

        self.assertNotIn("%add = alloca i32", llvm)
        self.assertIn("%t1 = add i32 0, 0", llvm)
        self.assertIn("store i32 %t1, i32* %x", llvm)

    def test_generates_engineering_style_write_and_verification_report(self):
        from compiler.llvm_ir import quads_to_llvm_ir, verify_llvm_ir

        quads = [
            ("main", "_", "_", "_"),
            ("=", "15", "_", "x"),
            ("para", "x", "_", "_"),
            ("call", "write", "_", "t1"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]
        llvm = quads_to_llvm_ir(quads)
        report = verify_llvm_ir(llvm)

        self.assertIn("declare i32 @printf(i8*, ...)", llvm)
        self.assertIn("@.fmt_int", llvm)
        self.assertIn("call i32 (i8*, ...) @printf", llvm)
        self.assertIn("Internal verifier: PASS", report)
        self.assertIn("External tools:", report)

    def test_llvm_verifier_reports_clang_fallback_commands(self):
        from compiler.llvm_ir import quads_to_llvm_ir, verify_llvm_ir

        llvm = quads_to_llvm_ir([("main", "_", "_", "_"), ("ret", "_", "_", "0"), ("sys", "_", "_", "_")])
        report = verify_llvm_ir(llvm)

        self.assertIn("clang -c outputs/llvm_ir.ll -o outputs/llvm_ir.obj", report)


class TargetCodeTests(unittest.TestCase):
    def test_converts_assignment_arithmetic_and_return(self):
        from compiler.target_code import quads_to_target_code

        quads = [
            ("main", "_", "_", "_"),
            ("=", "10", "_", "a"),
            ("+", "a", "2", "t1"),
            ("=", "t1", "_", "a"),
            ("ret", "_", "_", "a"),
            ("sys", "_", "_", "_"),
        ]
        target = quads_to_target_code(quads)

        self.assertIn("FUNC main", target)
        self.assertIn("MOV a, 10", target)
        self.assertIn("LOAD R1, a", target)
        self.assertIn("ADD R1, 2", target)
        self.assertIn("STORE t1, R1", target)
        self.assertIn("RET a", target)
        self.assertIn("END", target)

    def test_converts_conditional_and_unconditional_jumps(self):
        from compiler.target_code import quads_to_target_code

        quads = [
            ("main", "_", "_", "_"),
            ("=", "0", "_", "i"),
            ("J<", "i", "3", 4),
            ("J", "_", "_", 6),
            ("+", "i", "1", "t1"),
            ("J", "_", "_", 2),
            ("ret", "_", "_", "i"),
            ("sys", "_", "_", "_"),
        ]
        target = quads_to_target_code(quads)

        self.assertIn("L2:", target)
        self.assertIn("JL i, 3, L4", target)
        self.assertIn("JMP L6", target)
        self.assertIn("L6:", target)


class AssemblyTests(unittest.TestCase):
    def test_generates_masm16_for_assignment_arithmetic_and_return(self):
        from compiler.assembly import quads_to_masm16

        quads = [
            ("main", "_", "_", "_"),
            ("+", "1", "2", "t1"),
            ("=", "t1", "_", "x"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]
        assembly = quads_to_masm16(quads)

        self.assertIn("assume cs:code,ds:data,ss:stack,es:extended", assembly)
        self.assertIn("main:", assembly)
        self.assertIn("ADD AX,2", assembly)
        self.assertIn("MOV ss:[bp-", assembly)
        self.assertIn("int 21h", assembly)

    def test_generates_masm16_globals_without_duplicate_main_proc(self):
        from compiler.assembly import quads_to_masm16

        quads = [
            ("=", "3", "_", "limit"),
            ("main", "_", "_", "_"),
            ("J<", "i", "limit", 4),
            ("J", "_", "_", 5),
            ("ret", "_", "_", "limit"),
            ("sys", "_", "_", "_"),
        ]
        assembly = quads_to_masm16(quads, {"main": []})

        self.assertEqual(1, assembly.count("main:"))
        self.assertIn("limit dw 3", assembly)
        self.assertIn("CMP AX,limit", assembly)

    def test_generates_masm16_for_function_call_with_parameters(self):
        from compiler.assembly import quads_to_masm16

        quads = [
            ("add", "_", "_", "_"),
            ("+", "a", "b", "t1"),
            ("ret", "_", "_", "t1"),
            ("main", "_", "_", "_"),
            ("para", "2", "_", "_"),
            ("para", "3", "_", "_"),
            ("call", "add", "_", "t2"),
            ("ret", "_", "_", "t2"),
            ("sys", "_", "_", "_"),
        ]
        assembly = quads_to_masm16(quads, {"add": ["a", "b"], "main": []})

        self.assertIn("add:", assembly)
        self.assertIn("MOV AX,ss:[bp+4]", assembly)
        self.assertIn("ADD AX,ss:[bp+6]", assembly)
        self.assertIn("CALL add", assembly)
        self.assertIn("MOV AX,2", assembly)
        self.assertIn("MOV AX,3", assembly)
        self.assertIn("PUSH AX", assembly)

    def test_generates_masm16_for_builtin_read_write_without_external_calls(self):
        from compiler.assembly import quads_to_masm16

        quads = [
            ("main", "_", "_", "_"),
            ("call", "read", "_", "t1"),
            ("para", "t1", "_", "_"),
            ("call", "write", "_", "_"),
            ("sys", "_", "_", "_"),
        ]
        assembly = quads_to_masm16(quads, {"main": []})

        self.assertIn("CALL read", assembly)
        self.assertIn("CALL write", assembly)
        self.assertIn("read proc near", assembly)
        self.assertIn("write proc near", assembly)


class OptimizerTests(unittest.TestCase):
    def test_folds_constants_and_collapses_temporary_assignments(self):
        from compiler.optimizer import optimize_quads

        quads = [
            ("main", "_", "_", "_"),
            ("+", "1", "2", "t1"),
            ("=", "t1", "_", "x"),
            ("*", "x", "1", "t2"),
            ("=", "t2", "_", "y"),
            ("ret", "_", "_", "y"),
            ("sys", "_", "_", "_"),
        ]
        optimized = optimize_quads(quads)

        self.assertIn(("=", "3", "_", "x"), optimized)
        self.assertIn(("=", "x", "_", "y"), optimized)
        self.assertNotIn(("+", "1", "2", "t1"), optimized)
        self.assertNotIn(("*", "x", "1", "t2"), optimized)

    def test_preserves_control_flow_while_rewriting_known_operands(self):
        from compiler.optimizer import optimize_quads

        quads = [
            ("main", "_", "_", "_"),
            ("=", "0", "_", "i"),
            ("J<", "i", "3", 4),
            ("J", "_", "_", 6),
            ("+", "i", "0", "t1"),
            ("=", "t1", "_", "i"),
            ("ret", "_", "_", "i"),
            ("sys", "_", "_", "_"),
        ]
        optimized = optimize_quads(quads)

        self.assertIn(("J<", "i", "3", 4), optimized)
        self.assertIn(("J", "_", "_", 5), optimized)
        self.assertIn(("=", "i", "_", "i"), optimized)

    def test_remaps_jump_targets_after_removed_temporary_quads(self):
        from compiler.optimizer import optimize_quads

        quads = [
            ("main", "_", "_", "_"),
            ("+", "1", "2", "t1"),
            ("=", "t1", "_", "x"),
            ("J", "_", "_", 5),
            ("=", "0", "_", "x"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]
        optimized = optimize_quads(quads)

        self.assertIn(("=", "3", "_", "x"), optimized)
        self.assertIn(("J", "_", "_", 4), optimized)


class OptimizedTargetCodeTests(unittest.TestCase):
    def test_pipeline_generates_target_code_from_optimized_quads(self):
        from compiler.pipeline import run_pipeline

        result = run_pipeline("int main(){int x; x=1+2; return x;}")

        self.assertIn("MOV x, 3", result.texts["optimized_target_code"])
        self.assertIn("x = 3", result.texts["optimized_target_code"])
        self.assertNotIn("ADD R1, 2", result.texts["optimized_target_code"])
        self.assertIn("RET x", result.texts["optimized_target_code"])

    def test_optimized_target_code_uses_dag_reduced_quads(self):
        from compiler.pipeline import run_pipeline

        source = """
        main() {
            int a; int b; int c; int d; int x;
            a = 10;
            b = 5;
            c = a + b;
            d = a + b;
            x = c * d;
            write(x);
        }
        """
        result = run_pipeline(source)

        target_rows = [
            line for line in result.texts["target_code"].splitlines()
            if " | " in line and not line.startswith(("Line |", "---"))
        ]
        optimized_rows = [
            line for line in result.texts["optimized_target_code"].splitlines()
            if " | " in line and not line.startswith(("Line |", "---"))
        ]

        self.assertLess(len(optimized_rows), len(target_rows))
        self.assertIn("x = 225", result.texts["optimized_target_code"])


class ControlFlowDagTests(unittest.TestCase):
    def sample_quads(self):
        return [
            ("main", "_", "_", "_"),
            ("+", "a", "b", "t1"),
            ("+", "a", "b", "t2"),
            ("=", "t2", "_", "x"),
            ("J<", "x", "10", 7),
            ("+", "x", "1", "t3"),
            ("J", "_", "_", 8),
            ("=", "0", "_", "x"),
            ("ret", "_", "_", "x"),
            ("sys", "_", "_", "_"),
        ]

    def test_basic_blocks_identify_leaders_and_ranges(self):
        from compiler.cfg_dag import analyze_control_flow

        analysis = analyze_control_flow(self.sample_quads())

        self.assertEqual([0, 5, 7, 8], [block.start for block in analysis.basic_blocks])
        self.assertEqual([(0, 4), (5, 6), (7, 7), (8, 9)], [(block.start, block.end) for block in analysis.basic_blocks])
        self.assertIn("B0 [0..4]", analysis.basic_blocks_text)

    def test_cfg_records_successors_and_predecessors(self):
        from compiler.cfg_dag import analyze_control_flow

        analysis = analyze_control_flow(self.sample_quads())

        self.assertEqual(["B2", "B1"], analysis.cfg.successors["B0"])
        self.assertEqual(["B3"], analysis.cfg.successors["B1"])
        self.assertEqual(["B3"], analysis.cfg.successors["B2"])
        self.assertEqual(["B1", "B2"], analysis.cfg.predecessors["B3"])
        self.assertIn("B0 | B2, B1 | -", analysis.cfg_text)

    def test_dag_merges_common_subexpressions_inside_block(self):
        from compiler.cfg_dag import analyze_control_flow

        analysis = analyze_control_flow(self.sample_quads())

        self.assertTrue(any(record.expression == "a + b" and record.reused_by == ["t2"] for record in analysis.common_subexpressions))
        self.assertIn("common: a + b reused by t2", analysis.dag_text)
        self.assertIn("(=, t1, _, t2)", analysis.dag_optimized_quads_text)


class SourceFormatTests(unittest.TestCase):
    def test_formats_brace_blocks_with_indentation(self):
        from compiler.source_format import format_source

        source = "int main(){int x=1;if(x){return x;}else{return 0;}}"
        formatted = format_source(source)

        self.assertEqual(
            "int main() {\n"
            "    int x=1;\n"
            "    if(x) {\n"
            "        return x;\n"
            "    }\n"
            "    else {\n"
            "        return 0;\n"
            "    }\n"
            "}\n",
            formatted,
        )

    def test_formats_existing_multiline_code(self):
        from compiler.source_format import format_source

        source = "int main() {\nint i=0;\nwhile(i<3){\ni=i+1;\n}\nreturn i;\n}"
        formatted = format_source(source)

        self.assertIn("    int i=0;", formatted)
        self.assertIn("    while(i<3) {", formatted)
        self.assertIn("        i=i+1;", formatted)
        self.assertTrue(formatted.endswith("}\n"))


class LogAutomataTests(unittest.TestCase):
    def test_user_regex_matches_log_and_builds_graphs(self):
        from compiler.log_automata import analyze_log_with_regex

        result = analyze_log_with_regex(
            "2026-05-10 08:17:42 INFO ip=172.16.8.31 user=root status=200",
            r"\d{4}-\d{2}-\d{2}",
        )

        self.assertEqual(["2026-05-10"], [match.value for match in result.matches])
        self.assertIn("NFA Graph for regex", result.nfa_text)
        self.assertIn(r"q0 -- \d{4} --> q1", result.nfa_text)
        self.assertIn("DFA Graph from subset construction", result.dfa_text)
        self.assertIn("D0 = {q0}", result.dfa_text)
        self.assertIn("State | Input | Next", result.dfa_table_text)

    def test_user_regex_supports_ip_pattern(self):
        from compiler.log_automata import analyze_log_with_regex

        result = analyze_log_with_regex(
            "client=172.16.8.31 backup=192.168.1.100",
            r"(?:\d{1,3}\.){3}\d{1,3}",
        )

        self.assertEqual(["172.16.8.31", "192.168.1.100"], [match.value for match in result.matches])
        self.assertIn(r"(?:\d{1,3}\.){3}", result.nfa_text)
        self.assertIn("Accept:", result.dfa_text)

    def test_extracts_common_log_keywords(self):
        from compiler.log_automata import analyze_logs

        source = "2026-05-10 08:17:42 INFO ip=172.16.8.31 user=root status=200 action=login"
        result = analyze_logs(source)

        pairs = [(match.value, match.kind) for match in result.matches]
        self.assertIn(("2026-05-10", "DATE"), pairs)
        self.assertIn(("08:17:42", "TIME"), pairs)
        self.assertIn(("INFO", "LEVEL"), pairs)
        self.assertIn(("172.16.8.31", "IP"), pairs)
        self.assertIn(("200", "STATUS"), pairs)
        self.assertIn(("root", "USER"), pairs)
        self.assertIn(("login", "ACTION"), pairs)

    def test_outputs_nfa_and_dfa_construction_text(self):
        from compiler.log_automata import analyze_logs

        result = analyze_logs("2026-05-10 08:17:42 INFO 172.16.8.31 root status=200")

        self.assertIn("NFA for DATE", result.nfa_text)
        self.assertIn("States:", result.nfa_text)
        self.assertIn("Start:", result.nfa_text)
        self.assertIn("Accept:", result.nfa_text)
        self.assertIn("Transitions:", result.nfa_text)
        self.assertRegex(result.nfa_text, r"DATE_N\d+ --")
        self.assertIn("DFA for DATE", result.dfa_text)
        self.assertIn("DFA states from NFA subsets:", result.dfa_text)
        self.assertIn("D0 = {DATE_N0}", result.dfa_text)
        self.assertRegex(result.dfa_text, r"D\d+ --")
        self.assertIn("LEVEL", result.nfa_text)
        self.assertIn("IP", result.dfa_text)
        formatted = result.format_matches()
        self.assertIn("Line | Column | Kind | Value", formatted)
        self.assertIn("1 | 1-11 | DATE | 2026-05-10", formatted)

    def test_no_log_matches_returns_actionable_message(self):
        from compiler.log_automata import analyze_logs

        result = analyze_logs("int main(){return 0;}")

        self.assertEqual([], result.matches)
        self.assertIn("No log keywords matched", result.format_matches())


if __name__ == "__main__":
    unittest.main()
