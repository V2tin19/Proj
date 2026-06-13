# 后端技术审查文档

## 一、技术栈

| 层级     | 技术                  | 说明                                          |
| -------- | --------------------- | --------------------------------------------- |
| Web 框架 | FastAPI + Uvicorn     | 异步 Python Web 框架                          |
| 数据校验 | Pydantic v2           | 请求/响应模型定义 (`app/models/schemas.py`)   |
| LLM 调用 | httpx                 | 通过 OpenAI 兼容协议调用 DeepSeek/Qwen 等模型 |
| 向量嵌入 | sentence-transformers | 本地模型 `BAAI/bge-small-zh-v1.5`，惰性加载   |
| 文档生成 | python-docx           | 生成 .docx 文件，支持中文字体（宋体/黑体）    |
| 文档解析 | pypdf + python-docx   | 提取 .pdf/.docx/.txt/.md 中的文本             |
| 数据存储 | JSON 文件             | `data/` 目录下的 JSON 文件，带线程锁          |
| 容器化   | Docker                | 基于 python:3.11-slim 的单阶段构建            |

**计划中但未实现**：PostgreSQL + Alembic、Celery + Redis、Playwright E2E 测试。

## 二、项目结构

```
.
├── app/
│   ├── main.py                 # 入口：CORS、路由挂载
│   ├── config.py               # 环境变量配置
│   ├── models/
│   │   └── schemas.py          # Pydantic 模型定义
│   ├── routes/                 # API 路由层
│   │   ├── health.py           #   GET  /api/health
│   │   ├── templates.py        #   GET  /api/prompt-templates
│   │   ├── knowledge_base.py   #   知识库 CRUD + 配置
│   │   ├── resume.py           #   POST /api/generate-resume
│   │   ├── export.py           #   POST /api/export-resume/docx
│   │   └── chat.py             #   POST /api/chat (SSE 流式)
│   └── services/               # 业务逻辑层
│       ├── llm_client.py       #   LLM HTTP 客户端
│       ├── resume_generator.py #   简历生成（LLM + 本地降级）
│       ├── knowledge_base.py   #   知识库管理 + RAG 检索
│       ├── embedding_service.py#   向量嵌入服务
│       ├── docx_exporter.py    #   Word 文档生成
│       └── document_parser.py  #   文件文本提取
├── data/                       # 运行时数据（JSON）
├── tests/                      # 压测脚本
├── test_api.py                 # API 集成测试脚本
├── requirements.txt
├── Dockerfile
├── run.sh / run.bat            # 本地启动脚本
├── README.md                   # 项目总文档
├── README_DEPLOY.md            # 部署文档
└── TEAM_GUIDE.md               # 团队协作文档
```

## 三、交互逻辑简述

### 简历生成流程

```
客户端 POST /api/generate-resume
  ├─ resume.py 接收请求，解析 prompt template
  ├─ knowledge_base.py 执行 RAG 检索（token-overlap 或 vector-cosine）
  ├─ resume_generator.py 组装 prompt + RAG 上下文
  │   ├─ 尝试调用 LLM（llm_client.py -> 外部 API）
  │   │   └─ 成功：解析 JSON，规范化为 GeneratedResumeData
  │   └─ 失败/超时：降级到本地规则生成
  └─ 返回结构化简历数据
```

### 知识库管理流程

```
上传文档 -> document_parser.py 提取文本
         -> knowledge_base.py 分块存储到 JSON
         -> embedding_service.py 生成向量（可选）

检索时：按 token-overlap 或 vector-cosine 算法召回相关片段
```

### 文档导出流程

```
客户端 POST /api/export-resume/docx（携带结构化简历数据）
  -> docx_exporter.py 生成 Word 文档
  -> StreamingResponse 返回文件流
```

### Chat 代理流程

```
客户端 POST /api/chat（携带 messages + api_url + api_key）
  -> chat.py 将请求转发到外部 LLM API
  -> SSE 流式返回响应
```

## 四、明显不规范的部分

### 4.1 安全问题

| 问题                                                                                            | 位置                   | 严重程度 |
| ----------------------------------------------------------------------------------------------- | ---------------------- | -------- |
| **SSRF 漏洞**：`/api/chat` 接受客户端传入的任意 `api_url`，无任何校验，可探测内网服务、云元数据（已修改） | `routes/chat.py:33-39` | 高       |
| **无认证鉴权**：所有端点完全开放，无 JWT/Session/任何身份验证                                   | 全局                   | 高       |
| **无速率限制**：`/api/chat` 可被滥用为 LLM API 免费代理                                         | 全局                   | 中       |
| **CORS 过于宽松**：`allow_methods=["*"]` + `allow_headers=["*"]` + `allow_credentials=True`     | `main.py:15-21`        | 中       |
| **API Key 明文传输**：`api_key` 在请求体中，可能被日志记录（已修改）                                      | `routes/chat.py`       | 低       |

