# 系统测试用例说明

本目录是一套面向实验报告的系统级测试用例，覆盖主编译流水线、扩展任务和 GUI 编辑器功能。每个子目录对应一个功能模块，既包含可通过用例，也包含用于展示错误诊断的用例。

## 运行方式

在项目根目录执行：

```powershell
python examples/系统测试用例/run_system_tests.py
```

预期输出：

```text
system tests: PASS
covered: lexical, syntax, semantic, IR/interpreter, MASM16, log regex NFA/DFA, LLVM IR, CFG/DAG, GUI editor inputs
```

也可以在 GUI 中逐个打开 `.c` 或 `.log` 文件，点击“运行”或“日志识别”，对照下面的预期结果截图或记录。

## 01 词法分析

文件：
- `01_词法分析/lexical_all_tokens.c`
- `01_词法分析/lexical_errors.c`

覆盖点：
- 关键字：`const`、`int`、`char`、`while`
- 标识符、整数、字符、字符串
- 算术运算符、关系运算符、逻辑运算符、分隔符
- 非法字符、非法字符常量、未闭合字符串

预期：
- `lexical_all_tokens.c` 无诊断，`Tokens` 中能看到关键字、标识符、常量、运算符。
- `lexical_errors.c` 至少产生 `L003` 和 `L004`，编辑器下方诊断表显示词法错误。

## 02 语法分析

文件：
- `02_语法分析/syntax_control_flow.c`
- `02_语法分析/syntax_errors.c`

覆盖点：
- 函数定义与调用
- `if/else`
- `for` 循环
- `return`
- 缺少分号、表达式缺失、括号结构错误

预期：
- `syntax_control_flow.c` 无诊断，`AST` 中包含 `ForStmt`、`IfStmt`、`ReturnStmt`。
- `syntax_errors.c` 产生 `P001`、`P002` 等语法诊断。

## 03 语义分析

文件：
- `03_语义分析/semantic_symbols_ok.c`
- `03_语义分析/semantic_errors.c`

覆盖点：
- 常量表、变量表、函数表
- 重复声明
- 未声明标识符
- 函数参数个数错误
- 常量赋值错误

预期：
- `semantic_symbols_ok.c` 无诊断，`Functions` 中包含 `int inc(int)`。
- `semantic_errors.c` 产生 `301`、`302`、`305`、`309`。

## 04 中间代码与解释执行

文件：
- `04_中间代码与解释执行/interpreter_loop_factorial.c`
- `04_中间代码与解释执行/interpreter_branch_function.c`
- `04_中间代码与解释执行/interpreter_runtime_warning.c`

覆盖点：
- 四元式生成
- 循环执行
- 条件分支
- 函数调用
- 内置 `read/write`
- 运行期除零保护

预期：
- 阶乘用例解释执行输出 `builtin write(120)`。
- 分支函数用例解释执行输出 `builtin write(7)`。
- 除零用例不崩溃，`Interpreter` 中显示 division/modulo warning。

## 05 MASM16 汇编生成

文件：
- `05_MASM16汇编生成/assembly_basic_masm16.c`
- `05_MASM16汇编生成/assembly_read_write.c`

覆盖点：
- `assume cs:code,ds:data,ss:stack,es:extended`
- `data segment`、`code segment`
- `main:` 函数入口
- 用户函数标签，如 `add:`
- 条件跳转、循环跳转
- `read/write` DOS 输入输出过程

预期：
- `Assembly` 中只有一个 `main:`。
- 全局常量出现在 `data segment`。
- 函数调用前使用 `PUSH AX` 传参，被调用函数通过 `ss:[bp+4]` 等位置读取形参。
- 输出包含 `read proc near` 和 `write proc near`，可在 MASM16 环境中完成键盘输入和数字输出。

## 06 日志正则与 NFA/DFA

文件：
- `06_日志正则自动机/log_sample.log`
- `06_日志正则自动机/regex_patterns.txt`
- `06_日志正则自动机/no_match.log`

覆盖点：
- 日期、时间、IP、状态码、用户、动作
- 用户自定义正则
- 无匹配输入
- NFA 文本、DFA 文本、DFA 表、可视化图

