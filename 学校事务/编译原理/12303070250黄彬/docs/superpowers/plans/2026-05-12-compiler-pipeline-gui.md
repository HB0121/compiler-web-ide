# Compiler Pipeline GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Tkinter desktop compiler demo that runs lexical analysis, parsing, semantic analysis, and quadruple generation through one shared pipeline while writing course-friendly output files.

**Architecture:** Create a `compiler` package with shared token, AST, diagnostic, pipeline, and output APIs. Refactor the existing experiment algorithms into that package instead of chaining temporary text files. Keep `app.py` thin: it should call the pipeline and render returned text.

**Tech Stack:** Python standard library, `tkinter`, `ttk`, `unittest`, no third-party runtime dependencies.

---

## File Structure

- Create `compiler/__init__.py`: package marker and selected exports.
- Create `compiler/models.py`: `Token`, `Diagnostic`, `ASTNode`, `PipelineResult`, and formatting helpers.
- Create `compiler/lexer.py`: source-code scanner.
- Create `compiler/parser.py`: recursive-descent parser adapted from `exp2.py`.
- Create `compiler/semantic.py`: semantic analyzer adapted from `exp3.py`.
- Create `compiler/ir.py`: quadruple generator adapted from `exp4.py`.
- Create `compiler/pipeline.py`: orchestration and `outputs/` writer.
- Create `app.py`: Tkinter GUI.
- Create `tests/test_pipeline.py`: integrated checks using `unittest`.
- Preserve `已完成的算法代码/*.py` unchanged as reference.

---

### Task 1: Shared Models And Golden Sample

**Files:**
- Create: `compiler/__init__.py`
- Create: `compiler/models.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Create the package marker**

Write `compiler/__init__.py`:

```python
from .models import ASTNode, Diagnostic, PipelineResult, Token

__all__ = ["ASTNode", "Diagnostic", "PipelineResult", "Token"]
```

- [ ] **Step 2: Create shared models**

Write `compiler/models.py` with:

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Token:
    text: str
    code: int
    line: int
    column: int = 1
    kind: str = ""


@dataclass
class Diagnostic:
    phase: str
    line: int
    code: str
    message: str

    def format(self) -> str:
        return f"{self.line} {self.code} {self.phase}: {self.message}"


@dataclass
class ASTNode:
    name: str
    line: Optional[int] = None
    value: Optional[str] = None
    children: List["ASTNode"] = field(default_factory=list)

    def add_child(self, child: Optional["ASTNode"]) -> None:
        if child is not None:
            self.children.append(child)


@dataclass
class PipelineResult:
    tokens: List[Token]
    ast: Optional[ASTNode]
    diagnostics: List[Diagnostic]
    const_symbols: List[Dict[str, object]]
    var_symbols: List[Dict[str, object]]
    function_symbols: List[Dict[str, object]]
    quads: List[Tuple[object, object, object, object]]
    texts: Dict[str, str]


def format_ast(node: Optional[ASTNode], level: int = 0) -> str:
    if node is None:
        return ""
    lines: List[str] = []

    def walk(current: ASTNode, depth: int) -> None:
        indent = "  " * depth
        if current.name in {"Program", "Compound", "IfStmt", "WhileStmt", "ForStmt", "DoWhileStmt", "ExprStmt"}:
            label = current.name
        elif current.name in {"VarDecl", "ConstDecl", "FunctionDecl", "FunctionDef", "Param"}:
            label = f"{current.name}({current.value})[{current.line}]"
        elif current.name == "Call":
            label = f"Call({current.value})[{current.line}]"
        elif current.name in {"ContinueStmt", "BreakStmt", "ReturnStmt"}:
            label = f"{current.name}[{current.line}]"
        elif current.children or current.line is None:
            label = current.value if current.value else current.name
        else:
            label = f"{current.value or current.name}[{current.line}]"
        lines.append(f"{indent}{label}")
        for child in current.children:
            walk(child, depth + 1)

    walk(node, level)
    return "\n".join(lines) + "\n"


def max_line(node: Optional[ASTNode]) -> int:
    if node is None:
        return 0
    current = node.line or 0
    for child in node.children:
        current = max(current, max_line(child))
    return current
```

