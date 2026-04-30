"""
智能体 HTTP 入口：同步 JSON（/chat）与 SSE 流式（/chat/stream）（2.2.2 / 2.2.3 / 2.2.4）。
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory_service import get_execution_summary_for_user, list_session_messages_for_user
from app.agent.orchestrator import process_agent_chat
from app.agent.stream import iter_conversation_chat_sse
from app.api.deps.auth import CurrentUser, get_current_user
from app.api.deps.query import Paging
from app.core.exceptions import ValidationException
from app.db.session import get_db
from app.schemas.agent import (
    AgentChatAckData,
    AgentChatRequest,
    AgentSessionListData,
    AgentSessionMessagesData,
    AgentSessionRenameRequest,
    AgentSessionSummaryOut,
    AgentExecutionSummaryOut,
)
from app.schemas.common import ApiResponse
from app.services.conversation_service import list_my_conversations, rename_conversation
from app.services.llm_resolve_service import resolve_user_llm_config

router = APIRouter(prefix="/agent", tags=["agent"])


def _parse_user_id(user: CurrentUser) -> int:
    try:
        return int(user.user_id)
    except (TypeError, ValueError) as e:
        raise ValidationException("用户标识无效") from e


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
    uid = _parse_user_id(user)
    data = await process_agent_chat(payload, llm_cfg, db, user_id=uid, user=user)
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
    uid = _parse_user_id(user)
    return StreamingResponse(
        iter_conversation_chat_sse(payload, llm_cfg, user_id=uid, user=user),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=ApiResponse[AgentSessionListData])
async def list_agent_sessions(
    paging: Annotated[Paging, Depends()],
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionListData]:
    """当前用户的历史会话列表（分页，按更新时间倒序）。"""
    uid = _parse_user_id(user)
    data = await list_my_conversations(db, user_id=uid, page=paging.page, size=paging.size)
    return ApiResponse(data=data)


@router.patch(
    "/sessions/{session_id}",
    response_model=ApiResponse[AgentSessionSummaryOut],
)
async def rename_agent_session(
    session_id: UUID,
    body: AgentSessionRenameRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionSummaryOut]:
    """重命名会话展示标题。"""
    uid = _parse_user_id(user)
    data = await rename_conversation(db, user_id=uid, conversation_uuid=session_id, title=body.title)
    return ApiResponse(data=data)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ApiResponse[AgentSessionMessagesData],
)
async def list_session_messages(
    session_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionMessagesData]:
    """查询会话消息历史（2.2.4 F1.11）。"""
    uid = _parse_user_id(user)
    data = await list_session_messages_for_user(db, user_id=uid, conversation_uuid=session_id)
    return ApiResponse(data=data)


@router.get(
    "/sessions/{session_id}/execution-summary",
    response_model=ApiResponse[AgentExecutionSummaryOut],
)
async def get_execution_summary(
    session_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentExecutionSummaryOut]:
    uid = _parse_user_id(user)
    data = await get_execution_summary_for_user(db, user_id=uid, conversation_uuid=session_id)
    return ApiResponse(data=data)
