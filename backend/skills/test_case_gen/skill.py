"""
测试用例生成技能（2.2.2 注册 + 2.2.3 LLM）。

由注册表动态加载；LLM 调用经 app.services.test_case_gen_llm。
"""

from __future__ import annotations

import json
import logging

from app.core.exceptions import BusinessException
from app.contracts.skill import BaseSkill, SkillContext, SkillRunResult
from app.services.test_case_gen_llm import generate_test_cases_from_user_text, template_test_cases

logger = logging.getLogger(__name__)


class TestCaseGenSkill(BaseSkill):
    @property
    def skill_id(self) -> str:
        return "test_case_gen"

    @property
    def name(self) -> str:
        return "测试用例生成"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "根据需求描述生成结构化用例；请求中携带用户模型配置时走大模型，否则返回模板用例"

    async def run(self, ctx: SkillContext) -> SkillRunResult:
        if ctx.llm_config is not None:
            try:
                cases, raw = await generate_test_cases_from_user_text(
                    ctx.user_text,
                    ctx.llm_config,
                    chat_messages=ctx.llm_chat_messages,
                )
                return SkillRunResult(test_cases=cases, llm_raw_output=raw)
            except BusinessException:
                raise
            except Exception as e:
                logger.exception("LLM 调用失败")
                raise BusinessException(
                    message="调用大模型失败，请稍后重试",
                    details={"reason": str(e)},
                ) from e
        tpl = template_test_cases()
        return SkillRunResult(
            test_cases=tpl,
            llm_raw_output=json.dumps([c.model_dump() for c in tpl], ensure_ascii=False),
        )


def build_skill() -> BaseSkill:
    return TestCaseGenSkill()
