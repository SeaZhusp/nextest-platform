"""将用户选择的 LLM 配置解析为单次调用参数（读取 Key，校验归属）。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.repositories.user_llm_profile_repository import user_llm_profile_repository
from app.schemas.llm_invoke import LlmInvokeConfig


async def resolve_user_llm_config(
    db: AsyncSession,
    user_id_str: str,
    profile_id: int | None,
    temperature: float,
) -> LlmInvokeConfig | None:
    """
    未传 `profile_id` 时不调用大模型（技能侧走模板）。
    传了则必须属于当前用户。
    """
    if profile_id is None:
        return None
    try:
        uid = int(user_id_str)
    except (TypeError, ValueError) as e:
        raise ValidationException("用户标识无效") from e

    row = await user_llm_profile_repository.get_by_id(db, profile_id)
    if row is None or row.user_id != uid:
        raise NotFoundException("模型配置不存在")
    if not row.is_active:
        raise ValidationException("该模型配置已禁用，请在模型配置中启用后再试")

    return LlmInvokeConfig(
        api_base=row.api_base,
        api_key=row.api_key,
        model=row.model_name,
        temperature=temperature,
    )
