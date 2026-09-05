# 重构变更清单(相对前后端分支基线)

> **基线**:`origin/backend-dev`(后端)与 `origin/frontend-dev`(前端)在合并时刻的 HEAD。
> 两分支经 subtree merge 合入 main(提交 `7ab49bc`、`52ca895`,保留各自完整历史),
> 此后按 phase0 → phase5 顺序重构。本文逐项说明**自分支基线以来的全部变化**。
> 计划背景与诊断依据见 [REFACTOR_PLAN.md](REFACTOR_PLAN.md)。

## 0. 总览

| 维度 | 基线(两分支) | 当前(main) |
| --- | --- | --- |
| 仓库结构 | 文档在 main,代码分居两分支 | 单仓库:backend/ + frontend/ + 文档同仓 |
| 部署 | 手工 docker run + 各自 compose | 自包含发行包 + 标准部署脚本,零安装零网络 |
| 运行时进程 | 前端 nginx 镜像 + 后端容器(两套编排) | 单进程 FastAPI(同时托管前端),单端口 8000 |
| Node 依赖 | 构建产物需 nginx 服务 | 运行时零 Node、零 nginx;Node 仅开发机构建 |
| 后端存储 | JSON 文件(非原子、并发丢数据) | SQLite(WAL,原子,自迁移) |
| 鉴权 | 无(LLM 密钥裸奔) | X-Access-Code 口令 + 限流(可选启用) |
| 测试 | 0(pytest/vitest 均无) | 后端 62 例 + 前端 14 例,全部通过 |
| 构建产物 | 生产镜像跑 development 模式包 | production 构建,类型检查门禁 |

提交序列:`f0db45e`(phase0 统一编排与文档)→ `28ca058`(phase1 后端)→ `f57522c`(phase2 前端)→ `cef6374`(phase3 契约)→ `1455041`(phase5 去容器化)。
> 说明:phase0 当日曾引入 docker-compose/nginx 统一编排,后在 phase5 因网络约束废弃删除,由发行包路线替代。

## 1. 后端变化(backend/,基线为原 backend-dev)

### 1.1 存储层(并发安全,原 P0)
- **新增 `app/services/kb_store.py`**:SQLite 存储层(WAL 模式),`documents` / `chunks`(含 float32 向量 BLOB)/ `config` 三组表;替代原来的 `data/knowledge-base.json` + `data/vector-store.json` 全量读写。
  - 修复:原实现锁只包单次读/写、不包"读-改-写"整体,并发上传互相覆盖丢文档;写盘非原子,进程崩溃损坏文件后所有知识库接口 500。
  - 连接时自初始化 schema(库文件被删可自愈);旧 JSON 数据首次启动自动迁移(幂等)。
  - 检索不再每次全量读盘反序列化全部向量。
- **重写 `app/services/knowledge_base.py`**:改用 kb_store;向量检索 numpy 批量点积(替代纯 Python 双重循环);chunk/向量懒构建+缺失回填;保留 token-overlap 降级路径;`tokenize`/`chunk_text`/`score_chunk` 纯函数保留并纳入单测。

### 1.2 嵌入服务(`app/services/embedding_service.py` 重写)
- 模型从"首次请求时懒加载(在线下载 100MB)"改为**应用启动时后台线程预热**;`is_available()`(已安装)与 `is_ready()`(已加载)分离;加载失败记录原因并优雅降级,不再卡死首个请求。
- 新增 numpy 批量编码 `encode_to_np`;运行时无嵌入栈(如 lite 发行包)时自动降级关键词检索。

### 1.3 LLM 客户端(`app/services/llm_client.py` 重写)
- 全局共享 `httpx.AsyncClient`(连接复用,原为每请求新建)。
- **JSON 容错解析 `parse_json_from_llm`**:剥离 markdown 代码围栏、提取首个平衡大括号块、失败自动重试一次——修复"LLM 偶尔输出围栏导致静默降级且用户无感知"。
- 降级原因写入响应 `meta.fallbackReason`;删除永不可达的 `HTTPStatusError` 死分支;上游返回非 JSON(网关错误页)有明确报错。

