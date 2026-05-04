from typing import Literal

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="项目名称")
    description: str | None = Field(None, max_length=200, description="项目描述")


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50, description="项目名称")
    description: str | None = Field(None, max_length=200, description="项目描述；传空字符串可清空（见服务层约定）")


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    owner_name: str = Field(..., description="负责人展示名：优先昵称，否则用户名")
    my_role: str = Field(
        ...,
        description="当前用户在项目中的角色：owner / leader / tester",
    )
    created_at: str
    updated_at: str


class ProjectListData(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    size: int


class ProjectMemberOut(BaseModel):
    user_id: int
    username: str
    nickname: str | None
    role: str


class ProjectMemberListData(BaseModel):
    items: list[ProjectMemberOut]


class ProjectMemberAdd(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="被添加用户的登录名")
    role: Literal["leader", "tester"] = Field(..., description="成员角色，不可通过此处设为 owner")
