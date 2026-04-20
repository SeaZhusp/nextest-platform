"""OpenAI 兼容 Chat Completions 客户端（流式 / 非流式）。"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.schemas.llm_invoke import LlmInvokeConfig
from app.llm.retry import post_with_retry
from app.llm.parser import extract_content, extract_delta

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
        resp = await post_with_retry(client, _chat_url(config), headers=_headers(config), json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("LLM HTTP 错误 status=%s body=%s", e.response.status_code, e.response.text)
            raise RuntimeError(f"LLM 请求失败: HTTP {e.response.status_code}") from e
        data = resp.json()
    try:
        return extract_content(data)
    except (KeyError, IndexError, TypeError) as e:
        logger.error("LLM 响应结构异常: %s", data)
        raise RuntimeError("LLM 响应格式异常") from e


async def chat_completion_stream_deltas(
        messages: list[dict[str, Any]],
        *,
        config: LlmInvokeConfig,
) -> AsyncIterator[str]:
    """流式：逐段产出 assistant 的文本 delta"""

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "stream": True,
        "temperature": config.temperature,
    }

    async with httpx.AsyncClient(timeout=_timeout()) as client:

        # ✅ 第一步：用 retry 建立连接
        resp = await post_with_retry(
            client,
            _chat_url(config),
            headers=_headers(config),
            json=payload,
        )

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            body = await resp.aread()
            logger.error(
                "LLM 流式 HTTP 错误 status=%s body=%s",
                resp.status_code,
                body.decode()[:2000],
            )
            raise RuntimeError(f"LLM 流式请求失败: HTTP {resp.status_code}")

        # ✅ 第二步：正常读取流（不做 retry）
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
                    piece = extract_delta(chunk)

                    if piece:
                        yield str(piece)

                except (KeyError, IndexError, TypeError):
                    continue
