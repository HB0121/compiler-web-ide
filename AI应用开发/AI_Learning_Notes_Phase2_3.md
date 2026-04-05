# AI 应用开发学习笔记 (续)

**开发者**：黄彬 (12303070250)

**学习阶段**：第二阶段 (本地部署实战收尾) & 第三阶段 (MCP 协议前瞻)

---

## 一、 实战复盘：大模型幻觉与 JSON 解析异常

### 1. 经典工程报错：`JSONDecodeError`

在本地运行小参数模型（如 Qwen2.5:0.5b）进行结构化输出提取时，遇到了经典的词法/语法解析失败：

> `Expecting value: line 1 column 1 (char 0)`

**根本原因分析**：

尽管在 System Prompt 中严格定义了无 Markdown 标记的文法，但受限于小模型的“指令遵循 (Instruction Following)”能力不足，它依然按照训练语料中的惯性，输出了带有 ` ```json ` 标记的代码块。这导致 Python 的 JSON Parser 在词法扫描阶段遇到了非预期的反引号字符，直接触发异常。

### 2. 工程化解决方案 (防御性编程)

**方案 A：在语法解析前加入“词法清洗器” (正则预处理)**

借鉴编译器前端扫描器的做法，利用正则表达式将非法的 Token（Markdown 标记）清洗掉，只保留核心结构：

Python

```
import re

raw_output = response.choices[0].message.content
# 清洗掉 ```json 和 ``` 标记
cleaned_output = re.sub(r'```json\s*', '', raw_output)
cleaned_output = re.sub(r'```\s*', '', cleaned_output)
cleaned_output = cleaned_output.strip()

parsed_data = json.loads(cleaned_output)
```

**方案 B：开启 API 底层的“强约束 JSON 模式” (推荐)**

通过 `response_format` 参数，在模型底层推理阶段过滤掉不符合 JSON 文法的 Token 生成：

Python

```
response = client.chat.completions.create(
    model="qwen2.5", 
    messages=messages,
    temperature=0.1,
    response_format={"type": "json_object"} # 强制底层系统级 JSON 约束
)
```

---

## 二、 第三阶段前瞻：MCP (Model Context Protocol)

### 1. 核心概念与系统架构意义

在 AI 应用集成中，为了避免为每一个大模型和每一个外部数据源（文件、数据库、API）编写 $M \times N$ 次对接代码，MCP 引入了**标准化的双向 RPC 通信协议**。

这与编译原理中 LLVM 引入标准化中间表示 (IR) 的设计哲学一致，将系统架构的复杂度从 $M \times N$ 降维到 $M + N$。

### 2. MCP 核心角色划分

- **MCP Host (宿主)**：用户界面层（如 VS Code 插件、Claude Desktop）。
    
- **MCP Client (客户端)**：将大模型的意图翻译为标准的 MCP 协议请求。
    
- **MCP Server (服务端 - 开发重点)**：轻量级本地服务，负责封装本地数据和功能，向 Client 暴露。
    

### 3. MCP Server 提供的三大核心能力

1. **Resources (资源)**：以类似 URI 的格式暴露静态数据（例如向大模型暴露本地的 `.md` 实验报告文档）。
    
2. **Prompts (提示词)**：提供服务端定义好的、可复用的 System Prompts。
    
3. **Tools (工具)**：暴露可执行的函数签名。模型通过输出符合规范的 JSON 参数来请求调用这些工具（Function Calling 的标准化形式）。
    

---

## 三、 下一步计划

- [ ] **构建第一个 MCP Server**：使用 Python SDK 编写一个轻量级本地服务。
    
- [ ] **暴露本地能力**：尝试将本地文件读取或一个简单的计算函数封装为 MCP Tool。
    
- [ ] **客户端联调**：使用官方 Inspector 测试工具调用链路。
    

---

**笔记更新日期**：2026-04-05