GUI 操作：
1. 将 `log_sample.log` 内容粘贴到左侧编辑器。
2. 在 Regex 输入框填入 `(?:\d{1,3}\.){3}\d{1,3}`。
3. 点击“日志识别”。
4. 查看 `Log Extract`、`NFA Graph`、`DFA Graph`、`DFA Table`、`NFA Visual`、`DFA Visual`。

预期：
- IP 正则匹配 3 条 IP。
- NFA/DFA 文本显示状态、起始状态、接受状态和转换。
- 无匹配日志不报错，显示无匹配提示。

## 07 LLVM IR

文件：
- `07_LLVM_IR生成/llvm_branch_call.c`
- `07_LLVM_IR生成/llvm_modulo_loop.c`

覆盖点：
- `define`
- 局部变量 `alloca`
- `load/store`
- `br`
- `ret`
- 条件分支
- `LLVM Verify` 内部验证和外部工具链验证命令

预期：
- `LLVM IR` 中包含 `define i32 @main`。
- 包含局部变量分配 `alloca i32`。
- 包含 typed pointer 风格的 `load i32, i32*` 和 `store i32 ..., i32*`。
- 包含条件跳转 `br i1`。
- 包含返回语句 `ret i32`。
- `LLVM Verify` 显示 `Internal verifier: PASS`。
- 如果本机安装了完整 LLVM 工具链，可使用 `llvm-as outputs/llvm_ir.ll -o outputs/llvm_ir.bc` 和 `lli outputs/llvm_ir.ll` 做外部验证。
- 如果只有 `clang`，可使用 `clang -c outputs/llvm_ir.ll -o outputs/llvm_ir.obj` 验证 IR 能否被 LLVM 前端编译成目标文件；该命令不链接，因此不依赖 MSVC 运行库。
- 安装 Visual Studio C++ Build Tools 后，可在 `x64 Native Tools Command Prompt for VS` 中执行 `clang outputs\llvm_ir.ll -o outputs\llvm_ir.exe` 和 `outputs\llvm_ir.exe`，完成外部编译、链接和运行验证。
- 完整运行验证允许出现 `overriding the module target triple` warning，但不能出现 error；程序输出应与 `Interpreter` 的 `builtin write(...)` 或 `return_value` 一致。

## 08 CFG 与 DAG 优化

文件：
- `08_CFG与DAG优化/cfg_if_else.c`
- `08_CFG与DAG优化/dag_common_subexpr.c`
- `08_CFG与DAG优化/cfg_dag_complex.c`

覆盖点：
- Leaders 识别
- 基本块划分
- CFG 前驱/后继边
- 基本块内 DAG 构建
- 公共子表达式消除
- 优化前后四元式对比
- 基于 DAG 优化结果生成 `Optimized Target Code`
- 优化前后目标代码行数对比

预期：
- `cfg_if_else.c` 的 `Basic Blocks` 中有多个基本块。
- `CFG` 中显示 `Control Flow Graph`、前驱信息和 `B0 -> B1` 这类控制流边。
- `dag_common_subexpr.c` 的 `DAG` 中出现公共子表达式复用信息。
- `DAG Optimized Quads` 中减少重复的 `a + b` 计算。
- `cfg_dag_complex.c` 的 `Optimized Target Code` 行数应少于 `Target Code`，用于证明 DAG 优化结果已经进入目标代码生成阶段。
- `cfg_dag_complex.c` 优化后目标代码中应出现 `MOV c, 15`、`MOV d, 15`、`MOV x, 225` 这类常量传播/折叠结果。

## 09 GUI 编辑器功能

文件：
- `09_GUI编辑器功能/gui_realtime_errors.c`
- `09_GUI编辑器功能/gui_format_highlight.c`

覆盖点：
- 行号显示
- 实时错误标记
- 下方诊断表
- 关键字高亮
- 函数名高亮
- 格式化和自动缩进

GUI 操作：
1. 打开 `gui_realtime_errors.c`，观察第 3、4 行附近的红色错误标记和诊断表。
2. 打开 `gui_format_highlight.c`，点击“格式化”。
3. 查看代码缩进是否展开，关键字和函数名是否高亮。

预期：
- 错误用例产生语法诊断 `P002` 和语义诊断 `302`。
- 格式化后代码多行缩进清晰。
- 行号和错误行标记保持同步。
