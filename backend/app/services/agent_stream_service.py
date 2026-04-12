"""智能体 SSE 流（2.2.3 F1.9 / F1.10）。"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import uuid4

from app.schemas.agent import AgentChatRequest, TextPart
from app.services.skill.base import SkillContext
from app.services.skill.executor import execute_skill
from app.schemas.llm_invoke import LlmInvokeConfig
from app.services.test_case_gen_llm import (
    parse_test_cases_from_llm_text,
    stream_llm_text_deltas,
    template_test_cases,
)

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


async def iter_agent_chat_sse(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
) -> AsyncIterator[bytes]:
    """
    SSE 字节流：event + JSON data。

    - token: {"text": string}
    - done: {session_id, skill_id, parts, test_cases, used_template?}
    - error: {message, details?}
    """
    assert payload.parts is not None
    session_id = payload.session_id or uuid4()
    sid = str(session_id)
    user_text = "\n".join(p.text for p in payload.parts)
    skill_id = (payload.skill_id or "test_case_gen").strip() or "test_case_gen"
    parts_dump = [p.model_dump() for p in cast(list[TextPart], payload.parts)]

    try:
        if skill_id != "test_case_gen":
            ctx = SkillContext(
                user_text=user_text,
                session_id=sid,
                skill_id=skill_id,
                llm_config=llm_config,
            )
            result = await execute_skill(skill_id, ctx)
            yield _sse(
                "done",
                {
                    "session_id": sid,
                    "skill_id": skill_id,
                    "parts": parts_dump,
                    "test_cases": [c.model_dump() for c in result.test_cases],
                    "used_template": True,
                },
            )
            return

        if llm_config is None:
            cases = template_test_cases()
            yield _sse(
                "done",
                {
                    "session_id": sid,
                    "skill_id": skill_id,
                    "parts": parts_dump,
                    "test_cases": [c.model_dump() for c in cases],
                    "used_template": True,
                },
            )
            return

        chunks: list[str] = []
        async for delta in stream_llm_text_deltas(user_text, llm_config):
            chunks.append(delta)
            yield _sse("token", {"text": delta})

        full = "".join(chunks)
        try:
            cases = parse_test_cases_from_llm_text(full)
        except Exception as e:
            logger.warning("流式结束后解析 JSON 失败: %s", e)
            yield _sse(
                "error",
                {
                    "message": "模型输出不是合法用例 JSON，请缩短需求或重试",
                    "details": {"reason": str(e)},
                },
            )
            return

        yield _sse(
            "done",
            {
                "session_id": sid,
                "skill_id": skill_id,
                "parts": parts_dump,
                "test_cases": [c.model_dump() for c in cases],
                "used_template": False,
            },
        )
    except Exception as e:
        logger.exception("SSE 编排异常")
        yield _sse("error", {"message": str(e) or "流式生成失败"})
