from pydantic import BaseModel, Field


class ProjectModuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="模块名称（同级唯一）")
    parent_id: int | None = Field(None, description="父模块 ID，不传或 null 表示根节点")
    sort_order: int | None = Field(
        None,
        description="同级排序，越小越前；不传则排在同级最后",
    )
    description: str | None = Field(None, max_length=2000, description="模块说明")


class ProjectModuleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    parent_id: int | None = Field(
        None,
        description="父模块；显式传 null 表示移到根下",
    )
    sort_order: int | None = None
    description: str | None = Field(None, max_length=2000)


class ProjectModuleOut(BaseModel):
    id: int
    project_id: int
    parent_id: int | None
    name: str
    sort_order: int
    description: str | None
    created_at: str
    updated_at: str
    children: list["ProjectModuleOut"] = Field(default_factory=list)


ProjectModuleOut.model_rebuild()


class ProjectModuleTreeData(BaseModel):
    """整棵模块树（仅根节点列表，子节点嵌套在 children）。"""

    roots: list[ProjectModuleOut]
