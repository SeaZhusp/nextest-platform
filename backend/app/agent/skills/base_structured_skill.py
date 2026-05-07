"""Base skill for config+prompt driven structured outputs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from app.contracts.skill import BaseSkill, SkillContext, SkillRunResult
from app.core.exceptions import BusinessException
from app.agent.skills.config import load_skill_config
from app.agent.skills.structured_generation import (
    build_messages,
    format_prompt_template,
    generate_structured_items,
    resolve_messages,
)

TItem = TypeVar("TItem", bound=BaseModel)


class BaseStructuredSkill(BaseSkill, ABC, Generic[TItem]):
    """A skill that only needs config.json + prompt_template to work."""

    @property
    @abstractmethod
    def item_model(self) -> type[TItem]: ...

    def prompt_format_kwargs(self) -> dict[str, Any]:
        """Subclass may supply `.format()` kwargs when `config.json` uses `prompt_template` with placeholders."""
        return {}

    def error_message(self) -> str:
        return "模型输出不是合法结构化结果，请缩短需求或重试"

    def system_prompt(self) -> str:
        cfg = load_skill_config(self.skill_id)
        tpl = cfg.prompt_template
        if tpl:
            return format_prompt_template(tpl, **self.prompt_format_kwargs())
        return "请输出符合要求的结构化 JSON。"

    @property
    def name(self) -> str:
        cfg = load_skill_config(self.skill_id)
        return cfg.name or self.skill_id

    @property
    def version(self) -> str:
        cfg = load_skill_config(self.skill_id)
        return cfg.version or "0.0.0"

    @property
    def description(self) -> str:
        cfg = load_skill_config(self.skill_id)
        return cfg.description or ""

    def default_messages(self, user_text: str) -> list[dict[str, Any]]:
        return build_messages(system_prompt=self.system_prompt(), user_text=user_text)

    async def run(self, ctx: SkillContext) -> SkillRunResult:
        user_text = (ctx.user_text or "").strip()
        if not user_text:
            raise BusinessException("用户输入为空")

        if ctx.llm_config is None:
            raise BusinessException("未配置大模型，无法执行该技能")

        messages = resolve_messages(
            ctx_messages=ctx.llm_chat_messages,
            default_messages=self.default_messages(user_text),
        )

        items, raw = await generate_structured_items(
            user_text=user_text,
            llm_config=ctx.llm_config,
            messages=messages,
            item_model=self.item_model,
            error_message=self.error_message(),
        )
        return SkillRunResult(test_cases=items, llm_raw_output=raw)

