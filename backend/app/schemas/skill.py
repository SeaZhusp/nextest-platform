"""技能元数据（列表 API）。"""

from pydantic import BaseModel, ConfigDict, Field


class SkillMetaOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(..., description="技能唯一 ID，与目录名一致")
    name: str
    version: str
    description: str = ""
