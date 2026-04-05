# AI 应用开发学习笔记

**开发者**：黄彬 (12303070250)

**学习阶段**：第一阶段 - Skills (LLM 基础与提示词工程)

**当前进度**：100% (已通关 API 调用、上下文管理、结构化输出)

---

## 一、 AI 应用开发全路线图

1. **Skills**: 大模型基础、Prompt 工程、JSON 提取。
    
2. **本地部署**: 使用 Ollama/vLLM 托管开源模型（DeepSeek, Llama）。
    
3. **MCP (Model Context Protocol)**: 统一模型与外部数据源的通信协议。
    
4. **RAG (检索增强生成)**: 向量数据库、知识库构建。
    
5. **Agent Skills**: Function Calling 与工具定义。
    
6. **Agent**: 规划、记忆与自主行动循环。
    
7. **多 Agent 协作**: AutoGen/CrewAI，数字员工团队编排。
    
8. **实战整合**: 工业级端到端项目落地。
    

---

## 二、 环境准备与 API 配置

### 1. 库安装

使用 Python 官方 SDK 进行开发：

Bash

```
pip install openai python-dotenv
```

### 2. 环境变量配置 (最佳实践)

为了避免 Key 泄露，禁止在代码中硬编码。

- **Windows 系统级设置**：
    
    1. 系统属性 -> 环境变量 -> 用户变量 -> 新建 `OPENAI_API_KEY`。
        
    2. **关键点**：修改后必须重启 IDE（如 VS Code）以清除缓存。
        
- **验证命令 (PowerShell)**：
    
    PowerShell
    
    ```
    echo $env:OPENAI_API_KEY
    ```
    

---

## 三、 核心实战：构建带记忆的聊天机器人

### 1. 原理：大模型的无状态性 (Stateless)

大模型本身不具备“记忆”，它不会记得你上一轮说了什么。

- **解决方案**：在本地维护一个 `messages` 列表，包含 `system`, `user`, `assistant` 三种角色。
    
- **上下文流**：每次请求都将完整的 `messages` 列表发送给 API。
    

### 2. 核心代码逻辑

Python

```
from openai import OpenAI

# 自动读取系统环境变量 OPENAI_API_KEY
client = OpenAI()

messages = [
    {"role": "system", "content": "你是一个专业的编程助手。"}
]

while True:
    user_input = input("🧑 你: ")
    if user_input.lower() in ['quit', 'exit']: break
    
    messages.append({"role": "user", "content": user_input})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    
    reply = response.choices[0].message.content
    print(f"🤖 AI: {reply}")
    messages.append({"role": "assistant", "content": reply})
```

---

## 四、 进阶实战：结构化输出 (JSON Extraction)

### 1. 为什么需要结构化输出？

在工程化开发中，AI 必须作为“数据转换器”使用。我们需要将模糊的自然语言转化为代码可操作的 JSON 对象，这要求模型输出符合严格的文法约束。

### 2. Prompt Engineering 技巧

- **角色设定**：明确模型是“数据提取引擎”。
    
- **负向约束**：禁止输出 Markdown 标记（如 ```json）和解释性废话。
    
- **数据定义**：明确字段名（Key）及其数据类型（String/Boolean）。
    
- **低温度值**：设置 `temperature=0.1` 减少模型的随机性和幻觉。
    

### 3. 实战代码片段

Python

```
def extract_info(text):
    system_prompt = """请以纯 JSON 格式提取：{"name": str, "action": str, "is_urgent": bool}。禁止任何废话。"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.1
    )
    
    # 词法解析：将字符串转化为 Python 字典
    result = json.loads(response.choices[0].message.content)
    return result
```

---

## 五、 避坑指南 (Troubleshooting)

|**错误代码**|**现象**|**原因与对策**|
|---|---|---|
|**401 Unauthorized**|提示 `Incorrect API key`|1. Key 复制不全；2. 账号未充值或被风控；3. **最常见**：修改环境变量后未重启 IDE，程序读到了旧的失效缓存。|
|**JSONDecodeError**|解析 JSON 失败|模型在 JSON 前后加了提示语（如“好的，这是你的结果”）。需加强 System Prompt 约束或设置模型输出格式参数。|
|**429 Too Many Requests**|请求频率过高|免费额度耗尽或账号触发并发限制。|

---

## 六、 下一步计划

- [ ] **第二阶段：本地部署 (Local Deployment)**
    
    - 学习安装 Ollama。
        
    - 下载 DeepSeek-R1 或 Llama3 本地模型。
        
    - 实现本地 API 对接，彻底解决“Key 余额”和“网络环境”问题。
        

---

**笔记更新日期**：2026-04-05