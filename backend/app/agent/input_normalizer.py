"""Normalize incoming agent message parts into a stable internal shape."""

from __future__ import annotations

from app.agent.types import InputArtifact, NormalizedAgentInput
from app.schemas.agent import (
    AgentChatRequest,
    AudioUrlPart,
    FileRefPart,
    ImageBase64Part,
    ImageUrlPart,
    MessagePart,
    TextPart,
)


def _artifact_from_part(part: MessagePart) -> InputArtifact:
    if isinstance(part, TextPart):
        return InputArtifact(type="text", content=part.text, metadata={})
    if isinstance(part, ImageUrlPart):
        return InputArtifact(
            type="image_url",
            content=part.url,
            metadata={"mime_type": part.mime_type},
        )
    if isinstance(part, ImageBase64Part):
        return InputArtifact(
            type="image_base64",
            content=part.data,
            metadata={"mime_type": part.mime_type},
        )
    if isinstance(part, AudioUrlPart):
        return InputArtifact(type="audio_url", content=part.url, metadata={})
    if isinstance(part, FileRefPart):
        return InputArtifact(
            type="file_ref",
            content=part.attachment_id,
            metadata={"storage_key": part.storage_key},
        )
    raise ValueError(f"未知输入片段类型: {type(part)}")


def normalize_agent_input(payload: AgentChatRequest) -> NormalizedAgentInput:
    # payload is already validated by AgentChatRequest model validators.
    parts = payload.parts or []
    skill_id = payload.skill_id.strip()
    text_parts: list[TextPart] = [p for p in parts if isinstance(p, TextPart)]
    user_text = "\n".join(p.text for p in text_parts).strip()
    artifacts = [_artifact_from_part(p) for p in parts]

    return NormalizedAgentInput(
        skill_id=skill_id,
        user_text=user_text,
        text_parts=text_parts,
        artifacts=artifacts,
    )

