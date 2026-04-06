# AI 应用开发学习笔记 (续)

**开发者**：黄彬 (12303070250) **学习阶段**：第三阶段 (MCP 协议) & 第五、六阶段 (Agent 智能体闭环) **当前进度**：已打通“大脑（LLM）+ 手脚（Tools/MCP）”的完整逻辑。

---

## 一、 MCP (Model Context Protocol) 实战

### 1. 协议本质：标准化的中间表示 (IR)

为了避免为每个模型和每个工具重复编写对接代码，MCP 充当了 AI 领域的“通用接口”。

- **FastMCP 框架**：利用 Python 的类型注解（Type Hints）和 Docstrings，通过**反射机制**自动生成大模型可识别的 JSON Schema。
    
- **通信机制**：默认通过标准输入输出流 (`stdio`) 进行 JSON-RPC 通信。
    

### 2. 工具定义 (Tool Definition)

在代码层面，一个函数被标记为 `@mcp.tool()` 后，其函数签名就变成了智能体的“武器说明书”。

- **关键发现**：在 Inspector 调试时，传参必须严格符合函数定义的类型。若将整个 JSON 结构传给 `eval()`，会导致语义错误（返回字典而非计算结果）。
    

---

## 二、 Agent 智能体核心：ReAct 模式

智能体不再只是“生成文本”，而是通过 **思考 (Thought) -> 行动 (Action) -> 观察 (Observation)** 的循环来解决问题。

### 1. Function Calling (函数调用) 流程

大模型并不直接运行代码，它只负责**生成执行指令**。

1. **指令下达**：模型输出 `tool_calls`（包含函数名和参数 JSON）。
    
2. **环境执行**：后端 Python 代码截获指令，在本地物理机或 MCP Server 执行。
    
3. **结果回传**：将执行结果以 `role: tool` 的角色发回给模型。
    
4. **决策闭环**：模型根据结果，决定是继续调用工具还是给出最终答案。
    

### 2. 语义与语法的博弈

- **语法正确**：大模型生成的代码块或 JSON 通常符合语法逻辑。
    
- **语义幻觉**：在小规模本地模型（如 Qwen2.5-7B 以下）中，模型可能出现“让狗继承人”或“传参个数不对”的语义错误。
    
- **工程对策**：在 Agent 逻辑中加入**异常处理**和**结构化输出约束**，是保证系统健壮性的关键。
    

---

## 三、 核心代码范式 (Agent Skeleton)

Python

```
# 1. 定义工具集 (Tools Schema)
tools = [{"type": "function", "function": {"name": "xxx", ...}}]

# 2. 第一轮交互：获取行动指令
response = client.chat.completions.create(..., tools=tools)
tool_calls = response.choices[0].message.tool_calls

# 3. 本地执行与反馈
if tool_calls:
    for call in tool_calls:
        result = execute_local_func(call.function.arguments) # 真实执行
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

# 4. 第二轮交互：生成最终结论
final_res = client.chat.completions.create(messages=messages)
```

---

## 四、 避坑与心得 (Engineering Insights)

- **环境一致性**：修改 Windows 系统环境变量（如 `OLLAMA_MODELS`）后，必须重启所有终端和 IDE，否则会导致路径读取错误或 401 报错。
    
- **模型智商限制**：本地 7B 模型在处理多层嵌套括号的数学公式时，偶尔会遗漏括号，导致 `eval()` 结果不符预期。在后续 RAG 或 Agent 开发中，需要考虑引入**反思机制 (Reflection)**。
    
- **MCP 价值**：通过 MCP Inspector 调试，可以清晰地观察到 RPC 请求的 `initialize`、`tools/list` 和 `tools/call` 过程，这对于理解分布式系统通信非常有帮助。
    

---

## 五、 下一步计划

- [ ] **第四阶段：RAG (检索增强生成)**
    
    - 学习向量化 (Embedding) 与相似度检索。
        
    - 将《编译原理》实验报告导入向量数据库。
        
    - 实现基于私有文档的问答智能体。
        

---

**笔记更新日期**：2026-04-05