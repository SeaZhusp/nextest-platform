"""会话 SSE 流（2.2.3 F1.9 / F1.10 + 2.2.4 会话记忆）。"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any, cast

from app.db.session import session_factory
from app.schemas.agent import AgentChatRequest, TextPart
from app.schemas.llm_invoke import LlmInvokeConfig
from app.services.agent.memory_service import (
    assistant_persist_text_from_result,
    build_llm_messages_for_test_case_gen,
    load_prior_messages,
    resolve_agent_session,
    save_assistant_message,
    save_user_message,
)
from app.services.skill.base import SkillContext
from app.services.skill.executor import execute_skill
from app.services.test_case_gen_llm import (
    parse_test_cases_from_llm_text,
    stream_llm_text_deltas,
    template_test_cases,
)

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


async def iter_conversation_chat_sse(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
    *,
    user_id: int,
) -> AsyncIterator[bytes]:
    assert payload.parts is not None
    skill_id = (payload.skill_id or "test_case_gen").strip() or "test_case_gen"
    parts = cast(list[TextPart], payload.parts)
    parts_dump = [p.model_dump() for p in parts]
    user_text = "\n".join(p.text for p in parts)

    async with session_factory() as db:
        resolved = await resolve_agent_session(
            db,
            user_id=user_id,
            session_id=payload.session_id,
            skill_id=skill_id,
            parts=parts,
        )
        prior = await load_prior_messages(db, agent_session_id=resolved.row.id)
        await save_user_message(db, agent_session_id=resolved.row.id, parts=parts)
        await db.commit()

        sid = str(resolved.conversation_uuid)

        try:
            if skill_id != "test_case_gen":
                ctx = SkillContext(
                    user_text=user_text,
                    session_id=sid,
                    skill_id=skill_id,
                    llm_config=llm_config,
                )
                result = await execute_skill(skill_id, ctx)
                dump = [c.model_dump() for c in result.test_cases]
                asst = assistant_persist_text_from_result(
                    llm_raw_output=result.llm_raw_output,
                    test_cases_dump=dump,
                )
                await save_assistant_message(db, agent_session_id=resolved.row.id, text=asst)
                await db.commit()
                yield _sse(
                    "done",
                    {
                        "session_id": sid,
                        "skill_id": skill_id,
                        "parts": parts_dump,
                        "test_cases": dump,
                        "used_template": True,
                    },
                )
                return

            if llm_config is None:
                cases = template_test_cases()
                dump = [c.model_dump() for c in cases]
                asst = assistant_persist_text_from_result(
                    llm_raw_output=None,
                    test_cases_dump=dump,
                )
                await save_assistant_message(db, agent_session_id=resolved.row.id, text=asst)
                await db.commit()
                yield _sse(
                    "done",
                    {
                        "session_id": sid,
                        "skill_id": skill_id,
                        "parts": parts_dump,
                        "test_cases": dump,
                        "used_template": True,
                    },
                )
                return

            llm_messages = build_llm_messages_for_test_case_gen(
                prior_messages=prior,
                current_user_text=user_text,
            )

            chunks: list[str] = []
            async for delta in stream_llm_text_deltas(
                user_text,
                llm_config,
                chat_messages=llm_messages,
            ):
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

            dump = [c.model_dump() for c in cases]
            await save_assistant_message(db, agent_session_id=resolved.row.id, text=full)
            await db.commit()

            yield _sse(
                "done",
                {
                    "session_id": sid,
                    "skill_id": skill_id,
                    "parts": parts_dump,
                    "test_cases": dump,
                    "used_template": False,
                },
            )
        except Exception as e:
            logger.exception("SSE 编排异常")
            yield _sse("error", {"message": str(e) or "流式生成失败"})
