"""
测试用例生成：LLM 调用、JSON 解析与模板回退（2.2.3）。

技能包 `test_case_gen` 通过本模块调用统一 LLM 客户端，避免在 skill.py 内写 HTTP。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator

from app.core.exceptions import BusinessException
from app.schemas.llm_invoke import LlmInvokeConfig
from app.schemas.testcase import TestCaseItem
from app.services.llm.client import chat_completion_content, chat_completion_stream_deltas

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名资深软件测试工程师。请根据用户给出的需求描述，设计结构化测试用例。

硬性要求：
1. 只输出一个 JSON 数组，不要输出数组以外的任何文字、不要 Markdown 代码围栏。
2. 数组长度至少 3 条用例。
3. 每个元素必须是对象，且包含字段：case_no（字符串）、module、title、preconditions、steps、expected、priority。
4. preconditions 只描述「执行该用例前，系统/页面/数据应处于的状态」（例如：已打开登录页、已登出、测试账号已准备），不要复述用户整段需求原文。
5. steps 使用清晰编号步骤；expected 为可验证结果；priority 使用 P0/P1/P2。
"""


def build_messages(user_text: str) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text.strip()},
    ]


def template_test_cases() -> list[TestCaseItem]:
    """未配置 LLM 或解析失败策略回退时的占位用例（与技能原模板一致）。"""
    return [
        TestCaseItem(
            case_no="TC-AUTO-001",
            module="登录",
            title="手机号+验证码登录成功",
            preconditions="已打开登录页；网络正常；账号处于未登录状态；手机号已注册",
            steps="1. 输入合法手机号\n2. 获取短信验证码\n3. 在有效期内输入正确验证码\n4. 点击登录",
            expected="进入已登录态，跳转至登录后首页或约定落地页",
            priority="P0",
        ),
        TestCaseItem(
            case_no="TC-AUTO-002",
            module="登录",
            title="验证码错误或过期",
            preconditions="已打开登录页；已获取验证码且仍在有效期内（用于错误码场景）",
            steps="1. 输入手机号并获取验证码\n2. 输入错误验证码或过期验证码\n3. 点击登录",
            expected="提示验证码错误/失效，保持未登录，无 session 建立",
            priority="P1",
        ),
        TestCaseItem(
            case_no="TC-AUTO-003",
            module="登录",
            title="连续输错验证码锁定",
            preconditions="已打开登录页；同一手机号未处于锁定期",
            steps="1. 连续输入错误验证码至达到锁定阈值\n2. 再次尝试登录",
            expected="账号或登录方式被锁定，提示剩余锁定时间；期间无法登录成功",
            priority="P1",
        ),
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


def extract_json_array(raw: str) -> list[Any]:
    """从模型输出中截取 JSON 数组并解析（F1.10）。"""
    s = _strip_markdown_fences(raw)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[[\s\S]*\]", s)
    if not m:
        raise ValueError("模型输出中未找到 JSON 数组")
    return json.loads(m.group(0))


def parse_test_cases_from_llm_text(raw: str) -> list[TestCaseItem]:
    arr = extract_json_array(raw)
    if not isinstance(arr, list):
        raise ValueError("JSON 根类型必须为数组")
    if len(arr) < 3:
        raise ValueError(f"用例数量不足 3 条（当前 {len(arr)}）")
    out: list[TestCaseItem] = []
    for i, item in enumerate(arr):
        if not isinstance(item, dict):
            raise ValueError(f"第 {i + 1} 条用例不是对象")
        try:
            out.append(TestCaseItem.model_validate(item))
        except Exception as e:
            raise ValueError(f"第 {i + 1} 条用例字段不合法: {e}") from e
    return out


async def generate_test_cases_from_user_text(user_text: str, config: LlmInvokeConfig) -> list[TestCaseItem]:
    """非流式：一次请求拿全文再解析。"""
    messages = build_messages(user_text)
    content = await chat_completion_content(messages, config=config)
    try:
        return parse_test_cases_from_llm_text(content)
    except Exception as e:
        logger.warning("LLM 输出解析失败: %s", e)
        raise BusinessException(
            message="模型输出不是合法用例 JSON，请缩短需求或重试",
            details={"reason": str(e)},
        ) from e


async def stream_llm_text_deltas(user_text: str, config: LlmInvokeConfig) -> AsyncIterator[str]:
    """仅流式输出模型文本 delta（解析在流结束后由调用方完成）。"""
    messages = build_messages(user_text)
    async for d in chat_completion_stream_deltas(messages, config=config):
        if d:
            yield d
