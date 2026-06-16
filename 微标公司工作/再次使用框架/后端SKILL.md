---
name: "agilefast-backend-crud"
description: "在 AgileFast Java 项目中创建实体、Mapper、Service、Controller 以及标准 CRUD 接口时使用。优先遵循项目后端 CRUD 规范与通用 Controller 规范。"
---

# AgileFast 后端 CRUD 规范技能
当任务涉及新增实体、标准单表 CRUD 接口、配置管理接口或资源管理接口时，优先使用本技能。

## 先读规范

开始编码前先读取：

1. `../../../docs/通用/Harness Engineering P0 总览.md`
2. `../../../docs/通用/工作树并行开发与合并手册.md`
3. `../../../docs/后端/Harness Engineering P0 使用说明.md`
4. `../../../docs/后端/项目开发规范（后端）.md`
5. `../../../docs/后端/API模块创建规范（CRUD示例）.md`
6. `../../../docs/后端/通用Controller接口文档（CRUD Starter）.md`

## Harness P0 前置动作

1. 先在独立 worktree 中执行，不直接在当前脏工作树改后端代码。
2. 先在 `../../../discuss/exec-plans/active/` 新建或更新执行计划。
3. 如果任务属于全栈联动，先冻结接口契约，再进入后端段实现。

## 标准落地方式

标准单表 CRUD 优先采用：

```text
entity + mapper + service + controller
```

优先复用：

- `CrudServiceImpl<M, E, K>`
- `ServiceCrudController<S, E, K>`
- `BaseMapper<E>`

## 必须遵守

1. 持久层统一使用 `mapper` 命名，不新增 `dao`。
2. 新建实体类时，如果场景属于标准单表管理，默认同步生成通用 CRUD 接口。
3. 实体类优先放在 `entity` 包，字段补齐 `@Schema` 和表字段注释。
4. Controller 类补 `@Tag`，公开方法补 `@Operation`。
5. 优先使用 `MyBatis-Flex` 原生语义，避免重复声明同义能力。
6. 表结构脚本优先放模块自己的 `schema.sql` 或独立初始化脚本。
7. 不主动执行后端编译、打包、启动，由用户自行验证。
8. 不要写英文提示和英文描述，默认以中文为准。
9. 逻辑代码内必须补充必要注释，可以写在方法上方，也可以写在关键代码块前。

## 推荐实现顺序

1. 先补执行计划，明确代码归属、影响范围与验证方式。
2. 判断代码归属：当前 API 模块、starter 还是 `agilefast-biz`。
3. 先定义 `Entity` 和表结构脚本。
4. 再补 `Mapper`、`Service`、`Controller`。
5. 标准单表场景优先直接继承 `CrudServiceImpl + ServiceCrudController`。
6. 最后补齐 Swagger 注解、字段注释、模块说明与人工验证剧本。

## 输出检查

完成前至少自检以下几点：

- 是否把实体放到了 `entity` 包，持久层放到了 `mapper` 包。
- 是否在标准单表场景下生成了通用 CRUD 接口。
- 是否优先复用了 `CrudServiceImpl` 和 `ServiceCrudController`。
- 是否默认使用中文提示、中文注解和中文接口说明。
- 是否为关键逻辑代码补充了必要注释。
- 是否已经输出人工验证剧本，且包含启动模块、接口路径、请求示例、预期响应、数据库影响、回归点。
- 是否已经将结论回写到执行计划，必要时补充评审或交接记录。