### 1.4 对话接口(`app/routes/chat.py` 重写)
- **错误处理移到流开始之前**:先连接上游并校验状态码(401/400/502/504),失败返回真实 HTTP 状态码;修复"错误发生在响应头之后 → 客户端收到 200 + 断流"。
- 补 `stream=false` 分支(上游非流式响应,原来会产出空流且永不终止);上游 `choices` 空数组防护(原来 IndexError);兼容无空格 `data:` 行;SSE 协议写入文档(事件以空行分隔、多行 data 用换行还原)。

### 1.5 鉴权与限流(新增 `app/middleware.py`,原 P0)
- `AccessCodeMiddleware`:设置 `ACCESS_CODE` 后,除 `/api/health` 与 CORS 预检外所有接口要求 `X-Access-Code` 头,常数时间比较,失败 401(友好中文提示)。
- `RateLimitMiddleware`:`/api/chat`、`/api/generate-resume` 按 IP 滑动窗口限流(默认 30 次/分钟,`RATE_LIMIT_PER_MINUTE` 可调),超限 429。

### 1.6 数据模型(`app/models/schemas.py`)
- 所有简历字段接受显式 `null`(LLM/前端历史数据,null→"")——修复"日期为 null 时导出接口 500"。
- `meta` 从裸 dict 固化为 `GeneratedResumeMeta`(`provider` Literal 枚举 + `fallbackReason`);`matchAlgorithm` 收紧为 `token-overlap|vector-cosine` 枚举(非法值 422 而非静默接受);`embeddingProvider` 收紧为 `local`;ChatMessage.role 收紧为 `system|user|assistant`。
- `HealthResponse` 新增 `embedding`(ready/loading/not-installed)与 `auth`(enabled/disabled)字段。

### 1.7 路由层与横切面
- 阻塞操作统一进线程池执行器:文件 IO、文档解析、docx 构建、知识库读写(原来部分直接跑在事件环上,高并发会冻结 SSE)。
- 上传加固(`routes/knowledge_base.py` + `services/document_parser.py`):扩展名白名单、**magic byte 校验**(PK/%PDF/二进制检测)、大小预检(20MB)、损坏 docx 返回 400 而非 500、解析 docx 表格、GBK 解码 errors=replace。
- `services/template_service.py`:提示词模板按文件 mtime 缓存(原来每次请求读盘)。
- `app/main.py`:lifespan 统一初始化(数据目录/建库/迁移/模型预热/连接清理);中间件挂载;**前端静态托管 + SPA 回退**(详见 1.8)。
- `app/config.py`:`os.getenv` 散落配置 → `pydantic-settings` 集中(超时/温度/限流/数据目录/静态目录/访问口令),去除导入副作用。

### 1.8 新行为:后端托管前端(phase5 新增)
- 存在 `frontend/dist`(开发)或发行包 `static/` 时,`GET /` 与未知路径返回前端 `index.html`,静态资源直接由后端服务;`/api/*` 与 `/docs` 优先匹配不受影响;带扩展名的缺失资源返回 404。由此实现**单端口 8000 单进程**,替代"前端 nginx 镜像 + 反代"形态。

### 1.9 其他
- 依赖全部锁定版本(`requirements.txt`,原为无上界 `>=`);新增 pytest、pydantic-settings、numpy 显式声明。
- 移除 PyPDF2 死分支(pypdf 统一);运行 `.env` 不再要求 load_dotenv 顺序约定(pydantic-settings 接管)。
- 新增 `pytest.ini` 与 `tests/`:纯函数、SSE 解析、中间件(鉴权/限流独立 app)、知识库(SQLite/迁移/检索/假嵌入向量链路)、静态托管、API 冒烟(TestClient 全接口),共 62 例。

## 2. 前端变化(frontend/,基线为原 frontend-dev)

### 2.1 构建与工程化(原 P0)
- `vite.config.ts`:删除写死的 `mode: "development"`(**原生产镜像一直在跑 dev 包**)、`base "./"→"/"`、新增 vitest test 配置、defineConfig 切至 `vitest/config`。
- `tsconfig.app.json`:补 `@/*` 路径映射(原先依赖通配声明兜底)。
- `package.json`:更名 `ai-resume-frontend`、版本 1.0.0、engines 字段;删除 `crypto-js` 与指向已删目录的 `server` 脚本;`vite-plugin-svg-icons`/`fast-glob` 移至 devDependencies;新增 `dompurify`、`@fortawesome/fontawesome-free`、vitest/jsdom/@vue/test-utils;新增 `test` 脚本。

