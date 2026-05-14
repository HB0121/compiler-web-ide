# 系统测试用例说明

本目录是一套面向实验报告的系统级测试用例，覆盖主编译流水线、扩展任务和 GUI 编辑器功能。每个子目录对应一个功能模块，既包含可通过用例，也包含用于展示错误诊断的用例。

## 运行方式

在项目根目录执行：

```powershell
python examples/system_tests/run_system_tests.py
```

预期输出：

```text
system tests: PASS
covered: lexical, syntax, semantic, IR/interpreter, MASM16, log regex NFA/DFA, LLVM IR, CFG/DAG, GUI editor inputs
```

也可以在 GUI 中逐个打开 `.c` 或 `.log` 文件，点击“运行”或“日志识别”，对照下面的预期结果截图或记录。

## 01 词法分析

文件：
- `01_lexical/lexical_all_tokens.c`
- `01_lexical/lexical_errors.c`

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
- `02_syntax/syntax_control_flow.c`
- `02_syntax/syntax_errors.c`

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
- `03_semantic/semantic_symbols_ok.c`
- `03_semantic/semantic_errors.c`

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
- `04_ir_interpreter/interpreter_loop_factorial.c`
- `04_ir_interpreter/interpreter_branch_function.c`
- `04_ir_interpreter/interpreter_runtime_warning.c`

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
- `05_assembly_masm16/assembly_basic_masm16.c`
- `05_assembly_masm16/assembly_read_write.c`

覆盖点：
- `.MODEL SMALL`、`.DATA`、`.CODE`
- `main PROC`
- 用户函数 `fn_add PROC`
- 条件跳转、循环跳转
- `read/write` 内置函数汇编注释

预期：
- `Assembly` 中只有一个 `main PROC`。
- 全局常量出现在 `.DATA`。
- `read/write` 不生成外部 `call fn_read` 或 `call fn_write`。

## 06 日志正则与 NFA/DFA

文件：
- `06_log_regex_automata/log_sample.log`
- `06_log_regex_automata/regex_patterns.txt`
- `06_log_regex_automata/no_match.log`

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
- `07_llvm_ir/llvm_branch_call.c`

覆盖点：
- `define`
- `call`
- `br`
- `ret`
- 条件分支和函数调用

预期：
- `LLVM IR` 中包含 `define i32 @square`。
- 包含 `call i32 @square`。
- 包含条件跳转 `br i1`。

## 08 CFG 与 DAG 优化

文件：
- `08_cfg_dag_optimization/cfg_if_else.c`
- `08_cfg_dag_optimization/dag_common_subexpr.c`

覆盖点：
- Leaders 识别
- 基本块划分
- CFG 前驱/后继边
- 基本块内 DAG 构建
- 公共子表达式消除
- 优化前后四元式对比

预期：
- `cfg_if_else.c` 的 `Basic Blocks` 中有多个基本块。
- `CFG` 中显示 `CFG Edges`。
- `dag_common_subexpr.c` 的 `DAG` 中出现公共子表达式复用信息。
- `DAG Optimized Quads` 中减少重复的 `a + b` 计算。

## 09 GUI 编辑器功能

文件：
- `09_gui_editor_features/gui_realtime_errors.c`
- `09_gui_editor_features/gui_format_highlight.c`

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
- 错误用例产生语法和语义诊断。
- 格式化后代码多行缩进清晰。
- 行号和错误行标记保持同步。
