# C/S 化改造计划(Web/服务端模式 → 传统客户端/服务端模式)

> 状态:**计划待批准**(本文档只描述方案,未实施)。
> 前序:[REFACTOR_PLAN.md](REFACTOR_PLAN.md)(web 单体加固)、[CHANGES.md](CHANGES.md)(分支基线以来的变更)。
> 约束继承:**执行侧全程零网络**(见 §8 网络边界);iOS / macOS 不在支持范围。

---

## 1. 目标与范围

| 项 | 现状 | 目标 |
| --- | --- | --- |
| 分支模型 | main + archived 的 frontend-dev / backend-dev 远端分支 | **仅 main 一条分支**(归档 tag 留底) |
| 交付形态 | 浏览器访问服务端页面(web 模式) | **原生客户端**(Windows / Linux / Android)连接服务端 |
| 服务端 | FastAPI:API + 前端静态托管 | FastAPI:**纯 API 服务**(静态托管下线) |
| 访问控制 | 共享口令 X-Access-Code | **用户账号登录**(用户名/口令 → 令牌) |
| 客户端 UI | Vue 3 SPA(浏览器) | **同一套 Vue 代码复用**为客户端 UI |

不在本期范围(明确不做):iOS/macOS 客户端;客户端自动更新;自助注册(账号由管理员发放);服务端简历云端同步(见 §6.4,列为可选后续)。

## 2. 现状基线:保留 / 废弃清单

**原样保留(C/S 化的最大资产)**:
- 服务端全部业务能力:简历生成(本地降级)、LLM 代理(SSE)、RAG 知识库(SQLite)、Word 导出、鉴权中间件骨架、限流、测试体系(后端 62 例)。
- 前端全部 UI:5 套简历模板、编辑/预览、agent 工作台、aiDeep 对话、safeMarked 安全渲染、Worker 流式解析。

**废弃 / 改造**:
| 项 | 处置 |
| --- | --- |
| 服务端静态托管 + SPA 回退(`app/main.py`) | 迁移期保留(兼容存量浏览器用户)→ 客户端全平台就绪后删除 |
| X-Access-Code 共享口令 | 替换为账号令牌;`accessCode.ts`/设置页口令输入删除 |
| `baseURL: "/api"` 相对路径(axios+worker) | 改为可配置的**服务端绝对地址** |
| 发行包中的 web 交付形态 | 服务端发行包保留(纯 API 化);新增三平台客户端安装包 |

## 3. 关键决策:客户端技术选型

**推荐:Tauri 2(Rust 壳 + 复用现有 Vue 前端)**

| 方案 | Windows | Linux | Android | UI 复用 | 包体积 | 主要代价 |
| --- | --- | --- | --- | --- | --- | --- |
| **Tauri 2(推荐)** | ✅ | ✅ | ✅ | **全量复用 Vue** | 5-15MB | 需 Rust 工具链;Android 需 SDK/NDK |
| Flutter | ✅ | ✅ | ✅ | ❌ 全量重写(Dart) | 中 | UI/模板/逻辑全部重做,风险最高 |
| Electron + Capacitor | ✅ | ✅ | ✅ | 全量复用 | 80-150MB(Electron) | 两套壳维护;桌面端臃肿 |

推荐理由:现有资产是 Vue 3 + Vite 前端,Tauri 直接把它打包成三平台客户端,**业务 UI 零重写**;`html2pdf.js`(浏览器端 PDF)、SSE Worker、marked 渲染在系统 WebView 中行为一致;Tauri 2 的移动端已稳定支持 Android。代价是引入 Rust 构建链——但它只存在于**客户端壳层**(数百行胶水代码),业务逻辑不碰 Rust。

> 若团队强烈倾向 Flutter(如后续想做 iOS),本文档的阶段划分不受影响,仅 §7 换为 Flutter 实现;但工期需 +5-8 人日(UI 全量重写)。

## 4. 目标仓库结构(单分支)

```text
main(唯一分支;远端 dev 分支删除,打 archive/* tag 留底)
├── backend/                  # 服务端(原样保留目录名,纯 API 化)
│   └── scripts/build_release.sh     # 服务端发行包(保留,去静态托管)
├── client/                   # 原 frontend/ 改名(git mv 保历史)
│   ├── src/                  #   现有 Vue 源码(客户端 UI)
│   ├── src-tauri/            #   新增:Tauri 壳(Rust 胶水 + 三平台打包配置)
│   └── tests/                #   vitest 保留
├── deploy/                   # 服务端部署脚本(保留);新增客户端发布物清单
├── docs/ 或根目录             # server-api.md(原 backend-api.md,新增鉴权章节)
└── CS_MIGRATION_PLAN.md      # 本文档;完成后并入 CHANGES.md 记录
```

