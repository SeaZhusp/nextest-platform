"""OpenAI 兼容 Chat Completions 客户端（流式 / 非流式）。"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

import httpx

from app.core.config import settings
from app.schemas.llm_invoke import LlmInvokeConfig
from app.llm.exceptions import (
    LLMHTTPError,
    LLMParseError,
    LLMRateLimitError,
    LLMTimeoutError,
)
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
            raise LLMHTTPError(f"LLM 请求失败: HTTP {e.response.status_code}") from e
        try:
            data = resp.json()
        except ValueError as e:
            logger.error("LLM 响应 JSON 解析失败: %s", resp.text[:2000])
            raise LLMParseError("LLM 响应不是合法 JSON") from e
    try:
        return extract_content(data)
    except (KeyError, IndexError, TypeError) as e:
        logger.error("LLM 响应结构异常: %s", data)
        raise LLMParseError("LLM 响应格式异常") from e


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

    retries = 3
    headers = _headers(config)
    url = _chat_url(config)
    async with httpx.AsyncClient(timeout=_timeout()) as client:
        for i in range(retries):
            try:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code == 429:
                        if i == retries - 1:
                            raise LLMRateLimitError("LLM 流式请求触发限流，请稍后重试")
                        await asyncio.sleep(0.5 * (2 ** i))
                        continue

                    try:
                        resp.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        body = await resp.aread()
                        logger.error(
                            "LLM 流式 HTTP 错误 status=%s body=%s",
                            resp.status_code,
                            body.decode(errors="ignore")[:2000],
                        )
                        raise LLMHTTPError(f"LLM 流式请求失败: HTTP {resp.status_code}") from e

                    async for line in resp.aiter_lines():
                        if not line or line.startswith(":"):
                            continue
                        if not line.startswith("data: "):
                            continue

                        raw = line.removeprefix("data: ").strip()
                        if raw == "[DONE]":
                            return

                        try:
                            chunk = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        try:
                            piece = extract_delta(chunk)
                        except (KeyError, IndexError, TypeError):
                            continue

                        if piece:
                            yield str(piece)
                    return
            except httpx.TimeoutException as e:
                if i == retries - 1:
                    raise LLMTimeoutError("LLM 流式请求超时") from e
                await asyncio.sleep(0.5 * (2 ** i))
            except LLMRateLimitError:
                raise
            except Exception:
                if i == retries - 1:
                    raise
                await asyncio.sleep(0.5 * (2 ** i))
