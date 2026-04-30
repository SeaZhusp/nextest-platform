"""技能列表与独立调用（2.2.2）。"""

from pydantic import BaseModel, ConfigDict, Field

from fastapi import APIRouter, Depends

from app.api.deps.auth import CurrentUser, get_current_user
from app.schemas.common import ApiResponse
from app.schemas.skill import SkillMetaOut
from app.contracts.skill import SkillContext, SkillRunResult
from app.agent.skills.executor import execute_skill

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillInvokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_text: str = Field(..., min_length=1, max_length=5000)
    session_id: str | None = None


@router.get("", response_model=ApiResponse[list[SkillMetaOut]])
async def list_skills(
    _user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[list[SkillMetaOut]]:
    from app.agent.skills.registry import get_skill_registry

    return ApiResponse(data=get_skill_registry().list_meta())


@router.post("/{skill_id}/invoke", response_model=ApiResponse[SkillRunResult])
async def invoke_skill(
    skill_id: str,
    body: SkillInvokeRequest,
    _user: CurrentUser = Depends(get_current_user),
) -> ApiResponse[SkillRunResult]:
    """调试/直连执行技能（与 agent 编排层共用 executor）。"""
    sid = skill_id.strip()
    ctx = SkillContext(
        user_text=body.user_text,
        session_id=body.session_id,
        skill_id=sid,
    )
    result = await execute_skill(sid, ctx)
    return ApiResponse(data=result)