- [ ] **Step 3: Add an integration test skeleton**

Write `tests/test_pipeline.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the tests and verify they fail for missing pipeline**

Run: `python -m unittest tests.test_pipeline -v`

Expected: FAIL or ERROR containing `No module named 'compiler.pipeline'`.

---

### Task 2: Lexer

**Files:**
- Create: `compiler/lexer.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Add lexer unit coverage**

Append to `tests/test_pipeline.py`:

```python

class LexerTests(unittest.TestCase):
    def test_lexer_recognizes_comments_operators_and_lines(self):
        from compiler.lexer import Lexer

        source = "int main() {\\n  // comment\\n  int x = 1;\\n  x = x + 2;\\n}\\n"
        tokens, diagnostics = Lexer().tokenize(source)
        texts = [token.text for token in tokens]

        self.assertEqual([], diagnostics)
        self.assertEqual(["int", "main", "(", ")", "{", "int", "x", "=", "1", ";", "x", "=", "x", "+", "2", ";", "}"], texts)
        self.assertEqual(3, tokens[5].line)
```

- [ ] **Step 2: Implement the lexer**

Write `compiler/lexer.py`:

```python
from typing import List, Tuple

from .models import Diagnostic, Token


KEYWORDS = {
    "const": 100,
    "int": 101,
    "float": 102,
    "char": 103,
    "void": 104,
    "return": 105,
    "if": 106,
    "else": 107,
    "while": 108,
    "do": 109,
    "for": 110,
    "break": 111,
    "continue": 112,
}

OPERATORS = {
    "==": 201,
    "!=": 202,
    "<=": 203,
    ">=": 204,
    "&&": 205,
    "||": 206,
    "=": 207,
    ">": 208,
    "<": 209,
    "+": 210,
    "-": 211,
    "*": 212,
    "/": 213,
    "!": 214,
}

SEPARATORS = {
    ";": 301,
    ",": 302,
    "(": 303,
    ")": 304,
    "{": 305,
    "}": 306,
}

IDENTIFIER_CODE = 700
INT_LITERAL_CODE = 401
FLOAT_LITERAL_CODE = 402
CHAR_LITERAL_CODE = 403


class Lexer:
    def tokenize(self, source: str) -> Tuple[List[Token], List[Diagnostic]]:
        tokens: List[Token] = []
        diagnostics: List[Diagnostic] = []
        i = 0
        line = 1
        column = 1

        while i < len(source):
            ch = source[i]

            if ch in " \\t\\r":
                i += 1
                column += 1
                continue

            if ch == "\\n":
                i += 1
                line += 1
                column = 1
                continue

            if source.startswith("//", i):
                while i < len(source) and source[i] != "\\n":
                    i += 1
                    column += 1
                continue

            if source.startswith("/*", i):
                start_line = line
                start_column = column
                i += 2
                column += 2
                closed = False
                while i < len(source):
                    if source.startswith("*/", i):
                        i += 2
                        column += 2
                        closed = True
                        break
                    if source[i] == "\\n":
                        i += 1
                        line += 1
                        column = 1
                    else:
                        i += 1
                        column += 1
                if not closed:
                    diagnostics.append(Diagnostic("lexer", start_line, "L001", f"unclosed comment at column {start_column}"))
                continue

            if ch.isalpha() or ch == "_":
                start = i
                start_column = column
                while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                    i += 1
                    column += 1
                text = source[start:i]
                if text in KEYWORDS:
                    tokens.append(Token(text, KEYWORDS[text], line, start_column, "keyword"))
                else:
                    tokens.append(Token(text, IDENTIFIER_CODE, line, start_column, "identifier"))
                continue

            if ch.isdigit():
                start = i
                start_column = column
                has_dot = False
                while i < len(source) and (source[i].isdigit() or source[i] == "."):
                    if source[i] == ".":
                        if has_dot:
                            break
                        has_dot = True
                    i += 1
                    column += 1
                text = source[start:i]
                code = FLOAT_LITERAL_CODE if has_dot else INT_LITERAL_CODE
                kind = "float_literal" if has_dot else "int_literal"
                tokens.append(Token(text, code, line, start_column, kind))
                continue

            if ch == "'":
                start_column = column
                start = i
                i += 1
                column += 1
                while i < len(source) and source[i] != "'" and source[i] != "\\n":
                    i += 1
                    column += 1
                if i < len(source) and source[i] == "'":
                    i += 1
                    column += 1
                    tokens.append(Token(source[start:i], CHAR_LITERAL_CODE, line, start_column, "char_literal"))
                else:
                    diagnostics.append(Diagnostic("lexer", line, "L002", f"unclosed char literal at column {start_column}"))
                continue

            two = source[i:i + 2]
            if two in OPERATORS:
                tokens.append(Token(two, OPERATORS[two], line, column, "operator"))
                i += 2
                column += 2
                continue

            if ch in OPERATORS:
                tokens.append(Token(ch, OPERATORS[ch], line, column, "operator"))
                i += 1
                column += 1
                continue

            if ch in SEPARATORS:
                tokens.append(Token(ch, SEPARATORS[ch], line, column, "separator"))
                i += 1
                column += 1
                continue

            diagnostics.append(Diagnostic("lexer", line, "L003", f"unknown character {ch!r} at column {column}"))
            i += 1
            column += 1

        return tokens, diagnostics
```

