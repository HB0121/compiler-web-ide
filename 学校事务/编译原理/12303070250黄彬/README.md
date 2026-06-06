# 编译原理课程设计

本项目是一个基于 Tkinter 的桌面版编译原理课程设计系统，核心目标是把词法分析、语法分析、语义分析、中间代码生成、代码优化、目标代码生成、LLVM IR 输出、日志正则自动机识别等功能整合到一个可交互 GUI 中。

## 功能概览

- C-like 源代码编译流水线：词法分析、语法分析、语义分析、四元式生成、解释执行、LLVM IR 生成、目标代码生成。
- 编辑器辅助功能：行号、关键字/函数名高亮、自动缩进、格式化、实时错误标记、Diagnostics 错误表。
- 中间代码优化：四元式优化、基本块划分、CFG 构建、DAG 局部优化、优化前后代码对比。
- 后端输出：伪目标代码、MASM16 汇编、优化目标代码、工程级 LLVM IR。
- 日志正则自动机任务：输入日志和正则表达式，提取匹配内容，并展示 NFA/DFA 表格与可视化图。
- 文件输出：运行或导出后，将各阶段结果保存到 `outputs/` 目录。

## 最新目录结构

```text
12303070250黄彬/
├─ app.py                         # Tkinter 桌面 GUI 主程序
├─ README.md                      # 项目说明文档
├─ .gitignore                     # Git 忽略配置
├─ 12303070250黄彬.pdf             # 当前课程设计报告 PDF
├─ 2023级《编译原理课程设计》任务书（可选版）.docx
├─ compiler/                      # 编译器核心实现
│  ├─ lexer.py                    # 词法分析
│  ├─ parser.py                   # 语法分析与 AST 构建
│  ├─ semantic.py                 # 语义分析、符号表、语义诊断
│  ├─ ir.py                       # 四元式中间代码生成
│  ├─ interpreter.py              # 中间代码解释执行
│  ├─ optimizer.py                # 基础四元式优化
│  ├─ cfg_dag.py                  # 基本块、CFG、DAG 局部优化
│  ├─ target_code.py              # 伪目标代码生成
│  ├─ assembly.py                 # MASM16 汇编与后端目标代码生成
│  ├─ llvm_ir.py                  # LLVM IR 生成与验证信息
│  ├─ log_automata.py             # 日志正则匹配、NFA/DFA 构造与可视化数据
│  ├─ source_format.py            # 源代码格式化与自动缩进
│  ├─ models.py                   # Token、Diagnostic 等通用数据结构
│  ├─ pipeline.py                 # 统一编译流水线整合入口
│  └─ __init__.py
├─ tests/
│  └─ test_pipeline.py            # 单元测试
├─ examples/
│  ├─ normal_program.c            # 正常编译流程示例
│  ├─ error_program.c             # 错误诊断示例
│  ├─ optimization_program.c      # 优化对比示例
│  ├─ log_sample.log              # 日志识别示例
│  ├─ report_tests/               # 报告用测试材料
│  └─ 系统测试用例/                # 系统化测试用例
│     ├─ 01_词法分析/
│     ├─ 02_语法分析/
│     ├─ 03_语义分析/
│     ├─ 04_中间代码与解释执行/
│     ├─ 05_MASM16汇编生成/
│     ├─ 06_日志正则自动机/
│     ├─ 07_LLVM_IR生成/
│     ├─ 08_CFG与DAG优化/
│     ├─ 09_GUI编辑器功能/
│     ├─ README_系统测试说明.md
│     ├─ 系统测试用例总览.md
│     └─ run_system_tests.py
├─ outputs/                       # 程序运行和导出的阶段结果
├─ generate_submission_tests.py    # 课程提交测试文件生成脚本
├─ docs/                          # 课程设计补充文档与验证说明
│  ├─ LLVM_IR环境配置与运行分享.md
│  └─ 实验报告测试用例.md
├─ 项目介绍/                       # 报告、答辩或说明用图片素材
├─ ppt/                           # 演示文稿相关文件
├─ video/                         # 演示视频相关文件
├─ 全部测试程序/                    # 老师提供的课程测试程序
└─ __pycache__/                   # Python 缓存目录，可忽略
```

## 启动方式

进入项目目录：

```powershell
cd "D:\Users\28197\Documents\GitHub\bivote_rep\学校事务\编译原理\12303070250黄彬"
```

使用 Codex 环境中的 Python 启动：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

如果本机 Python 已正确配置，也可以使用：

```powershell
python app.py
```

## GUI 使用流程

