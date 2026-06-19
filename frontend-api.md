# 前端 API 接口文档

> 📋 **文档用途**：本文档定义了前端应用与后端服务之间的 API 接口规范，供前端开发、后端开发和测试人员参考。
>
> **最后更新**：2026-06-18

---

## 目录

- [基础信息](#基础信息)
- [1. 健康检查](#1-健康检查)
- [2. AI 对话（流式响应）](#2-ai-对话流式响应)
- [3. Prompt 模板管理](#3-prompt-模板管理)
- [4. 知识库管理](#4-知识库管理)
- [5. 简历生成](#5-简历生成)
- [6. 简历导出](#6-简历导出)
- [附录：接口总览表](#附录接口总览表)

---

## 基础信息

### API 基础路径

```
开发环境：http://localhost:5173/api（通过 Vite 代理转发到后端）
生产环境：由部署配置决定
```

### 通用说明

- **数据格式**：所有接口使用 JSON 格式传输数据
- **超时设置**：请求超时时间为 60 秒
- **字符编码**：UTF-8
- **Content-Type**：`application/json`（文件上传除外）

### 错误处理

当请求失败时，后端会返回相应的 HTTP 状态码：

| 状态码 | 含义           | 常见原因                     |
| ------ | -------------- | ---------------------------- |
| 400    | 请求参数错误   | 请求体格式错误或缺少必填字段 |
| 401    | 认证失败       | API Key 无效或未配置         |
| 404    | 资源不存在     | 接口路径错误或资源已被删除   |
| 500    | 服务器内部错误 | 后端服务异常                 |

---

## 1. 健康检查

### 接口说明

用于检查后端服务是否正常运行。前端可以在应用启动时调用此接口，确认后端服务可用。

### 请求

```
GET /api/health
```

**无需请求参数**

### 响应

```json
{
  "ok": true,
  "now": "2026-06-14T21:00:00Z",
  "provider": "dashscope"
}
```

### 响应字段说明

| 字段       | 类型    | 说明                            |
| ---------- | ------- | ------------------------------- |
| `ok`       | boolean | 服务状态，`true` 表示正常       |
| `now`      | string  | 当前服务器时间（ISO 8601 格式） |
| `provider` | string  | 当前使用的 AI 服务提供商        |

### 使用场景

- 应用启动时检测后端服务状态
- 网络异常时诊断连接问题
- 监控系统定期健康检查

---

## 2. AI 对话（流式响应）

### 接口说明

与 AI 进行对话交流。采用 **SSE（Server-Sent Events）** 技术实现流式响应，让用户可以实时看到 AI 生成的内容，提升用户体验。

> ⚡ **流式响应**：数据会分块传输，前端可以逐步显示内容，而不是等待整个响应完成。

### 请求

```
POST /api/chat
Content-Type: application/json
```

### 请求体

```json
{
  "messages": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮你的吗？"
    },
    {
      "role": "user",
      "content": "帮我写一份简历"
    }
  ],
  "stream": true
}
```

### 请求字段说明

| 字段                 | 类型    | 必填 | 说明                                             |
| -------------------- | ------- | ---- | ------------------------------------------------ |
| `messages`           | array   | ✅    | 对话历史记录数组                                 |
| `messages[].role`    | string  | ✅    | 消息角色：`"user"`（用户）或 `"assistant"`（AI） |
| `messages[].content` | string  | ✅    | 消息内容                                         |
| `stream`             | boolean | ✅    | 是否启用流式响应，固定为 `true`                  |

### 响应格式

响应为 **SSE 流**，格式如下：

```
data: 你好
data: ，我来
data: 帮你
data: 写一份
data: 简历
data: [DONE]
```

### 响应处理说明

1. **逐行读取**：每一行以 `data:` 开缀
2. **拼接内容**：将 `data:` 后面的文本拼接起来，形成完整的 AI 回复
3. **结束标志**：收到 `data: [DONE]` 表示响应结束
4. **错误处理**：如果响应为空或格式错误，应显示友好提示

### 前端实现参考

前端通过 Web Worker（`aiWorker.ts`）处理 SSE 流：

```typescript
// 简化示例
const reader = response.body.getReader();
const decoder = new TextDecoder();
let currentText = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  // 解码并按行分割
  const text = decoder.decode(value, { stream: true });
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6).trim();
      if (data === '[DONE]') {
        // 流结束
        return currentText;
      }
      currentText += data;
      // 更新 UI 显示
      onUpdate(currentText);
    }
  }
}
```

### 使用场景

- AI 智能体工作台的对话功能
- AI 深度对话页面
- 任何需要与 AI 交互的场景

---

## 3. Prompt 模板管理

### 接口说明

获取系统预设的 Prompt 模板列表。这些模板用于指导 AI 生成特定风格的简历内容。

### 请求

```
GET /api/prompt-templates
```

**无需请求参数**

### 响应

```json
[
  {
    "id": "template_001",
    "name": "简约风格",
    "style": "简洁明了",
    "targetAudience": "应届毕业生",
    "description": "适合初次求职的毕业生，突出教育背景和实习经历",
    "systemPrompt": "你是一位专业的简历顾问，请根据以下信息生成一份简约风格的简历..."
  },
  {
    "id": "template_002",
    "name": "商务风格",
    "style": "专业正式",
    "targetAudience": "职场人士",
    "description": "适合有工作经验的求职者，突出工作成就和专业技能",
    "systemPrompt": "你是一位专业的简历顾问，请根据以下信息生成一份商务风格的简历..."
  }
]
```

### 响应字段说明

| 字段             | 类型   | 说明                       |
| ---------------- | ------ | -------------------------- |
| `id`             | string | 模板唯一标识符             |
| `name`           | string | 模板名称（用户可见）       |
| `style`          | string | 模板风格描述               |
| `targetAudience` | string | 目标用户群体               |
| `description`    | string | 模板详细描述               |
| `systemPrompt`   | string | 系统提示词（用于 AI 生成） |

### 使用场景

- 简历生成页面的模板选择
- AI 智能体工作台的模板配置
- 模板市场展示

---

## 4. 知识库管理

知识库用于存储用户上传的参考资料，AI 在生成简历时可以参考这些资料，提升生成质量（RAG 功能）。

### 4.1 获取知识库配置

获取当前知识库的配置参数，如分块大小、检索数量等。

#### 请求

```
GET /api/knowledge-base/config
```

#### 响应

```json
{
  "chunkSize": 500,
  "chunkOverlap": 50,
  "retrievalTopK": 3,
  "matchAlgorithm": "cosine",
  "embeddingProvider": "dashscope"
}
```

#### 响应字段说明

| 字段                | 类型   | 说明                            |
| ------------------- | ------ | ------------------------------- |
| `chunkSize`         | number | 文本分块大小（字符数）          |
| `chunkOverlap`      | number | 分块重叠长度（字符数）          |
| `retrievalTopK`     | number | 检索返回的最相关文档数量        |
| `matchAlgorithm`    | string | 相似度匹配算法（如 `"cosine"`） |
| `embeddingProvider` | string | 向量化服务提供商                |

---

### 4.2 更新知识库配置

修改知识库的配置参数。修改后可能需要重新构建索引。

#### 请求

```
PUT /api/knowledge-base/config
Content-Type: application/json
```

#### 请求体

```json
{
  "chunkSize": 600,
  "chunkOverlap": 100,
  "retrievalTopK": 5,
  "matchAlgorithm": "cosine",
  "embeddingProvider": "dashscope"
}
```

> 📝 **注意**：所有字段均为必填，需要提供完整的配置对象。

#### 响应

返回更新后的完整配置对象（同 4.1 响应格式）。

---

### 4.3 获取文档列表

获取知识库中所有已上传的文档。

#### 请求

```
GET /api/knowledge-base/documents
```

#### 响应

```json
[
  {
    "id": "doc_001",
    "name": "前端岗位描述.txt",
    "category": "job",
    "content": "负责公司前端项目开发...",
    "createdAt": "2026-06-14T21:00:00Z"
  },
  {
    "id": "doc_002",
    "name": "优秀简历模板.pdf",
    "category": "template",
    "content": "姓名：张三...",
    "createdAt": "2026-06-15T10:30:00Z"
  }
]
```

#### 响应字段说明

| 字段        | 类型   | 说明                                 |
| ----------- | ------ | ------------------------------------ |
| `id`        | string | 文档唯一标识符                       |
| `name`      | string | 文档名称                             |
| `category`  | string | 文档分类（如 `"job"`、`"template"`） |
| `content`   | string | 文档内容（文本形式）                 |
| `createdAt` | string | 创建时间（ISO 8601 格式）            |

---

### 4.4 创建文档

通过文本内容创建新的知识库文档。

#### 请求

```
POST /api/knowledge-base/documents
Content-Type: application/json
```

#### 请求体

```json
{
  "name": "前端岗位描述",
  "category": "job",
  "content": "负责公司前端项目开发，要求熟悉 Vue、React 等框架..."
}
```

#### 请求字段说明

| 字段       | 类型   | 必填 | 说明     |
| ---------- | ------ | ---- | -------- |
| `name`     | string | ✅    | 文档名称 |
| `category` | string | ✅    | 文档分类 |
| `content`  | string | ✅    | 文档内容 |

#### 响应

返回创建成功的文档对象（包含 `id` 和 `createdAt`）。

---

### 4.5 上传文档（文件）

通过文件上传创建知识库文档。

#### 请求

```
POST /api/knowledge-base/documents/upload
Content-Type: multipart/form-data
```

#### 请求体

- `file`：要上传的文件（单个文件）

#### 响应

返回创建成功的文档对象（同 4.4 响应格式）。

#### 使用示例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/knowledge-base/documents/upload', {
  method: 'POST',
  body: formData
});
```

---

### 4.6 删除文档

从知识库中删除指定文档。

#### 请求

```
DELETE /api/knowledge-base/documents/{documentId}
```

#### 路径参数

| 参数         | 类型   | 说明            |
| ------------ | ------ | --------------- |
| `documentId` | string | 要删除的文档 ID |

#### 响应

```json
{
  "removed": true
}
```

#### 响应字段说明

| 字段      | 类型    | 说明                      |
| --------- | ------- | ------------------------- |
| `removed` | boolean | 删除状态，`true` 表示成功 |

---

## 5. 简历生成

### 接口说明

根据用户填写的信息和选择的模板，调用 AI 生成结构化的简历内容。支持 RAG（检索增强生成）功能，可以参考知识库中的资料。

### 请求

```
POST /api/generate-resume
Content-Type: application/json
```

### 请求体

```json
{
  "name": "张三",
  "gender": "男",
  "age": "22",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "website": "https://github.com/zhangsan",
  "school": "深圳技术大学",
  "major": "计算机科学与技术",
  "degree": "本科",
  "politicalStatus": "共青团员",
  "applicationPosition": "前端开发工程师",
  "targetRole": "前端工程师",
  "targetIndustry": "互联网",
  "ranking": "前10%",
  "courses": "数据结构、操作系统、计算机网络",
  "skillsText": "Vue3、TypeScript、React、Node.js",
  "honorsText": "校级奖学金、ACM 竞赛银奖",
  "interests": "编程、阅读、篮球",
  "selfIntroduction": "热爱技术，有较强的学习能力和团队合作精神...",
  "templateId": "templateA",
  "enableRag": true,
  "retrievalTopK": 3,
  "wordCount": 500,
  "educationExperiences": [
    {
      "school": "深圳技术大学",
      "degree": "本科",
      "major": "计算机科学与技术",
      "startDate": "2022-09",
      "endDate": "2026-06"
    }
  ],
  "workExperiences": [
    {
      "company": "某科技有限公司",
      "position": "前端开发实习生",
      "startDate": "2025-07",
      "endDate": "2025-09",
      "description": "负责公司内部管理系统的前端开发..."
    }
  ],
  "projectExperiences": [
    {
      "projectName": "在线简历生成器",
      "role": "前端开发",
      "startDate": "2025-03",
      "endDate": "2025-06",
      "briefIntroduction": "基于 Vue3 的在线简历生成工具",
      "description": "使用 Vue3 + TypeScript 开发，支持多种模板选择和实时预览..."
    }
  ]
}
```

### 请求字段说明

#### 基本信息

| 字段              | 类型   | 必填 | 说明                          |
| ----------------- | ------ | ---- | ----------------------------- |
| `name`            | string | ✅    | 姓名                          |
| `gender`          | string | ✅    | 性别                          |
| `age`             | string | ✅    | 年龄                          |
| `phone`           | string | ✅    | 手机号码                      |
| `email`           | string | ✅    | 电子邮箱                      |
| `website`         | string | ❌    | 个人网站/GitHub               |
| `school`          | string | ✅    | 学校名称                      |
| `major`           | string | ✅    | 专业                          |
| `degree`          | string | ✅    | 学历（如 `"本科"`、`"硕士"`） |
| `politicalStatus` | string | ❌    | 政治面貌                      |

#### 求职意向

| 字段                  | 类型   | 必填 | 说明     |
| --------------------- | ------ | ---- | -------- |
| `applicationPosition` | string | ✅    | 申请职位 |
| `targetRole`          | string | ❌    | 目标角色 |
| `targetIndustry`      | string | ❌    | 目标行业 |

#### 学业信息

| 字段               | 类型   | 必填 | 说明                     |
| ------------------ | ------ | ---- | ------------------------ |
| `ranking`          | string | ❌    | 成绩排名（如 `"前10%"`） |
| `courses`          | string | ❌    | 相关课程                 |
| `skillsText`       | string | ❌    | 技能描述（文本形式）     |
| `honorsText`       | string | ❌    | 荣誉奖项（文本形式）     |
| `interests`        | string | ❌    | 兴趣爱好                 |
| `selfIntroduction` | string | ❌    | 自我介绍                 |

#### AI 生成配置

| 字段            | 类型    | 必填 | 说明                            |
| --------------- | ------- | ---- | ------------------------------- |
| `templateId`    | string  | ✅    | 选择的模板 ID                   |
| `enableRag`     | boolean | ❌    | 是否启用 RAG 功能，默认 `false` |
| `retrievalTopK` | number  | ❌    | RAG 检索的文档数量，默认 `3`    |
| `wordCount`     | number  | ❌    | 期望的简历字数                  |

#### 教育经历

| 字段                               | 类型   | 必填 | 说明                        |
| ---------------------------------- | ------ | ---- | --------------------------- |
| `educationExperiences`             | array  | ✅    | 教育经历数组                |
| `educationExperiences[].school`    | string | ✅    | 学校名称                    |
| `educationExperiences[].degree`    | string | ✅    | 学历                        |
| `educationExperiences[].major`     | string | ✅    | 专业                        |
| `educationExperiences[].startDate` | string | ✅    | 开始时间（格式：`YYYY-MM`） |
| `educationExperiences[].endDate`   | string | ✅    | 结束时间（格式：`YYYY-MM`） |

#### 工作经历

| 字段                            | 类型   | 必填 | 说明         |
| ------------------------------- | ------ | ---- | ------------ |
| `workExperiences`               | array  | ❌    | 工作经历数组 |
| `workExperiences[].company`     | string | ✅    | 公司名称     |
| `workExperiences[].position`    | string | ✅    | 职位         |
| `workExperiences[].startDate`   | string | ✅    | 开始时间     |
| `workExperiences[].endDate`     | string | ✅    | 结束时间     |
| `workExperiences[].description` | string | ✅    | 工作描述     |

#### 项目经历

| 字段                                     | 类型   | 必填 | 说明         |
| ---------------------------------------- | ------ | ---- | ------------ |
| `projectExperiences`                     | array  | ❌    | 项目经历数组 |
| `projectExperiences[].projectName`       | string | ✅    | 项目名称     |
| `projectExperiences[].role`              | string | ✅    | 担任角色     |
| `projectExperiences[].startDate`         | string | ✅    | 开始时间     |
| `projectExperiences[].endDate`           | string | ✅    | 结束时间     |
| `projectExperiences[].briefIntroduction` | string | ✅    | 项目简介     |
| `projectExperiences[].description`       | string | ✅    | 项目详细描述 |

### 响应

```json
{
  "resumeData": {
    "personalInfo": {
      "name": "张三",
      "gender": "男",
      "phone": "13800138000",
      "email": "zhangsan@example.com",
      "university": "深圳技术大学",
      "politicalStatus": "共青团员",
      "website": "https://github.com/zhangsan",
      "avatar": "",
      "major": "计算机科学与技术",
      "applicationPosition": "前端开发工程师",
      "age": "22"
    },
    "education": [
      {
        "id": 1,
        "school": "深圳技术大学",
        "degree": "本科",
        "major": "计算机科学与技术",
        "startDate": "2022-09",
        "endDate": "2026-06"
      }
    ],
    "workExperience": [
      {
        "id": 1,
        "company": "某科技有限公司",
        "position": "前端开发实习生",
        "startDate": "2025-07",
        "endDate": "2025-09",
        "description": "负责公司内部管理系统的前端开发..."
      }
    ],
    "skills": [
      {
        "id": 1,
        "skillName": "Vue3"
      },
      {
        "id": 2,
        "skillName": "TypeScript"
      }
    ],
    "projects": [
      {
        "id": 1,
        "projectName": "在线简历生成器",
        "role": "前端开发",
        "startDate": "2025-03",
        "endDate": "2025-06",
        "briefIntroduction": "基于 Vue3 的在线简历生成工具",
        "description": "使用 Vue3 + TypeScript 开发..."
      }
    ],
    "honors": [
      {
        "id": 1,
        "honorName": "校级奖学金",
        "date": "2024-10",
        "description": ""
      }
    ],
    "summary": "热爱技术，有较强的学习能力和团队合作精神..."
  },
  "meta": {
    "provider": "dashscope",
    "templateId": "templateA",
    "templateName": "简约风格",
    "knowledgeHits": [
      {
        "documentId": "doc_001",
        "documentName": "前端岗位描述",
        "category": "job",
        "score": 0.85
      }
    ]
  }
}
```

### 响应字段说明

#### resumeData（简历数据）

| 字段             | 类型   | 说明              |
| ---------------- | ------ | ----------------- |
| `personalInfo`   | object | 个人信息          |
| `education`      | array  | 教育经历列表      |
| `workExperience` | array  | 工作经历列表      |
| `skills`         | array  | 技能列表          |
| `projects`       | array  | 项目经历列表      |
| `honors`         | array  | 荣誉奖项列表      |
| `summary`        | string | AI 生成的个人总结 |

#### meta（元数据）

| 字段                           | 类型   | 说明                 |
| ------------------------------ | ------ | -------------------- |
| `provider`                     | string | AI 服务提供商        |
| `templateId`                   | string | 使用的模板 ID        |
| `templateName`                 | string | 模板名称             |
| `knowledgeHits`                | array  | RAG 检索到的相关文档 |
| `knowledgeHits[].documentId`   | string | 文档 ID              |
| `knowledgeHits[].documentName` | string | 文档名称             |
| `knowledgeHits[].category`     | string | 文档分类             |
| `knowledgeHits[].score`        | number | 相似度分数（0-1）    |

### 使用场景

- Agent 页面的简历生成功能
- 批量简历生成
- 简历内容优化

---

## 6. 简历导出

### 接口说明

将生成的简历数据导出为 Word 文档（.docx 格式）。

### 请求

```
POST /api/export-resume/docx
Content-Type: application/json
```

### 请求体

请求体为 `resumeData` 对象（即简历生成接口响应中的 `resumeData` 部分）。

```json
{
  "personalInfo": {
    "name": "张三",
    "gender": "男",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "university": "深圳技术大学",
    "politicalStatus": "共青团员",
    "website": "",
    "avatar": "",
    "major": "计算机科学与技术",
    "applicationPosition": "前端开发工程师",
    "age": "22"
  },
  "education": [...],
  "workExperience": [...],
  "skills": [...],
  "projects": [...],
  "honors": [...],
  "summary": "..."
}
```

### 响应

- **响应类型**：`Blob`（二进制文件流）
- **Content-Type**：`application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **文件名**：由后端设置，或前端通过 `<a download>` 指定

### 前端使用示例

```javascript
async function downloadDocx(resumeData) {
  const response = await fetch('/api/export-resume/docx', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resumeData)
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${resumeData.personalInfo.name}_简历.docx`;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

### 使用场景

- 简历预览页面的下载功能
- 批量导出简历
- 简历分享

---

## 附录：接口总览表

| 方法     | 路径                                   | 用途             | 请求体   | 响应类型  |
| -------- | -------------------------------------- | ---------------- | -------- | --------- |
| `GET`    | `/api/health`                          | 健康检查         | 无       | JSON      |
| `POST`   | `/api/chat`                            | AI 对话（流式）  | JSON     | SSE 流    |
| `GET`    | `/api/prompt-templates`                | 获取 Prompt 模板 | 无       | JSON 数组 |
| `GET`    | `/api/knowledge-base/config`           | 获取知识库配置   | 无       | JSON      |
| `PUT`    | `/api/knowledge-base/config`           | 更新知识库配置   | JSON     | JSON      |
| `GET`    | `/api/knowledge-base/documents`        | 获取文档列表     | 无       | JSON 数组 |
| `POST`   | `/api/knowledge-base/documents`        | 创建文档         | JSON     | JSON      |
| `POST`   | `/api/knowledge-base/documents/upload` | 上传文档         | FormData | JSON      |
| `DELETE` | `/api/knowledge-base/documents/{id}`   | 删除文档         | 无       | JSON      |
| `POST`   | `/api/generate-resume`                 | AI 生成简历      | JSON     | JSON      |
| `POST`   | `/api/export-resume/docx`              | 导出 Word 文件   | JSON     | Blob      |

---

## 附录：TypeScript 类型定义

以下是前端使用的 TypeScript 接口定义，可供后端开发参考：

```typescript
// Prompt 模板
interface PromptTemplate {
  id: string;
  name: string;
  style: string;
  targetAudience: string;
  description: string;
  systemPrompt: string;
}

// 知识库配置
interface KnowledgeBaseConfig {
  chunkSize: number;
  chunkOverlap: number;
  retrievalTopK: number;
  matchAlgorithm: string;
  embeddingProvider: string;
}

// 知识库文档
interface KnowledgeDocument {
  id: string;
  name: string;
  category: string;
  content: string;
  createdAt: string;
}

// 简历生成请求
interface ResumeGenerateRequest {
  name: string;
  gender: string;
  age: string;
  phone: string;
  email: string;
  website: string;
  school: string;
  major: string;
  degree: string;
  politicalStatus: string;
  applicationPosition: string;
  targetRole: string;
  targetIndustry: string;
  ranking: string;
  courses: string;
  skillsText: string;
  honorsText: string;
  interests: string;
  selfIntroduction: string;
  templateId: string;
  enableRag: boolean;
  retrievalTopK?: number;
  wordCount?: number;
  educationExperiences: StudentEducationInput[];
  workExperiences: StudentWorkInput[];
  projectExperiences: StudentProjectInput[];
}

// 简历生成响应
interface GeneratedResumeResponse {
  resumeData: GeneratedResumeData;
  meta: {
    provider: string;
    templateId: string;
    templateName: string;
    knowledgeHits: Array<{
      documentId: string;
      documentName: string;
      category: string;
      score: number;
    }>;
  };
}
```

---

## 附录：常见问题

### Q1: 为什么 AI 对话接口使用 SSE 而不是 WebSocket？

**A**: SSE（Server-Sent Events）是单向通信，适合服务器向客户端推送数据的场景。AI 对话只需要服务器向客户端推送生成的内容，不需要双向通信，因此 SSE 更简单、更高效。

### Q2: RAG 功能是什么？

**A**: RAG（Retrieval-Augmented Generation，检索增强生成）是一种技术，通过检索知识库中的相关文档作为上下文，帮助 AI 生成更准确、更个性化的内容。启用 RAG 后，AI 会参考用户上传的资料来生成简历。

### Q3: 如何处理网络异常？

**A**: 建议在前端实现以下错误处理：

1. 请求超时：显示"网络请求超时，请稍后重试"
2. 网络断开：显示"网络连接已断开，请检查网络设置"
3. 服务器错误：显示"服务器异常，请联系管理员"

### Q4: 文件上传有什么限制？

**A**: 文件上传的限制取决于后端配置，通常包括：

- 文件大小限制（如 10MB）
- 文件类型限制（如 .txt, .pdf, .doc, .docx）
- 同时上传文件数量限制

---

> 📝 **文档维护说明**
>
> 本文档应与后端 API 保持同步更新。如有接口变更，请及时更新本文档。
>
> 如有问题或建议，请联系前端开发组。
