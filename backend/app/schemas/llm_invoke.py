"""单次 LLM 调用参数（不落库）。"""

from pydantic import BaseModel, ConfigDict, Field


class LlmInvokeConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    api_base: str = Field(..., min_length=1, description="OpenAI 兼容 Base，如 https://api.deepseek.com/v1")
    api_key: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
