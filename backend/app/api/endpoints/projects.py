from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.api.deps.query import Paging
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectListData,
    ProjectMemberAdd,
    ProjectMemberListData,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

ParticipationQuery = Literal["all", "owned", "joined"]

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ApiResponse[ProjectListData])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
    paging: Paging = Depends(),
    participation: ParticipationQuery = Query(
        "all",
        description=(
            "all=我创建或我加入；owned=仅我作为负责人的项目；"
            "joined=仅我作为成员且非负责人的项目"
        ),
    ),
) -> ApiResponse[ProjectListData]:
    svc = ProjectService()
    data = await svc.list_projects(
        db,
        user_id=current.user_id,
        page=paging.page,
        size=paging.size,
        participation=participation,
    )
    return ApiResponse(data=data)


@router.post("", response_model=ApiResponse[ProjectOut])
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectOut]:
    svc = ProjectService()
    data = await svc.create_project(db, user_id=current.user_id, payload=payload)
    return ApiResponse(data=data)


@router.get("/{project_id}/members", response_model=ApiResponse[ProjectMemberListData])
async def list_project_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectMemberListData]:
    svc = ProjectService()
    data = await svc.list_project_members(db, user_id=current.user_id, project_id=project_id)
    return ApiResponse(data=data)


@router.post("/{project_id}/members", response_model=ApiResponse[ProjectMemberOut])
async def add_project_member(
    project_id: int,
    payload: ProjectMemberAdd,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectMemberOut]:
    svc = ProjectService()
    data = await svc.add_project_member(
        db,
        user_id=current.user_id,
        project_id=project_id,
        payload=payload,
    )
    return ApiResponse(data=data)


@router.delete("/{project_id}/members/{member_user_id}", response_model=ApiResponse[Any])
async def remove_project_member(
    project_id: int,
    member_user_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[Any]:
    svc = ProjectService()
    await svc.remove_project_member(
        db,
        user_id=current.user_id,
        project_id=project_id,
        member_user_id=member_user_id,
    )
    return ApiResponse(data=None)


@router.get("/{project_id}", response_model=ApiResponse[ProjectOut])
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectOut]:
    svc = ProjectService()
    data = await svc.get_project(db, user_id=current.user_id, project_id=project_id)
    return ApiResponse(data=data)


@router.patch("/{project_id}", response_model=ApiResponse[ProjectOut])
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectOut]:
    svc = ProjectService()
    data = await svc.update_project(
        db,
        user_id=current.user_id,
        project_id=project_id,
        payload=payload,
    )
    return ApiResponse(data=data)


@router.delete("/{project_id}", response_model=ApiResponse[Any])
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[Any]:
    svc = ProjectService()
    await svc.delete_project(db, user_id=current.user_id, project_id=project_id)
    return ApiResponse(data=None)
