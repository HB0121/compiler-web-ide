# 仿 12306 机票抓取与自动更新系统 · 设计文档

> **题目编号**：3.1.7
> **课程**：综合课程设计 III（WEB 方向）
> **年级**：2023 级
> **文档版本**：v1.0
> **创建日期**：2026-06-11
> **文档状态**：待复审

---

## 0. 需求澄清记录

在动手设计前，通过 6 个澄清问题确认了以下关键决策：

| # | 维度 | 决策 |
|---|---|---|
| 1 | 数据源 | 爬取公开网页 HTML（携程/去哪儿/航司官网） |
| 2 | 爬虫技术栈 | Python Scrapy + Java SpringBoot 调度（双服务） |
| 3 | 团队规模 | 两人组队 |
| 4 | AI 任务 | 基础（出行建议）+ 进阶（RAG 购票时机）都做 |
| 5 | 前端形式 | Vue 3 PC 端 + 微信小程序 |
| 6 | 部署目标 | 公网部署（云服务器 + 域名 + HTTPS） |

---

## 1. 题目原文与需求拆解

### 1.1 任务书原文 4 大功能要求

```
① 抓取可靠的机票数据      ⭐ 核心
② 将机票信息存入数据库
③ 提供机票数据接口        ⭐ 关键（软件对软件，不是 UI）
④ 前端页面展示
```

### 1.2 需求拆解（按"输入-处理-输出"建模）

| 需求编号 | 输入 | 处理 | 输出 |
|---|---|---|---|
| F1. 数据抓取 | 目标 URL 队列、代理池 | HTTP 请求 + HTML 解析 + 字段提取 | 原始机票数据 |
| F2. 数据清洗 | 原始机票数据 | 三关校验 + 异常过滤 + 格式标准化 | 干净机票数据 |
| F3. 数据存储 | 干净机票数据 | upsert 到 MySQL | 持久化记录 |
| F4. 数据接口 | 客户端 HTTP 请求 | SpringBoot 查询 + 缓存 | JSON 响应 |
| F5. 前端展示 | JSON 数据 | Vue / 小程序渲染 | 用户界面 |
| F6. AI 出行建议（基础） | 自然语言 | NLU 解析 + 本地检索 + 大模型生成 | 出行方案 |
| F7. AI 购票时机（进阶） | 自然语言 + 节假日 | RAG 检索 + 大模型生成 | 分析报告 |

### 1.3 非功能需求

| 维度 | 要求 |
|---|---|
| 性能 | API P99 < 500ms；爬虫吞吐量 ≥ 100 航班/分钟 |
| 可靠性 | 数据入库成功率 > 95%；爬虫异常重试 3 次 |
| 可维护 | 模块职责清晰；新数据源可在 1 天内接入 |
| 可观测 | 所有数据可追溯到原始 HTML；关键路径有日志 |
| 合规 | 遵守 robots.txt；请求频率 ≤ 1 req/3s/源 |

---

## 2. 设计原则

1. **数据可靠性优先**：所有入库数据必须经过"格式校验 → 完整性校验 → 合理性校验"三关
2. **架构清晰**：Python、Java、前端三端职责分离，单端独立可测试
3. **可观测性**：每条数据可追溯（哪个爬虫、什么时间、哪个数据源、原始 HTML 路径）
4. **可扩展性**：新增数据源只需加一个爬虫，**不改 Java 端和前端**
5. **AI 渐进增强**：基础 AI 任务独立可用，进阶 RAG 作为可选增强

---

## 3. 系统总体架构

### 3.1 架构总览

