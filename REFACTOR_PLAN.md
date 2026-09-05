# 重构计划与执行记录(2026-09)

> 本文档记录本次"达到可交付使用级别"重构的诊断结论、已确认决策、执行内容与验收清单。
> 分支代码审查发现的问题均附文件证据;执行细节见 git log(phase0–phase4 提交)。

## 一、目标

让项目达到 **可交付使用级别**:干净 Linux 机器上通过**自包含发行包**一键部署启动
(Phase 5 起,原 Docker 方案因网络事故被废弃,见文末 Phase 5);
端到端核心流程(填表 → AI 生成 → 预览 → 导出 Word/PDF)可用;具备访问控制、并发安全、
最小回归测试与零偏差文档。

## 二、重构前诊断摘要(证据见 git 历史)

### 后端(原 backend-dev 分支)
| 级别 | 问题 |
| --- | --- |
| P0 | 知识库 JSON 读改写无整体锁、非原子写 → 并发丢数据/崩溃损坏(`app/services/knowledge_base.py`) |
| P0 | BGE 嵌入模型懒加载在请求路径,首请求在线下载 100MB(`app/services/embedding_service.py`) |
| P0 | 运行时数据写容器层无卷,重建容器即丢(`Dockerfile` + 部署文档) |
| P0 | `/api/chat`、`/api/generate-resume` 零鉴权限流(LLM 密钥裸奔) |
| P1 | LLM JSON 解析零容错且静默降级;chat SSE 错误发生在响应头之后;阻塞操作跑在事件环;向量全精度 JSON + 纯 Python 余弦;零 pytest;依赖未锁版本且默认拉 CUDA torch;Dockerfile root/无 HEALTHCHECK;上传仅扩展名校验 |

### 前端(原 frontend-dev 分支)
| 级别 | 问题 |
| --- | --- |
| P0 | `vite.config.ts` 写死 `mode:"development"`,生产镜像跑 dev 包 |
| P0 | history 路由 + nginx 无 SPA fallback → 刷新任意路由 404 |
| P0 | nginx 指向 `host.docker.internal` 且 compose 无 extra_hosts → Linux 上 /api 全断 |
| P0 | marked 输出未消毒 + 31 处 `v-html` → XSS |
| P0 | 测试为零 |
| P1 | templateC/D 图标全失效;templateA 字体 404;主题色契约分裂;5 套模板脚本复制粘贴;6 个编辑组件重复 deep watcher + 60 行拖拽 ×5;agent 页 1190 行上帝文件;Worker 无超时且丢失换行;PDF 导出容器泄漏;死代码一批 |

### 契约与部署
- main README API 表 3 处错误(export 路由、generate-resume 误标 SSE、漏 /upload)
- SSE 换行:后端转义续行,前端不还原 → 多行回复丢换行
- nginx 默认 `client_max_body_size 1m` → 20MB 上传约定在生产 413 失效
- 两分支各搞各的 compose;3001 端口残留 3 处;部署命令与实际不符

## 三、已确认决策(与负责人沟通确定)

1. **合并为单仓库**:frontend/、backend/ 迁入 main(subtree merge 保留历史);验收后下线两个 dev 分支。
   (原「根目录统一 docker-compose」已在 Phase 5 改为自包含发行包路线)
2. **加简单口令鉴权**:`ACCESS_CODE` 环境变量 + `X-Access-Code` 请求头,前端设置页填一次。
3. **知识库迁移 SQLite**:标准库 sqlite3 + WAL,向量 float32 blob + numpy 批量点积。

## 四、执行内容(已完成)

- **Phase 0 仓库与编排**:两分支 subtree 合并;根 `.env.example`;README/3001 残留修正。
  (当日的 docker-compose/nginx 统一编排文件已在 Phase 5 删除,由发行包路线替代)
