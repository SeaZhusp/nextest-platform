from pydantic import BaseModel, Field, field_validator, model_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    password_confirm: str = Field(min_length=6, max_length=100)

    @field_validator("username")
    @classmethod
    def strip_username(cls, v: str) -> str:
        return v.strip()

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
    role: str
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