- [ ] **Step 3: Run lexer tests**

Run: `python -m unittest tests.test_pipeline.LexerTests -v`

Expected: PASS.

---

### Task 3: Parser

**Files:**
- Create: `compiler/parser.py`
- Modify: `compiler/models.py`

- [ ] **Step 1: Implement parser by adapting `exp2.py`**

Create `compiler/parser.py` by copying the `Parser` class structure from `已完成的算法代码/exp2.py`, then change imports and add diagnostics:

```python
from typing import List, Optional, Tuple

from .models import ASTNode, Diagnostic, Token


TYPE_WORDS = {"int", "float", "char", "void"}
ASSIGN_OPS = {"="}
LOGICAL_OPS = {"&&", "||"}
EQUALITY_OPS = {"==", "!="}
RELATIONAL_OPS = {">", "<", ">=", "<="}
ADD_OPS = {"+", "-"}
MUL_OPS = {"*", "/"}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.diagnostics: List[Diagnostic] = []

    def current_token(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def peek(self, offset: int = 1) -> Optional[Token]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def match_text(self, text: str) -> Optional[Token]:
        token = self.current_token()
        if token and token.text == text:
            self.pos += 1
            return token
        return None

    def expect_text(self, text: str) -> Optional[Token]:
        token = self.match_text(text)
        if token is None:
            current = self.current_token()
            line = current.line if current else (self.tokens[-1].line if self.tokens else 1)
            self.diagnostics.append(Diagnostic("parser", line, "P001", f"expected {text!r}"))
        return token

    def parse(self) -> Tuple[ASTNode, List[Diagnostic]]:
        return self.parse_program(), self.diagnostics

    # Copy the remaining parse_program, declaration, statement, and expression methods from exp2.py.
    # Keep the same node names used by exp2.py: Program, VarDecl, ConstDecl, FunctionDef,
    # FunctionDecl, Param, Compound, IfStmt, WhileStmt, ForStmt, DoWhileStmt, ExprStmt,
    # ContinueStmt, BreakStmt, ReturnStmt, Call, and operator text nodes.
```

