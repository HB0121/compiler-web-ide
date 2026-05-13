# Compiler Testcase Merge Design

## Goal

Make the programs under `01编译器测试用例/*.txt` run through the current Web IDE compiler pipeline while preserving the existing project extensions: MASM output, LLVM IR output, DAG/CFG analysis, compile logs, and log scanner output.

The implementation must not directly overwrite the current core compiler files with the versions from `待加入的代码`. Those files are reference material only. Their useful semantics should be selectively merged into the current implementation.

## Scope

The merge targets four backend compiler stages:

- `Lexer`
- `Parser`
- `IRGenerator`
- `Interpreter`

The integration boundary remains `CompileController`. The API response shape should continue to include `tokens`, `ast`, `quads`, `assemblyCode`, `llvmIR`, `compileLog`, `cfgAnalysis`, `logScanner`, `interpreterOutput`, and `diagnostics`.

## Non-Goals

- Do not remove MASM, LLVM, DAG/CFG, compile logging, or log scanner features.
- Do not replace the current backend files wholesale.
- Do not add a separate "test compatibility mode" with a second compiler path.
- Do not make hard-coded output messages or test-specific behavior part of the user-facing compiler semantics.

## Required Language Support

The current compiler should gain the semantics needed by the testcase folder:

- Array declarations such as `int a[50];`.
- Array reads such as `a[i]`.
- Array writes such as `a[i] = expr;`.
- `read(n);` as an input statement.
- `n = read();` as an input expression.
- `main(void)` function declarations.
- `i++` and `i--` where they appear in update-style expressions.
- Existing recursive and nested function calls must continue to work.

## Lexer Design

Start from the current `Lexer` and keep its existing diagnostics and structure. Add only the missing token support:

- `++`
- `--`

Do not adopt the compressed reference implementation from `待加入的代码/Lexer.java`, because it drops or weakens current diagnostics such as unclosed string reporting.

## Parser Design

Start from the current `Parser` and selectively merge syntax support:

- Parse array declarations into `ArrayDecl` nodes.
- Parse array element access into `ArrayAccess` nodes.
- Allow `ArrayAccess` as an assignment left-hand side.
- Parse `read(n);` as a function-call statement with one target child.
- Continue supporting `n = read();` through expression parsing.
- Treat `void` in a function parameter list as an empty parameter list for declarations such as `int main(void)`.
- Translate `i++` and `i--` in assignment/update contexts into normal `Assign` AST nodes equivalent to `i = i + 1` and `i = i - 1`.

The parser should continue to emit diagnostics for missing delimiters and unexpected tokens instead of silently swallowing malformed source.

## IR Design

Start from the current `IRGenerator` and add array-specific quads:

- `ALLOC size _ name`: allocate an integer array.
- `=[] name index temp`: read `name[index]` into `temp`.
- `[]= value index name`: write `value` into `name[index]`.

Keep current function support:

- Function bodies are skipped during top-level execution.
- `FUNC`, `PARAM`, `CALL`, and `RET` remain the function-call protocol.
- `CALL main` and `EXIT` are still emitted as startup glue.
- `break` and `continue` still use the loop backpatching logic.

For `read(n);`, emit a `READ _ _ n` quad. For `n = read();`, keep emitting a `READ` into a temporary and assign that value through the expression path.

## Interpreter Design

Add array runtime state to the current `Interpreter`:

- Store arrays in a `Map<String, int[]>`.
- Execute `ALLOC` by allocating the named array.
- Execute `=[]` by reading a checked array element into the target variable.
- Execute `[]=` by writing a checked array element.

Input should support repeated reads deterministically. It may use a fixed default input sequence for automated testcase execution, then fall back to `9` when the sequence is exhausted. This behavior should be implementation-neutral, not tied to a single testcase name or described with test-specific output text.

Array bounds errors or reads from missing arrays should not crash the Web IDE request. They should degrade predictably by returning `0` or skipping the write, with a clear runtime note if the implementation already has a suitable place for runtime messages.

## Extension Compatibility

Existing extensions must remain in the API response.

If MASM, LLVM, or DAG/CFG logic does not fully understand `ALLOC`, `=[]`, or `[]=`, it should skip or represent those operations conservatively instead of throwing an exception that prevents the interpreter result from returning.

The log scanner feature is independent from source compilation and must keep working.

## Verification Plan

Run backend compilation/tests first.

Then verify compiler behavior against all `.txt` programs under `01编译器测试用例`. The preferred check is a small batch harness that feeds each source into the compile pipeline and records:

- whether diagnostics were emitted,
- whether IR was generated,
- whether interpretation completed,
- whether the API/pipeline threw an exception.

High-priority manual checks:

- `test5.4.txt`: global array Fibonacci sequence.
- `test5.5.txt`: local array sorting with repeated `read()`.
- `test4.1-*`, `test4.2-*`, `test4.3.txt`, `test5.1.txt`, `test5.2.txt`, `test5.3.txt`: recursive calls and nested function expressions.

Some provided testcase files contain intentional syntax mistakes or non-standard function names such as `input`/`output`. Those should be reported as diagnostics unless explicitly mapped later.

## Risks

- Array quads may require small compatibility updates in MASM, LLVM, and DAG code so that extension generation does not fail.
- The fixed input sequence can affect expected output. It should be documented in test output and isolated in interpreter input handling.
- The parser currently carries several responsibilities in one class; changes should stay localized to avoid introducing unrelated grammar regressions.
