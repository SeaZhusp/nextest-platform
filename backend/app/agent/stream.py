"""Agent SSE 流：流式执行与会话记忆持久化。"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

from app.agent.executor import execute_plan_steps
from app.agent.input_normalizer import normalize_agent_input
from app.agent.memory_service import (
    assistant_persist_text_from_result,
    build_llm_messages_for_test_case_gen,
    load_prior_messages,
    resolve_agent_session,
    save_assistant_message,
    save_user_message,
)
from app.agent.planner import plan_for_chat
from app.agent.policies import resolve_execution_policy
from app.agent.types import ExecutionResult, ExecutionTrace
from app.api.deps.auth import CurrentUser
from app.db.session import session_factory
from app.schemas.agent import AgentChatRequest
from app.schemas.llm_invoke import LlmInvokeConfig
from app.contracts.skill import SkillContext
from app.agent.skills.executor import execute_skill
from app.agent.skills.structured_generation import (
    build_messages,
    default_prompt_vars,
    parse_items,
    render_prompt,
    stream_llm_text,
)
from app.agent.skills.config import load_skill_config
from app.schemas.testcase import TestCaseItem

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict[str, Any]) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def _trace_dump(exec_result: ExecutionResult) -> list[dict[str, Any]]:
    return [t.model_dump() for t in exec_result.traces]


async def iter_conversation_chat_sse(
    payload: AgentChatRequest,
    llm_config: LlmInvokeConfig | None,
    *,
    user_id: int,
    user: CurrentUser | None = None,
) -> AsyncIterator[bytes]:
    current_step = ""
    step_names: dict[str, str] = {}

    def step_payload(step_id: str, label: str, status: str) -> dict[str, Any]:
        nonlocal current_step
        current_step = step_id
        return {"step_id": step_id, "label": label, "status": status}

    normalized = normalize_agent_input(payload)
    skill_id = normalized.skill_id
    parts = normalized.text_parts
    parts_dump = [p.model_dump() for p in parts]
    user_text = normalized.user_text

    async with session_factory() as db:
        resolved = await resolve_agent_session(
            db,
            user_id=user_id,
            session_id=payload.session_id,
            skill_id=skill_id,
            parts=parts,
        )
        prior = await load_prior_messages(db, conversation_id=resolved.row.id)
        await save_user_message(db, conversation_id=resolved.row.id, parts=parts)
        await db.commit()

        sid = str(resolved.conversation_uuid)

        try:
            yield _sse("step", step_payload("plan", "plan", "running"))
            steps = plan_for_chat(normalized)
            step_names = {s.step_id: (s.name or s.step_id) for s in steps}
            yield _sse("plan", {"steps": [{"step_id": s.step_id, "label": s.name or s.step_id} for s in steps]})
            yield _sse("step", step_payload("plan", "plan", "succeeded"))
            policy = resolve_execution_policy(skill_id, user=user)
            if skill_id != "test_case_gen":
                yield _sse(
                    "step",
                    step_payload("call_skill", step_names.get("call_skill", "call_skill"), "running"),
                )
                ctx = SkillContext(
                    user_text=user_text,
                    session_id=sid,
                    skill_id=skill_id,
                    llm_config=llm_config,
                    input_artifacts=[a.model_dump() for a in normalized.artifacts],
                )
                result, exec_result = await execute_plan_steps(
                    steps=steps,
                    call_skill=execute_skill,
                    skill_id=skill_id,
                    ctx=ctx,
                    policy=policy,
                )
                yield _sse(
                    "step",
                    step_payload("call_skill", step_names.get("call_skill", "call_skill"), "succeeded"),
                )
                dump = [c.model_dump() for c in result.test_cases]
                yield _sse("step", step_payload("persist", "persist", "running"))
                asst = assistant_persist_text_from_result(
                    llm_raw_output=result.llm_raw_output,
                    test_cases_dump=dump,
                )
                await save_assistant_message(
                    db,
                    conversation_id=resolved.row.id,
                    text=asst,
                    execution=exec_result.model_dump(),
                )
                await db.commit()
                yield _sse("step", step_payload("persist", "persist", "succeeded"))
                yield _sse("step", step_payload("respond", step_names.get("respond", "respond"), "running"))
                yield _sse(
                    "done",
                    {
                        "session_id": sid,
                        "skill_id": skill_id,
                        "parts": parts_dump,
                        "test_cases": dump,
                        "used_template": True,
                        "execution": {"status": exec_result.status, "traces": _trace_dump(exec_result)},
                    },
                )
                return

            if llm_config is None:
                yield _sse(
                    "error",
                    {
                        "message": "未配置大模型，无法执行该技能",
                        "details": {"reason": "llm_config is null"},
                    },
                )
                return

            started = time.perf_counter()
            llm_messages = build_llm_messages_for_test_case_gen(
                prior_messages=prior,
                current_user_text=user_text,
            )
            # If skill config provides prompt_template, override system prompt in multi-turn messages.
            try:
                cfg = load_skill_config("test_case_gen")
                if cfg.prompt_template:
                    sp = render_prompt(cfg.prompt_template, vars=default_prompt_vars())
                    if llm_messages and isinstance(llm_messages, list) and llm_messages[0].get("role") == "system":
                        llm_messages[0]["content"] = sp
            except Exception:
                pass

            chunks: list[str] = []
            try:
                yield _sse(
                    "step",
                    step_payload("call_skill", step_names.get("call_skill", "call_skill"), "running"),
                )
                async with asyncio.timeout(policy.step_timeout_seconds):
                    async for delta in stream_llm_text(
                        llm_config=llm_config,
                        messages=llm_messages,
                    ):
                        chunks.append(delta)
                        yield _sse("token", {"text": delta})
            except TimeoutError:
                yield _sse(
                    "error",
                    {
                        "message": "流式生成超时，请缩短输入或重试",
                        "details": {"timeout_seconds": policy.step_timeout_seconds},
                    },
                )
                return

            full = "".join(chunks)
            yield _sse(
                "step",
                step_payload("call_skill", step_names.get("call_skill", "call_skill"), "succeeded"),
            )
            yield _sse("step", step_payload("parse_output", "parse_output", "running"))
            try:
                cases = parse_items(
                    full,
                    item_model=TestCaseItem,
                    min_items=int(default_prompt_vars().min_cases),
                )
            except Exception as e:
                logger.warning("流式结束后解析 JSON 失败: %s", e)
                yield _sse("step", step_payload("parse_output", "parse_output", "failed"))
                yield _sse(
                    "error",
                    {
                        "message": "模型输出不是合法用例 JSON，请缩短需求或重试",
                        "details": {"reason": str(e)},
                    },
                )
                return
            yield _sse("step", step_payload("parse_output", "parse_output", "succeeded"))

            dump = [c.model_dump() for c in cases]
            exec_result = ExecutionResult(
                status="succeeded",
                traces=[
                    ExecutionTrace(
                        step_id="call_skill",
                        status="succeeded",
                        duration_ms=int((time.perf_counter() - started) * 1000),
                        output_summary=f"generated={len(dump)}",
                    ),
                    ExecutionTrace(
                        step_id="respond",
                        status="succeeded",
                        duration_ms=0,
                        output_summary="sse_done",
                    ),
                ],
                outputs={"test_case_count": len(dump)},
            )
            yield _sse("step", step_payload("persist", "persist", "running"))
            await save_assistant_message(
                db,
                conversation_id=resolved.row.id,
                text=full,
                execution=exec_result.model_dump(),
            )
            await db.commit()
            yield _sse("step", step_payload("persist", "persist", "succeeded"))
            yield _sse("step", step_payload("respond", step_names.get("respond", "respond"), "running"))

            yield _sse(
                "done",
                {
                    "session_id": sid,
                    "skill_id": skill_id,
                    "parts": parts_dump,
                    "test_cases": dump,
                    "used_template": False,
                    "execution": {"status": exec_result.status, "traces": _trace_dump(exec_result)},
                },
            )
        except Exception as e:
            logger.exception("SSE 编排异常")
            if current_step:
                yield _sse("step", step_payload(current_step, "执行中断", "failed"))
            yield _sse("error", {"message": str(e) or "流式生成失败"})

