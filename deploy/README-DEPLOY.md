# AI 简历生成器 — 发行包离线部署说明

本包为**自包含发行包**:内嵌 Python 解释器、标准库、全部依赖、后端服务与前端页面。
目标机器**无需安装 Python、Node、数据库,全程零网络**。

## 包结构

```text
ai-resume-server-<平台>-<lite|full>/
├── runtime/          # 内嵌 Python(勿改动)
├── app/              # 后端服务(FastAPI)
├── static/           # 前端页面(由后端直接托管,单端口)
├── data/             # 种子数据;运行时生成的 kb.sqlite3 也在 data/ 下,升级时保留即可
├── deploy/           # 部署脚本
├── .env.example      # 配置模板
└── README-DEPLOY.md  # 本文件
```

`lite` 与 `full` 的唯一区别:full 含向量语义检索(嵌入模型栈,约 +1.1GB);
lite 的 RAG 自动降级为关键词检索,其余功能完全一致。

## Linux 部署(systemd,推荐)

```bash
tar -xzf ai-resume-server-linux-x86_64-lite.tar.gz
cd ai-resume-server-linux-x86_64-lite

# 1. 配置(必须)
cp .env.example .env
vi .env        # 填 LLM_API_URL / LLM_API_KEY;建议设置 ACCESS_CODE 访问口令

# 2. 安装并启动(需要 root;自动创建 ai-resume 用户与 systemd 服务)
sudo ./deploy/install.sh          # PORT=9000 sudo ./deploy/install.sh 可改端口

# 3. 验证
curl http://127.0.0.1:8000/api/health
# 浏览器访问 http://<服务器IP>:8000
```

常用命令:

```bash
sudo systemctl status ai-resume      # 状态
sudo systemctl restart ai-resume     # 重启
journalctl -u ai-resume -f           # 日志
./deploy/stop.sh / status.sh         # 免 systemd 环境
```

无 root 权限时,install.sh 自动降级为用户级安装(`~/.local/share/ai-resume`),
用 `./deploy/start.sh` 前台启动(建议配合 tmux)。

## Windows 部署

```powershell
Expand-Archive ai-resume-server-windows-x86_64-lite.zip
cd ai-resume-server-windows-x86_64-lite
# 编辑 .env(复制 .env.example)
cd deploy
powershell -ExecutionPolicy Bypass -File install.ps1     # 注册计划任务并启动
```

卸载:`powershell -File uninstall.ps1`。

## 升级与数据

- 升级 = 备份 `data/` 目录 → 解压新包覆盖 → 还原 `data/` 与 `.env` → 重启服务。
- 知识库数据在 `data/kb.sqlite3`(SQLite,跨平台通用)。

## 端口与安全

| 配置(.env)   | 说明                                        |
| -------------- | ------------------------------------------- |
| `LLM_API_URL`  | OpenAI 兼容接口地址(DashScope/DeepSeek 等) |
| `LLM_API_KEY`  | 模型密钥(服务端保管,前端不接触)          |
| `ACCESS_CODE`  | 访问口令;设置后前端「网站配置」页需填入     |
| `PORT`/`HOST`  | 启动参数(start.sh/systemd 读取)            |

建议生产环境务必设置 `ACCESS_CODE`,避免模型密钥被滥用。

## 已知平台边界

- linux 包在 x86_64 + glibc 2.31+ 的主流发行版(Debian 11+/Ubuntu 20.04+/RHEL 9+)可直接运行;
  其他架构/平台请用对应机器执行 `backend/scripts/build_release.sh`(或 Windows 的
  `build_release.ps1`)在本平台构建,流程完全一致。
