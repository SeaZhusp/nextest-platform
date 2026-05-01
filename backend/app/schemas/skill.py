"""技能相关 schema：运行时注册表元数据。"""

from pydantic import BaseModel, ConfigDict, Field


class SkillMetaOut(BaseModel):
    """GET /skills：已加载技能包元数据（与 backend/skills 一致）。"""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(..., description="技能唯一 ID，与目录名一致")
    name: str
    version: str
    description: str = ""
    default_render: str = Field(default="table", description="默认渲染模式")
    render_modes: list[str] = Field(default_factory=lambda: ["table"], description="允许的渲染模式列表")
