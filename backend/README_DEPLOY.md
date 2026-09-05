# 后端部署说明(单机/本地开发参考)

> **生产部署请使用自包含发行包**:在仓库根目录执行 `backend/scripts/build_release.sh`
> 打包,目标机解压后运行 `deploy/install.sh` 即可,零安装、零网络、零 Node。
> 详见根 README 与 [deploy/README-DEPLOY.md](../deploy/README-DEPLOY.md)。
> 本文档仅覆盖后端源码方式运行(开发/调试)。

## 环境要求

- Python 3.11+(自建虚拟环境,不要装进系统)
- `sentence-transformers` 的 BGE 模型在应用启动时后台预热;首次会自动下载(约 100MB,
  可用 `HF_ENDPOINT` 指向镜像加速;发行包 full 档已内嵌,离线可用)

## 1. 安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 环境变量

在 `backend/.env`(或仓库根目录,`pydantic-settings` 会读取工作目录下 `.env`):

```env
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_API_KEY=your-api-key-here
LLM_MODEL=qwen-plus
ACCESS_CODE=            # 生产环境建议设置;设置后业务接口要求 X-Access-Code 头
```

完整变量清单见根目录 `.env.example`。

## 3. 开发模式

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 生产/发行包内为单 uvicorn 实例:阻塞操作已全部进线程池,单进程即可承载并发;
> 多进程会重复加载嵌入模型且与 SQLite 单写者语义不匹配,**不要**使用 `--workers`。

## 4. 测试

```bash
pytest                 # 62+ 用例(纯函数/SSE/中间件/知识库/静态托管/API 冒烟)
python test_api.py     # API 冒烟脚本(需服务已启动,默认打 127.0.0.1:8000)
```

## 5. 运行时说明

- 知识库数据:`data/kb.sqlite3`(SQLite WAL),旧版 JSON 启动时自动迁移
- 前端页面:若存在 `frontend/dist`(或发行包 `static/`),后端直接托管,单端口 8000
- 嵌入模型不可用时(如 lite 包),向量检索自动降级为关键词检索,接口行为不变
