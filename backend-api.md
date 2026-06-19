# 后端 API 接口文档

> **基础地址**：`http://localhost:8000`（可通过 `HOST` / `PORT` 环境变量修改）
>
> **所有接口前缀**：`/api`
>
> **交互式文档**：启动服务后访问 `http://localhost:8000/docs`（Swagger UI），可在线调试所有接口

---

## 目录

1. [根路径](#1-根路径)
2. [健康检查](#2-健康检查)
3. [模板列表](#3-模板列表)
4. [生成简历](#4-生成简历)
5. [导出简历为 Word](#5-导出简历为-word)
6. [知识库管理](#6-知识库管理)
7. [AI 对话](#7-ai-对话)
8. [环境变量](#8-环境变量)

---

## 1. 根路径

### `GET /`

简单的存活检测，返回服务运行状态和文档入口地址。

**响应** `200 OK`

```json
{
  "message": "AI Resume Backend is running",
  "docs": "/docs"
}
```

---

## 2. 健康检查

### `GET /api/health`

检查服务是否正常运行，以及 LLM 是否已配置。适合用于运维监控或前端判断后端就绪状态。

**响应** `200 OK`

```json
{
  "ok": true,
  "now": "2026-06-14T10:30:00.000000+00:00",
  "provider": "llm-configured"
}
```

| 字段       | 类型   | 说明                                                                                                               |
| ---------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| `ok`       | bool   | 始终为 `true`（服务挂了就不会返回了）                                                                              |
| `now`      | string | 当前 UTC 时间（ISO 8601）                                                                                          |
| `provider` | string | `"llm-configured"` — LLM 已配置，可正常使用 AI 功能；`"local-fallback"` — 未配置 LLM，生成简历时将使用本地规则降级 |

---

## 3. 模板列表

### `GET /api/prompt-templates`

获取所有简历生成模板。前端用这个列表展示模板选择器，用户选中的模板 ID 会传给生成接口。

**响应** `200 OK`

```json
[
  {
    "id": "campus-concise",
    "name": "简约校招版",
    "style": "简约风格",
    "targetAudience": "通用校招与实习投递",
    "description": "强调基础信息完整、结构清晰、适合大多数学生首版简历。",
    "systemPrompt": "你是一名高校就业指导老师……"
  }
]
```

| 字段             | 类型   | 说明                                        |
| ---------------- | ------ | ------------------------------------------- |
| `id`             | string | 模板 ID，生成简历时传这个值                 |
| `name`           | string | 模板中文名称，展示用                        |
| `style`          | string | 风格标签                                    |
| `targetAudience` | string | 适用场景                                    |
| `description`    | string | 模板说明                                    |
| `systemPrompt`   | string | 发给 LLM 的系统提示词（前端一般不需要使用） |

**当前内置 5 个模板**：

| ID                      | 名称       | 适用场景                          |
| ----------------------- | ---------- | --------------------------------- |
| `campus-concise`        | 简约校招版 | 通用校招与实习投递                |
| `business-professional` | 商务正式版 | 互联网/金融等正式求职             |
| `creative-highlight`    | 创意亮点版 | 设计/运营/市场类岗位              |
| `tech-rag`              | 技术研发版 | 技术岗求职（支持 RAG 知识库增强） |
| `graduate-research`     | 升学科研版 | 考研/保研/留学申请                |

---

## 4. 生成简历

### `POST /api/generate-resume`

核心接口。接收学生填写的信息，返回结构化简历数据。

**工作流程**：前端收集用户输入 → 调用此接口 → 获得 JSON 格式的简历数据 → 传给导出接口生成 Word 文件。

**请求体** `application/json`

```json
{
  "name": "张三",
  "gender": "男",
  "age": "22",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "website": "",
  "school": "某某大学",
  "major": "计算机科学与技术",
  "degree": "本科",
  "politicalStatus": "共青团员",
  "applicationPosition": "Java后端开发",
  "targetRole": "后端开发工程师",
  "targetIndustry": "互联网",
  "ranking": "前10%",
  "courses": "数据结构,算法设计,操作系统",
  "skillsText": "Java\nSpring Boot\nMySQL",
  "honorsText": "国家奖学金\nACM铜奖",
  "interests": "开源贡献,技术博客",
  "selfIntroduction": "热爱编程，喜欢钻研新技术",
  "templateId": "tech-rag",
  "enableRag": true,
  "retrievalTopK": null,
  "wordCount": 800,
  "educationExperiences": [
    {
      "school": "某某大学",
      "degree": "本科",
      "major": "计算机科学与技术",
      "startDate": "2021-09",
      "endDate": "2025-06"
    }
  ],
  "workExperiences": [
    {
      "company": "某科技公司",
      "position": "后端实习生",
      "startDate": "2024-07",
      "endDate": "2024-09",
      "description": "负责后端接口开发\n参与数据库优化"
    }
  ],
  "projectExperiences": [
    {
      "projectName": "校园二手交易平台",
      "role": "后端负责人",
      "startDate": "2023-03",
      "endDate": "2023-06",
      "briefIntroduction": "基于Spring Boot的校园二手交易系统",
      "description": "负责后端架构设计与核心模块开发\n实现用户认证、商品管理、订单系统"
    }
  ]
}
```

**请求字段说明**

| 字段                   | 类型      | 必填 | 说明                                                                   |
| ---------------------- | --------- | ---- | ---------------------------------------------------------------------- |
| `name`                 | string    | 否   | 姓名                                                                   |
| `gender`               | string    | 否   | 性别                                                                   |
| `age`                  | string    | 否   | 年龄                                                                   |
| `phone`                | string    | 否   | 电话                                                                   |
| `email`                | string    | 否   | 邮箱                                                                   |
| `website`              | string    | 否   | 个人主页 / GitHub / 博客链接                                           |
| `school`               | string    | 否   | 学校名称                                                               |
| `major`                | string    | 否   | 专业                                                                   |
| `degree`               | string    | 否   | 学历（本科/硕士/博士等）                                               |
| `politicalStatus`      | string    | 否   | 政治面貌                                                               |
| `applicationPosition`  | string    | 否   | 应聘岗位（出现在简历头部）                                             |
| `targetRole`           | string    | 否   | 目标职位（用于 LLM 理解求职方向）                                      |
| `targetIndustry`       | string    | 否   | 目标行业                                                               |
| `ranking`              | string    | 否   | 成绩排名（如 "前10%"）                                                 |
| `courses`              | string    | 否   | 主修课程，逗号或换行分隔，上限 5000 字                                 |
| `skillsText`           | string    | 否   | 技能清单，换行分隔，上限 5000 字                                       |
| `honorsText`           | string    | 否   | 荣誉奖项，换行分隔，上限 5000 字                                       |
| `interests`            | string    | 否   | 兴趣爱好，逗号分隔，上限 2000 字                                       |
| `selfIntroduction`     | string    | 否   | 自我介绍 / 自我评价，上限 10000 字                                     |
| `templateId`           | string    | 否   | 模板 ID（见[接口 3](#3-模板列表)）。为空或找不到时，自动使用第一个模板 |
| `enableRag`            | bool      | 否   | 是否启用知识库检索增强，默认 `true`                                    |
| `retrievalTopK`        | int\|null | 否   | 检索返回的参考片段数量，范围 1-100，`null` 表示使用知识库默认值        |
| `wordCount`            | int       | 否   | 简历正文目标字数，默认 800，范围 300-2000                              |
| `educationExperiences` | array     | 否   | 教育经历列表                                                           |
| `workExperiences`      | array     | 否   | 工作/实习经历列表                                                      |
| `projectExperiences`   | array     | 否   | 项目经历列表                                                           |

> **提示**：所有字段均为可选，但至少应提供 `name` 和部分经历信息，否则生成的简历内容会很空泛。

**响应** `200 OK`

```json
{
  "resumeData": {
    "personalInfo": {
      "name": "张三",
      "gender": "男",
      "phone": "13800138000",
      "email": "zhangsan@example.com",
      "university": "某某大学",
      "politicalStatus": "共青团员",
      "website": "",
      "avatar": "",
      "major": "计算机科学与技术",
      "applicationPosition": "Java后端开发",
      "age": "22"
    },
    "education": [
      {
        "id": 1,
        "school": "某某大学",
        "degree": "本科",
        "major": "计算机科学与技术",
        "startDate": "2021-09",
        "endDate": "2025-06"
      }
    ],
    "workExperience": [
      {
        "id": 100,
        "company": "某科技公司",
        "position": "后端实习生",
        "startDate": "2024-07",
        "endDate": "2024-09",
        "description": "- 负责后端接口开发\n- 参与数据库优化"
      }
    ],
    "skills": [
      { "id": 300, "skillName": "Java" },
      { "id": 301, "skillName": "Spring Boot" }
    ],
    "projects": [
      {
        "id": 200,
        "projectName": "校园二手交易平台",
        "role": "后端负责人",
        "startDate": "2023-03",
        "endDate": "2023-06",
        "briefIntroduction": "基于Spring Boot的校园二手交易系统",
        "description": "- 负责后端架构设计与核心模块开发\n- 实现用户认证、商品管理、订单系统"
      }
    ],
    "honors": [
      { "id": 400, "honorName": "国家奖学金", "date": "", "description": "" }
    ],
    "summary": "该同学面向后端开发工程师进行求职……"
  },
  "meta": {
    "provider": "llm",
    "templateId": "tech-rag",
    "templateName": "技术研发版",
    "knowledgeHits": [
      {
        "documentId": "doc-tech-project",
        "documentName": "技术项目描述参考",
        "category": "技术岗位",
        "score": 0.8521
      }
    ]
  }
}
```

**响应字段说明**

| 字段                        | 类型   | 说明                                                                      |
| --------------------------- | ------ | ------------------------------------------------------------------------- |
| `resumeData`                | object | 结构化简历数据，可直接传给[导出接口](#5-导出简历为-word)生成 Word         |
| `resumeData.personalInfo`   | object | 个人信息                                                                  |
| `resumeData.education`      | array  | 教育经历，按原始顺序                                                      |
| `resumeData.workExperience` | array  | 工作/实习经历                                                             |
| `resumeData.skills`         | array  | 技能列表                                                                  |
| `resumeData.projects`       | array  | 项目经历                                                                  |
| `resumeData.honors`         | array  | 荣誉奖项                                                                  |
| `resumeData.summary`        | string | 个人总结 / 自我评价（LLM 生成）                                           |
| `meta.provider`             | string | `"llm"` — LLM 生成；`"local-fallback"` — LLM 不可用，使用本地规则降级生成 |
| `meta.templateId`           | string | 实际使用的模板 ID                                                         |
| `meta.templateName`         | string | 实际使用的模板名称                                                        |
| `meta.knowledgeHits`        | array  | RAG 检索命中的知识库文档（`enableRag=false` 时为空数组）                  |

**错误响应**

| 状态码 | 场景                           |
| ------ | ------------------------------ |
| `400`  | 没有可用的模板（模板数据为空） |
| `500`  | 服务内部错误                   |

> **降级机制**：当 LLM 超时（55 秒）或调用失败时，系统不会报错，而是自动降级到本地规则生成简历。通过 `meta.provider` 字段可以判断实际使用了哪种方式。前端可以根据此字段决定是否提示用户"AI 生成暂不可用"。

---

## 5. 导出简历为 Word

### `POST /api/export-resume/docx`

将结构化简历数据导出为 `.docx` 文件。请求体就是[接口 4](#4-生成简历)返回的 `resumeData` 部分。

**请求体** `application/json`

直接传接口 4 响应中的 `resumeData` 对象（完整结构见接口 4 的响应示例）。

**响应** `200 OK`

- `Content-Type`: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- `Content-Disposition`: `attachment; filename="resume.docx"`
- 响应体为 Word 文件的二进制流

**错误响应**

| 状态码 | 场景                                    |
| ------ | --------------------------------------- |
| `500`  | Word 文件生成失败（通常是数据格式异常） |

**前端调用示例**

```javascript
const response = await fetch('/api/export-resume/docx', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(resumeData)  // 接口4返回的 resumeData
});

if (!response.ok) {
  throw new Error('导出失败');
}

const blob = await response.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'resume.docx';
a.click();
URL.revokeObjectURL(url);  // 释放内存
```

---

## 6. 知识库管理

知识库用于 RAG（检索增强生成）——在生成简历时，系统会从知识库中检索相关内容作为参考，让 LLM 生成更专业的简历。

### 6.1 获取知识库配置

#### `GET /api/knowledge-base/config`

**响应** `200 OK`

```json
{
  "chunkSize": 180,
  "chunkOverlap": 30,
  "retrievalTopK": 3,
  "matchAlgorithm": "token-overlap",
  "embeddingProvider": "local"
}
```

| 字段                | 类型   | 说明                                                                                                        |
| ------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| `chunkSize`         | int    | 文本分块大小（字符数），范围 50-2000                                                                        |
| `chunkOverlap`      | int    | 分块重叠字符数，范围 0-500                                                                                  |
| `retrievalTopK`     | int    | 检索返回的最大结果数，范围 1-100                                                                            |
| `matchAlgorithm`    | string | `"token-overlap"` — 关键词匹配（速度快）；`"vector-cosine"` — 向量语义匹配（更智能，需加载 embedding 模型） |
| `embeddingProvider` | string | 向量嵌入提供方，目前仅支持 `"local"`（使用 `BAAI/bge-small-zh-v1.5` 模型）                                  |

### 6.2 更新知识库配置

#### `PUT /api/knowledge-base/config`

**请求体**：与上面的响应结构相同，所有字段必填。

```json
{
  "chunkSize": 200,
  "chunkOverlap": 50,
  "retrievalTopK": 5,
  "matchAlgorithm": "token-overlap",
  "embeddingProvider": "local"
}
```

**响应** `200 OK`：返回更新后的完整配置。

### 6.3 获取文档列表

#### `GET /api/knowledge-base/documents`

返回知识库中的所有文档。

**响应** `200 OK`

```json
[
  {
    "id": "doc-campus-format",
    "name": "校招简历通用规范",
    "category": "写作规范",
    "content": "校招简历建议采用一页结构……",
    "createdAt": "2026-05-17T00:00:00.000Z"
  }
]
```

| 字段        | 类型   | 说明                    |
| ----------- | ------ | ----------------------- |
| `id`        | string | 文档 ID（系统自动生成） |
| `name`      | string | 文档名称                |
| `category`  | string | 分类标签                |
| `content`   | string | 文档正文内容            |
| `createdAt` | string | 创建时间（ISO 8601）    |

### 6.4 创建文档

#### `POST /api/knowledge-base/documents`

手动创建一篇知识库文档。

**请求体**

```json
{
  "name": "后端开发面经",
  "category": "技术岗",
  "content": "Java后端开发需要掌握Spring Boot、MySQL、Redis等技术栈。"
}
```

| 字段       | 类型   | 必填 | 说明                              |
| ---------- | ------ | ---- | --------------------------------- |
| `name`     | string | 是   | 文档名称，1-200 字符              |
| `category` | string | 否   | 分类标签，最多 100 字符，默认为空 |
| `content`  | string | 是   | 文档正文，1-500,000 字符          |

**响应** `201 Created`：返回创建的文档对象（含 `id` 和 `createdAt`）。

### 6.5 上传文件到知识库

#### `POST /api/knowledge-base/documents/upload`

上传一个文件，系统自动提取文本内容并存入知识库。

**请求体** `multipart/form-data`

| 字段   | 类型 | 说明         |
| ------ | ---- | ------------ |
| `file` | file | 要上传的文件 |

**支持的文件格式**：`.docx`、`.pdf`、`.txt`、`.md`

**文件大小限制**：最大 20MB

**响应** `201 Created`：返回创建的文档对象。文件名（去掉扩展名）作为文档名称，分类自动设为 `"文件上传"`。

**错误响应**

| 状态码 | 场景                                                 |
| ------ | ---------------------------------------------------- |
| `400`  | 缺少文件名                                           |
| `400`  | 文件内容为空                                         |
| `400`  | 文件大小超过 20MB 限制                               |
| `400`  | 不支持的文件格式（仅支持 .docx / .pdf / .txt / .md） |
| `400`  | 未能从文件中提取到文本内容                           |
| `500`  | 文件解析失败                                         |

### 6.6 删除文档

#### `DELETE /api/knowledge-base/documents/{document_id}`

**路径参数**

| 参数          | 类型   | 说明            |
| ------------- | ------ | --------------- |
| `document_id` | string | 要删除的文档 ID |

**响应** `200 OK`

```json
{ "removed": true }
```

**错误响应**

| 状态码 | 场景       |
| ------ | ---------- |
| `404`  | 文档不存在 |

---

## 7. AI 对话

### `POST /api/chat`

与 LLM 进行流式对话。返回 SSE（Server-Sent Events）流，适用于实时打字机效果展示。

> **安全说明**：API Key 由后端统一管理，前端不需要也不应该传递任何密钥。

**请求体** `application/json`

```json
{
  "messages": [
    { "role": "system", "content": "你是一个简历助手" },
    { "role": "user", "content": "帮我优化这段项目描述" }
  ],
  "stream": true
}
```

| 字段                 | 类型   | 必填 | 说明                                                                    |
| -------------------- | ------ | ---- | ----------------------------------------------------------------------- |
| `messages`           | array  | 是   | 对话消息列表，至少 1 条                                                 |
| `messages[].role`    | string | 是   | `"system"`（系统设定）、`"user"`（用户输入）或 `"assistant"`（AI 回复） |
| `messages[].content` | string | 是   | 消息内容                                                                |
| `stream`             | bool   | 否   | 是否流式返回，默认 `true`。设为 `false` 时等待完整响应后一次性返回      |

**响应** `200 OK`

- `Content-Type`: `text/event-stream`
- 流式返回 SSE 事件：

```
data: 你好
data: ，我可以
data: 帮你
data: 优化
data: 项目描述。
data: [DONE]
```

每个 `data:` 行是一段增量文本。`data: [DONE]` 表示生成结束。

> **前端处理建议**：使用 `EventSource` 或 `fetch` + `ReadableStream` 读取流式响应。收到 `data: [DONE]` 时关闭连接。注意 SSE 数据中的换行会被转义为 `\ndata:` 前缀，需要拼接还原。

**错误响应**

| 状态码 | 场景                                                                      |
| ------ | ------------------------------------------------------------------------- |
| `400`  | 请求格式错误（如 `messages` 为空）                                        |
| `401`  | API Key 无效或已过期                                                      |
| `502`  | 后端未配置 LLM（缺少 `LLM_API_URL` / `LLM_API_KEY`），或上游 API 返回错误 |
| `502`  | 无法连接到上游 LLM API（网络问题或地址错误）                              |
| `504`  | 连接上游 LLM API 超时（120 秒）                                           |

---

## 8. 环境变量

| 变量               | 别名                        | 默认值                                        | 说明                                            |
| ------------------ | --------------------------- | --------------------------------------------- | ----------------------------------------------- |
| `LLM_API_URL`      | `OPENAI_COMPATIBLE_API_URL` | 空（不填则无法使用 LLM）                      | LLM API 端点地址                                |
| `LLM_API_KEY`      | `OPENAI_API_KEY`            | 空                                            | LLM API 密钥                                    |
| `LLM_MODEL`        | `OPENAI_MODEL`              | `qwen-plus`                                   | 模型名称                                        |
| `PORT`             | —                           | `8000`                                        | 服务端口                                        |
| `HOST`             | —                           | `127.0.0.1`                                   | 服务监听地址                                    |
| `CORS_ORIGINS`     | —                           | `http://localhost:5173,http://127.0.0.1:5173` | 允许的跨域来源，逗号分隔                        |
| `CHAT_TEMPERATURE` | —                           | `0.7`                                         | Chat 接口的 LLM 温度参数（0.0-2.0，越高越随机） |

> **关于别名**：每个变量同时支持主名称和别名，优先使用主名称。例如设置 `LLM_API_URL` 或 `OPENAI_COMPATIBLE_API_URL` 效果相同，方便从 OpenAI SDK 项目迁移。

**配置示例**

DeepSeek：

```bash
LLM_API_URL=https://api.deepseek.com/chat/completions
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=deepseek-chat
```

通义千问：

```bash
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=qwen-plus
```

本地 Ollama（无需密钥）：

```bash
LLM_API_URL=http://localhost:11434/v1/chat/completions
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
```
