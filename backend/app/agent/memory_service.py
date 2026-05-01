"""智能体会话记忆：解析 session、读写消息。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.context import build_test_case_gen_llm_messages
from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.conversation import Conversation, ConversationMessage
from app.repositories.conversation_repository import conversation_repository
from app.schemas.agent import (
    AgentExecutionOut,
    AgentExecutionSummaryOut,
    AgentHistoryMessageOut,
    AgentSessionMessagesData,
    AgentSessionLatestEditedOutputData,
    AgentSessionLatestEditedOutputRequest,
    TextPart,
)


@dataclass
class ResolvedAgentSession:
    row: Conversation
    conversation_uuid: UUID
    is_new_session: bool


def _parts_to_content_json(parts: list[TextPart]) -> dict:
    return {"parts": [p.model_dump() for p in parts]}


async def resolve_agent_session(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: UUID | None,
    skill_id: str,
    parts: list[TextPart] | None = None,
) -> ResolvedAgentSession:
    # skill_id is validated at outer boundary (input normalizer).
    sid = skill_id.strip()
    if session_id is None:
        new_uuid = uuid4()
        initial_title = _title_from_first_user_input(parts or [])
        row = await conversation_repository.create_for_user(
            db,
            conversation_uuid=str(new_uuid),
            user_id=user_id,
            skill_id=sid,
            title=initial_title,
        )
        return ResolvedAgentSession(row=row, conversation_uuid=new_uuid, is_new_session=True)

    su = str(session_id)
    row = await conversation_repository.get_by_uuid_for_user(db, conversation_uuid=su, user_id=user_id)
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    if row.skill_id != sid:
        row.skill_id = sid
        await db.flush()
    return ResolvedAgentSession(row=row, conversation_uuid=session_id, is_new_session=False)


async def load_prior_messages(
    db: AsyncSession,
    *,
    conversation_id: int,
) -> list[ConversationMessage]:
    return await conversation_repository.list_messages(db, conversation_id=conversation_id)


def build_llm_messages_for_test_case_gen(
    *,
    prior_messages: list[ConversationMessage],
    current_user_text: str,
) -> list[dict]:
    return build_test_case_gen_llm_messages(
        prior_messages=prior_messages,
        current_user_text=current_user_text,
        max_rounds=settings.agent_context_max_rounds,
    )


def _title_from_first_user_input(parts: list[TextPart], *, max_len: int = 200) -> str:
    text = "\n".join(p.text for p in parts).strip()
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


async def save_user_message(
    db: AsyncSession,
    *,
    conversation_id: int,
    parts: list[TextPart],
) -> None:
    await conversation_repository.create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content_json=_parts_to_content_json(parts),
    )
    await db.flush()
    await conversation_repository.touch_updated_at(db, conversation_id)


async def save_assistant_message(
    db: AsyncSession,
    *,
    conversation_id: int,
    text: str,
    execution: dict | None = None,
    plan_steps: list[dict] | None = None,
) -> None:
    content_json: dict = {"text": text}
    try:
        parsed_cases = json.loads(text)
        if isinstance(parsed_cases, list):
            content_json["raw_payload"] = _build_document_payload_from_testcases(parsed_cases)
    except Exception:
        content_json["raw_payload"] = _build_document_payload_from_testcases([])
    if execution is not None:
        content_json["execution"] = execution
    if plan_steps is not None:
        content_json["plan_steps"] = plan_steps
    await conversation_repository.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content_json=content_json,
    )
    await db.flush()
    await conversation_repository.touch_updated_at(db, conversation_id)


def assistant_persist_text_from_result(*, llm_raw_output: str | None, test_cases_dump: list[dict]) -> str:
    if llm_raw_output is not None and llm_raw_output.strip():
        return llm_raw_output
    return json.dumps(test_cases_dump, ensure_ascii=False)


def _build_document_payload_from_testcases(test_cases_dump: list[dict]) -> dict:
    rows: list[dict] = []
    for i, item in enumerate(test_cases_dump):
        row = item if isinstance(item, dict) else {}
        rows.append(
            {
                "key": str(row.get("id") or row.get("case_no") or i),
                "case_no": str(row.get("case_no") or ""),
                "module": str(row.get("module") or ""),
                "title": str(row.get("title") or ""),
                "preconditions": str(row.get("preconditions") or ""),
                "steps": str(row.get("steps") or ""),
                "expected": str(row.get("expected") or ""),
                "priority": str(row.get("priority") or "P2"),
            }
        )
    markdown_lines = ["# 测试用例报告", "", "| 编号 | 模块 | 标题 | 优先级 |", "| --- | --- | --- | --- |"]
    for r in rows:
        markdown_lines.append(
            f"| {r['case_no']} | {r['module']} | {r['title']} | {r['priority']} |"
        )
    return {
        "tableRows": rows,
        "markdown": "\n".join(markdown_lines),
        "mindmap": [],
        "sync": {
            "revision": 0,
            "lastEditedBy": "system",
            "lastEditedAt": 0,
        },
    }


def assistant_baseline_content_from_content_json(content: dict[str, object]) -> str:
    edited_payload = content.get("edited_payload")
    if isinstance(edited_payload, dict):
        md = edited_payload.get("markdown")
        if isinstance(md, str) and md.strip():
            return md
        rows = edited_payload.get("tableRows")
        if isinstance(rows, list):
            return json.dumps(rows, ensure_ascii=False)

    raw_payload = content.get("raw_payload")
    if isinstance(raw_payload, dict):
        md = raw_payload.get("markdown")
        if isinstance(md, str) and md.strip():
            return md
        rows = raw_payload.get("tableRows")
        if isinstance(rows, list):
            return json.dumps(rows, ensure_ascii=False)

    text = content.get("text")
    return text if isinstance(text, str) else json.dumps(content, ensure_ascii=False)


async def patch_latest_assistant_edited_output_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
    body: AgentSessionLatestEditedOutputRequest,
) -> AgentSessionLatestEditedOutputData:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")

    msg = await conversation_repository.get_latest_assistant_message(db, conversation_id=row.id)
    if msg is None:
        raise NotFoundException("当前会话暂无助手消息可编辑")

    current = dict(msg.content_json) if isinstance(msg.content_json, dict) else {}
    current_revision = int(current.get("edited_revision") or 0)
    if body.edited_revision < current_revision:
        raise ValidationException("编辑版本落后，请刷新后重试")

    next_revision = current_revision + 1
    current["edited_payload"] = body.edited_payload
    current["edited_revision"] = next_revision
    current["edited_meta"] = {
        "source_view": "manual",
    }
    msg.content_json = current
    await db.flush()
    await conversation_repository.touch_updated_at(db, row.id)
    await db.commit()
    return AgentSessionLatestEditedOutputData(
        session_id=str(conversation_uuid),
        message_id=int(msg.id),
        edited_revision=next_revision,
        edited_payload=body.edited_payload,
    )


async def restore_latest_assistant_raw_output_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> AgentSessionLatestEditedOutputData:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")

    msg = await conversation_repository.get_latest_assistant_message(db, conversation_id=row.id)
    if msg is None:
        raise NotFoundException("当前会话暂无助手消息可恢复")

    current = dict(msg.content_json) if isinstance(msg.content_json, dict) else {}
    raw_payload = current.get("raw_payload")
    if not isinstance(raw_payload, dict):
        raise ValidationException("当前消息没有可恢复的原始版")

    current_revision = int(current.get("edited_revision") or 0)
    next_revision = current_revision + 1
    current["edited_payload"] = raw_payload
    current["edited_revision"] = next_revision
    current["edited_meta"] = {
        "source_view": "restore_raw",
    }
    msg.content_json = current
    await db.flush()
    await conversation_repository.touch_updated_at(db, row.id)
    await db.commit()
    return AgentSessionLatestEditedOutputData(
        session_id=str(conversation_uuid),
        message_id=int(msg.id),
        edited_revision=next_revision,
        edited_payload=raw_payload,
    )


async def list_session_messages_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> AgentSessionMessagesData:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    rows = await conversation_repository.list_messages(db, conversation_id=row.id)
    out: list[AgentHistoryMessageOut] = []
    for m in rows:
        role_raw = (m.role or "").strip()
        role: Literal["user", "assistant"] = (
            cast(Literal["user", "assistant"], role_raw)
            if role_raw in ("user", "assistant")
            else "user"
        )
        out.append(
            AgentHistoryMessageOut(
                id=int(m.id),
                role=role,
                content_json=dict(m.content_json) if isinstance(m.content_json, dict) else {},
                execution=_parse_execution_from_content_json(m.content_json),
                created_at=m.created_at.isoformat() if m.created_at else "",
            )
        )
    return AgentSessionMessagesData(
        session_id=str(conversation_uuid),
        title=(row.title or "").strip(),
        skill_id=row.skill_id,
        messages=out,
    )


async def get_execution_summary_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
) -> AgentExecutionSummaryOut:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")
    rows = await conversation_repository.list_messages(db, conversation_id=row.id)

    assistant_rows = [m for m in rows if (m.role or "").strip() == "assistant"]
    executions: list[AgentExecutionOut] = []
    for m in assistant_rows:
        ex = _parse_execution_from_content_json(m.content_json)
        if ex is not None:
            executions.append(ex)

    succeeded = sum(1 for e in executions if e.status == "succeeded")
    failed = sum(1 for e in executions if e.status == "failed")
    total_duration_ms = 0
    last_status = executions[-1].status if executions else None
    for e in executions:
        for t in e.traces:
            total_duration_ms += int(t.duration_ms or 0)

    return AgentExecutionSummaryOut(
        session_id=str(conversation_uuid),
        total_assistant_messages=len(assistant_rows),
        total_executions=len(executions),
        succeeded=succeeded,
        failed=failed,
        total_duration_ms=total_duration_ms,
        last_status=last_status,
    )


def _parse_execution_from_content_json(content_json: object) -> AgentExecutionOut | None:
    if not isinstance(content_json, dict):
        return None
    raw = content_json.get("execution")
    if not isinstance(raw, dict):
        return None
    try:
        return AgentExecutionOut.model_validate(raw)
    except Exception:
        return None