Then complete the omitted methods from `exp2.py` with these exact naming changes:

- Rename `parse_Program` to `parse_program`.
- Replace calls to `parse_Program()` with `parse_program()`.
- Keep expression precedence methods unchanged.
- Replace silent missing `;`, `)`, and `}` matches with `expect_text`.
- Keep identifier detection as `token.code == 700`.
- Keep literals as `token.code >= 400 and token.code != 700`.

- [ ] **Step 2: Ensure AST formatting supports parser output**

Review `compiler/models.py`. No structural change is expected if parser emits the node names listed above.

- [ ] **Step 3: Run parser through smoke test**

Run: `python -m unittest tests.test_pipeline.PipelineSmokeTests.test_pipeline_outputs_expected_sections -v`

Expected: still fails because `compiler.pipeline` is not implemented. Parser import errors should not appear once Task 4 introduces pipeline.

---

### Task 4: Semantic Analyzer

**Files:**
- Create: `compiler/semantic.py`

- [ ] **Step 1: Implement semantic analyzer by adapting `exp3.py`**

Create `compiler/semantic.py` with the same `SemanticAnalyzer` behavior as `exp3.py`, but remove `parse_ast` because the parser now returns `ASTNode` directly. Use `node.name`, `node.value`, `node.line`, and `node.children` instead of `node.node_type`, `node.content`, `node.line_num`, and `node.children`.

Required public API:

```python
from typing import Dict, List, Tuple

from .models import ASTNode, Diagnostic, max_line


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table_stack: List[Dict[str, Dict[str, object]]] = [{}]
        self.errors: List[Tuple[int, int]] = []
        self.diagnostics: List[Diagnostic] = []
        self.history_symbols = {"const": [], "var": [], "func": []}
        self.current_func_ret_type = None
        self.current_func_has_return = False
        self.current_func_has_mismatch_return = False

    def analyze_program(self, node: ASTNode):
        self.analyze(node)
        self.errors.sort(key=lambda item: item[0])
        self.diagnostics = [
            Diagnostic("semantic", line, str(code), self.message_for_code(code))
            for line, code in self.errors
        ]
        return self

    def message_for_code(self, code: int) -> str:
        return {
            301: "duplicate declaration",
            302: "undeclared identifier",
            303: "duplicate function declaration or definition",
            304: "undefined function",
            305: "function argument count mismatch",
            306: "function argument type mismatch",
            307: "return type mismatch or missing return",
            308: "illegal break",
            309: "assignment to const",
            310: "expression type mismatch",
        }.get(code, "semantic error")
```

Then port the remaining methods from `exp3.py` with the attribute mapping above. Preserve existing error-code behavior.

- [ ] **Step 2: Add semantic regression test**

Append to `tests/test_pipeline.py`:

```python

class SemanticTests(unittest.TestCase):
    def test_semantic_reports_undeclared_identifier(self):
        from compiler.pipeline import run_pipeline

        result = run_pipeline("int main() { x = 1; return 0; }")
        codes = [diagnostic.code for diagnostic in result.diagnostics]

        self.assertIn("302", codes)
        self.assertIn("302", result.texts["semantic_errors"])
```

- [ ] **Step 3: Run semantic test after pipeline exists**

Run after Task 6: `python -m unittest tests.test_pipeline.SemanticTests -v`

Expected after Task 6: PASS.

---

### Task 5: Quadruple Generator

**Files:**
- Create: `compiler/ir.py`

- [ ] **Step 1: Implement AST conversion and quadruple generation**

Create `compiler/ir.py` by reusing `QuadGenerator` from `exp4.py`, but add a converter from shared AST nodes to the IR node classes used by the generator:

