from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_skills_dir() -> Path:
    """backend/skills（相对本文件 backend/app/core/config.py）。"""
    return Path(__file__).resolve().parent.parent.parent / "skills"


class Settings(BaseSettings):
    # App
    app_name: str = "NexTest Platform API"
    environment: str = "dev"
    debug: bool = True
    api_prefix: str = "/api"

    # Auth / Token
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_days: int = 1
    jwt_refresh_token_expire_days: int = 7
    access_token_expire_minutes: int = 60

    # Web
    cors_origins: list[str] = ["*"]
    trusted_hosts: list[str] = ["*"]

    # Database
    database_url: str = (
        "mysql+asyncmy://root:123456@127.0.0.1:3306/nextest"
        "?charset=utf8mb4"
    )

    # 智能体 / 用户输入（阶段一 2.2.1）
    agent_max_user_text_chars: int = 5000
    # 会话记忆：进入 LLM 的最近对话轮数（阶段一 2.2.4 F1.12，一轮 = user + assistant）
    agent_context_max_rounds: int = 6
    # 模型返回 JSON 数组时允许的最少条数（默认 1；若需与路线图 F1.7 对齐可改为 3）
    agent_min_generated_test_cases: int = Field(default=1, ge=1, le=100)
    # 轻量计划执行策略
    agent_max_plan_steps: int = Field(default=8, ge=1, le=100)
    agent_max_tool_calls: int = Field(default=4, ge=1, le=100)
    agent_step_timeout_seconds: float = Field(default=30.0, gt=0.0, le=300.0)
    agent_step_timeout_seconds_test_case_gen: float = Field(default=60.0, gt=0.0, le=600.0)
    agent_step_retry_times: int = Field(default=1, ge=0, le=5)
    agent_total_timeout_seconds: float = Field(default=90.0, gt=0.0, le=1800.0)
    agent_policy_overrides_json: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON overrides for execution policy by skill/role/member_level.",
    )

    # 技能包目录（阶段一 2.2.2）；可通过环境变量 SKILLS_DIR 覆盖绝对路径
    skills_dir: Path = Field(default_factory=_default_skills_dir)

    # LLM（底层 client 超时）
    llm_timeout_seconds: float = 120.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