## 5. 分阶段实施(总估算 10-12 人日)

### Phase A 单分支收敛(0.5 天)
1. `git tag archive/backend-dev origin/backend-dev`、`archive/frontend-dev`(留底);
2. **经确认后**删除两个远端 dev 分支(此前指示"暂不动",届时需你点头);
3. main 启用单分支工作流(沿用 TEAM_GUIDE 的 main 直开模式);
4. 验收:`git branch -a` 仅剩 main;tag 可随时恢复归档代码。

### Phase B 服务端 C/S 化(2-3 天)
1. **账号与令牌(零新依赖)**:
   - `users` 表(scrypt 哈希,`hashlib.scrypt` 标准库)+ `tokens` 表(随机 opaque 令牌,哈希落库,带过期/吊销);
   - `POST /api/auth/login {username,password}` → `{token, expiresAt, role}`;
   - 首次启动从环境变量引导创建管理员(`ADMIN_USERNAME`/`ADMIN_PASSWORD`);
   - 鉴权中间件从"共享口令比对"改为 `Authorization: Bearer <token>` 校验;401 语义不变;
   - 知识库管理接口收紧为 `role=admin`;生成/对话按**用户**限流(替代按 IP)。
2. **API 契约**:backend-api.md 增补鉴权章节;`/api/health` 保持免鉴权(客户端探活)。
3. **web 模式下线开关**:静态托管默认关闭(`SERVE_WEB=0`),迁移期可用环境变量临时打开;Phase F 物理删除。
4. 测试:新增 auth 用例(登录/过期/吊销/权限/限流按用户);调整静态托管用例;全量 pytest 绿。
5. 验收:curl 层面完成 登录→带令牌调用→错误口令 401→普通用户禁入知识库管理。

