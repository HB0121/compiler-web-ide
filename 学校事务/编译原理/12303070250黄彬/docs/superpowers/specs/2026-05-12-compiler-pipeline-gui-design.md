# Compiler Pipeline GUI Design

## Goal

Build an integrated compiler course-design application around the existing algorithm code. The program supports a C-like subset already covered by the current parser, semantic analyzer, and intermediate-code generator:

- `int`, `float`, `char`, `void`, `const`
- variable and constant declarations
- function declarations and definitions
- `if/else`, `while`, `do-while`, `for`
- `break`, `continue`, `return`
- function calls
- arithmetic, relational, equality, logical, unary, and assignment expressions

The final application should work both as a demonstrable Tkinter desktop app and as a file-output tool for course inspection.

## Architecture

The existing experiment files (`exp2.py`, `exp3.py`, and `exp4.py`) remain as reference material. New code should be organized into a small package:

- `compiler/token.py`: shared token and diagnostic data classes.
- `compiler/ast.py`: shared AST node, AST formatting, and AST conversion helpers.
- `compiler/lexer.py`: new lexical analyzer from source code to token list.
- `compiler/parser.py`: refactor the usable logic from `exp2.py` to consume shared tokens and produce the shared AST.
- `compiler/semantic.py`: refactor the usable logic from `exp3.py` to analyze the shared AST directly.
- `compiler/ir.py`: refactor the usable logic from `exp4.py` to generate quadruples from the shared AST.
- `compiler/pipeline.py`: one public pipeline function that runs all compiler phases and returns a structured result.
- `app.py`: Tkinter GUI entry point.

This avoids the current mismatch where `exp2.py` outputs text AST, `exp3.py` reparses text AST, and `exp4.py` uses a separate mini parser.

## Data Flow

1. The user enters source code in the GUI or opens a source file.
2. `Lexer` produces tokens and lexical diagnostics.
3. `Parser` consumes tokens and produces a shared AST plus syntax diagnostics.
4. `SemanticAnalyzer` consumes the shared AST and produces semantic diagnostics and symbol tables.
5. `QuadGenerator` consumes the shared AST and produces quadruples.
6. `PipelineResult` exposes all phase outputs for both GUI display and file export.

If an earlier phase reports blocking errors, later phases should still display the outputs that are safe to compute. For example, token output should still be shown when syntax analysis fails.

## GUI Design

The Tkinter window should prioritize course demonstration:

- Left side: source editor with open, save, run, clear, and export buttons.
- Right side: notebook tabs for tokens, AST, semantic errors, constants, variables, functions, and quadruples.
- Bottom status area: current file path, run status, and summary counts.

The GUI should not require extra third-party dependencies. It should use Python's standard `tkinter` and `ttk` modules.

## File Output

Every successful run should create or refresh an `outputs/` directory with:

- `tokens.txt`
- `ast.txt`
- `semantic_errors.txt`
- `const.txt`
- `var.txt`
- `function.txt`
- `quads.txt`

The output format should stay close to the existing experiment files so prior algorithm behavior remains recognizable.

## Error Handling

The application should collect diagnostics instead of crashing on malformed input. Diagnostics should include at least line number, phase, code or category, and message. GUI tabs should display diagnostics in plain text tables.

The semantic analyzer should preserve the existing error-code style where possible:

- `301`: duplicate declaration
- `302`: undeclared identifier
- `303`: duplicate function declaration or definition
- `304`: undefined function
- `305`: function argument count mismatch
- `306`: function argument type mismatch
- `307`: return type mismatch or missing return
- `308`: illegal break
- `309`: assignment to const
- `310`: expression type mismatch

## Testing

Testing should focus on integrated behavior:

- lexer recognizes keywords, identifiers, literals, operators, separators, comments, and line numbers
- parser builds AST for declarations, functions, loops, branches, calls, and expressions
- semantic analyzer reports known error codes on representative invalid programs
- intermediate-code generator emits quadruples for assignments, expressions, branches, loops, calls, and returns
- pipeline writes all expected files under `outputs/`

The first implementation can use small sample source strings and script-level checks instead of a large test framework if the repository has no existing test setup.

## Non-Goals

This design does not add arrays, `switch/case/default`, standard library I/O, preprocessing, pointer syntax, struct syntax, or full C grammar compatibility. Those can be later extensions after the integrated pipeline is stable.
