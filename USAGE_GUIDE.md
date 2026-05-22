# AI 简历智能体 —— 使用教程

## 项目简介

基于大模型的学生个人简历撰写智能体。同学填写个人信息 → 选择简历模板 → AI 自动生成排版精美的简历 → 可预览、下载。

- **前端**：Vue 3 + Vite + TypeScript（已存在于仓库 `develop` 分支）
- **后端**：Python FastAPI（本教程重点）

---

## 目录

1. [环境准备](#1-环境准备)
2. [安装步骤](#2-安装步骤)
3. [启动服务](#3-启动服务)
4. [API 使用指南](#4-api-使用指南)
5. [接入大模型](#5-接入大模型)
6. [前后端联调](#6-前后端联调)
7. [常见问题](#7-常见问题)

---

## 1. 环境准备

| 依赖 | 版本要求 | 用途 |
|---|---|---|
| Python | 3.11+ | 后端运行 |
| Node.js | 16+ | 前端运行 |
| Git | - | 拉取代码 |

### 检查环境

```bash
# Python
python --version   # 需 >= 3.11

# Node.js
node --version     # 需 >= 16
npm --version

# Git
git --version
```

---

## 2. 安装步骤

### 2.1 拉取项目

```bash
git clone https://github.com/T34851969/Proj.git
cd Proj

# 切换到 develop 分支（前端代码在此分支）
git checkout develop
```

### 2.2 安装前端依赖

```bash
# 在项目根目录（前端目录）
npm install
```

### 2.3 安装后端依赖

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows (Git Bash / WSL)
source venv/Scripts/activate
# Linux / macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> **提示**：每次新开终端都需要重新激活虚拟环境 `source venv/Scripts/activate`

---

## 3. 启动服务

### 方式一：前后端同时启动（推荐开发用）

**终端 1 —— 启动后端：**

```bash
cd Proj/backend
source venv/Scripts/activate

# 默认端口 8000
uvicorn app.main:app --reload

# 或指定端口 3001（与前端正端代理默认配置一致）
PORT=3001 uvicorn app.main:app --reload
```

**终端 2 —— 启动前端：**

```bash
cd Proj
npm run dev
```

前端默认打开 `http://localhost:5173`，后端在 `http://localhost:8000`（或 3001）。

### 方式二：使用启动脚本

```bash
cd Proj/backend
source venv/Scripts/activate
bash run.sh
```

### 验证后端是否启动成功

```bash
# 健康检查
curl http://localhost:8000/api/health

# 预期返回
{"ok": true, "now": "2026-05-18T08:00:00", "provider": "local-fallback"}
```

访问 `http://localhost:8000/docs` 可查看交互式 API 文档（Swagger UI）。

---

## 4. API 使用指南

### 4.1 查看简历模板

```bash
curl http://localhost:8000/api/prompt-templates
```

返回 5 种模板：`简约校招版`、`商务正式版`、`创意亮点版`、`技术研发版`、`升学科研版`。

### 4.2 生成简历（核心接口）

```bash
curl -X POST http://localhost:8000/api/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "gender": "男",
    "age": "22",
    "phone": "13800138000",
    "email": "zhangsan@example.com",
    "school": "某某大学",
    "major": "计算机科学与技术",
    "degree": "本科",
    "applicationPosition": "Java后端开发",
    "targetRole": "后端开发工程师",
    "ranking": "前10%",
    "courses": "数据结构,算法设计,操作系统,计算机网络",
    "skillsText": "Java\nSpring Boot\nMySQL\nRedis\nLinux",
    "honorsText": "国家奖学金\nACM铜奖",
    "interests": "开源贡献,技术博客",
    "selfIntroduction": "热爱编程，喜欢钻研新技术",
    "templateId": "tech-rag",
    "enableRag": false,
    "educationExperiences": [
      {"school": "某某大学", "degree": "本科", "major": "计算机科学与技术", "startDate": "2021-09", "endDate": "2025-06"}
    ],
    "workExperiences": [],
    "projectExperiences": [
      {"projectName": "校园二手交易平台", "role": "后端负责人", "startDate": "2023-03", "endDate": "2023-06", "briefIntroduction": "基于Spring Boot的校园二手交易系统", "description": "负责后端架构设计与核心模块开发\n实现用户认证、商品管理、订单系统"}
    ]
  }'
```

**返回结构说明：**

```json
{
  "resumeData": {
    "personalInfo": { "name": "...", "phone": "...", "major": "..." },
    "education": [{ "school": "...", "degree": "..." }],
    "workExperience": [],
    "skills": [{ "skillName": "Java" }],
    "projects": [{ "projectName": "...", "description": "..." }],
    "honors": [{ "honorName": "国家奖学金" }],
    "summary": "张三面向后端开发工程师进行求职..."
  },
  "meta": {
    "provider": "local-fallback",
    "templateId": "tech-rag",
    "templateName": "技术研发版",
    "knowledgeHits": []
  }
}
```

### 4.3 知识库管理

```bash
# 查看配置
curl http://localhost:8000/api/knowledge-base/config

# 查看文档
curl http://localhost:8000/api/knowledge-base/documents

# 添加文档
curl -X POST http://localhost:8000/api/knowledge-base/documents \
  -H "Content-Type: application/json" \
  -d '{"name": "优秀简历范例", "category": "技术岗", "content": "项目名称：电商微服务架构重构..."}'

# 删除文档
curl -X DELETE http://localhost:8000/api/knowledge-base/documents/doc-1234567890
```

知识库开启后（`enableRag: true`），生成简历时会自动检索相关片段注入 AI 上下文。

---

## 5. 接入大模型

### 5.1 配置环境变量

在项目根目录创建 `.env` 文件，或在启动命令前设置：

```bash
# 阿里云百炼（通义千问）示例
export LLM_API_URL="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
export LLM_API_KEY="sk-xxxxxxxxxxxxxxxx"
export LLM_MODEL="qwen-plus"
```

### 5.2 Windows 设置环境变量

```bash
# Git Bash
export LLM_API_KEY="sk-xxx"
export LLM_API_URL="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# CMD
set LLM_API_KEY=sk-xxx

# PowerShell
$env:LLM_API_KEY="sk-xxx"
```

### 5.3 支持的模型

| 平台 | API URL | 模型名 |
|---|---|---|
| 阿里云百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions` | `qwen-plus`, `qwen-max` |
| DeepSeek | `https://api.deepseek.com/v1/chat/completions` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `gpt-3.5-turbo`, `gpt-4` |
| 其他 OpenAI-Compatible | 自定义 | 自定义 |

### 5.4 验证模型是否生效

```bash
curl http://localhost:8000/api/health
# 若配置了 API，返回 "provider": "llm-configured"
```

---

## 6. 前后端联调

### 6.1 端口对齐

前端 `vite.config.ts` 中的代理配置：

```ts
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:3001",  // <-- 前端代理目标
      changeOrigin: true,
    },
  },
},
```

**方案 A（推荐）：后端跑在 3001**

```bash
cd backend
PORT=3001 uvicorn app.main:app --reload
```

前端直接 `npm run dev` 即可联调。

**方案 B：后端跑在 8000，改前端代理**

修改 `vite.config.ts`：

```ts
target: "http://127.0.0.1:8000",
```

然后重启前端 `npm run dev`。

### 6.2 前端页面操作流程

1. 打开 `http://localhost:5173`
2. 点击左侧表单填写个人信息、教育背景、项目经历等
3. 选择右侧简历模板（如"技术研发版"）
4. 点击生成 → 前端调用 `POST /api/generate-resume`
5. 右侧实时预览生成的简历
6. 可导出为 PDF

### 6.3 设置页面配置模型（前端内置）

前端「设置」页面可独立配置 AI 对话用的 API，但**简历生成后端的模型**由后端环境变量控制。两者是分离的：

- **简历生成** → 后端 `LLM_API_URL` + `LLM_API_KEY`
- **AI 润色/对话** → 前端设置页面用户自行填写

---

## 7. 常见问题

### Q1: 后端启动报错 `ModuleNotFoundError: No module named 'fastapi'`

**解决**：虚拟环境未激活或未安装依赖

```bash
cd backend
source venv/Scripts/activate
pip install -r requirements.txt
```

### Q2: 前端请求后端返回 404 / 连不上

**解决**：检查端口是否对齐

```bash
# 确认后端实际运行端口
curl http://localhost:3001/api/health   # 如果后端跑在 3001
curl http://localhost:8000/api/health   # 如果后端跑在 8000

# 修改 vite.config.ts 中的 target 与后端端口一致
```

### Q3: LLM 调用失败，始终返回 `local-fallback`

**解决**：
1. 检查环境变量是否设置正确
2. 确认 API Key 有效
3. 查看后端日志中的具体错误信息
4. 某些国内模型需开启 `response_format`，已在代码中自动设置

### Q4: 中文显示乱码

**解决**：确保终端使用 UTF-8 编码

```bash
# Git Bash
chcp 65001
```

### Q5: 知识库检索没有效果

**解决**：知识库默认使用简单的 token 重叠算法。确保：
1. 已添加文档到知识库
2. 查询词与文档内容有足够的关键词重叠
3. `enableRag` 设置为 `true`

---

## 快速参考命令

```bash
# 一键启动后端（在 backend 目录）
source venv/Scripts/activate && PORT=3001 uvicorn app.main:app --reload

# 一键启动前端（在项目根目录）
npm run dev

# 测试生成简历
curl -s -X POST http://localhost:8000/api/generate-resume \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","templateId":"campus-concise","enableRag":false}'
```

---

## 文件清单

```
Proj/
├── backend/                     # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 入口
│   │   ├── config.py            # 配置
│   │   ├── models/schemas.py    # 数据模型
│   │   ├── routes/              # API 路由
│   │   └── services/            # 业务逻辑
│   ├── data/                    # 模板 & 知识库数据
│   ├── requirements.txt         # Python 依赖
│   └── run.sh                   # 启动脚本
├── src/                         # 前端 Vue 源码
├── server/                      # 原 Node.js 后端（已弃用）
└── USAGE_GUIDE.md               # 本教程
```

---

## 下一步建议

1. **接入真实 LLM**：申请阿里云百炼或 DeepSeek API Key，配置环境变量
2. **扩展知识库**：在网页上上传优秀简历，作为 RAG 上下文
3. **Docker 部署**：编写 `Dockerfile` + `docker-compose.yml` 方便团队统一部署
4. **PDF 导出**：后端可增加 `Markdown → HTML → PDF` 流水线
5. **向量检索升级**：将简单 token 重叠替换为 FAISS / Milvus + Embedding