1. 在左侧编辑器输入或打开 C-like 源代码。
2. 编写代码时查看行号、语法高亮和下方 `Diagnostics` 实时诊断。
3. 点击 `格式化` 可自动整理缩进。
4. 点击 `运行` 执行完整编译流水线。
5. 在右侧结果导航中查看 Tokens、AST、四元式、解释执行、LLVM IR、MASM16 汇编、CFG/DAG 等结果。
6. 进行 4.1 日志任务时，在左侧输入日志内容，在 `Regex` 输入框填写正则表达式，或从常用下拉框选择正则，再点击 `日志识别`。
7. 点击 `导出` 将当前流水线结果写入 `outputs/`。

## 任务对应关系

| 任务 | 已实现内容 | 主要文件 | GUI 入口 |
| --- | --- | --- | --- |
| 3.1 | MASM16 汇编目标代码生成，支持函数、参数、条件跳转、循环、读写过程 | `compiler/assembly.py` | `Assembly` |
| 3.2 | 中间代码解释执行 | `compiler/interpreter.py` | `Interpreter` |
| 4.1 | 日志正则匹配，NFA/DFA 构造与可视化展示 | `compiler/log_automata.py` | `Log Extract`, `NFA Graph`, `DFA Graph`, `NFA Visual`, `DFA Visual` |
| 4.2 | LLVM IR 生成与外部编译验证 | `compiler/llvm_ir.py` | `LLVM IR`, `LLVM Verify` |
| 4.3 | 编辑器高亮、自动缩进、实时错误标记、Diagnostics 错误提示 | `app.py`, `compiler/source_format.py` | 左侧编辑器与 `Diagnostics` |
| 4.4 | 基本块划分、CFG 构建、DAG 局部优化、优化前后可视化对比 | `compiler/cfg_dag.py`, `compiler/optimizer.py` | `Basic Blocks`, `CFG`, `DAG`, `CFG Visual`, `DAG Visual`, `DAG Optimized Quads` |

## 输出文件说明

`outputs/` 目录用于保存运行和导出的阶段结果，常见文件包括：

- `tokens.txt`：词法分析 Token 列表
- `ast.txt`：语法树文本
- `semantic_errors.txt`：语义错误列表
- `const.txt`、`var.txt`、`function.txt`：符号表
- `quads.txt`：原始四元式
- `optimized_quads.txt`：优化后的四元式
- `interpreter.txt`：解释执行结果
- `llvm_ir.ll`：工程级 LLVM IR 文件
- `llvm_ir.txt`：GUI 展示用 LLVM IR 文本
- `llvm_verify.txt`：LLVM IR 内置检查和外部 `clang` 验证结果
- `target_code.txt`：目标代码展示
- `assembly.asm`：MASM16 汇编输出
- `optimized_target_code.txt`：优化后的目标代码展示
- `log_extract.txt`：日志正则提取结果
- `log_nfa.txt`、`log_dfa.txt`：日志正则自动机文本

说明：MASM16 汇编中，用户函数会自动加 `fn_` 前缀以避免与 MASM 指令重名。例如源程序函数 `add` 会生成 `fn_add:`，调用处生成 `CALL fn_add`；`main` 保持 `main:`。

## 验证命令

生成课程要求的提交测试文件：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\generate_submission_tests.py
```

默认会扫描 `全部测试程序/01编译器测试用例/` 中所有 `test*.txt`，并生成到 `提交测试文件/`。每个用例包含：

- `test*.txt`：源程序
- `test*.int`：Token 序列、AST、中间代码、MASM16 汇编程序代码、编译诊断
- `test*.doc`：Word 可打开的运行结果输出文档，包含运行界面摘要、源程序、解释执行摘要和诊断信息

运行全量单元测试：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m unittest discover -s tests -q
```

运行系统测试：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" .\examples\系统测试用例\run_system_tests.py
```

检查 Python 文件语法：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m compileall app.py compiler tests
```

LLVM IR 外部验证需要在 `x64 Native Tools Command Prompt for VS` 中运行：

```cmd
cd /d D:\Users\28197\Documents\GitHub\bivote_rep\学校事务\编译原理\12303070250黄彬
clang -c outputs\llvm_ir.ll -o outputs\llvm_ir.obj
clang outputs\llvm_ir.ll -o outputs\llvm_ir.exe
outputs\llvm_ir.exe
```

如果 `clang -c` 能生成 `.obj`，说明 LLVM IR 语法和类型可被外部编译器接受；如果能进一步链接生成 `.exe` 并运行，则可结合项目内置 `Interpreter` 对照验证运行语义。