```python
from typing import List, Optional, Tuple

from .models import ASTNode


class IRNode:
    pass


class Program(IRNode):
    def __init__(self, nodes): self.nodes = nodes


class FuncDef(IRNode):
    def __init__(self, name, body): self.name = name; self.body = body


class Block(IRNode):
    def __init__(self, stmts): self.stmts = stmts


class VarDecl(IRNode):
    def __init__(self, name, value): self.name = name; self.value = value


class Assign(IRNode):
    def __init__(self, var, expr): self.var = var; self.expr = expr


class BinOp(IRNode):
    def __init__(self, op, left, right): self.op = op; self.left = left; self.right = right


class UnaryOp(IRNode):
    def __init__(self, op, expr): self.op = op; self.expr = expr


class RelOp(IRNode):
    def __init__(self, op, left, right): self.op = op; self.left = left; self.right = right


class LogicalAnd(IRNode):
    def __init__(self, left, right): self.left = left; self.right = right


class LogicalOr(IRNode):
    def __init__(self, left, right): self.left = left; self.right = right


class LogicalNot(IRNode):
    def __init__(self, expr): self.expr = expr


class Identifier(IRNode):
    def __init__(self, name): self.name = name


class Constant(IRNode):
    def __init__(self, val): self.val = str(val)


class Return(IRNode):
    def __init__(self, expr): self.expr = expr


class Break(IRNode):
    pass


class Continue(IRNode):
    pass


class If(IRNode):
    def __init__(self, cond, true_block, false_block=None):
        self.cond = cond; self.true_block = true_block; self.false_block = false_block


class While(IRNode):
    def __init__(self, cond, body): self.cond = cond; self.body = body


class DoWhile(IRNode):
    def __init__(self, body, cond): self.body = body; self.cond = cond


class For(IRNode):
    def __init__(self, init, cond, step, body):
        self.init = init; self.cond = cond; self.step = step; self.body = body


class FuncCall(IRNode):
    def __init__(self, name, args): self.name = name; self.args = args
```

Copy `QuadGenerator` from `exp4.py`, changing `self.quads.append([op, arg1, arg2, result])` to `self.quads.append((op, arg1, arg2, result))`.

Add converter functions:

```python
def generate_quads(ast: Optional[ASTNode]) -> List[Tuple[object, object, object, object]]:
    if ast is None:
        return []
    ir = convert_node(ast)
    generator = QuadGenerator()
    generator.generate(ir)
    return generator.quads
```

Implement `convert_node` for these shared AST names:

- `Program` -> `Program`
- `FunctionDef` -> `FuncDef`
- `Compound` -> `Block`
- `VarDecl` and `ConstDecl` -> `VarDecl`
- `=` -> `Assign`
- `+`, `-`, `*`, `/` -> `BinOp`, except unary `-` when one child exists -> `UnaryOp`
- `>`, `<`, `>=`, `<=`, `==`, `!=` -> `RelOp`
- `&&` -> `LogicalAnd`
- `||` -> `LogicalOr`
- `!` -> `LogicalNot`
- `Call` -> `FuncCall`
- `ReturnStmt` -> `Return`
- `BreakStmt` -> `Break`
- `ContinueStmt` -> `Continue`
- `IfStmt`, `WhileStmt`, `DoWhileStmt`, `ForStmt` -> matching control-flow nodes
- leaf identifier or literal -> `Identifier` or `Constant`

- [ ] **Step 2: Add quad formatting**

Add:

```python
def format_quads(quads: List[Tuple[object, object, object, object]]) -> str:
    lines = []
    for i, quad in enumerate(quads):
        parts = []
        for item in quad:
            if isinstance(item, int):
                parts.append(str(item))
            elif item == "_":
                parts.append("'_'")
            else:
                parts.append(f"'{str(item).strip()}'")
        lines.append(f"{i}: ({parts[0]}, {parts[1]}, {parts[2]}, {parts[3]})")
    return "\n".join(lines) + ("\n" if lines else "")
```

---

### Task 6: Pipeline And Output Files

**Files:**
- Create: `compiler/pipeline.py`

