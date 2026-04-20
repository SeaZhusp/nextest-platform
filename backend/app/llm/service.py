from typing import Any

from app.llm.client import (
    chat_completion_content,
    chat_completion_stream_deltas,
)
from app.schemas.llm_invoke import LlmInvokeConfig


async def chat(
        messages: list[dict[str, Any]],
        *,
        config: LlmInvokeConfig,
        stream: bool = False,
):
    if stream:
        return chat_completion_stream_deltas(messages, config=config)
    return await chat_completion_content(messages, config=config)