```
┌────────────────────────────────────────────────────────────┐
│                        用户层 (Frontend)                    │
│  ┌──────────────────┐           ┌──────────────────────┐   │
│  │  Vue 3 PC 端      │           │  微信小程序端          │   │
│  │  (航班查询/筛选)  │           │  (出行规划/AI对话)    │   │
│  └────────┬─────────┘           └──────────┬───────────┘   │
└───────────┼────────────────────────────────┼──────────────┘
            │ HTTPS / REST                    │
            ▼                                 ▼
┌────────────────────────────────────────────────────────────┐
│                    接入层 (Nginx 反向代理)                   │
│   静态资源 │ 域名 │ HTTPS │ 限流 │ Gzip                     │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│                   应用层 (SpringBoot 调度 + API 网关)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ 航班API  │ │ AI服务   │ │ 用户API  │ │ 爬虫调度中心    │ │
│  │          │ │ (星火)   │ │          │ │ (Quartz)       │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ RAG 检索服务 (FAISS + 历史价格)  ← 进阶 AI 任务       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────┘
                         │ JDBC
                         ▼
┌────────────────────────────────────────────────────────────┐
│                    数据层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  MySQL 8.0   │  │  Redis 7     │  │  FAISS 索引文件   │  │
│  │  (业务数据)   │  │ (缓存/去重)  │  │  (进阶 RAG 向量)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│                  数据采集层 (Python 爬虫集群)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Scrapy-A │  │ Scrapy-B │  │ Scrapy-C │  │  ...     │   │
│  │ 携程爬虫  │  │ 去哪儿爬虫│  │ 航司爬虫 │  │ 预留扩展  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  代理池 │ 频率控制 │ User-Agent 轮换 │ 异常重试        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈

| 层 | 技术 | 版本 | 理由 |
|---|---|---|---|
| 爬虫 | Python + Scrapy | 3.11 / 2.11 | 异步高性能、社区成熟、动态页面好处理 |
| 反爬 | fake-useragent + 自建代理池 | — | 必修 |
| 数据清洗 | Pandas + 自定义规则 | 2.x | 异常值检测、缺失值填充 |
| 调度 | SpringBoot + Quartz | 3.x / 2.3+ | 定时触发爬虫、任务编排 |
| API | SpringBoot + MyBatis-Plus | 3.2 / 3.5 | 课程重点 |
| 数据库 | MySQL + Redis | 8.0 / 7 | 经典组合 |
| 缓存 | Redis | — | 热门航线、价格缓存 |
| 向量库 | FAISS | 1.7+ | 进阶 RAG 用 |
| 嵌入模型 | text2vec-base-chinese | — | 本地免费，价格描述向量化 |
| 大模型 | 讯飞星火 v3.5 | — | 免费额度 |
| 前端 PC | Vue 3 + Element Plus + ECharts | — | 课程主流 |
| 前端 MP | 微信原生小程序 | — | 不引入新框架 |
| 反向代理 | Nginx | 1.24 | 静态 + HTTPS |
| 服务器 | 阿里云轻量 / 腾讯云轻量 | 2C4G | 备案前可用港服 |

---

## 4. 核心模块划分

### 4.1 后端模块（SpringBoot）

```
backend/
├── flight-api          # 航班查询/筛选/详情 API
├── ai-assistant        # AI 出行建议（基础任务）
├── rag-service         # 进阶 RAG 检索
├── crawler-scheduler   # 爬虫调度中心（Quartz）
├── data-sync           # 爬虫结果同步（监听 MySQL binlog 或轮询）
├── user-service        # 用户/收藏/历史
└── common              # 通用工具（响应包装、异常、限流）
```

### 4.2 爬虫模块（Python / Scrapy）

```
crawler/
├── crawlers/
│   ├── ctrip/          # 携程
│   ├── qunar/          # 去哪儿
│   └── airline/        # 航司官网
├── middlewares/
│   ├── proxy.py        # 代理池
│   ├── retry.py        # 重试
│   └── throttle.py     # 频率控制
├── pipelines/
│   ├── cleaner.py      # 清洗
│   ├── validator.py    # 校验
│   └── mysql.py        # 落库
└── utils/
    ├── parsers.py      # 字段解析
    └── holidays.py     # 节假日识别
