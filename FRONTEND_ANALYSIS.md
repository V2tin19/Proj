# 前端分析文档

> 基于 `frontend-dev` 分支代码分析，2026-06-08

---

## 一、技术栈

| 层面 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3（Composition API + `<script setup>`） | 3.5 |
| 语言 | TypeScript（严格模式） | 5.7 |
| 构建工具 | Vite | 6.1 |
| UI 组件库 | Ant Design Vue | 4.2 |
| 状态管理 | Pinia + pinia-plugin-persistedstate | 3.0 |
| 路由 | Vue Router（HTML5 history） | 4.5 |
| HTTP 客户端 | Axios | 1.7 |
| PDF 导出 | html2pdf.js（客户端） | 0.10 |
| Markdown 渲染 | marked | 15.0 |
| 颜色工具 | chroma-js | 3.1 |
| SVG 图标 | vite-plugin-svg-icons | 2.0 |
| 容器化 | Docker（Node 18 构建 → nginx 运行） | — |

---

## 二、项目结构

```bash
├── index.html                      # SPA 入口（lang="zh-CN"）
├── package.json                    # 依赖与脚本
├── vite.config.ts                  # Vite 配置：Vue 插件、SVG 图标、@ 别名、/api 代理
├── tsconfig.json / .app / .node    # TypeScript 配置（严格模式）
├── worker.js                       # Cloudflare Worker 代理（LLM API CORS 转发）
├── Dockerfile.client               # 多阶段构建：Node 编译 → nginx 运行
├── docker-compose.yml              # web + nginx 两个服务
├── nginx/                          # 反向代理配置（/ → web, /api → 后端:8000）
├── public/
│   ├── resumeData.json             # 示例简历数据
│   └── templates.json              # 模板注册表（5 个模板）
└── src/
    ├── main.ts                     # 应用入口：注册 Pinia、Router、Antd
    ├── App.vue                     # 根组件：Header + <router-view>（keep-alive aiDeep）
    ├── router/index.ts             # 5 个路由 + 404 兜底
    ├── store/
    │   ├── useResumeStore.ts       # 简历数据 CRUD，localStorage 持久化
    │   └── useSettingsStore.ts     # 主题、API Key、模型配置（persisted）
    ├── api/
    │   ├── agentAPI.ts             # 后端 API 客户端（/api 代理）
    │   └── qwenAPI.ts              # 直接 LLM 对话，通过 WorkerPool
    ├── worker/
    │   ├── workerPool.ts           # Web Worker 线程池（固定 4 个 worker）
    │   └── aiWorker.ts             # Worker：SSE 流式请求 /api/chat
    ├── views/
    │   ├── resume/                 # 简历编辑器（左编辑 + 右预览分栏）
    │   │   ├── index.vue           # 布局容器
    │   │   └── components/         # 个人信息、教育、工作、技能、项目、荣誉、自评、AI增强
    │   ├── template/               # 模板市场（卡片网格）
    │   ├── agent/                  # AI 智能体工作台（信息填写 + 知识库 + 生成）
    │   ├── aiDeep/                 # AI 深度对话（聊天界面，keep-alive）
    │   ├── setting/                # API 配置页
    │   ├── coding.vue              # 占位页（未使用）
    │   └── 404.vue
    ├── template/                   # 简历视觉模板
    │   ├── templateA-D/            # 4 个生产模板（config.json + index.vue + preview.jpg）
    │   └── dev/                    # 开发参考模板
    ├── types/                      # TypeScript 类型定义（resume、agent、template 等）
    ├── constants/                  # 段落顺序常量
    ├── data/                       # 默认空简历数据模板
    ├── utils/                      # 颜色生成、模板加载、数组重排
    ├── directives/                 # 图片懒加载指令
    └── assets/                     # 样式（theme/dark）、字体、SVG 图标、图片
```

---

## 三、交互逻辑简述

### 核心数据流

```
用户填写表单 → useResumeStore（Pinia）→ localStorage 持久化
                                      ↓
                            选择模板 → template 组件渲染预览
                                      ↓
                   AI 智能体工作台 → POST /api/generate-resume → 后端 LLM + RAG
                                      ↓
                            生成结果 → 合并回 store → 更新预览
                                      ↓
                         导出 PDF（html2pdf.js 客户端）
                         导出 DOCX（POST /api/export-resume/docx 服务端）
```

### 页面路由

| 路径 | 页面 | 功能 |
|------|------|------|
| `/` | resume | 简历编辑器主页面，左侧表单编辑 + 右侧实时预览 |
| `/template` | template | 模板市场，浏览并选择简历模板 |
| `/agent` | agent | AI 智能体工作台，填写信息 → AI 生成结构化简历 |
| `/aiDeep` | aiDeep | AI 深度对话，聊天式交互（keep-alive 保持状态） |
| `/setting` | setting | 配置 API Key、API 地址、模型名称 |

### 关键交互细节