- [ ] **Step 1: Implement orchestration**

Write `compiler/pipeline.py`:

```python
from pathlib import Path
from typing import Dict, Iterable

from .ir import format_quads, generate_quads
from .lexer import Lexer
from .models import Diagnostic, PipelineResult, Token, format_ast
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
    tokens, lexer_diags = Lexer().tokenize(source)
    ast = None
    parser_diags = []
    semantic = SemanticAnalyzer()
    quads = []

    if tokens:
        ast, parser_diags = Parser(tokens).parse()

    if ast is not None:
        semantic.analyze_program(ast)
        quads = generate_quads(ast)

    diagnostics = list(lexer_diags) + list(parser_diags) + list(semantic.diagnostics)
    texts = build_texts(tokens, ast, diagnostics, semantic, quads)

    return PipelineResult(
        tokens=tokens,
        ast=ast,
        diagnostics=diagnostics,
        const_symbols=semantic.history_symbols["const"],
        var_symbols=semantic.history_symbols["var"],
        function_symbols=semantic.history_symbols["func"],
        quads=quads,
        texts=texts,
    )


def build_texts(tokens, ast, diagnostics, semantic, quads) -> Dict[str, str]:
    return {
        "tokens": format_tokens(tokens),
        "ast": format_ast(ast),
        "semantic_errors": format_semantic_errors(diagnostics),
        "const": format_symbols(semantic.history_symbols["const"], "const"),
        "var": format_symbols(semantic.history_symbols["var"], "var"),
        "function": format_symbols(semantic.history_symbols["func"], "func"),
        "quads": format_quads(quads),
    }


def format_tokens(tokens: Iterable[Token]) -> str:
    return "".join(f"{token.text} {token.code} {token.line}\n" for token in tokens)


def format_semantic_errors(diagnostics: Iterable[Diagnostic]) -> str:
    semantic = [d for d in diagnostics if d.phase == "semantic"]
    return "".join(f"{d.line} {d.code}\n" for d in semantic)


def format_symbols(symbols, kind: str) -> str:
    lines = []
    for item in symbols:
        if kind == "func":
            params = item.get("params") or []
            params_text = ", ".join(params) if params else "void"
            lines.append(f"{item['type']} {item['name']}({params_text})")
        else:
            lines.append(f"{item['type']} {item['name']}")
    return "\n".join(lines) + ("\n" if lines else "")


def write_outputs(result: PipelineResult, output_dir: Path = Path("outputs")) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in OUTPUT_NAMES.items():
        (output_dir / filename).write_text(result.texts.get(key, ""), encoding="utf-8")
```

- [ ] **Step 2: Run pipeline smoke tests**

Run: `python -m unittest tests.test_pipeline.PipelineSmokeTests -v`

Expected: PASS after parser, semantic analyzer, and IR converter are complete.

- [ ] **Step 3: Run semantic tests**

Run: `python -m unittest tests.test_pipeline.SemanticTests -v`

Expected: PASS.

---

### Task 7: Tkinter GUI

**Files:**
- Create: `app.py`

- [ ] **Step 1: Implement GUI entry point**

Write `app.py`:

