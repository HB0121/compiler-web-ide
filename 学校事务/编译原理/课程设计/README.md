# 编译原理课程设计

本项目是一个带 Tkinter 桌面 GUI 的简化编译器课程设计系统，支持从源程序编辑、实时错误提示，到词法分析、语法分析、语义分析、中间代码生成、解释执行、LLVM IR 风格输出、目标代码生成和优化前后对比。

## 启动方式

在 PowerShell 中进入项目目录：

```powershell
cd "D:\Users\28197\Documents\GitHub\bivote_rep\学校事务\编译原理\课程设计"
```

使用项目当前可用的 Python 运行：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
```

如果本机已经配置好 Python，也可以尝试：

```powershell
python app.py
```

## 使用流程

1. 在左侧编辑器输入或打开 C-like 源码。
2. 编码时查看左侧行号和下方 Diagnostics 面板，错误行会实时标红。
3. 点击 `格式化` 可自动按花括号层级整理缩进。
4. 点击 `运行` 执行完整编译流水线。
5. 在右侧结果导航中查看各阶段输出。
6. 点击 `导出` 将结果写入 `outputs/` 目录。

## GUI 功能

- 源码编辑器
  - 行号显示
  - 关键字、函数名、数字、字面量、注释高亮
  - 自动缩进
  - 一键格式化
  - 实时错误行标记

- 诊断提示
  - 下方 `Diagnostics` 面板显示行号、阶段、错误码、错误信息
  - 点击错误项可跳转到对应源码行

- 编译结果查看
  - Tokens
  - AST
  - Semantic Errors
  - Const Symbols
  - Var Symbols
  - Functions
  - Quadruples
  - Optimized Quads
  - Interpreter
  - LLVM IR
  - Target Code
  - Optimized Target Code

## 课程设计功能对照

| 任务 | 实现内容 | 主要文件 | GUI 入口 | 输出文件 |
| --- | --- | --- | --- | --- |
| 3.2 | 中间代码解释器 | `compiler/interpreter.py` | `Interpreter` | `outputs/interpreter.txt` |
| 4.1 | 四元式到简化目标代码 | `compiler/target_code.py` | `Target Code` | `outputs/target_code.txt` |
| 4.2 | 四元式到 LLVM IR 风格代码 | `compiler/llvm_ir.py` | `LLVM IR` | `outputs/llvm_ir.txt` |
| 4.3 | 中间代码优化、编辑器高亮、自动缩进、实时错误提示 | `compiler/optimizer.py`, `compiler/source_format.py`, `app.py` | `Optimized Quads`, 编辑器区域 | `outputs/optimized_quads.txt` |
| 4.4 | 优化后目标代码生成 | `compiler/pipeline.py`, `compiler/target_code.py` | `Optimized Target Code` | `outputs/optimized_target_code.txt` |

## 输出文件说明

运行或导出后，`outputs/` 目录中会生成：

- `tokens.txt`：词法分析结果
- `ast.txt`：语法树文本
- `semantic_errors.txt`：语义错误
- `const.txt`：常量表
- `var.txt`：变量表
- `function.txt`：函数表
- `quads.txt`：原始四元式
- `optimized_quads.txt`：优化后四元式
- `interpreter.txt`：中间代码解释执行结果
- `llvm_ir.txt`：LLVM IR 风格代码
- `target_code.txt`：目标代码
- `optimized_target_code.txt`：优化后目标代码

## 验证命令

运行全部测试：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m unittest tests.test_pipeline -v
```

检查 Python 文件语法：

```powershell
& "C:\Users\28197\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -B -m compileall app.py compiler tests
```

