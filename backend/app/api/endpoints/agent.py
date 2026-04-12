"""
智能体 HTTP 入口：同步 JSON（/chat）与 SSE 流式（/chat/stream）（2.2.2 / 2.2.3）。
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.agent import AgentChatAckData, AgentChatRequest
from app.schemas.common import ApiResponse
from app.services.agent_service import process_agent_chat
from app.services.agent_stream_service import iter_agent_chat_sse
from app.services.llm_resolve_service import resolve_user_llm_config

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ApiResponse[AgentChatAckData])
async def chat(
    payload: AgentChatRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentChatAckData]:
    """
    提交一轮用户输入（`parts` 或 `content`），按 `skill_id` 执行已注册技能（非流式，一次返回）。
    """
    llm_cfg = await resolve_user_llm_config(
        db,
        user.user_id,
        payload.llm_profile_id,
        payload.temperature,
    )
    data = await process_agent_chat(payload, llm_cfg)
    return ApiResponse(data=data)


@router.post("/chat/stream")
async def chat_stream(
    payload: AgentChatRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    同 /chat 请求体，以 **SSE** 推送生成过程（2.2.3）。

    事件类型见仓库文档 `docs/agent-sse-protocol.md`。
    """
    llm_cfg = await resolve_user_llm_config(
        db,
        user.user_id,
        payload.llm_profile_id,
        payload.temperature,
    )
    return StreamingResponse(
        iter_agent_chat_sse(payload, llm_cfg),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
