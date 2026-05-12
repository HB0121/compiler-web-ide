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


if __name__ == "__main__":
    unittest.main()
