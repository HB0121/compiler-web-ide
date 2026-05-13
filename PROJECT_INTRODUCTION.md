# Compiler Web IDE — 在线编译器集成开发环境

## 项目简介

Compiler Web IDE 是一个**基于 Web 的在线编译器**，允许用户在浏览器中编写类 C 语言源代码，并通过完整的四阶段编译流水线（词法分析 → 语法分析 → 中间代码生成 → 解释执行）实时查看编译过程各阶段的中间结果。本项目是一个教学演示性质的编译器系统，适用于编译原理课程的实验与实践。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | Vue 3 (Composition API) | 3.5 |
| **前端构建** | Vite | 8.0 |
| **代码编辑器** | Monaco Editor (`@guolao/vue-monaco-editor`) | — |
| **HTTP 客户端** | Axios | 1.16 |
| **后端** | Java + Spring Boot | 17 / 4.0.6 |
| **后端构建** | Maven | — |

## 项目结构

```
backup/
├── compiler-backend/                # 后端：Spring Boot 编译器引擎
│   ├── pom.xml                      # Maven 项目配置
│   └── src/main/java/com/huangbin/compiler/
│       ├── CompilerBackendApplication.java   # 应用入口
│       ├── controller/
│       │   └── CompileController.java        # REST API 控制器
│       ├── model/
│       │   ├── Token.java                    # 词法单元
│       │   ├── ASTNode.java                  # 抽象语法树节点
│       │   ├── Diagnostic.java               # 编译诊断信息
│       │   ├── CompileRequest.java           # 编译请求 DTO
│       │   └── CompileResult.java            # 编译结果聚合
│       ├── lexer/
│       │   └── Lexer.java                    # 手写词法分析器
│       ├── parser/
│       │   └── Parser.java                   # 递归下降语法分析器
│       ├── ir/
│       │   └── IRGenerator.java              # 三地址码中间代码生成器
│       └── interpreter/
│           └── Interpreter.java              # 基于调用栈的解释器
│
└── compiler-frontend/               # 前端：Vue 3 Web IDE
    └── compiler-frontend/
        ├── package.json
        ├── vite.config.js
        ├── index.html
        └── src/
            ├── main.js
            ├── App.vue              # 主组件（整个 IDE 界面）
            └── style.css
```

## 系统架构

```
┌─────────────────────────┐         POST /api/compile         ┌─────────────────────────┐
│      compiler-frontend  │  ───────────────────────────────> │     compiler-backend     │
│                         │                                   │                          │
│  ┌───────────────────┐  │                                   │  ┌────────────────────┐  │
│  │   Monaco Editor   │  │     { "sourceCode": "..." }       │  │  CompileController │  │
│  │   (C 语言模式)     │  │                                   │  └────────┬───────────┘  │
│  └───────────────────┘  │                                   │           │              │
│           │             │                                   │           ▼              │
│           ▼             │                                   │  ┌────────────────────┐  │
│  ┌───────────────────┐  │                                   │  │   ① Lexer          │  │
│  │   "Run" 按钮       │──┤                                   │  │   (词法分析)        │  │
│  └───────────────────┘  │                                   │  └────────┬───────────┘  │
│                         │                                   │           │              │
│  ┌───────────────────┐  │     { tokens, ast, quads,         │           ▼              │
│  │   结果展示面板      │  │      interpreterOutput,          │  ┌────────────────────┐  │
│  │  ┌──────────────┐ │  │      diagnostics, success }       │  │   ② Parser         │  │
│  │  │ Tokens       │ │  │  <─────────────────────────────── │  │   (语法分析)        │  │
│  │  │ AST          │ │  │                                   │  └────────┬───────────┘  │
│  │  │ IR (四元式)   │ │  │                                   │           │              │
│  │  │ 运行结果      │ │  │                                   │           ▼              │
│  │  │ 诊断信息      │ │  │                                   │  ┌────────────────────┐  │
│  │  │ Raw JSON     │ │  │                                   │  │   ③ IRGenerator    │  │
│  │  └──────────────┘ │  │                                   │  │   (中间代码生成)    │  │
│  └───────────────────┘  │                                   │  └────────┬───────────┘  │
│                         │                                   │           │              │
└─────────────────────────┘                                   │           ▼              │
                                                              │  ┌────────────────────┐  │
                                                              │  │   ④ Interpreter    │  │
                                                              │  │   (解释执行)        │  │
                                                              │  └────────────────────┘  │
                                                              │                          │
                                                              └─────────────────────────┘
```

## 编译流水线

整个编译过程分为四个阶段，前一阶段无错误时才会继续执行下一阶段：

### 第一阶段：词法分析（Lexer）

手写的单趟词法分析器，逐字符扫描源码，支持单字符前瞻（`peek`）。

- **关键字识别**（代码 101-116）：`int`, `float`, `char`, `void`, `main`, `if`, `else`, `while`, `for`, `read`, `write`, `const`, `return`, `break`, `continue`, `do`
- **运算符识别**（代码 201-215）：`==`, `!=`, `<=`, `>=`, `&&`, `||`, `=`, `>`, `<`, `+`, `-`, `*`, `/`, `%`, `!`
- **定界符识别**（代码 301-308）：`(`, `)`, `{`, `}`, `[`, `]`, `;`, `,`
- **标识符**（代码 400）、**整数字面量**（代码 500）、**浮点数字面量**（代码 501）、**字符串字面量**（代码 800）
- **注释处理**：支持单行注释 `//` 和多行注释 `/* */`
- **错误诊断**：未闭合引号、未识别字符等词法错误

