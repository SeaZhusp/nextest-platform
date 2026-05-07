from __future__ import annotations

from app.contracts.skill import BaseSkill
from app.agent.skills.base_structured_skill import BaseStructuredSkill
from app.schemas.testcase import TestCaseItem


class TestCaseGenSkill(BaseStructuredSkill[TestCaseItem]):
    @property
    def item_model(self) -> type[TestCaseItem]:
        return TestCaseItem


def build_skill() -> BaseSkill:
    return TestCaseGenSkill()