### 4.2 代码质量问题

| 问题                                                                                                                                       | 位置                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| **跨模块引用私有函数**：`resume.py` 导入 `templates.py` 的 `_load_templates`，应抽取到 service 层（已修改）                                          | `routes/resume.py:8`                                                                    |
| **已废弃 API**：使用 `asyncio.get_event_loop()`（Python 3.10+ 废弃），6 处（已修改）                                                                 | `routes/templates.py:25`, `routes/knowledge_base.py:21,52,69,81`, `routes/resume.py:42` |
| **未使用的导入**：`chat.py` 的 `json`、`docx_exporter.py` 的 `List`、`embedding_service.py` 的 `Optional`、`resume.py` 的 `PromptTemplate`（已修改） | 各文件                                                                                  |
| **配置变量定义但未使用**：`config.py` 中的 `HOST` 和 `PORT` 从未被导入（已修改）                                                                     | `config.py:27-28`                                                                       |
| **无日志配置**：应用未配置 root logger，INFO 级别日志在生产环境会被静默丢弃                                                                | 全局                                                                                    |
| **错误信息语言不一致**：中文和英文错误信息混用，无统一规范                                                                                 | 全局                                                                                    |
| **线程锁在多进程下失效**：`threading.Lock` 仅在单进程模式下有效，uvicorn 多 worker 模式下不安全                                            | `services/knowledge_base.py:22`                                                         |

### 4.3 数据不一致

| 问题                                                                                                                        | 位置                         |
| --------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **种子数据算法名错误**：`"matchAlgorithm": "keyword-overlap"` 不是合法值，代码只识别 `"token-overlap"` 和 `"vector-cosine"`（已修改） | `data/knowledge-base.json:6` |
| **端口不一致**：README 要求后端运行在 3001 端口，代码默认 8000，`config.py` 默认 127.0.0.1，`run.sh` 默认 0.0.0.0（已修改）           | 多处                         |
| **embeddingProvider 值不匹配**：种子数据 `"local-fallback"` vs 代码默认 `"local"`（已修改）                                           | `data/knowledge-base.json:7` |

## 五、未完成的部分

### 5.1 TEAM_GUIDE.md 中明确规划但完全未实现

| 功能                                 | 状态   | 说明                                                                     |
| ------------------------------------ | ------ | ------------------------------------------------------------------------ |
| **数据库层**（PostgreSQL + Alembic） | 未开始 | 当前使用 JSON 文件存储，无数据库代码                                     |
| **认证鉴权**                         | 未开始 | 无任何 auth 中间件、JWT、Session 管理                                    |
| **Celery + Redis 异步任务**          | 未开始 | TEAM_GUIDE 中有 `celery -A app.worker worker` 示例，但无任何 worker 代码 |
| **pytest 单元测试**                  | 未开始 | 合并检查清单要求 "unit tests pass (pytest)"，但无任何 pytest 文件        |
| **Playwright E2E 测试**              | 未开始 | 仅在 TEAM_GUIDE 中提及                                                   |
| **deploy.sh 部署脚本**               | 未开始 | TEAM_GUIDE 提及由运维负责人维护，但文件不存在                            |
| **结构化日志/监控**                  | 未开始 | 仅有零散的 `logger.warning()` 调用                                       |

### 5.2 README 中提及但未实现

| 功能                   | 状态                      |
| ---------------------- | ------------------------- |
| **PDF 导出**           | 未开始（仅有 DOCX 导出）  |
| **docker-compose.yml** | 未开始（仅有 Dockerfile） |

### 5.3 代码中的隐式缺陷

| 问题                                                                                    | 位置                          |
| --------------------------------------------------------------------------------------- | ----------------------------- |
| LLM 返回的 JSON 解析无异常处理，`json.loads()` 失败会直接 500                           | `services/llm_client.py:65`   |
| 文件上传 `file.read()` 无 IOError 处理                                                  | `routes/knowledge_base.py:34` |
| 导出响应未设置 `Content-Length` 头                                                      | `routes/export.py:20-24`      |
| Chat 消息列表无 `max_length` 限制，可发送任意数量消息                                   | `models/schemas.py:187`       |
| 种子文档内容极短（50-100 字），远低于 chunkSize=180，RAG 检索实际只有一块，检索价值有限 | `data/knowledge-base.json`    |

## 六、总结

当前后端是一个可运行的 MVP 原型，核心的 LLM 简历生成 + RAG 检索 + DOCX 导出流程已跑通。但在安全性、工程规范、基础设施方面存在明显短板：

- **安全**：SSRF、无认证、无限速是最紧迫的问题
- **规范**：废弃 API、跨模块耦合、配置不一致需要清理
- **完整性**：数据库、认证、异步任务、测试框架等 TEAM_GUIDE 中规划的基础能力均未开始

建议优先级：安全修复 > 配置统一 > 代码清理 > 基础设施建设。
