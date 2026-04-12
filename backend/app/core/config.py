from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_skills_dir() -> Path:
    """backend/skills（相对本文件 backend/app/core/config.py）。"""
    return Path(__file__).resolve().parent.parent.parent / "skills"


class Settings(BaseSettings):
    app_name: str = "NexTest Platform API"
    environment: str = "dev"
    debug: bool = True
    api_prefix: str = "/api"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_days: int = 1
    jwt_refresh_token_expire_days: int = 7
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["*"]
    trusted_hosts: list[str] = ["*"]
    database_url: str = (
        "mysql+asyncmy://root:123456@127.0.0.1:3306/nextest"
        "?charset=utf8mb4"
    )

    # 智能体 / 用户输入（阶段一 2.2.1）
    agent_max_user_text_chars: int = 5000

    # 技能包目录（阶段一 2.2.2）；可通过环境变量 SKILLS_DIR 覆盖绝对路径
    skills_dir: Path = Field(default_factory=_default_skills_dir)

    # LLM 超时（智能体实际调用使用用户保存的模型配置；以下为遗留字段，可供脚本等使用）
    llm_api_base: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
