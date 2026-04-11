from pydantic import BaseModel, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=4, max_length=50)
    nickname: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    password_confirm: str = Field(min_length=6, max_length=100)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()

    @field_validator("nickname", mode="before")
    @classmethod
    def normalize_nickname(cls, v: object) -> str:
        if v is None:
            raise ValueError("昵称不能为空")
        if not isinstance(v, str):
            raise ValueError("昵称须为字符串")
        s = v.strip()
        if not s:
            raise ValueError("昵称不能为空")
        if len(s) > 50:
            raise ValueError("昵称最多 50 个字符")
        return s

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            raise ValueError("两次输入的密码不一致")
        return self


class UserPublic(BaseModel):
    id: int
    username: str
    email: str | None = None
    nickname: str | None = None
    phone: str | None = None
    user_type: str
    is_active: bool
    last_login_at: str | None = None
    created_at: str
    updated_at: str


class AuthSessionData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_info: UserPublic


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPairData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
