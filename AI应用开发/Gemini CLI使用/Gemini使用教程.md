# Gemini CLI 使用教程

Gemini CLI 是 Google 提供的命令行人工智能工具，允许你在终端中直接与 Gemini 模型交互，进行代码辅助、问答、文件处理等操作。

本教程基于 `Gemini CLI v0.40.1` 版本编写。

---

## 1. 快速开始与认证

### 1.1 启动
在终端中直接输入以下命令启动：
```bash
gemini
```

### 1.2 身份验证 (`/auth`)
首次使用或出现认证错误时（如你之前遇到的 "Further action is required"），需要验证 Google 账号。

*   **命令**: 输入 `/auth`
*   **作用**: 重新登录或验证你的 Google 账号身份。
*   **注意**: 确保你的账号拥有 Gemini Code Assist 权限（如截图显示的 Google One AI Pro 订阅）。

---

## 2. 常用命令列表

Gemini CLI 使用斜杠命令（Slash Commands）来控制工具行为。

| 命令 | 功能描述 |
| :--- | :--- |
| `/auth` | 管理 Google 账号登录状态。 |
| `/clear` | 清除当前对话历史，开始新的对话上下文。 |
| `/help` | 显示所有可用命令的帮助信息。 |
| `/upgrade` | 查看当前计划详情（如截图中的 `/upgrade`），或升级服务。 |
| `/exit` | 退出 CLI。 |
| `@` (At 符号) | 引用特定文件或文件夹内容（例如 `@README.md`）。 |

---

## 3. 核心功能演示

### 3.1 直接对话
你可以像与 Chatbot 聊天一样直接输入自然语言。

```text
> 解释一下什么是递归？
> 帮我把这段 Python 代码转换成 Go 语言。
```

### 3.2 引用文件上下文
这是 CLI 最强大的功能之一。你可以让 AI "阅读" 你当前目录下的文件。

**示例：让 AI 总结当前目录下的代码**
```text
> @src/main.py 请帮我检查这个文件有没有潜在的 Bug。
```

**示例：基于现有文件生成新内容**
```text
> @package.json 请根据这个配置文件，帮我写一个对应的 Dockerfile。
```

### 3.3 代码生成与编辑
你可以直接要求它生成代码，它通常会以代码块形式输出。

```text
> 帮我写一个 Node.js 的 Express 服务器，监听 3000 端口。
```

---

## 4. 常见问题排查

### 4.1 遇到 "Further action is required" (需要进一步操作)
这是账号风控或验证提示。
*   **解决方法**: 在 CLI 中输入 `1` (对应 `Verify your account`) 并按回车。系统通常会弹出一个浏览器窗口让你确认安全验证。

### 4.2 遇到容量错误 (Capacity Errors)
如截图中黄色警告框所示，Google 正在调整流量优先级。
*   **现象**: 在高负载时段可能会收到 "Service Unavailable" 或排队提示。
*   **解决方法**: 稍后重试。

### 4.3 快捷键提示
*   `Ctrl + C`: 中断当前正在生成的响应。
*   `Up Arrow`: 查看历史输入命令。

---

## 5. 进阶技巧：构建 Prompt

为了获得更好的结果，建议使用清晰的结构：

1.  **角色设定**: "你是一名资深的 Python 后端工程师..."
2.  **上下文引用**: "@database_schema.sql ..."
3.  **具体任务**: "请根据上述 schema，使用 SQLAlchemy 生成对应的 Model 类。"
4.  **约束条件**: "请添加详细的注释，并使用 Type Hinting。"

**完整示例**:
```text
> 你是一名前端专家。@src/components/Button.tsx 请重构这个组件，使其支持 Tailwind CSS，并添加一个 loading 状态的样式。不要改变原有的 onClick 逻辑。
```

---

## 6. 退出

输入以下命令结束会话：
```text
/exit
```