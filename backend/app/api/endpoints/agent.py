"""
智能体 HTTP 入口：同步 JSON（/chat）与 SSE 流式（/chat/stream）（2.2.2 / 2.2.3 / 2.2.4）。
"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.memory_service import (
    get_execution_summary_for_user,
    list_session_messages_for_user,
    patch_latest_assistant_edited_output_for_user,
    restore_latest_assistant_raw_output_for_user,
)
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
    AgentSessionLatestEditedOutputData,
    AgentSessionLatestEditedOutputRequest,
)
from app.schemas.common import ApiResponse
from app.services.conversation_service import (
    delete_conversation,
    list_my_conversations,
    rename_conversation,
)
from app.services.agent_service import export_agent_session_excel_for_user
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
    request: Request,
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
        iter_conversation_chat_sse(payload, llm_cfg, user_id=uid, user=user, request=request),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=ApiResponse[AgentSessionListData])
async def list_agent_conversations(
    paging: Annotated[Paging, Depends()],
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionListData]:
    """当前用户的历史会话列表（分页，按更新时间倒序）。"""
    uid = _parse_user_id(user)
    data = await list_my_conversations(db, user_id=uid, page=paging.page, size=paging.size)
    return ApiResponse(data=data)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[AgentSessionSummaryOut],
)
async def rename_agent_conversation(
    conversation_id: UUID,
    body: AgentSessionRenameRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionSummaryOut]:
    """重命名对话展示标题。"""
    uid = _parse_user_id(user)
    data = await rename_conversation(db, user_id=uid, conversation_uuid=conversation_id, title=body.title)
    return ApiResponse(data=data)


@router.delete("/conversations/{conversation_id}", response_model=ApiResponse[dict[str, bool]])
async def delete_agent_conversation(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[dict[str, bool]]:
    uid = _parse_user_id(user)
    await delete_conversation(db, user_id=uid, conversation_uuid=conversation_id)
    return ApiResponse(data={"ok": True})


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ApiResponse[AgentSessionMessagesData],
)
async def list_conversation_messages(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionMessagesData]:
    """查询对话消息历史（2.2.4 F1.11）。"""
    uid = _parse_user_id(user)
    data = await list_session_messages_for_user(db, user_id=uid, conversation_uuid=conversation_id)
    return ApiResponse(data=data)


@router.get(
    "/conversations/{conversation_id}/execution-summary",
    response_model=ApiResponse[AgentExecutionSummaryOut],
)
async def get_conversation_execution_summary(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentExecutionSummaryOut]:
    uid = _parse_user_id(user)
    data = await get_execution_summary_for_user(db, user_id=uid, conversation_uuid=conversation_id)
    return ApiResponse(data=data)


@router.patch(
    "/conversations/{conversation_id}/messages/latest-edited-output",
    response_model=ApiResponse[AgentSessionLatestEditedOutputData],
)
async def patch_latest_edited_output(
    conversation_id: UUID,
    body: AgentSessionLatestEditedOutputRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionLatestEditedOutputData]:
    uid = _parse_user_id(user)
    data = await patch_latest_assistant_edited_output_for_user(
        db,
        user_id=uid,
        conversation_uuid=conversation_id,
        body=body,
    )
    return ApiResponse(data=data)


@router.patch(
    "/conversations/{conversation_id}/messages/latest-edited-output/restore-raw",
    response_model=ApiResponse[AgentSessionLatestEditedOutputData],
)
async def restore_latest_raw_output(
    conversation_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentSessionLatestEditedOutputData]:
    uid = _parse_user_id(user)
    data = await restore_latest_assistant_raw_output_for_user(
        db,
        user_id=uid,
        conversation_uuid=conversation_id,
    )
    return ApiResponse(data=data)


@router.get("/conversations/{conversation_id}/export")
async def export_session_excel(
    conversation_id: UUID,
    source: Literal["edited", "raw"] = "edited",
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    uid = _parse_user_id(user)
    content, file_name = await export_agent_session_excel_for_user(
        db,
        user_id=uid,
        conversation_uuid=conversation_id,
        source=source,
    )
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Cache-Control": "no-store",
        },
    )