```

### 4.3 前端模块

**Vue 3 PC 端**：
```
frontend-pc/
├── pages/
│   ├── search/         # 搜索
│   ├── result/         # 结果
│   ├── detail/         # 详情
│   ├── ai-assistant/   # AI 对话
│   └── price-trend/    # 价格趋势
└── components/         # 通用组件
```

**微信小程序**：
```
frontend-mp/
├── pages/
│   ├── index/          # 首页（搜索）
│   ├── result/         # 结果
│   ├── ai/             # AI 对话
│   └── mine/           # 我的
└── utils/              # 工具
```

### 4.4 团队分工（2 人各 50%）

| 成员 | 负责模块 | 工作量 |
|---|---|---|
| **A · 数据端** | Python 爬虫（3 个数据源）+ 数据清洗 + MySQL 表设计 + 节假日数据维护 + 部署 | 50% |
| **B · 服务端+前端** | SpringBoot 全栈 + Vue PC 端 + 微信小程序 + AI 双任务 + RAG 检索 | 50% |
| 共同 | 报告撰写、答辩 PPT、GitHub 双人提交记录 | — |

> 注：MySQL 表设计由 A 主笔，B 审核，避免命名/类型不一致

---

## 5. 数据模型设计

### 5.1 核心表

```sql
-- 机场字典
CREATE TABLE airport (
    code        VARCHAR(8)  PRIMARY KEY,   -- IATA 代码: PEK
    name_cn     VARCHAR(64) NOT NULL,      -- 北京首都国际机场
    name_en     VARCHAR(128),
    city_cn     VARCHAR(32) NOT NULL,      -- 北京
    city_code   VARCHAR(8),                -- BJS
    latitude    DECIMAL(10,6),
    longitude   DECIMAL(10,6)
);

-- 航司字典
CREATE TABLE airline (
    code        VARCHAR(8)  PRIMARY KEY,   -- CA
    name_cn     VARCHAR(64) NOT NULL,      -- 中国国际航空
    name_en     VARCHAR(128),
    logo_url    VARCHAR(256)
);

-- 航班（核心实体）
CREATE TABLE flight (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    flight_no       VARCHAR(16)  NOT NULL,           -- CA1234
    airline_code    VARCHAR(8)   NOT NULL,           -- CA
    from_airport    VARCHAR(8)   NOT NULL,           -- PEK
    to_airport      VARCHAR(8)   NOT NULL,           -- PVG
    depart_time     DATETIME     NOT NULL,
    arrive_time     DATETIME     NOT NULL,
    duration_min    INT          NOT NULL,           -- 分钟
    aircraft_model  VARCHAR(32),                     -- 738
    price_economy   DECIMAL(10,2),
    price_business  DECIMAL(10,2),
    price_first     DECIMAL(10,2),
    seats_left      INT,                              -- 剩余座位
    data_source     VARCHAR(16)  NOT NULL,           -- ctrip/qunar/airline
    crawled_at      DATETIME     NOT NULL,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_flight_date (flight_no, depart_time, data_source),
    INDEX idx_route_date (from_airport, to_airport, depart_time),
    INDEX idx_price (price_economy)
);

-- 价格历史（进阶 AI 任务依赖）
CREATE TABLE flight_price_history (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    flight_id       BIGINT       NOT NULL,
    depart_date     DATE         NOT NULL,           -- 起飞日期
    price           DECIMAL(10,2) NOT NULL,
    class_type      VARCHAR(16)  NOT NULL,           -- economy/business/first
    recorded_at     DATETIME     NOT NULL,
    INDEX idx_flight_date (flight_id, depart_date)
);

-- 用户
CREATE TABLE user (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(32)  UNIQUE NOT NULL,
    password        VARCHAR(128) NOT NULL,           -- BCrypt
    nickname        VARCHAR(32),
    avatar_url      VARCHAR(256),
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- 用户搜索历史
CREATE TABLE search_history (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    query_json      JSON         NOT NULL,           -- {from,to,date,...}
    result_count    INT,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at)
);

-- AI 对话会话
CREATE TABLE ai_session (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT,
    session_uuid    VARCHAR(64)  UNIQUE NOT NULL,
    type            VARCHAR(16)  NOT NULL,           -- advice/timing
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- AI 对话消息
CREATE TABLE ai_message (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    session_id      BIGINT       NOT NULL,
    role            VARCHAR(16)  NOT NULL,           -- user/assistant
    content         TEXT         NOT NULL,
    token_count     INT,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id, created_at)
);

-- 节假日信息
CREATE TABLE holiday (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    holiday_date    DATE         NOT NULL,
    name            VARCHAR(64)  NOT NULL,           -- 春节/国庆/...
    type            VARCHAR(16)  NOT NULL,           -- statutory/traditional
    year            INT          NOT NULL,
    UNIQUE KEY uk_date (holiday_date)
);
```

### 5.2 向量库（FAISS）

存储在文件系统 `data/faiss/flight_index.bin`，元数据存 MySQL `flight_embedding` 表：
- 向量维度：768（text2vec-base-chinese）
- 每条记录：`{flight_id, text_embedding, raw_text, holiday_flag}`
- `raw_text` 格式：`"2026-10-01 PEK-PVG CA1234 经济舱680元 国庆假期首日"`
- 重建策略：每周日凌晨全量重建

---

## 6. 关键数据流程

### 6.1 数据采集与入库

```
[Scrapy 启动]
   │
   ▼
