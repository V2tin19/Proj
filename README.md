# AI Resume Frontend

Vue 3 + Vite 构建的简历生成前端，通过 nginx 反向代理连接后端 FastAPI 服务。

**核心功能**：简历编辑与预览、AI 智能体生成、知识库管理、PDF/Word 导出。

---

## 目录

1. [环境要求](#1-环境要求)
2. [本地开发](#2-本地开发)
3. [Docker 部署](#3-docker-部署)
4. [项目结构](#4-项目结构)

---

## 1. 环境要求

| 依赖 | 最低版本 |
|------|---------|
| Node.js | 18 |
| npm | 9 |
| Docker | 20.10+（部署用） |

---

## 2. 本地开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

> 开发时前端代理配置在 `vite.config.ts` 中，默认转发 `/api` 到 `http://127.0.0.1:3001`。

---

## 3. Docker 部署

### 3.1 前置条件

确保后端 FastAPI 服务已启动，默认期望后端在 **本机 8000 端口** 运行。

如果后端部署在其他机器，修改 `nginx/conf.d/default.conf` 中的 `proxy_pass` 地址。

### 3.2 快速启动

```bash
# 构建并启动（前端 + nginx）
docker compose up --build -d
```

访问：`http://localhost:8080`

### 3.3 与后端联调

推荐目录结构：

```
Proj/
├── frontend/     # 本仓库（frontend-dev 分支）
└── backend/      # FastAPI 后端（backend-dev 分支）
```

**Step 1：启动后端**

```bash
cd backend

# 创建 .env（大模型凭据由后端统一管理）
cat > .env << 'EOF'
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=sk-你的Key
LLM_MODEL=qwen-plus
EOF

# 启动容器
docker build -t proj-backend .
docker run -d \
  --name proj_backend \
  -p 8000:8000 \
  -v backend_data:/app/data \
  --env-file .env \
  proj-backend
```

> 前端不再保存或传递 API Key、API URL、模型名称。这些配置统一在后端 `.env` 中设置。

**Step 2：启动前端**

```bash
cd ../frontend
docker compose up --build -d
```

**Step 3：验证**

| 地址 | 说明 |
|------|------|
| `http://localhost:8080` | 前端页面 |
| `http://localhost:8080/api/health` | 后端健康检查（经 nginx 代理） |
| `http://localhost:8080/docs` | FastAPI Swagger 文档 |
| `http://localhost:8000/api/health` | 直接访问后端 |

### 3.4 常用命令

```bash
# 查看运行状态
docker ps

# 查看日志
docker compose logs -f nginx
docker compose logs -f web

# 停止服务
docker compose down

# 重启
docker compose restart

# 重新构建
docker compose up --build -d
```

### 3.5 后端地址配置

如果后端不在本机，修改 `nginx/conf.d/default.conf`：

```nginx
location /api/ {
    proxy_pass http://192.168.1.100:8000/api/;  # 改成实际IP
    ...
}
```

然后重启 nginx：

```bash
docker compose restart nginx
```

> Windows Docker Desktop 需开启 **Settings → Resources → Network → Enable host networking**，`host.docker.internal` 才能正常解析。

---

## 4. 项目结构

```
.
├── Dockerfile.client       # 前端构建镜像
├── docker-compose.yml      # 前端 + nginx 编排
├── nginx/
│   ├── nginx.conf          # nginx 主配置
│   └── conf.d/
│       └── default.conf    # 反向代理规则
├── src/                    # Vue 源码
│   ├── api/                # API 接口封装
│   ├── views/              # 页面组件
│   │   ├── resume/         # 简历编辑与预览（含 PDF/Word 导出）
│   │   ├── agent/          # AI 智能体工作台（生成 + 知识库管理）
│   │   └── setting/        # 网站配置（主题等前端设置）
│   ├── components/         # 公共组件
│   └── ...
└── public/                 # 静态资源
```