1. **简历编辑 ↔ 预览联动**：编辑区表单变更通过 Pinia store 实时同步到预览组件，预览使用用户选择的模板组件动态渲染。
2. **AI 对话流式响应**：`qwenAPI.ts` 通过 `WorkerPool`（4 个 Web Worker）发起 SSE 流式请求，worker 解析 `data:` 行后 postMessage 回主线程，UI 逐步显示 AI 回复。
3. **模板动态加载**：`public/templates.json` 注册模板元数据，运行时通过 `import.meta.glob` + `defineAsyncComponent` 按需加载所选模板组件。
4. **主题切换**：`useSettingsStore.toggleTheme()` 切换 `.dark` 类，CSS 变量在 `theme.css` / `dark.css` 之间切换。
5. **PDF 导出**：克隆模板 DOM → 内联 CSS 变量 → html2pdf.js 渲染为 A4 PDF。DOCX 通过后端接口生成。

---

## 四、不符合规范的部分

### 4.1 安全问题

**`v-html` 直接渲染未消毒的 Markdown/HTML 内容 — XSS 风险**

- `src/template/templateA/index.vue`：使用 `v-html="marked(...)"` 渲染简历各段落（荣誉、技能、工作描述、项目描述、自评）。`marked` 将 Markdown 转为原始 HTML 后直接注入 DOM。
- `src/views/aiDeep/components/AIChat.vue`：AI 回复通过 `v-html="formatMessage(msg.content)"` 渲染，同样无消毒。
- **修复方案**：引入 DOMPurify 对 `marked` 输出进行消毒，或使用 `marked` 的 `sanitizer` 选项。

### 4.2 Vue 反模式

| 问题 | 位置 | 说明 |
|------|------|------|
| 全局 DOM 副作用 | `templateA/index.vue` onMounted | 直接设置 `document.documentElement.style.fontSize`，影响整个页面而非组件自身 |
| 冗余深度监听 | `personalInfo.vue` | `watch(resumeStore.$state, { deep: true })` 触发重复的 `saveToLocalStorage()`，store 的每个 action 已自行保存 |
| 编译宏显式导入 | `AIEnhancePopover.vue` | `import { defineProps, defineEmits } from 'vue'` — 这些是 `<script setup>` 编译宏，无需导入 |
| `let` 用于 ref | `resumePreview.vue` | `let open = ref(false)` 应使用 `const` |

### 4.3 TypeScript 问题

| 问题 | 位置 |
|------|------|
| `String`（对象包装类型）代替 `string`（原始类型） | `types/template.d.ts`（folderPath, thumbnail, author, link）、`types/resume.d.ts`（currentTemplate） |
| 使用 `any` 类型 | `personalInfo.vue`（handleAvatarChange）、`resumePreview.vue`（exportToWord payload）、`lazyLoad.ts`（binding 参数） |
| 字符串代替布尔值 | `AIEnhancePopover.vue`：`arrowPointAtCenter="true"` 传字符串而非布尔值 |

### 4.4 代码风格不一致

- **命名混用**：`padding_left_right`、`padding_top_bottom`（snake_case）与其他属性（camelCase）不一致。
- **组件命名**：`resumeEdit`、`resumePreview` 小写导入，Vue 惯例应为 PascalCase。
- **CSS 变量命名**：混用 kebab-case（`--border-color`）和 camelCase（`--themeColor1`）。
- **引号风格**：部分文件用单引号，部分用双引号。

### 4.5 残留调试代码

- `src/worker/workerPool.ts`：`console.log(\`任务${taskId}分配给 Worker:${worker}\`)` — 调试日志留在生产代码中。
- `src/api/agentAPI.ts`：拦截器中的 `console.error` 可接受，但应使用统一的日志方案。

### 4.6 潜在内存泄漏

- **拖拽事件监听器**：`resumePreview.vue` 中 `document.addEventListener("mousemove/mouseup")` 在 `startDragging` 添加，但组件卸载时未清理这些监听器。
- **WorkerPool 未终止**：`qwenAPI.ts` 中模块级单例 `WorkerPool` 从未调用 `terminate()`。

### 4.7 Vite 配置问题

- `vite.config.ts` 硬编码 `mode: "development"`，导致生产构建也以开发模式运行，可能包含开发专用代码和警告。

### 4.8 无障碍（Accessibility）

- `<input type="color">` 缺少 `aria-label`。
- `v-for` 使用 `index` 作为 key（`template/index.vue`），应用唯一标识。
- 无跳过导航链接。

### 4.9 后端逻辑泄漏到前端

以下内容属于后端职责，但存在于前端代码中，违反前后端分离原则。

#### 4.9.1 `worker.js` — 服务端代理混入前端仓库（已修改）

项目根目录的 `worker.js` 是一个 **Cloudflare Workers 服务端代理**，负责：
- 处理 CORS 头
- 转发 Authorization 头
- 默认路由到阿里云 DashScope API（`env.API_URL` 可覆盖）
- 强制启用 `stream: true`
- 透传 SSE 流式响应

