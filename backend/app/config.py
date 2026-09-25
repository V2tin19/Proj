"""Configuration loaded from environment variables (pydantic-settings).

All timeouts, limits and paths live here so routes/services never hardcode magic numbers.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # LLM(支持 OpenAI SDK 风格的别名变量)
    # ------------------------------------------------------------------
    llm_api_url: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_URL", "OPENAI_COMPATIBLE_API_URL"),
    )
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
    )
    llm_model: str = Field(
        default="qwen-plus",
        validation_alias=AliasChoices("LLM_MODEL", "OPENAI_MODEL"),
    )
    chat_temperature: float = 0.7

    # ------------------------------------------------------------------
    # 访问控制 / 限流
    # ------------------------------------------------------------------
    # required = 商业模式:除 health/auth 外所有接口需 Bearer 令牌(或旧口令兼容);
    # optional = 迁移期兼容:允许匿名访问(配合旧 X-Access-Code 门禁使用)
    auth_mode: str = "required"
    # [legacy 迁移期] 旧版共享口令;设置后仍接受 X-Access-Code 头(Phase F 移除)
    access_code: str = ""
    # 每分钟每 IP 允许的生成/对话类请求数
    rate_limit_per_minute: int = 30

    # ------------------------------------------------------------------
    # 账号体系(自助注册)
    # ------------------------------------------------------------------
    registration_mode: str = "open"  # open|invite|closed
    invite_code: str = ""            # registration_mode=invite 时必填
    admin_username: str = ""         # 首次启动引导创建运营者账号
    admin_password: str = ""
    token_ttl_days: int = 7
    lockout_threshold: int = 5       # 连续失败 N 次锁定
    lockout_minutes: int = 15

    # ------------------------------------------------------------------
    # 超时(秒)
    # ------------------------------------------------------------------
    llm_timeout: float = 55.0   # 生成简历的 LLM 调用
    chat_timeout: float = 120.0  # SSE 对话上游

    # ------------------------------------------------------------------
    # 服务
    # ------------------------------------------------------------------
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ------------------------------------------------------------------
    # 数据目录(测试可覆盖;发行包中为包根下 data/)
    # ------------------------------------------------------------------
    data_dir: Path = BASE_DIR / "data"

    # ------------------------------------------------------------------
    # 前端静态产物目录(留空自动探测:发行包 static/ 或开发仓 frontend/dist)
    # ------------------------------------------------------------------
    static_dir: str = ""

    @property
    def resolved_static_dir(self) -> Path | None:
        if self.static_dir:
            path = Path(self.static_dir)
            return path if path.is_dir() else None
        for candidate in (BASE_DIR / "static", BASE_DIR.parent / "frontend" / "dist"):
            if (candidate / "index.html").is_file():
                return candidate
        return None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def prompt_templates_path(self) -> Path:
        return self.data_dir / "prompt-templates.json"

    @property
    def kb_db_path(self) -> Path:
        return self.data_dir / "kb.sqlite3"

    @property
    def legacy_kb_json_path(self) -> Path:
        return self.data_dir / "knowledge-base.json"


settings = Settings()