- **Phase 1 后端**:`kb_store.py` SQLite 存储层(WAL,启动自动迁移旧 JSON);嵌入模型启动预热 + 构建期预下载;LLM 客户端 JSON 容错(围栏剥离/大括号提取/重试一次)+ 全局连接复用 + `meta.fallbackReason`;chat SSE 先校验后建流 + `stream=false` 分支 + 空 choices 防护;`X-Access-Code` 中间件(常数时间比较) + 按 IP 限流(429);阻塞操作统一进 executor;上传 magic byte 校验 + 大小预检 + docx 表格解析;Dockerfile 免 apt/非 root/HEALTHCHECK/CPU torch;requirements 锁版本;pytest 54 例。
- **Phase 2 前端**:构建模式修复;`safeMarked`(marked+DOMPurify)替换 31 处 v-html;Worker 重写(按事件聚合还原换行、125s 超时中止、error 标记、口令注入);API 层 ApiError + 401 统一提示 + 口令拦截器;设置页口令输入;`useResumeStyle`/`useDragReorder` composable 收敛模板与编辑页重复代码;colorShades 改 computed(修换色);字体/图标修复;模板注册单源 + dev 模板下架;agent 拆出 KnowledgeBasePanel;PDF 导出 try/finally + app.unmount + html2pdf 动态导入;死代码清理;vitest 14 例。
- **Phase 3 文档**:backend-api.md / frontend-api.md / README 与实现逐条对齐(鉴权、限流、枚举、默认值、示例值)。

## 五、验收清单(Definition of Done)

- [x] 干净 Linux:发行包解压 + `deploy/install.sh` 一键部署(已在部署机验证)
- [ ] `http://localhost:8080` 可访问,刷新 `/agent`、`/template` 等路由不 404
- [ ] 端到端:填表 → 生成 → 预览 → 导出 Word/PDF 成功
- [ ] 上传 5MB PDF 入知识库 → 生成时 RAG 命中
- [ ] 设置 `ACCESS_CODE` 后:匿名调用业务接口返回 401,带口令正常
- [ ] 并发 10 个知识库写入不丢数据(SQLite WAL)
- [x] 后端 `pytest` 全绿(62 例);前端 `npm run test` 全绿(14 例);`npm run build` 含类型检查通过
- [ ] 生产镜像为 production 构建(vue devtools 无提示、`import.meta.env.PROD === true`)
- [ ] 文档与实现零偏差

## 六、风险与回滚

- SQLite 迁移为一次性、幂等;旧 JSON 保留在 data/ 目录可人工恢复。
- 模板重构未改视觉:如需比对,用同一样例数据截图对照重构前后。
- 原 frontend-dev / backend-dev 分支只读归档,合并窗口前已在团队通报。

---

## Phase 5(追加):去容器化 · 自包含发行包

### 背景
Docker 镜像构建期间的大流量下载(基础镜像/torch/依赖)被判定与服务器网络故障相关,
负责人紧急叫停:**即日起禁止一切网络操作;放弃 Docker**。改为「分平台自包含二进制发行包 +
标准部署脚本」路线。所幸 Docker 阶段前所有关键产物(前端 dist、后端 venv、全部测试)均已
就绪,剩余工作在零网络条件下完成。

### 形态决策
- 真单文件二进制不可行:本地无 PyInstaller 且不可联网安装。
- 采用**自包含发行包**:内嵌 Python 解释器 + 标准库 + site-packages + 后端源码 + 前端静态
  产物 + 部署脚本,目标机解压即用,零安装、零下载、零 Node、零 nginx。
- 默认 **lite**(剔除 torch/transformers 等嵌入栈 ~1.13GB,RAG 自动降级关键词检索,已测),
  构建脚本保留 `--full` 开关。
- Docker 资产(仓库文件 + 本工作区产生的镜像)彻底删除。

### 关键改动
- 后端新增前端静态托管 + SPA 回退(`app/main.py`),单端口 8000 单进程;新增 7 个静态托管用例。
- `backend/scripts/build_release.sh`(linux,--full 可选)/ `build_release.ps1`(windows):
  组装 runtime(解释器+标准库+site-packages)、自举验证、tar.gz/zip + SHA256。
- `deploy/`:install.sh(systemd 自动安装,无 root 降级用户级)、uninstall/start/stop/status.sh、
  ai-resume.service 模板、windows(install.ps1/start.bat/stop.bat/uninstall.ps1)、README-DEPLOY.md。
- Node 结论:**运行时零 Node;构建仅开发机需要;不替换前端栈**(README §8)。

### 交付物
- `dist-release/ai-resume-server-linux-x86_64-lite.tar.gz`(+SHA256SUMS)
- Windows/macOS 包:在对应平台用同一构建脚本产出(物理上无法交叉构建,已提供脚本与文档)