这是一个需要独立部署的服务端组件，与 Vue 构建流程无关，不应放在前端仓库中。应归属后端或独立的边缘函数项目。

#### 4.9.2 API Key 由前端持有和传递（已修改）

`src/store/useSettingsStore.ts` 通过 `pinia-plugin-persistedstate` 将 `aliApiKey` 持久化到 **localStorage**。`src/views/setting/index.vue` 提供 UI 让用户直接在浏览器输入 API Key。

前端持有 API Key 存在以下风险：
- localStorage 易受 XSS 攻击窃取
- 用户可自行替换为任意 Key，绕过后端的用量控制和计费
- 前端代码中 API Key 以明文形式在内存中流转

API Key 应由后端统一管理，前端不应接触。

#### 4.9.3 LLM API 地址和模型参数由前端控制（已修改）

- `useSettingsStore` 中 `aliApiUrl` 默认值来自 `import.meta.env.VITE_API_URL`，但用户可在设置页修改为任意地址。
- `src/worker/aiWorker.ts` 硬编码 `temperature: 0.7`。
- 前端向后端 `/api/chat` 发送请求时，将 `api_url`、`api_key`、`model` 一并传给后端，后端仅作透明代理转发。

这意味着后端 `/api/chat` 没有自己的业务逻辑，完全听命于前端传参。模型选择、API 地址路由、温度参数等模型调用策略应由后端决定。

#### 4.9.4 SSE 协议解析在前端完成（已修改）

`src/worker/aiWorker.ts` 在 Web Worker 中解析 OpenAI 格式的 SSE 流：
- 按 `\n` 分割，过滤空行
- 识别 `data: ` 前缀并剥离
- 处理 `[DONE]` 终止标志
- 解析 `choices[0].delta.content` 提取增量内容

这是 LLM API 的协议实现细节，应封装在后端。前端只需接收后端标准化后的内容流。

#### 4.9.5 前端直接编排 LLM 调用链路（已修改）

`qwenAPI.ts` → `workerPool.ts` → `aiWorker.ts` → `/api/chat` → 外部 LLM API

整条链路由前端驱动：前端决定并发策略（4 worker 线程池）、传递凭据、解析协议。后端仅是透明转发层。正确的架构应是：前端发送语义化请求（如"用此模板生成简历"），后端负责凭据管理、模型选择、并发控制和协议处理。

---

## 五、未完成的部分

### 5.1 占位页面

- **`src/views/coding.vue`**：功能开发中占位页面，显示"预计 2024年Q2 上线"（已过期）。该页面未在 `router/index.ts` 中注册路由，属于死代码。

### 5.2 TODO / 注释代码

| 位置 | 内容 |
|------|------|
| `aiDeep/components/AIChat.vue` | 注释掉的"AI帮答"按钮，附 `<!-- TODO -->` |
| `main.ts` | 注释掉的 `ConfigProvider` 导入和 SVG 注册 |
| `aiDeep/index.vue` | 注释掉的 CSS flex 布局 |
| `store/index.ts` | 导出的 `setupStores` 函数创建了第二个 Pinia 实例，从未被使用 |

### 5.3 双重 Pinia 初始化

`main.ts` 创建一个 Pinia 实例并注册。`store/index.ts` 另外创建一个独立的 Pinia 实例并导出 `setupStores` 函数，但该函数从未被调用。`store/index.ts` 中的 Pinia 实例是死代码。

### 5.4 模板配置拼写错误

`src/template/dev/config.json` 中 `"id": "devlop"` — 应为 `"develop"`。

### 5.5 未集成功能

- Agent 页面提示"后续可以继续接本地 DeepSeek/Qwen 模型、文件上传解析和 Word 导出"，但 Word 导出仅在 resumePreview 中实现，未集成到 agent 工作流。
- `package.json` 中 `"server": "node server/index.mjs"` 脚本引用的 `server/index.mjs` 文件不存在。

---

## 六、优先修复建议

1. **高优先**：为 `marked` 输出添加 DOMPurify 消毒，消除 XSS 风险。
2. **高优先**：将 API Key 管理移至后端，前端不再持有和传递 Key。`worker.js` 移出前端仓库。（已修改）
3. **高优先**：后端 `/api/chat` 应自主管理模型调用策略（API 地址、模型选择、温度参数），前端仅传语义化请求。（已修改）
4. **高优先**：SSE 协议解析移至后端，前端接收标准化内容流。（已修改）
5. **高优先**：移除 `vite.config.ts` 中的 `mode: "development"` 硬编码。
6. **中优先**：修复 `templateA/index.vue` 全局字体大小副作用，改为组件作用域。
7. **中优先**：移除 `personalInfo.vue` 的冗余深度监听。
8. **中优先**：修复 TypeScript 类型定义中的 `String` → `string`。
9. **低优先**：清理 `coding.vue` 死代码、注释代码、调试 console.log。
10. **低优先**：统一命名规范和代码风格。
