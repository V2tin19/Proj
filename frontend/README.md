# AI Resume Frontend

Vue 3 + Vite 构建的简历生成前端,构建产物由 nginx 服务,并将 `/api` 反向代理到后端 FastAPI。

**核心功能**:简历编辑与预览、AI 智能体生成、知识库管理、PDF/Word 导出。

> **部署已统一到仓库根目录**:全栈启动请回到仓库根目录使用 `docker compose up -d --build`(见根 README)。
> 本目录说明前端本地开发与镜像构建。

---

## 目录

1. [环境要求](#1-环境要求)
2. [本地开发](#2-本地开发)
3. [镜像构建](#3-镜像构建)
4. [项目结构](#4-项目结构)

---

## 1. 环境要求

| 依赖 | 最低版本 |
|------|---------|
| Node.js | 18(建议 20) |
| npm | 9 |
| Docker | 20.10+(部署用) |

---

## 2. 本地开发

```bash
# 安装依赖(项目本地 node_modules,不影响全局)
npm ci

# 启动开发服务器(需后端先在本机 8000 端口运行)
npm run dev
```

> 开发时前端代理配置在 `vite.config.ts` 中,默认转发 `/api` 到 `http://127.0.0.1:8000`。

---

## 3. 镜像构建

`Dockerfile` 为多阶段构建:node:20-alpine 内 `npm ci && npm run build`(生产模式),产物交由 `nginx:stable-alpine` 服务,镜像内已包含统一 nginx 配置(SPA fallback、gzip、`/api` 反代、25MB 上传限制)。

```bash
# 单独构建前端镜像(一般直接用根目录 docker compose 即可)
docker build -t proj-web .
```

生产环境 `/api` 的代理目标是 compose 网络内的 `http://backend:8000`,不再依赖 `host.docker.internal`(该域名仅 Docker Desktop 可用,Linux 上会断链)。

---

## 4. 项目结构

```
.
├── Dockerfile              # 前端构建镜像(构建 + nginx 运行)
├── nginx/
│   ├── nginx.conf          # nginx 主配置(gzip)
│   └── conf.d/
│       └── default.conf    # 静态服务 + /api 反代 + SSE 配置
├── src/                    # Vue 源码
│   ├── api/                # API 接口封装
│   ├── views/              # 页面组件
│   │   ├── resume/         # 简历编辑与预览(含 PDF/Word 导出)
│   │   ├── agent/          # AI 智能体工作台(生成 + 知识库管理)
│   │   └── setting/        # 网站配置(主题、访问口令)
│   ├── components/         # 公共组件
│   └── ...
└── public/                 # 静态资源
```