### 第二阶段：语法分析（Parser）

递归下降的语法分析器，采用**优先级攀登法**（Precedence Climbing）处理表达式。

AST 节点类型包括：
- **程序结构**：`Program`（根节点）、`FuncDecl`（函数声明）、`VarDecl`（变量声明）、`Compound`（代码块）
- **控制流**：`IfStmt`、`WhileStmt`、`DoWhileStmt`、`ForStmt`、`BreakStmt`、`ContinueStmt`、`ReturnStmt`
- **表达式/运算**：`Assign`、`Identifier`、`Literal`、`String`、`FuncCall`、`BinOp`、`RelOp`、`UnaryOp`

优先级层次（从高到低）：
1. 因子（字面量、标识符、函数调用、`read()`、一元取反、括号表达式）
2. 乘除取模（`*` `/` `%`）
3. 加减（`+` `-`）
4. 关系运算（`>` `<` `>=` `<=` `==` `!=`）
5. 逻辑运算（`&&` `||`）

### 第三阶段：中间代码生成（IR Generator）

将 AST 转换为**三地址码**（Three-Address Code），以四元式（`op, arg1, arg2, result`）的形式表示。

指令集包括：
- **赋值/算术/逻辑**：`=`, `+`, `-`, `*`, `/`, `%`, `>`, `<`, `>=`, `<=`, `==`, `!=`, `&&`, `||`
- **跳转**：`J`（无条件跳转）、`J!=`（条件跳转）
- **函数调用**：`FUNC`（函数标签）、`PARAM`（参数压栈）、`CALL`（函数调用）、`RET`（返回）
- **输入输出**：`READ`、`write`、`write_str`
- **程序终止**：`EXIT`

采用**回填技术**（Backpatching）处理控制流语句中的前向跳转。维护 `LoopContext` 栈来管理嵌套循环中的 `break`/`continue` 跳转。程序入口自动注入 `CALL main` + `EXIT` 指令。

### 第四阶段：解释执行（Interpreter）

基于**调用栈架构**的指令解释器，直接执行四元式序列。

- **激活记录**（Frame）：包含局部变量内存映射、返回地址和返回值目标
- **变量作用域**：优先查找当前帧局部变量，回退到全局内存
- **函数调用机制**：
  1. `PARAM` 指令将实参值压入参数缓冲区
  2. `CALL` 指令创建新 Frame，绑定形参名到实参值，压栈，跳转到函数体
  3. `RET` 指令弹出当前 Frame，将返回值写入调用者的目标变量，跳回返回地址
- **内置函数**：
  - `write(x)`：输出整数值到控制台缓冲区
  - `write("str")`：输出字符串，遇到 `\n` 或"换行"时刷新缓冲区
  - `read()`：模拟输入，返回固定值 9
- **安全限制**：最大执行步数 10000 步，防止无限循环/递归

## 自定义语言规范

本编译器支持的是一种简化的类 C 语言，具备以下特性：

- **数据类型**：`int`、`float`、`char`、`void`
- **常量声明**：`const` 修饰符
- **控制流**：`if/else`、`while`、`do-while`、`for`、`break`、`continue`、`return`
- **函数**：支持参数传递和返回值
- **表达式**：算术运算、关系运算、逻辑运算
- **输入输出**：`read()` 和 `write()`
- **注释**：单行注释 `//`，多行注释 `/* */`

## 前端界面

前端是一个 Vue 3 单页面应用，采用 VS Code 风格的深色主题布局：

- **左侧**：Monaco Editor 代码编辑器（C 语言语法高亮、深色主题、16px 字号）
- **右侧**：六个结果展示标签页
  - **Tokens** — 词法单元表格（行号、列号、文本、类型、代码）
  - **AST** — 带缩进和连接线的树形可视化
  - **四元式** — 三地址码指令列表
  - **运行结果** — 模拟终端输出的绿底黑字控制台
  - **诊断** — 编译错误/警告信息列表
  - **Raw JSON** — 完整原始响应 JSON

点击"Run"按钮后，前端自动切换标签页：编译成功 → 运行结果，编译失败 → 诊断信息。

## 快速启动

### 后端

```bash
cd compiler-backend
./mvnw spring-boot:run
# 默认监听 http://localhost:8080
```

### 前端

```bash
cd compiler-frontend/compiler-frontend
npm install
npm run dev
# 默认监听 http://localhost:5173
```

启动后在浏览器中打开前端地址，在编辑器中输入类 C 语言代码，点击"Run"即可查看完整编译过程。

## API 接口

### POST /api/compile

**请求体：**
```json
{
  "sourceCode": "void main() { write(\"Hello World\\n\"); }"
}
```

**响应体：**
```json
{
  "success": true,
  "tokens": [{ "text": "void", "code": 105, "line": 1, "column": 1, "kind": "keyword" }, ...],
  "ast": { "name": "Program", "children": [...], ... },
  "quads": ["FUNC main _ _", "write_str Hello World _", "RET _ _ _", "CALL main _ _", "EXIT _ _ _"],
  "interpreterOutput": ["Hello World"],
  "diagnostics": []
}
```
