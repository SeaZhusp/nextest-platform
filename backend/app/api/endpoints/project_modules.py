from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.project_module import (
    ProjectModuleCreate,
    ProjectModuleOut,
    ProjectModuleTreeData,
    ProjectModuleUpdate,
)
from app.services.project_module_service import ProjectModuleService

router = APIRouter(prefix="/projects", tags=["project-modules"])


@router.get("/{project_id}/modules/tree", response_model=ApiResponse[ProjectModuleTreeData])
async def get_project_module_tree(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectModuleTreeData]:
    svc = ProjectModuleService()
    data = await svc.get_tree(db, user_id=current.user_id, project_id=project_id)
    return ApiResponse(data=data)


@router.post("/{project_id}/modules", response_model=ApiResponse[ProjectModuleOut])
async def create_project_module(
    project_id: int,
    payload: ProjectModuleCreate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectModuleOut]:
    svc = ProjectModuleService()
    data = await svc.create_module(
        db,
        user_id=current.user_id,
        project_id=project_id,
        payload=payload,
    )
    return ApiResponse(data=data)


@router.get("/{project_id}/modules/{module_id}", response_model=ApiResponse[ProjectModuleOut])
async def get_project_module(
    project_id: int,
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectModuleOut]:
    svc = ProjectModuleService()
    data = await svc.get_module(
        db,
        user_id=current.user_id,
        project_id=project_id,
        module_id=module_id,
    )
    return ApiResponse(data=data)


@router.patch("/{project_id}/modules/{module_id}", response_model=ApiResponse[ProjectModuleOut])
async def update_project_module(
    project_id: int,
    module_id: int,
    payload: ProjectModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[ProjectModuleOut]:
    svc = ProjectModuleService()
    data = await svc.update_module(
        db,
        user_id=current.user_id,
        project_id=project_id,
        module_id=module_id,
        payload=payload,
    )
    return ApiResponse(data=data)


@router.delete("/{project_id}/modules/{module_id}", response_model=ApiResponse[Any])
async def delete_project_module(
    project_id: int,
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = Depends(get_current_user),
) -> ApiResponse[Any]:
    svc = ProjectModuleService()
    await svc.delete_module(
        db,
        user_id=current.user_id,
        project_id=project_id,
        module_id=module_id,
    )
    return ApiResponse(data=None)
