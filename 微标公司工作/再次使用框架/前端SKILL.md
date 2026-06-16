---
name: "agilefast-frontend-list-page"
description: "在 AgileFast Web 项目中创建或改造列表页、CRUD 页时使用。优先遵循项目前端页面开发规范，统一页面骨架、国际化、搜索表单和弹窗交互。"
---

# AgileFast 前端列表页规范技能
当任务涉及 `Web/playground` 中的列表页、CRUD 页、配置管理页时，优先使用本技能。

## 先读规范

先读取以下文档，再开始改页面：

1. `../../../docs/通用/Harness Engineering P0 总览.md`
2. `../../../docs/前端/Harness Engineering P0 使用说明.md`
3. `../../../docs/前端/前端页面开发规范.md`
4. `../../../docs/前端/页面分层与边界规则.md`
5. `../../../docs/前端/前端接口对接规范.md`
6. 如页面属于既有模块，再读取同目录已有页面实现

## Harness P0 前置动作

1. 先在独立 worktree 中执行，不直接在当前脏工作树改页面。
2. 先在 `../../../discuss/exec-plans/active/` 新建或更新执行计划。
3. 如果任务属于全栈联动，先冻结接口契约，再进入前端段实现。

## 标准骨架

优先采用以下结构：

```text
src/views/{domain}/{page}/
├── index.vue
├── data.tsx
├── form-data.tsx
├── form-utils.ts
└── components/
   └── XxxModal.vue
```

职责约定：

- `index.vue` 负责页面编排、查询参数组装、打开弹窗、删除和批量操作。
- `data.tsx` 负责 `searchFormSchemas`、`columns` 和展示格式化。
- `form-data.tsx` 负责 `formSchemas` 和字段联动。
- `form-utils.ts` 负责表单值转换、配置组装和辅助方法。
- `components/` 负责弹窗、卡片、复杂展示组件。

## 必须遵守

1. 列表页优先使用 `useYlVxeTableCard`。
2. 搜索区优先使用 `yl-dc-form`，让查询条件直接对接 `QueryParamEntity.terms`。
3. 新增和编辑优先使用 `useVbenModal + useVbenForm`。
4. 文案优先走资源级国际化，新增 `src/locales/langs/{lang}/{resource}.json`。
5. 图标统一使用 `createIconifyIcon`。
6. 不主动新增真实业务静态路由，业务路由由用户或后端菜单配置提供。
7. `index.vue` 中不要堆积表格 schema、表单 schema 或长段格式化逻辑。
8. 不要写英文提示和英文描述，默认以中文为准。
9. 逻辑代码内必须补充必要注释，可以写在方法上方，也可以写在关键逻辑前。

## 推荐实现顺序

1. 先补执行计划，冻结资源名称、接口路径、列表字段、搜索字段和编辑字段。
2. 先建 `api` 类型和接口注释，再写 `data.tsx`。
3. 用 `index.vue` 串起 `useYlVxeTableCard`、批量操作和弹窗。
4. 用 `components/XxxModal.vue` 收口新增和编辑逻辑。
5. 补齐 `zh-CN` 和 `en-US` 语言文件。
6. 按默认顺序完成前端验证，并将结果回写到执行计划。

## 输出检查

完成前至少自检以下几点：

- 是否使用了 `index.vue + data.tsx + components/` 的结构。
- 是否使用了 `useYlVxeTableCard`、`yl-dc-form`、`useVbenModal`。
- 是否新增了独立的资源级国际化文件。
- 是否默认以中文为主，没有新增英文提示和英文描述。
- 是否把复杂逻辑留在了合适的文件，而不是全部堆在 `index.vue`。
- 是否为关键逻辑代码补充了必要注释。
- 是否按顺序完成了 `lint -> typecheck -> 需要时 test:unit -> 页面交互变更时 test:e2e`。
- 是否已经将验证结论回写到执行计划，必要时补充评审或交接记录。
