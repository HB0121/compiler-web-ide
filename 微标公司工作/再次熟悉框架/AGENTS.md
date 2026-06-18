# 项目总入口

## 1. 定位说明

`AGENTS.md` 是当前仓库的总入口文档。

它只负责三件事：

- 提供仓库级导航
- 定义任务路由与执行闭环
- 明确高优先级约束

详细文档索引、领域阅读顺序和专题说明统一下沉到 `docs/` 与对应目录 README，不在本文件重复展开。

## 2. 仓库导航

- `docs/`：正式规范与长期有效说明，优先阅读 [docs/AGENTS.md](./docs/AGENTS.md)
- `discuss/`：执行计划、评审、交接与阶段性质量事实，优先阅读 [discuss/AGENTS.md](./discuss/AGENTS.md)
- `Web/`：前端工作区入口，优先阅读 [Web/AGENTS.md](./Web/AGENTS.md)
- `Java/`：后端工作区入口，优先阅读 [Java/AGENTS.md](./Java/AGENTS.md)
- 项目本地技能目录：当前实现位于 `.codex/skills/`，优先级高于全局同名技能

## 3. 首次阅读建议

如果是第一次进入当前项目，建议按以下顺序建立上下文：

1. [docs 目录导航](./docs/AGENTS.md)
2. [Harness Engineering P0 总览](./docs/通用/Harness%20Engineering%20P0%20总览.md)
3. [仓库级架构与依赖规则](./docs/通用/仓库级架构与依赖规则.md)
4. 根据任务类型进入 [前端文档入口](./docs/前端/README.md) 或 [后端文档入口](./docs/后端/README.md)
5. 需要查看执行事实时，再读 [discuss 目录导航](./discuss/AGENTS.md)

## 4. 任务路由

- 后端标准 CRUD、资源管理、配置管理任务：优先使用 [`agilefast-backend-crud`](./.codex/skills/agilefast-backend-crud/SKILL.md)
- 前端列表页、CRUD 页、配置页任务：优先使用 [`agilefast-frontend-list-page`](./.codex/skills/agilefast-frontend-list-page/SKILL.md)
- 部署查询、制品上传、JAR/站点部署、状态与日志查看任务：优先使用 [`mid-deploy-bot`](./.codex/skills/deploy-mid/SKILL.md)
- 非标准业务逻辑：先在 `discuss/exec-plans/active/` 写执行计划，再决定代码落位与依赖边界
- 全栈联动任务：必须先冻结接口契约，再拆分前后端执行单元

## 5. 标准流程

1. 优先在独立 worktree 中执行体系化任务，不直接在当前脏工作树改动
2. 在 `discuss/exec-plans/active/` 新建或更新执行计划
3. 根据任务类型读取正式文档与项目本地技能
4. 完成实现或文档修改
5. 按对应领域规则完成验证
6. 在 `discuss/reviews/` 记录评审结论或问题
7. 完成后将计划沉淀到 `discuss/exec-plans/completed/`，需要交接时补 `discuss/handoffs/`

## 6. 验证与收尾规则

- 前端默认验证顺序：`lint -> typecheck -> 需要时 test:unit -> 页面交互变更时 test:e2e`
- 后端默认不由 AI 主动执行编译、打包、启动；必须输出结构化人工验证剧本
- 后端人工验证剧本至少包含：启动模块、接口路径、请求示例、预期响应、数据库影响、回归点
- 同类问题连续出现 3 次以上时，必须升级为根规则、正式文档、本地技能或检查脚本，而不是只修一次代码
- 任务完成闭环与收尾要求统一见 [docs/通用/Harness 闭环执行规范.md](./docs/通用/Harness%20闭环执行规范.md)
- 任务默认信任等级、授权边界与快速反馈要求统一见 [docs/通用/任务分层信任与授权规则.md](./docs/通用/任务分层信任与授权规则.md)
- 页面交互改动的浏览器级反馈要求统一见 [docs/通用/浏览器反馈闭环规范.md](./docs/通用/浏览器反馈闭环规范.md)

## 7. 高优先级约束

- 正式规范统一放在 `docs/`
- 计划、评审、交接、阶段性质量事实统一放在 `discuss/`
- 后端编译、打包、启动、联调验证默认由用户手动执行
- 当前项目的本地技能以当前仓库内技能目录定义为准，现阶段目录为 `.codex/skills/`
- 前端页面生成与样式调整时，默认保持简洁、规整、耐用，不做偏装饰化和偏营销化视觉
- 代码注释不能只停留在方法级别；类型、接口、配置对象和关键字段默认要求补充注释
