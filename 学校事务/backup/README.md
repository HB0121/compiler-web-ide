# Compiler Web IDE

基于 **Vue 3 + Spring Boot** 的在线编译器，支持完整的四阶段编译流水线：**词法分析 → 语法分析 → 中间代码生成 → 解释执行**。适用于编译原理课程的实验与实践。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue 3 (Composition API) | 3.5 |
| 前端构建 | Vite | 8.0 |
| 代码编辑器 | Monaco Editor | — |
| 后端 | Java + Spring Boot | 17 / 4.0.6 |
| 后端构建 | Maven | — |

## 系统架构

```
POST /api/compile { sourceCode }
          │
          ▼
┌─────────────────────┐
│  ① Lexer 词法分析    │ ──→ tokens
├─────────────────────┤
│  ② Parser 语法分析   │ ──→ AST
├─────────────────────┤
│  ③ IRGenerator      │ ──→ 四元式
├─────────────────────┤
│  ④ Interpreter 解释  │ ──→ 运行输出
└─────────────────────┘
```

## 项目结构

```
├── compiler-backend/          # Spring Boot 编译器引擎
│   └── src/main/java/com/huangbin/compiler/
│       ├── controller/        # REST API
│       ├── lexer/             # 词法分析器
│       ├── parser/            # 递归下降语法分析器
│       ├── ir/                # 中间代码生成 (三地址码)
│       ├── interpreter/       # 调用栈解释器
│       ├── codegen/           # 目标代码生成
│       ├── regex/             # 正则→NFA→DFA
│       └── model/             # 数据模型
│
├── compiler-frontend/         # Vue 3 前端 IDE
│   └── compiler-frontend/
│       └── src/
│           ├── App.vue        # 主组件
│           └── main.js
│
└── 01编译器测试用例/            # 测试用例集
```

## 快速启动

### 后端

```bash
cd compiler-backend
./mvnw spring-boot:run
# 监听 http://localhost:8080
```

### 前端

```bash
cd compiler-frontend/compiler-frontend
npm install
npm run dev
# 监听 http://localhost:5173
```

启动后在浏览器打开前端地址，在编辑器中输入类 C 语言代码，点击 **Run** 即可查看编译全过程的中间结果。

## API

### `POST /api/compile`

请求：

```json
{
  "sourceCode": "void main() { write(\"Hello World\\n\"); }"
}
```

响应：

```json
{
  "success": true,
  "tokens": [{ "text": "void", "code": 105, "line": 1, "column": 1, "kind": "keyword" }],
  "ast": { "name": "Program", "children": [] },
  "quads": ["FUNC main _ _", "write_str Hello World _", "CALL main _ _", "EXIT _ _ _"],
  "interpreterOutput": ["Hello World"],
  "diagnostics": []
}
```

## 支持的语言特性

- 数据类型：`int` `float` `char` `void`
- 控制流：`if/else` `while` `do-while` `for` `break` `continue` `return`
- 表达式：算术运算、关系运算、逻辑运算
- 函数：参数传递、返回值
- I/O：`read()` `write()`

## License

MIT
