from __future__ import annotations

import logging

from app.contracts.skill import SkillContext, SkillRunResult
from app.agent.skills.base_structured_skill import BaseStructuredSkill
from app.schemas.testcase import TestCaseItem

logger = logging.getLogger(__name__)


class TestCaseGenSkill(BaseStructuredSkill[TestCaseItem]):
    @property
    def item_model(self) -> type[TestCaseItem]:
        return TestCaseItem


def build_skill() -> BaseSkill:
    return TestCaseGenSkill()
