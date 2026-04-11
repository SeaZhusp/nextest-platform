from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str | None
    email: str | None
    phone: str | None
    user_type: str
    is_active: bool
    last_login_at: str | None
    created_at: str
    updated_at: str


class UserListData(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    size: int


class UserActiveRequest(BaseModel):
    is_active: bool
