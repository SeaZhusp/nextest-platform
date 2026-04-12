"""
智能体对话请求 / 用户输入片段模型（阶段一 2.2.1）。

- 推荐使用 `parts` 承载多模态预留；亦可单独传 `content`（等价于单段 text）。
- 一期仅允许 `type=text` 的片段。
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Self, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings
from app.schemas.testcase import TestCaseItem


class TextPart(BaseModel):
    """文本片段（一期唯一可用）。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    text: str = Field(..., min_length=1, description="用户输入的纯文本")


class ImageUrlPart(BaseModel):
    """图片 URL（预留，一期拒绝）。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["image_url"] = "image_url"
    url: str
    mime_type: str | None = None


class ImageBase64Part(BaseModel):
    """Base64 图片（预留，一期拒绝）。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["image_base64"] = "image_base64"
    data: str
    mime_type: str | None = None


class AudioUrlPart(BaseModel):
    """音频 URL（预留，一期拒绝）。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["audio_url"] = "audio_url"
    url: str


class FileRefPart(BaseModel):
    """对象存储文件引用（预留，一期拒绝）；二期可与文档上传对齐。"""

    model_config = ConfigDict(extra="forbid")

    type: Literal["file_ref"] = "file_ref"
    attachment_id: str
    storage_key: str | None = None


MessagePart = Annotated[
    Union[TextPart, ImageUrlPart, ImageBase64Part, AudioUrlPart, FileRefPart],
    Field(discriminator="type"),
]


class AgentChatRequest(BaseModel):
    """
    对话请求体。

    - `parts` 与 `content` 二选一；同时提供则校验失败。
    - 一期：所有片段必须为 TextPart，且合并文本长度 ≤ 配置上限。
    """

    model_config = ConfigDict(extra="forbid")

    session_id: UUID | None = Field(
        default=None,
        description="已有会话 ID（与 /agent/chat 或 /chat/stream 返回的 session_id 一致）；不传则创建新会话并持久化",
    )
    skill_id: str | None = Field(
        default="test_case_gen",
        max_length=64,
        description="技能 ID，默认测试用例生成",
    )
    parts: list[MessagePart] | None = Field(
        default=None,
        description="消息片段列表（推荐）",
    )
    content: str | None = Field(
        default=None,
        description="便捷字段：等价于单段 type=text；与 parts 互斥",
    )
    llm_profile_id: int | None = Field(
        default=None,
        description="用户自备大模型配置 ID；不传则技能不调用 LLM（如返回模板用例）",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度，随请求传入并写入本轮 LLM 调用",
    )

    @model_validator(mode="before")
    @classmethod
    def merge_content_into_parts(cls, data: Any) -> Any:
        """将 content 转为单段 text parts（before 阶段处理，避免与 __init__ 关键字参数冲突）。"""
        if not isinstance(data, dict):
            return data
        content = data.get("content")
        parts = data.get("parts")
        if content is not None and parts is not None:
            raise ValueError("不能同时提供 content 与 parts，请只使用其中一种")
        if content is not None:
            text = str(content).strip()
            if not text:
                raise ValueError("content 不能为空")
            return {
                **data,
                "parts": [TextPart(text=text)],
                "content": None,
            }
        return data

    @model_validator(mode="after")
    def validate_phase1_text_only_and_length(self) -> Self:
        if self.parts is None:
            raise ValueError("必须提供 parts 或 content")

        parts = list(self.parts)
        if not parts:
            raise ValueError("parts 不能为空")

        for p in parts:
            if not isinstance(p, TextPart):
                raise ValueError(
                    f"当前阶段仅支持文本输入，不支持片段类型: {getattr(p, 'type', type(p))}"
                )

        total = sum(len(p.text) for p in parts)
        if total > settings.agent_max_user_text_chars:
            raise ValueError(
                f"文本总长度不能超过 {settings.agent_max_user_text_chars} 个字符（当前 {total}）"
            )

        return self


class AgentChatAckData(BaseModel):
    """对话一轮应答：回显输入 + 技能产出用例（2.2.2 由技能填充）。"""

    session_id: str
    skill_id: str
    parts: list[TextPart]
    test_cases: list[TestCaseItem] = Field(
        default_factory=list,
        description="由 skill 执行生成的结构化用例；LLM 接入前可为模板/占位数据",
    )


class AgentHistoryMessageOut(BaseModel):
    """会话单条消息（2.2.4 查询）。"""

    model_config = ConfigDict(extra="forbid")

    id: int
    role: Literal["user", "assistant"]
    content_json: dict[str, Any]
    created_at: str


class AgentSessionMessagesData(BaseModel):
    """某会话下全部消息（按时间升序）。"""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    title: str = Field(default="", description="会话展示名")
    skill_id: str = Field(default="", description="当前技能 ID")
    messages: list[AgentHistoryMessageOut]


class AgentSessionSummaryOut(BaseModel):
    """历史会话列表项。"""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    title: str
    skill_id: str
    updated_at: str


class AgentSessionListData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AgentSessionSummaryOut]
    total: int
    page: int
    size: int


class AgentSessionRenameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200, description="新标题")
