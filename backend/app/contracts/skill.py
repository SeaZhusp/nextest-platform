"""Skill contracts shared by runtime and skill packages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.llm_invoke import LlmInvokeConfig
from app.schemas.testcase import TestCaseItem


class SkillContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_text: str = Field(default="", description="Current user input text merged from parts.")
    session_id: str | None = None
    skill_id: str = ""
    llm_config: LlmInvokeConfig | None = Field(
        default=None,
        description="Optional user-selected LLM config for this round.",
    )
    llm_chat_messages: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional chat messages prepared by orchestrator for multi-turn generation.",
    )
    input_artifacts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Normalized input artifacts for multimodal-capable skills.",
    )


class SkillRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_cases: list[TestCaseItem] = Field(default_factory=list)
    llm_raw_output: str | None = Field(
        default=None,
        description="Raw LLM output persisted as assistant message when available.",
    )


class BaseSkill(ABC):
    """Skills live under backend/skills/<skill_id>/skill.py and expose build_skill()."""

    @property
    @abstractmethod
    def skill_id(self) -> str: ...

    @property
    def name(self) -> str:
        return self.skill_id

    @property
    def version(self) -> str:
        return "0.0.0"

    @property
    def description(self) -> str:
        return ""

    @abstractmethod
    async def run(self, ctx: SkillContext) -> SkillRunResult:
        """Run skill logic. DB access should stay in orchestrator/service layers."""

