"""Prompt provider for test_case_gen skill."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "config.json"


def _load_prompt_template() -> str | None:
    try:
        raw = json.loads(_config_path().read_text(encoding="utf-8"))
    except Exception:
        return None
    tpl = raw.get("prompt_template")
    if isinstance(tpl, str) and tpl.strip():
        return tpl
    return None


def get_system_prompt_for_test_case_gen() -> str:
    n = int(settings.agent_min_generated_test_cases)
    soft_hint = (
        "需求简单时满足条数即可；若场景多面、边界多，请主动多生成几条便于评审。"
        if n <= 1
        else ""
    )
    tpl = _load_prompt_template()
    if tpl:
        return tpl.format(min_cases=n, soft_hint=soft_hint)
    return f"""你是一名资深软件测试工程师。请根据用户给出的需求描述，设计结构化测试用例。

硬性要求：
1. 只输出一个 JSON 数组，不要输出数组以外的任何文字、不要 Markdown 代码围栏。
2. 数组至少包含 {n} 条用例。{soft_hint}
3. 每个元素必须是对象，且包含字段：case_no（字符串）、module、title、preconditions、steps、expected、priority。
4. preconditions 只描述「执行该用例前，系统/页面/数据应处于的状态」（例如：已打开登录页、已登出、测试账号已准备），不要复述用户整段需求原文。
5. steps 使用清晰编号步骤；expected 为可验证结果；priority 使用 P0/P1/P2。
"""