[生成 URL 队列] → [代理池获取 IP] → [设置随机 UA]
   │
   ▼
[HTTP GET 请求] ─── 失败 ──→ [指数退避重试 3 次] → 放弃 + 告警
   │ 成功
   ▼
[解析 HTML/JSON 提取字段]
   │
   ▼
[Validator 三关校验] ─── 失败 ──→ [DropItem + 记录原 HTML 到 /data/failed/]
   │ 通过                         （可追溯到原始 HTML）
   ▼
[Cleaner 清洗] (去空格/单位统一/时间格式)
   │
   ▼
[MySQL upsert] (以 flight_no+depart_time+data_source 为唯一键)
   │
   ▼
[Redis 缓存更新] (热门航线 TTL 5min)
   │
   ▼
[Quartz 任务] 监听价格变化,触发"AI 购票时机"异步计算
```

**三关校验内容**：

1. **格式校验**：必填字段非空、日期合法、价格是数字
2. **完整性校验**：起飞时间 < 到达时间、票价 > 0、机场代码在字典内
3. **合理性校验**：经济舱 < 头等舱、票价波动 < 50%（突变视为异常）

### 6.2 用户查询

```
[Vue 发送 GET /api/flights?from=PEK&to=PVG&date=...]
   │
   ▼
[Nginx 反代 + HTTPS 终止]
   │
   ▼
[SpringBoot Controller]
   │
   ├─→ [Redis 查缓存] 命中 → 返回
   │
   └─→ 未命中 → [MySQL 查询] → [缓存写入] → 返回
   │
   ▼
[Vue 渲染] (ECharts 画价格趋势)
```

### 6.3 AI 出行建议（基础任务）

```
[前端输入] "下周五去北京出差，预算 1200"
   │
   ▼
[POST /api/ai/advice] (SpringBoot)
   │
   ├─ 步骤 1: [NLU 解析] 提取 {目的地:北京, 时间:下周五, 预算:1200}
   │   (正则 + 关键词 + 讯飞星火 NLU 辅助)
   │
   ├─ 步骤 2: [本地检索] SELECT * FROM flight
   │           WHERE to='PEK' AND date BETWEEN ... AND ...
   │           AND price <= 1200
   │           ORDER BY 综合推荐分 DESC LIMIT 10
   │
   ├─ 步骤 3: [构造 Prompt] 模板:
   │   "你是出行规划助手。候选航班(节选):[...JSON]
   │    用户需求:{...}。请生成:
   │    1) 推荐航班(理由)  2) 出行建议  3) 注意事项"
   │
   └─ 步骤 4: [调用讯飞星火] → [流式返回 SSE] → 前端打字机展示
```

### 6.4 AI 购票时机预测（进阶 RAG）

```
[用户问] "国庆去东京，机票什么时候买最划算？"
   │
   ▼
[POST /api/ai/timing] (SpringBoot)
   │
   ├─ 步骤 1: [NLU 解析] {目的地:东京(可类比上海/广州出境), 
   │                  时间:国庆(2026-10-01), 任务:购票时机}
   │
   ├─ 步骤 2: [RAG 检索] FAISS 向量库检索
   │   (a) 历史同期价格序列 (b) 节假日信息表
   │   → top-5 相关历史规律
   │
   ├─ 步骤 3: [构造 Prompt] 注入:
   │   - 检索到的历史规律(节选)
   │   - 当年节假日安排
   │   - 用户问题
   │   → 讯飞星火生成分析报告
   │
   └─ 步骤 4: [流式返回] 报告内容(最佳购票时段/涨价风险/多轮追问入口)
