from sqlalchemy import BigInteger, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ModelBase


class AgentSession(ModelBase):
    """智能体会话（2.2.4：对外以 session_uuid 标识，等价于路线图中的 sessions）。"""

    __tablename__ = "agent_sessions"

    session_uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        comment="对外会话 ID（UUID 字符串）",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属用户",
    )
    skill_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="当前技能 ID",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="会话名称",
    )

    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="session",
    )


class AgentMessage(ModelBase):
    """会话消息（用户片段 JSON + 助手全文等，等价于路线图中的 messages）。"""

    __tablename__ = "agent_messages"

    agent_session_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属会话主键",
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="user / assistant",
    )
    content_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="用户：{parts:[...]}；助手：{text: 模型原文或等价 JSON 文本}",
    )

    session: Mapped["AgentSession"] = relationship("AgentSession", back_populates="messages")
