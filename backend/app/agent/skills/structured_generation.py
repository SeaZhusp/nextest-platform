"""Common structured generation utilities for skills."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, AsyncIterator, TypeVar

from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import BusinessException
from app.llm.client import chat_completion_content, chat_completion_stream_deltas
from app.schemas.llm_invoke import LlmInvokeConfig

logger = logging.getLogger(__name__)

TItem = TypeVar("TItem", bound=BaseModel)


@dataclass(frozen=True)
class PromptVars:
    min_cases: int
    soft_hint: str


def default_prompt_vars() -> PromptVars:
    n = int(settings.agent_min_generated_test_cases)
    soft_hint = (
        "需求简单时满足条数即可；若场景多面、边界多，请主动多生成几条便于评审。"
        if n <= 1
        else ""
    )
    return PromptVars(min_cases=n, soft_hint=soft_hint)


def render_prompt(template: str, *, vars: PromptVars) -> str:
    try:
        return template.format(min_cases=vars.min_cases, soft_hint=vars.soft_hint)
    except Exception:
        return template


def build_messages(*, system_prompt: str, user_text: str) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text.strip()},
    ]


def _strip_markdown_fences(s: str) -> str:
    s = s.strip()
    if not s.startswith("```"):
        return s
    lines = s.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _fenced_code_contents(raw: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", raw, flags=re.IGNORECASE):
        inner = (m.group(1) or "").strip()
        if inner:
            out.append(inner)
    return out


def _try_parse_json_array_from_string(s: str) -> list[Any] | None:
    s = s.strip()
    if not s:
        return None
    try:
        v = json.loads(s)
        return v if isinstance(v, list) else None
    except json.JSONDecodeError:
        pass
    start = s.find("[")
    if start < 0:
        return None
    try:
        val, _ = json.JSONDecoder().raw_decode(s, start)
    except json.JSONDecodeError:
        return None
    return val if isinstance(val, list) else None


def extract_json_array(raw: str) -> list[Any]:
    raw = raw.strip()
    candidates: list[str] = []
    candidates.extend(_fenced_code_contents(raw))
    stripped = _strip_markdown_fences(raw)
    if stripped not in candidates:
        candidates.append(stripped)
    if raw not in candidates:
        candidates.append(raw)

    seen: set[str] = set()
    for s in candidates:
        if not s or s in seen:
            continue
        seen.add(s)
        arr = _try_parse_json_array_from_string(s)
        if arr is not None:
            return arr
    raise ValueError("模型输出中未找到合法 JSON 数组（请避免在数组前后夹杂未转义的方括号说明文字）")


def parse_items(
    raw: str,
    *,
    item_model: type[TItem],
) -> list[TItem]:
    arr = extract_json_array(raw)
    out: list[TItem] = []
    for i, item in enumerate(arr):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i + 1} 条不是对象")
        out.append(item_model.model_validate(item))
    return out


async def generate_structured_items(
    *,
    user_text: str,
    llm_config: LlmInvokeConfig,
    messages: list[dict[str, Any]],
    item_model: type[TItem],
    error_message: str,
) -> tuple[list[TItem], str]:
    content = await chat_completion_content(messages, config=llm_config)
    try:
        items = parse_items(content, item_model=item_model)
        return items, content
    except Exception as e:
        logger.warning("LLM 输出解析失败: %s", e)
        raise BusinessException(
            message=error_message,
            details={"reason": str(e)},
        ) from e


async def stream_llm_text(
    *,
    llm_config: LlmInvokeConfig,
    messages: list[dict[str, Any]],
) -> AsyncIterator[str]:
    async for d in chat_completion_stream_deltas(messages, config=llm_config):
        if d:
            yield d


def resolve_messages(
    *,
    ctx_messages: list[dict[str, Any]] | None,
    default_messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if ctx_messages is not None and isinstance(ctx_messages, list) and ctx_messages:
        return ctx_messages
    return default_messages