```

**多轮对话管理**：用 Redis 存 `session_id → 对话历史`，每轮带 5 轮上下文。

---

## 7. 错误处理

### 7.1 错误分类与处理

| 错误类型 | 触发场景 | 处理策略 | 用户感知 |
|---|---|---|---|
| **爬虫层** | | | |
| 网络超时 | 目标站响应慢 | 指数退避重试 3 次 + 切换代理 | 后台告警，**前端无感** |
| 反爬封禁 | 429/403 | 冷却 30 分钟 + 告警 + 降级到备用源 | 数据延迟更新 |
| 解析失败 | 页面改版 | 进入"待修复队列"，人工介入 | 该数据源停服 |
| **数据层** | | | |
| 校验失败 | 价格为空/时间倒序 | DropItem + 记录原 HTML | 数据不入库 |
| 数据库连接 | MySQL 挂 | 连接池重试 + 告警 | 5xx 错误 |
| **应用层** | | | |
| API 参数非法 | 缺出发地 | 400 + 详细错误码 | 友好提示 |
| AI 调用失败 | 讯飞超时 | 本地降级到规则引擎（按价格排序） | 仍返回结果 |
| **前端层** | | | |
| 网络断 | 移动端弱网 | 重试按钮 + 离线缓存上次结果 | 提示网络异常 |
| 数据空 | 无航班 | 友好空态 + 推荐临近日期 | "暂无航班" |

### 7.2 日志与监控

- **Python 端**：Scrapy 内置日志 + 异常 HTML 落盘到 `/data/failed/{date}/`
- **Java 端**：Logback + 文件日志，按 INFO/WARN/ERROR 分级
- **监控指标**（简单版）：爬虫成功率、入库条数、API P99 延迟、AI 调用次数
- **告警渠道**：钉钉/企业微信 Webhook（可选）

---

## 8. 测试策略

任务书未硬性要求测试，但写进设计体现工程能力。

### 8.1 测试分层

| 层 | 工具 | 范围 |
|---|---|---|
| 爬虫单测 | pytest | 解析函数、清洗规则、校验器 |
| Java 单测 | JUnit5 + Mockito | Service 层、工具类 |
| Java 接口测试 | Postman + Newman | 全部 REST API |
| 前端组件测试（可选） | Vitest | 复杂组件 |
| 端到端（可选） | Playwright | 关键路径 |
| AI 评估（加分项） | 人工评测 + 样例集 | 准备 20 条样例 prompt |

### 8.2 必测关键路径

1. 爬虫 → 解析 → 校验 → 入库 完整链路（**重点**）
2. 三关校验中"异常数据"是否被拦截
3. 缓存命中 vs 缓存穿透
4. AI 出行建议：5 条不同输入的输出质量
5. 进阶 RAG：检索返回的 top-5 与人工判断一致性

---

## 9. 部署与运维

### 9.1 服务器规划

| 服务 | 部署位置 | 配置 |
|---|---|---|
| Python 爬虫 | 容器 1（独立） | 1C2G |
| SpringBoot | 容器 2 / 系统服务 | 1C2G |
| MySQL | 容器 3 / RDS | 1C1G（初期） |
| Redis | 容器 4 | 512M |
| Nginx | 宿主机 | — |

> 最低配置：2C4G 单机（学习/演示场景）

### 9.2 部署架构

```
[用户]
   │
   ▼
[Cloudflare / 阿里云 DNS] (HTTPS + 缓存)
   │
   ▼