### Phase C 桌面客户端:Windows + Linux(3-4 天)
1. `git mv frontend client`;引入 `client/src-tauri`(tauri.conf.json 指向 Vue 构建产物);
2. **UI 适配(改动集中在 4 处)**:
   - 新增「服务器设置」:服务端地址(http://host:8000)首次启动引导配置,存 Tauri store;
   - `agentAPI.ts` baseURL 与 `aiWorker.ts` fetch 改为 `{serverUrl}/api`;
   - 登录页 + 令牌管理(替代 accessCode;401 全局拦截跳登录);
   - Word 下载改走 Tauri 保存对话框插件(Android 复用同一抽象)。
3. 打包:Windows(NSIS 安装包)/ Linux(deb + AppImage);免安装绿色版可选;
4. 验收:双平台安装包在干净系统安装 → 配服务端地址 → 登录 → 生成/预览/PDF/Word 全链路。

### Phase D Android 客户端(3-4 天)
1. Android Studio 工具链(SDK/NDK/JDK 17)+ Rust android targets(见 §8 网络边界);
2. `tauri android build` 产出 APK(Release 签名:生成 keystore,口令交由负责人保管,不入库);
3. 专项适配:明文 HTTP 局域网访问声明(cleartext)、移动端布局(已有 768/480 断点基础)、令牌安全存储、SSE 前台运行验证;
4. 验收:Android 10+ 真机两台(高/低端)安装 → 连接局域网服务端 → 全链路(生成/对话流式/导出)。

### Phase E 发布与文档(1 天)
1. 客户端发布物归档 `dist-release/`(win-setup.exe / linux.deb / app.apk + SHA256SUMS);
2. 文档:server-api.md(鉴权)、client/README(构建指南)、根 README 改写为 C/S 形态;
3. CHANGES.md 追加 C/S 化变更记录。

### Phase F web 模式退役(0.5 天)
1. 删除服务端静态托管与 SPA 回退代码 + 相关测试;
2. 删除 SERVE_WEB 开关;`views/setting` 中口令残留清理;
3. 全量回归(后端 pytest + 前端 vitest + 三平台冒烟);CHANGES/README 终版。

## 6. 关键设计说明

### 6.1 鉴权为什么用 opaque 令牌而非 JWT
吊销即删库一行、无需签名密钥管理、`secrets` + `hashlib.scrypt` 全标准库(**零新增依赖**,延续发行包零网络约束);单服务端实例下没有 JWT 的跨服务校验需求。

### 6.2 令牌有效期与续期
默认 7 天滑动过期(每次请求顺延);客户端 401 自动跳登录页。v1 不做 refresh token(时长足够,吊销能力强)。

### 6.3 多用户与知识库边界
v1 维持**单共享知识库**(管理员维护),生成时全体用户可检索——与学生简历场景一致,避免 v1 引入按用户隔离的索引复杂度;`meta.knowledgeHits` 不变。

### 6.4 简历数据归属
v1 简历草稿**继续存客户端本地**(Tauri webview 的 localStorage,按设备隔离,天然离线可用);
"换设备同步"列为后续可选(服务端加 resumes 表 + 同步接口,不影响本期)。

### 6.5 兼容窗口
迁移期服务端同时支持 web(可显式打开)与 C/S 两态;Phase F 后仅 C/S。存量浏览器用户需换装客户端——发布通告由负责人把握节奏。

## 7. 客户端 UI 改动明细(供排期评估)

| 文件/模块 | 改动 |
| --- | --- |
| `client/src/api/agentAPI.ts` | baseURL 从常量改为响应式 serverUrl;登录/令牌拦截器 |
| `client/src/worker/aiWorker.ts` | fetch 绝对地址 + 令牌头(自 postMessage 初始化参数取) |
| `utils/accessCode.ts` + 设置页口令块 | **删除**,替换为登录态模块(`utils/auth.ts`) |
| 新增 `views/login/` | 登录页 + 服务器地址引导(首次启动) |
| `store/useSettingsStore.ts` | 增加 serverUrl / 登录态;Tauri store 持久化 |
| Word 导出 `resumePreview.vue` | blob 锚点下载 → Tauri 保存对话框(桌面/移动统一封装) |
| `Header` 引导文案 | 按客户端语境改写 |
| 路由守卫 | 未登录 → /login;401 全局跳转 |

## 8. 网络边界(硬约束声明)

延续既有约束:**我的执行全程零网络**。本计划中唯一无法离线完成的环节与处置:

| 环节 | 需要联网的内容 | 处置 |
| --- | --- | --- |
| Tauri/Rust 工具链 | rustup、crates 依赖、平台链接器 | 在**构建机**上由团队一次性安装;`cargo vendor` 后可重复离线构建 |
| Android 工具链 | JDK17、Android SDK/NDK、Gradle 依赖 | 同上,构建机一次性下载;Gradle 离线缓存 |
| npm 依赖 | @tauri-apps/cli、@tauri-apps/api 等少量新增 | 一次 `npm install` 更新 lockfile,此后 `npm ci` 离线 |

即:**每次联网只为"首次搭建构建机"**;之后所有构建、打包、测试均可离线重复。哪些下载由谁执行(或明确授权我执行)请在批准本计划时一并指定。

## 9. 风险与对策

| 风险 | 对策 |
| --- | --- |
| Tauri 2 Android 成熟度 | 锁定版本;Phase D 先冒烟再铺开;真机矩阵覆盖高低端 |
| html2pdf 在低端安卓 WebView 性能 | Phase D 实测;必要时 PDF 改为"由服务端生成"(服务端已有 docx 链路可扩展) |
| SSE 在移动网络切换时断流 | Worker 已有超时;补自动重连与断点提示(小改动) |
| 多平台回归面扩大 | 每平台维护冒烟清单;后端测试保持全绿作为回归基线 |
| 局域网明文 HTTP | 内网场景可接受;文档标注生产建议走 HTTPS 反代(可选,不阻塞交付) |
| keystore/密钥保管 | 口令不入库;负责人线下保管;丢失即重签(客户端无强绑定) |

## 10. 总验收清单

- [ ] `git branch -a` 仅 main;archive tag 存在
- [ ] 服务端:登录/令牌/角色/按用户限流全通过;pytest 全绿;web 托管已移除
- [ ] Windows 安装包 + Linux deb/AppImage:干净系统安装即用,全链路可用
- [ ] Android APK:Android 10+ 真机安装即用,全链路可用(含 SSE 流式对话)
- [ ] 三平台共用同一套 Vue UI,业务功能与 web 时代对齐(生成/预览/PDF/Word/知识库[管理员])
- [ ] 发布物 + SHA256SUMS + 文档(server-api/client 构建/部署)齐备
