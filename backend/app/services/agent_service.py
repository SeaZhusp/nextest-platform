from __future__ import annotations

import io
import json
from typing import Literal
from uuid import UUID

from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.repositories.conversation_repository import conversation_repository
from app.schemas.testcase import multiline_field_from_llm


ExportSource = Literal["edited", "raw"]


def _normalize_rows_from_payload(payload: dict) -> list[dict[str, str]]:
    rows_raw = payload.get("table")
    if not isinstance(rows_raw, list):
        return []
    rows: list[dict[str, str]] = []
    for i, row in enumerate(rows_raw):
        r = row if isinstance(row, dict) else {}
        rows.append(
            {
                "case_no": str(r.get("case_no") or f"TC-{i + 1}"),
                "module": str(r.get("module") or ""),
                "title": str(r.get("title") or ""),
                "preconditions": multiline_field_from_llm(r.get("preconditions")),
                "steps": multiline_field_from_llm(r.get("steps")),
                "expected": multiline_field_from_llm(r.get("expected")),
                "priority": str(r.get("priority") or "P2"),
            }
        )
    return rows


def _rows_from_content_json(content_json: dict, source: ExportSource) -> list[dict[str, str]]:
    payload = content_json.get("edited_payload") if source == "edited" else content_json.get("raw_payload")
    if isinstance(payload, dict):
        rows = _normalize_rows_from_payload(payload)
        if rows:
            return rows

    text = content_json.get("text")
    if isinstance(text, str) and text.strip():
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                rows: list[dict[str, str]] = []
                for i, item in enumerate(parsed):
                    r = item if isinstance(item, dict) else {}
                    rows.append(
                        {
                            "case_no": str(r.get("case_no") or f"TC-{i + 1}"),
                            "module": str(r.get("module") or ""),
                            "title": str(r.get("title") or ""),
                            "preconditions": multiline_field_from_llm(r.get("preconditions")),
                            "steps": multiline_field_from_llm(r.get("steps")),
                            "expected": multiline_field_from_llm(r.get("expected")),
                            "priority": str(r.get("priority") or "P2"),
                        }
                    )
                return rows
        except Exception:
            return []
    return []


def _build_excel_bytes(rows: list[dict[str, str]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "test_cases"

    headers = ["编号", "模块", "标题", "前置条件", "步骤", "预期", "优先级"]
    keys = ["case_no", "module", "title", "preconditions", "steps", "expected", "priority"]
    ws.append(headers)
    for r in rows:
        ws.append([r.get(k, "") for k in keys])

    for idx, width in enumerate([16, 18, 34, 34, 34, 34, 10], start=1):
        ws.column_dimensions[chr(64 + idx)].width = width

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


async def export_agent_session_excel_for_user(
    db: AsyncSession,
    *,
    user_id: int,
    conversation_uuid: UUID,
    source: ExportSource = "edited",
) -> tuple[bytes, str]:
    row = await conversation_repository.get_by_uuid_for_user(
        db,
        conversation_uuid=str(conversation_uuid),
        user_id=user_id,
    )
    if row is None:
        raise NotFoundException("会话不存在或无权访问")

    msg = await conversation_repository.get_latest_assistant_message(db, conversation_id=row.id)
    if msg is None or not isinstance(msg.content_json, dict):
        raise NotFoundException("当前会话暂无可导出的助手结果")

    rows = _rows_from_content_json(msg.content_json, source)
    if not rows:
        raise ValidationException("当前结果没有可导出的表格数据")

    file_name = f"testcases_{row.conversation_uuid}.xlsx"
    return _build_excel_bytes(rows), file_name

