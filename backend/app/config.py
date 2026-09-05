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
    # 留空 = 不启用鉴权;设置后所有 /api 业务接口要求 X-Access-Code 头
    access_code: str = ""
    # 每分钟每 IP 允许的生成/对话类请求数
    rate_limit_per_minute: int = 30

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
    # 数据目录(测试可覆盖;Docker 中挂载命名卷到 /app/data)
    # ------------------------------------------------------------------
    data_dir: Path = BASE_DIR / "data"

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
