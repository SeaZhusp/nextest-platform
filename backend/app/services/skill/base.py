"""技能基类与运行上下文（2.2.2：统一入参，便于 executor 与后续 LLM 编排）。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.llm_invoke import LlmInvokeConfig
from app.schemas.testcase import TestCaseItem


class SkillContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_text: str = Field(default="", description="当前轮用户文本（由 parts 拼接）")
    session_id: str | None = None
    skill_id: str = ""
    llm_config: LlmInvokeConfig | None = Field(
        default=None,
        description="当前轮用户自备大模型参数；未传则技能侧不调用 LLM",
    )


class SkillRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_cases: list[TestCaseItem] = Field(default_factory=list)


class BaseSkill(ABC):
    """技能实现需放在 backend/skills/<skill_id>/skill.py 并由 build_skill() 导出实例。"""

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
        """执行技能；禁止在此直接访问 DB（由编排层注入或后续扩展）。"""
