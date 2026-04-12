"""OpenAI 兼容 Chat Completions 客户端（流式 / 非流式）。"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.schemas.llm_invoke import LlmInvokeConfig

logger = logging.getLogger(__name__)


def _chat_url(config: LlmInvokeConfig) -> str:
    return f"{config.api_base.rstrip('/')}/chat/completions"


def _headers(config: LlmInvokeConfig) -> dict[str, str]:
    key = (config.api_key or "").strip()
    if not key:
        raise RuntimeError("缺少 API Key，无法调用大模型")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(settings.llm_timeout_seconds)


async def chat_completion_content(
    messages: list[dict[str, Any]],
    *,
    config: LlmInvokeConfig,
) -> str:
    """非流式：返回 assistant 纯文本。"""
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "stream": False,
        "temperature": config.temperature,
    }
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        resp = await client.post(_chat_url(config), headers=_headers(config), json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("LLM HTTP 错误 status=%s body=%s", e.response.status_code, e.response.text)
            raise RuntimeError(f"LLM 请求失败: HTTP {e.response.status_code}") from e
        data = resp.json()
    try:
        return str(data["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError) as e:
        logger.error("LLM 响应结构异常: %s", data)
        raise RuntimeError("LLM 响应格式异常") from e


async def chat_completion_stream_deltas(
    messages: list[dict[str, Any]],
    *,
    config: LlmInvokeConfig,
) -> AsyncIterator[str]:
    """流式：逐段产出 assistant 的文本 delta（可能为空字符串，调用方忽略）。"""
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "stream": True,
        "temperature": config.temperature,
    }
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        async with client.stream(
            "POST",
            _chat_url(config),
            headers=_headers(config),
            json=payload,
        ) as resp:
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError:
                body = await resp.aread()
                logger.error("LLM 流式 HTTP 错误 status=%s body=%s", resp.status_code, body.decode()[:2000])
                raise RuntimeError(f"LLM 流式请求失败: HTTP {resp.status_code}")

            async for line in resp.aiter_lines():
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    raw = line.removeprefix("data: ").strip()
                    if raw == "[DONE]":
                        break
                    try:
                        chunk = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    try:
                        choice0 = chunk["choices"][0]
                        delta = choice0.get("delta") or {}
                        piece = delta.get("content")
                        if piece:
                            yield str(piece)
                    except (KeyError, IndexError, TypeError):
                        continue
