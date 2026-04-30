"""
智能体上下文组装：从已持久化消息截取最近 K 轮，拼入 LLM messages。

一期仅将用户文本写入 user content；未知片段类型预留为跳过。
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.models.conversation import ConversationMessage
from app.services.test_case_gen_llm import get_system_prompt_for_test_case_gen

logger = logging.getLogger(__name__)


def complete_pairs_only(rows: list[ConversationMessage]) -> list[ConversationMessage]:
    """去掉末尾未成对的 user（例如上一轮 LLM 失败仅有 user 行）。"""
    if len(rows) % 2 == 1:
        return rows[:-1]
    return rows


def user_display_text_from_content_json(content: dict[str, Any]) -> str:
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    texts: list[str] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        if p.get("type") != "text":
            logger.debug("跳过非 text 消息片段（一期未实现）: %s", p.get("type"))
            continue
        t = p.get("text")
        if isinstance(t, str) and t.strip():
            texts.append(t.strip())
    return "\n".join(texts)


def assistant_text_from_content_json(content: dict[str, Any]) -> str:
    t = content.get("text")
    if isinstance(t, str):
        return t
    return json.dumps(content, ensure_ascii=False)


def build_test_case_gen_llm_messages(
    *,
    prior_messages: list[ConversationMessage],
    current_user_text: str,
    max_rounds: int,
    system_prompt: str | None = None,
) -> list[dict[str, Any]]:
    """
    取最近 max_rounds 轮（每轮 user+assistant 各一条 DB 行），再追加本轮 user。
    """
    sp = system_prompt if system_prompt is not None else get_system_prompt_for_test_case_gen()
    paired = complete_pairs_only(prior_messages)
    max_rows = max(0, max_rounds) * 2
    tail = paired[-max_rows:] if len(paired) > max_rows else paired

    out: list[dict[str, Any]] = [{"role": "system", "content": sp}]
    for m in tail:
        if m.role == "user":
            out.append(
                {
                    "role": "user",
                    "content": user_display_text_from_content_json(m.content_json),
                }
            )
        elif m.role == "assistant":
            out.append(
                {
                    "role": "assistant",
                    "content": assistant_text_from_content_json(m.content_json),
                }
            )
    out.append({"role": "user", "content": current_user_text.strip()})
    return out

