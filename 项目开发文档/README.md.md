# AI Fitness Planner

  

本项目是一个面向个人使用的本地优先 AI 健身计划桌面应用骨架。

当前阶段的目标是先跑通桌面界面、基础配置读取和本地 SQLite 数据存储。

  

## 环境要求

- Windows

- Python 3.12.x

- Git

  

## 初始化步骤

1. 安装 Python 3.12.x，并确保使用该解释器创建虚拟环境。

2. 在项目根目录创建并激活虚拟环境：

  

```powershell

python -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -r requirements.txt

```

  

3. 将 `.env.example` 复制为 `.env`，填入模型配置。

  

## 启动应用

```powershell

.\.venv\Scripts\Activate.ps1

python -m app.main

```

  

## 运行测试

```powershell

.\.venv\Scripts\Activate.ps1

pytest

```

  

## 当前阶段验证目标

- 可以启动最小 PySide6 桌面窗口

- 可以创建 SQLite 数据库并写入示例资料

- 可以从 `.env` 读取模型配置并识别缺失项

- 至少有一个基础 smoke test 通过