### 2.2 安全(原 P0)
- **新增 `utils/safeMarked.ts`**(marked + DOMPurify),替换全部 **31 处**未消毒的 `v-html="marked(...)"`(5 套简历模板 + AIChat 消息渲染与面试评分)——AI 返回内容可被注入,原样进 innerHTML 属 XSS。

### 2.3 Worker 与流式(原 P1)
- `worker/aiWorker.ts` 重写:按 SSE 规范**以空行分隔事件、事件内多行 data 用 `\n` 还原**(修复多行回复换行全部丢失);`AbortController` 125 秒超时(修复后端挂起时 UI 永久 loading);请求头注入 `X-Access-Code`;错误以 `error: true` 标记回报并区分超时/网络异常。
- `worker/workerPool.ts`:删除构造器内被覆盖的死 `onmessage`、`console.log` 调试残留;`activeTasks` 计数修正;回调签名增加 error 透传。

### 2.4 API 层与鉴权对接
- `api/agentAPI.ts`:请求拦截器自动注入 `X-Access-Code`;响应拦截器将错误规范化为 `ApiError{code,message}`(含 401/403/413/429/502/504 中文文案),401 全局去重提示。
- `store/useSettingsStore.ts` 新增 `accessCode`(存取收敛在 `utils/accessCode.ts`,localStorage);`views/setting` 新增访问口令输入与保存;`components/Header` 过时引导文案修正(不再引导去配置已迁移到后端的模型接口)。

### 2.5 简历模板收敛(原 P1)
- **新增 `composables/useResumeStyle.ts`**:5 套模板逐字复制的 script(resumeStyle/sectionStyle/字号全局副作用)收敛为一处,模板只保留布局 HTML/CSS。
- 修复:templateD/dev 的 `colorShades` 由一次性 ref 快照改为 computed(**换主题色即时生效**,原来纹丝不动);templateA 重复且路径错误的 `@font-face` 删除(全局 theme.css 已正确声明);templateC/D 的 Font Awesome 图标补依赖修复(原来全部渲染为空白);`dev` 开发模板对模板市场下架;模板注册收敛为 `public/templates.json` 单源(删除 5 份漂移的 `config.json`)。

### 2.6 编辑页去重(原 P1)
- **新增 `composables/useDragReorder.ts`**:5 个分区组件逐字复制的 ~60 行拖拽逻辑归一。
- 持久化:6 个组件各自对 `$state` 的 deep watcher(每敲一个字触发 6 次全量 JSON.stringify + localStorage 写)收敛为 `resumeEdit.vue` 单一 `$subscribe`。
- 修复复制粘贴文案 bug(工作经历删除弹窗写着"确定要删除当前技能?")。

### 2.7 agent 页拆分(原 P1 上帝文件)
- 知识库管理域(配置/录入/上传/列表)整体抽出为 `views/agent/components/KnowledgeBasePanel.vue`(自含状态与样式,`index.vue` 1190 → ~990 行);主文件删除对应状态与函数。

### 2.8 导出与稳定性
- PDF 导出(`views/resume/components/resumePreview.vue`):try/finally 保证临时容器清理(原来失败即泄漏)+ 独立 app 实例 `unmount`(原来从不卸载)+ html2pdf 动态 import(~800KB 移出主包)+ 重复点击防抖 + 成功/失败提示;模板列表为空不再 `templates[0]` 崩溃。
- Word 导出去掉 `payload as any`,补 `GeneratedResumeData` 类型。

### 2.9 清理(原 P1/P2)
- 删除死代码:`views/coding.vue`(未注册路由、"2024Q2 发布"过期占位)、`components/narrow/`、`store/index.ts` 的 `setupStores`(从未调用)、`useResumeStore.loadFromLocalStorage`(读写 key 不一致的死代码)、示例数据契约外 `address` 字段。
- `public/resumeData.json` 移除 30KB base64 头像外的冗余字段(与后端 schema 对齐)。

### 2.10 测试
- 新增 vitest(`tests/`):safeMarked 安全渲染 6 例、normalizeSectionOrder/moveItem 纯函数 5 例、accessCode 存取 3 例,共 14 例;`npm run build`(vue-tsc 严格检查)作为类型门禁。

## 3. 部署与基础设施(phase5,彻底改变)

