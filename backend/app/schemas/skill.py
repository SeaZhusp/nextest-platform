"""技能相关 schema：`SkillMetaOut` 为运行时注册表；其余为技能目录 DB（广场 + 管理端）。"""

from pydantic import BaseModel, ConfigDict, Field


class SkillMetaOut(BaseModel):
    """GET /skills：已加载技能包元数据（与 backend/skills 一致）。"""

    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(..., description="技能唯一 ID，与目录名一致")
    name: str
    version: str
    description: str = ""


# --- 技能目录表 `skills`（手动维护） ---


class SkillCreate(BaseModel):
    skill_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="", max_length=8000)
    capability_tags: list[str] = Field(default_factory=list)
    icon_key: str | None = Field(None, max_length=64)
    is_published: bool = True
    sort_order: int = 0


class SkillUpdate(BaseModel):
    skill_id: str | None = Field(None, min_length=1, max_length=64)
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    capability_tags: list[str] | None = None
    icon_key: str | None = None
    is_published: bool | None = None
    sort_order: int | None = None


class SkillPlazaItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: str
    name: str
    description: str
    capability_tags: list[str] = Field(default_factory=list)
    icon_key: str | None = None
    is_published: bool
    sort_order: int
    use_count: int
    runtime_available: bool = Field(
        ...,
        description="当前进程 SkillRegistry 是否已加载该 skill_id",
    )


class SkillPlazaDetailOut(SkillPlazaItemOut):
    """详情接口与列表项字段一致（无额外长文）。"""


class SkillPlazaListData(BaseModel):
    items: list[SkillPlazaItemOut]
    total: int
    page: int
    size: int


class SkillAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: str
    name: str
    description: str
    capability_tags: list[str] = Field(default_factory=list)
    icon_key: str | None = None
    is_published: bool
    sort_order: int
    use_count: int
    runtime_available: bool
    created_at: str
    updated_at: str


class SkillAdminListData(BaseModel):
    items: list[SkillAdminOut]
    total: int
    page: int
    size: int
