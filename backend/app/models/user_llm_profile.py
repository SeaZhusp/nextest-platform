from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ModelBase


class UserLlmProfile(ModelBase):
    """用户自备大模型配置（API Key 明文落库，列表接口不返回 Key）。"""

    __tablename__ = "user_llm_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户 ID",
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="other",
        comment="模型提供商：openai/deepseek/qwen/zhipu/anthropic/other",
    )
    display_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="展示名称（下拉中显示）",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用",
    )
    api_base: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="OpenAI 兼容 API Base，如 https://api.deepseek.com/v1",
    )
    model_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="模型名，如 deepseek-chat",
    )
    api_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="API Key",
    )
    key_last4: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="",
        comment="Key 后若干位展示用",
    )
