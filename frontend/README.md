# AI Resume Frontend

Vue 3 + Vite 构建的简历生成前端。**构建产物为纯静态文件,运行时由后端 FastAPI 直接托管**
(单端口 8000),不需要 Node、不需要 nginx。

> **生产部署请使用自包含发行包**(见根 README / deploy/README-DEPLOY.md)。
> 本目录说明前端本地开发与构建。

---

## 1. 环境要求

| 依赖 | 最低版本 | 用途 |
|------|---------|------|
| Node.js | 18(建议 20) | 仅开发构建,运行时不需要 |
| npm | 9 | 同上 |

## 2. 本地开发

```bash
# 安装依赖(项目本地 node_modules,不影响全局)
npm ci

# 启动开发服务器(需后端先在本机 8000 端口运行)
npm run dev
```

> 开发时前端代理配置在 `vite.config.ts` 中,默认转发 `/api` 到 `http://127.0.0.1:8000`。

## 3. 构建

```bash
npm run build        # vue-tsc 严格类型检查 + 生产构建 → dist/
npm run test         # vitest 单元测试
```

构建产物 `dist/` 的去向(二选一):
- **发行包**:`backend/scripts/build_release.sh` 会把 `dist/` 打进发行包 `static/` 目录,由后端托管;
- **开发自测**:`npm run preview` 本地预览构建结果。

生产形态下 `/api` 与页面同源(后端 SPA 托管),不存在跨域与代理配置问题。

## 4. 项目结构

```
.
├── src/
│   ├── api/                # API 封装(axios 统一实例 + 访问口令注入)
│   ├── composables/        # useResumeStyle / useDragReorder 公共逻辑
│   ├── utils/safeMarked.ts # marked + DOMPurify 安全渲染
│   ├── views/              # 页面组件(resume/agent/aiDeep/template/setting)
│   ├── store/              # Pinia 状态
│   ├── worker/             # Web Worker(SSE 流式,带超时中止)
│   └── template/           # 5 套简历布局模板(共享 useResumeStyle)
├── tests/                  # vitest 用例
└── public/                 # 静态资源(templates.json 为模板注册唯一来源)
```