[Nginx]
   ├── /api/*   → SpringBoot (8080)
   ├── /        → Vue 静态文件 (/var/www/frontend-pc)
   └── /mp/     → 微信小程序后端 (同 SpringBoot)
   │
   ▼
[SpringBoot] → MySQL + Redis + FAISS
   │
   ▼
[Python 爬虫] → MySQL
```

### 9.3 运维要点

- HTTPS：Let's Encrypt 自动签发 + crontab 续期
- 备份：MySQL 每日全量备份到 OSS
- 日志切割：logrotate 每日切割
- 进程守护：systemd / supervisor

---

## 10. 开发路线图

> 总周期 63 天（约 9 周），按"天"为最小粒度跟踪。

| 阶段 | 天数 | 任务 | 里程碑 |
|---|---|---|---|
| ① 基础搭建 | Day 1-7 | MySQL 建表、SpringBoot 初始化、Scrapy 模板 | 项目骨架可跑 |
| ② 爬虫攻坚 | Day 8-21 | 1 个数据源跑通 + 三关校验 + 清洗 | 数据库 ≥1000 条 |
| ③ API + 前端 | Day 22-28 | 查询/筛选/详情 API + Vue 基础页面 | PC 端可演示 |
| ④ AI 基础 | Day 29-35 | AI 出行建议助手（讯飞星火对接） | 基础 AI 任务完成 |
| ⑤ 进阶 RAG | Day 36-42 | FAISS 索引构建 + 检索 + 报告生成 | 进阶 AI 任务完成 |
| ⑥ 小程序 | Day 43-49 | 微信小程序（核心页 + AI 对话页） | 双端可用 |
| ⑦ 部署 | Day 50-56 | Nginx + HTTPS + 域名 + 监控 | 公网可访问 |
| ⑧ 收尾 | Day 57-63 | 报告撰写 + 查重 + 答辩 PPT + U 盘 | 终版提交 |

---

## 11. 风险与应对

| 风险 | 等级 | 应对策略 |
|---|---|---|
| 目标网站改版导致爬虫失效 | 高 | 设计抽象的 Parser 接口，多源备份，每周回归测试 |
| 反爬封禁 IP | 高 | 自建代理池 + UA 轮换 + 频率 ≤ 1req/3s |
| 公开页面数据不全（缺价格等） | 中 | 爬多个数据源交叉验证；缺失值标记后用历史均值填充 |
| 讯飞星火 API 限额耗尽 | 中 | 申请多账号轮换；本地规则引擎降级 |
| 备案审核周期长 | 中 | 用港服或海外节点（演示可用） |
| FAISS 索引与 MySQL 不一致 | 中 | 重建时双写（先写新索引再切） |

---

## 12. 报告与答辩要点

### 12.1 报告目录映射

| 章节 | 内容 | 来源 |
|---|---|---|
| 第 1 章 绪论 | 背景、目标、意义 | 任务书 + 本文档 §1 |
| 第 2 章 需求分析 | 功能需求、非功能需求、用例图 | 本文档 §1.2、§1.3 |
| 第 3 章 系统设计 | 架构、技术栈、模块划分、数据模型 | 本文档 §3-§5 |
| 第 4 章 详细设计 | 关键流程、接口设计、数据库设计 | 本文档 §6、§5 |
| 第 5 章 系统实现 | 核心代码、爬虫实现、AI 集成 | 实现阶段产出 |
| 第 6 章 系统测试 | 测试用例、测试结果 | 本文档 §8 |
| 第 7 章 部署与运维 | 部署架构、运维要点 | 本文档 §9 |
| 第 8 章 总结与展望 | 工作总结、不足与改进 | 实现阶段产出 |

### 12.2 答辩演示路径

1. 打开公网域名 → 展示首页（PC）
2. 搜索"北京→上海" → 展示结果列表
3. 点击详情 → 展示航班详情 + 价格趋势图
4. 打开 AI 出行建议 → 输入自然语言 → 展示 AI 回复
5. 打开进阶 RAG 购票时机 → 输入"国庆去东京" → 展示分析报告
6. 切到小程序 → 展示双端一致体验
7. 打开爬虫监控页 → 展示实时抓取状态
8. Q&A

---

## 附录 A：参考资料

### 官方文档
- 讯飞星火 API：https://www.xfyun.cn/doc/spark/Web.html
- Moonshot Kimi API：https://platform.moonshot.cn/docs/api/chat
- SpringBoot 官方：https://spring.io/projects/spring-boot
- Scrapy 官方：https://scrapy.org/

### 参考视频（B 站）
- `BV1PE411i7CV` SpringBoot 基础教程
- `BV18E411a7mC` Vue 基础教程
- `BV1K5sCeSEFu` 大模型 API 调用（Vue+SpringBoot 实战）
- `BV1Cxj7zjEng` 多轮对话与 RAG
- `BV1JV4y1e7iU` RAG 向量知识库入门

### Python 包
- `scrapy` 2.11+
- `fake-useragent` 1.5+
- `pandas` 2.x
- `sqlalchemy` 2.x
- `pymysql` 1.1+
- `langchain` 0.1+
- `faiss-cpu` 1.7+
- `sentence-transformers` 2.x

---

**文档结束。** 请复审后告知是否需要修改。