```python
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from compiler.pipeline import run_pipeline, write_outputs


SAMPLE = """const int limit = 3;

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


class CompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Compiler Course Design")
        self.geometry("1180x720")
        self.current_file = None
        self.result = None
        self._build_ui()
        self.source.insert("1.0", SAMPLE)

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=6)

        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Run", command=self.run).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Export", command=self.export_outputs).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="Clear", command=self.clear).pack(side=tk.LEFT, padx=3)

        main = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=2)

        ttk.Label(left, text="Source Code").pack(anchor=tk.W)
        self.source = tk.Text(left, wrap=tk.NONE, undo=True)
        self.source.pack(fill=tk.BOTH, expand=True)

        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill=tk.BOTH, expand=True)
        self.views = {}
        for key, title in [
            ("tokens", "Tokens"),
            ("ast", "AST"),
            ("semantic_errors", "Semantic Errors"),
            ("const", "Const Symbols"),
            ("var", "Var Symbols"),
            ("function", "Functions"),
            ("quads", "Quadruples"),
        ]:
            frame = ttk.Frame(self.tabs)
            text = tk.Text(frame, wrap=tk.NONE)
            text.pack(fill=tk.BOTH, expand=True)
            self.tabs.add(frame, text=title)
            self.views[key] = text

        self.status = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status, anchor=tk.W).pack(fill=tk.X, padx=8, pady=4)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("C source", "*.c *.txt"), ("All files", "*.*")])
        if not path:
            return
        self.current_file = Path(path)
        self.source.delete("1.0", tk.END)
        self.source.insert("1.0", self.current_file.read_text(encoding="utf-8"))
        self.status.set(f"Opened {self.current_file}")

    def save_file(self):
        if self.current_file is None:
            path = filedialog.asksaveasfilename(defaultextension=".c", filetypes=[("C source", "*.c"), ("Text", "*.txt")])
            if not path:
                return
            self.current_file = Path(path)
        self.current_file.write_text(self.source.get("1.0", tk.END), encoding="utf-8")
        self.status.set(f"Saved {self.current_file}")

    def run(self):
        source = self.source.get("1.0", tk.END)
        self.result = run_pipeline(source)
        for key, view in self.views.items():
            view.delete("1.0", tk.END)
            view.insert("1.0", self.result.texts.get(key, ""))
        write_outputs(self.result, Path("outputs"))
        self.status.set(
            f"Run complete: {len(self.result.tokens)} tokens, "
            f"{len(self.result.diagnostics)} diagnostics, {len(self.result.quads)} quadruples"
        )

    def export_outputs(self):
        if self.result is None:
            self.run()
        write_outputs(self.result, Path("outputs"))
        messagebox.showinfo("Export", "Outputs written to outputs/")

    def clear(self):
        self.source.delete("1.0", tk.END)
        for view in self.views.values():
            view.delete("1.0", tk.END)
        self.status.set("Cleared")


if __name__ == "__main__":
    CompilerApp().mainloop()
```

- [ ] **Step 2: Run GUI import check**

Run: `python -m py_compile app.py`

Expected: no output and exit code 0.

---

### Task 8: Final Verification

**Files:**
- Modify only if verification exposes concrete defects.

- [ ] **Step 1: Run all tests**

Run: `python -m unittest -v`

Expected: all tests pass.

- [ ] **Step 2: Run pipeline manually**

Run: `python -c "from compiler.pipeline import run_pipeline, write_outputs; r=run_pipeline('int main(){int x=1;return x;}'); write_outputs(r); print(r.texts['quads'])"`

Expected: output contains a `main` entry, assignment quadruple, `ret`, and `sys`; `outputs/` contains all seven expected files.

- [ ] **Step 3: Compile all Python files**

Run: `python -m compileall compiler app.py tests`

Expected: all files compile successfully.

- [ ] **Step 4: Manual GUI launch**

Run: `python app.py`

Expected: a Tkinter window opens, the bundled sample source is visible, Run fills all result tabs, and `outputs/` is refreshed.

---

## Self-Review Notes

- Spec coverage: tasks cover shared architecture, lexer, parser, semantic analyzer, quadruple generator, pipeline file output, GUI, and verification.
- Scope: arrays, switch, standard library I/O, preprocessing, pointers, structs, and full C grammar are intentionally excluded.
- Type consistency: all phases use `Token`, `ASTNode`, `Diagnostic`, and `PipelineResult` from `compiler.models`.
- Risk: Task 3 and Task 4 rely on careful porting from the existing experiment files. Keep their behavior close to the originals and avoid unrelated grammar expansion.
