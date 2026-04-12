from pydantic import BaseModel, Field, model_validator


class UserLlmProfileCreate(BaseModel):
    provider: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="模型提供商标识：openai/deepseek/qwen/zhipu/anthropic/other",
    )
    display_name: str = Field(default="", max_length=128, description="展示名称，可空则默认用模型名")
    api_base: str = Field(..., min_length=1, max_length=512, description="OpenAI 兼容 API Base")
    model_name: str = Field(..., min_length=1, max_length=128, description="模型名")
    api_key: str = Field(..., min_length=1, max_length=2048, description="API Key")
    is_active: bool = Field(default=True, description="是否启用")

    @model_validator(mode="after")
    def default_display_name(self) -> "UserLlmProfileCreate":
        if not (self.display_name or "").strip():
            object.__setattr__(self, "display_name", self.model_name.strip())
        return self


class UserLlmProfileUpdate(BaseModel):
    provider: str | None = Field(default=None, min_length=1, max_length=32)
    display_name: str | None = Field(default=None, max_length=128)
    api_base: str | None = Field(default=None, min_length=1, max_length=512)
    model_name: str | None = Field(default=None, min_length=1, max_length=128)
    api_key: str | None = Field(default=None, min_length=1, max_length=2048)
    is_active: bool | None = None


class UserLlmProfileOut(BaseModel):
    id: int
    provider: str
    display_name: str
    api_base: str
    model_name: str
    key_last4: str
    api_key_masked: str
    is_active: bool


class UserLlmProfileDetailOut(UserLlmProfileOut):
    """详情（含明文 Key，仅归属用户可拉取）"""

    api_key: str


class UserLlmProfileListResponse(BaseModel):
    items: list[UserLlmProfileOut]


class LlmConnectionTestRequest(BaseModel):
    """未保存配置时的连通性测试。"""

    api_base: str = Field(..., min_length=1, max_length=512)
    model_name: str = Field(..., min_length=1, max_length=128)
    api_key: str = Field(..., min_length=1, max_length=2048)


class LlmConnectionTestResult(BaseModel):
    ok: bool = True
    message: str = "连接成功"


class UserLlmProfileActivePatch(BaseModel):
    """启用 / 禁用"""

    is_active: bool
