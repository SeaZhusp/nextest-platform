from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ModelBase


class Skill(ModelBase):
    """技能目录（手动维护）；上架后出现在技能广场。执行仍以磁盘技能包 + SkillRegistry 为准。"""

    __tablename__ = "skills"

    skill_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="与 backend/skills/<skill_id> 一致",
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="展示名称")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="", comment="列表短描述")
    capability_tags: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="核心能力标签 JSON 数组",
    )
    icon_key: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="图标 key")
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="上架：在技能广场展示；下架仅管理端可见",
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序，越小越前")
    use_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="使用次数：智能体以该技能发起新会话时 +1",
    )
