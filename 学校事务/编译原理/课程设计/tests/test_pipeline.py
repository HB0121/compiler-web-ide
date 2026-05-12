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
        self.assertIn("int limit", result.texts["const"])
        self.assertIn("int total", result.texts["var"])
        self.assertIn("int add(int, int)", result.texts["function"])
        self.assertIn("call", result.texts["quads"])

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

    def test_lexer_rejects_empty_and_multi_character_literals(self):
        from compiler.lexer import Lexer

        tokens, diagnostics = Lexer().tokenize("char empty = ''; char multi = 'ab';")

        self.assertEqual([], [token for token in tokens if token.code == 403])
        self.assertEqual(2, len(diagnostics))
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

    def test_mismatched_prototype_definition_reports_duplicate_function(self):
        analyzer = self.analyze_source("int f(int a); float f(float b){return b;} int main(){return 0;}")

        self.assertIn("303", [diagnostic.code for diagnostic in analyzer.diagnostics])

    def test_declared_only_function_call_reports_undefined_function(self):
        analyzer = self.analyze_source("int f(); int main(){return f();}")

        self.assertIn("304", [diagnostic.code for diagnostic in analyzer.diagnostics])

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


if __name__ == "__main__":
    unittest.main()