- **删除全部 Docker 资产**:根 `docker-compose.yml`、`backend/Dockerfile`、`frontend/Dockerfile`、`frontend/nginx/`、两份 `.dockerignore`(phase0 曾重建统一编排,phase5 按网络约束弃用)。
- **新增 `backend/scripts/build_release.sh`**(linux)与 `build_release.ps1`(windows):自包含发行包构建——内嵌 Python 解释器+标准库+site-packages(lite 剔除 torch/transformers 等嵌入栈 ~1.13GB,`--full` 保留)+后端源码+前端产物+部署脚本;构建期自举验证;产出 tar.gz/zip + SHA256SUMS。全程本地拷贝,零网络。
- **新增 `deploy/` 标准部署脚本**:`install.sh`(systemd 自动安装;无 root 自动降级用户级 `systemctl --user`)、`uninstall.sh`、`start.sh/stop.sh/status.sh`(无 systemd 兜底)、`ai-resume.service.template`、`windows/`(install.ps1/start.bat/stop.bat/uninstall.ps1)、`README-DEPLOY.md`(离线部署手册)。
- 产物:`dist-release/ai-resume-server-linux-x86_64-lite.tar.gz`(59MB),已在本机解压冒烟并正式部署(systemd 自启,八项回环验证通过)。
- 根 `.gitignore`、`.env.example`(含 ACCESS_CODE/RATE_LIMIT 说明)为新增。

## 4. 文档变化

| 文档 | 变化 |
| --- | --- |
| `README.md` | 全面重写:单仓库结构、发行包部署、真实 API 表(修正 3 处错误:export 路由、generate-resume 非 SSE、补 upload)、环境变量、**Node.js 评估结论** |
| `backend-api.md` | 与实现对齐:访问控制、限流 429、health 新字段、fallbackReason、chat 错误码、SSE 还原规则、SQLite 存储说明、过时示例修正 |
| `frontend-api.md` | 同步:鉴权/限流说明、matchAlgorithm/embeddingProvider/provider 示例值修正、category 可选、enableRag 默认 true |
| `backend/README_DEPLOY.md` | 重写:单实例约束(撤回原多 worker 建议)、本地开发与测试指引 |
| `frontend/README.md` | 重写:Node 仅开发构建、构建产物由后端托管 |
| `REFACTOR_PLAN.md` | 新增:计划、诊断、决策、Phase 5 网络约束与形态变更记录 |
| `CHANGES.md` | 新增:本文(逐项变更清单) |
| `TEAM_GUIDE.md` | 未改动(协作规范仍然有效) |

## 5. 对外契约变化(联调必读)

| 变化 | 说明 |
| --- | --- |
| 鉴权头(可选) | 设置 `ACCESS_CODE` 后,除 health 外全部接口需 `X-Access-Code`,缺失/错误 401 |
| 限流 | chat/generate-resume 默认 30 次/分钟/IP,超限 429 |
| SSE 换行 | 多行 data 需按事件聚合后以 `\n` 还原(前端 Worker 已实现) |
| 错误语义 | chat 错误在流开始前返回真实状态码;422 用于参数/枚举校验失败 |
| 新字段 | `meta.fallbackReason`;health 的 `embedding`/`auth` |
| null 容错 | 日期等字段传 null 不再 500;LLM 返回非数字 id 自动回退序号 |
| 收紧校验 | matchAlgorithm/embeddingProvider/role 传入非法值返回 422(原来静默接受) |
| 端口形态 | 生产单端口 8000(API+页面同源);nginx/5173 不再是部署链路的一部分 |

## 6. 测试与验证基线

- 后端 pytest **62 例**:文本工具与 JSON 容错、SSE 解析、中间件、知识库(含假嵌入向量链路、旧 JSON 迁移)、静态托管、API 冒烟(health/模板/KB CRUD+上传/生成降级/null 容错导出/导出/chat 错误路径)。
- 前端 vitest **14 例** + `npm run build` 类型门禁。
- 端到端(部署机回环):health / 首页 / SPA 刷新 / 静态资源 / 生成 / docx 导出 / KB 上传 / 数据落盘,八项通过。
- 已知边界:lite 发行包无向量检索(自动降级关键词,已测);Windows/macOS 包需在对应平台用同仓库构建脚本产出;linux 包面向 x86_64 + glibc 2.31+ 主流发行版。
