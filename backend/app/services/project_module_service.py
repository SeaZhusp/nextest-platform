from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ProjectMemberRoleEnum
from app.core.exceptions import AuthorizationException, ConflictException, NotFoundException, ValidationException
from app.models.project import Project
from app.models.project_module import ProjectModule
from app.repositories.project_module_repository import ProjectModuleRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project_module import (
    ProjectModuleCreate,
    ProjectModuleOut,
    ProjectModuleTreeData,
    ProjectModuleUpdate,
)


def _parse_user_id(user_id: str) -> int:
    try:
        return int(user_id)
    except (TypeError, ValueError) as e:
        raise ValidationException("无效的用户身份") from e


def _can_manage_modules(*, project: Project, uid: int, member_role: str | None) -> bool:
    if int(project.owner_id) == uid:
        return True
    if member_role == ProjectMemberRoleEnum.LEADER.value:
        return True
    return False


def _to_out(m: ProjectModule) -> ProjectModuleOut:
    return ProjectModuleOut(
        id=int(m.id),
        project_id=int(m.project_id),
        parent_id=int(m.parent_id) if m.parent_id is not None else None,
        name=m.name,
        sort_order=m.sort_order,
        description=m.description,
        created_at=m.created_at.isoformat() if m.created_at else "",
        updated_at=m.updated_at.isoformat() if m.updated_at else "",
        children=[],
    )


def _build_tree(modules: list[ProjectModule]) -> list[ProjectModuleOut]:
    if not modules:
        return []
    stubs: dict[int, ProjectModuleOut] = {int(m.id): _to_out(m) for m in modules}
    roots: list[ProjectModuleOut] = []
    for m in modules:
        node = stubs[int(m.id)]
        pid = int(m.parent_id) if m.parent_id is not None else None
        if pid is None:
            roots.append(node)
        else:
            parent = stubs.get(pid)
            if parent is not None:
                parent.children.append(node)
            else:
                roots.append(node)
    _sort_module_outs(roots)
    for s in stubs.values():
        _sort_module_outs(s.children)
    return roots


def _sort_module_outs(nodes: list[ProjectModuleOut]) -> None:
    nodes.sort(key=lambda n: (n.sort_order, n.id))


def _collect_descendant_ids(modules: list[ProjectModule], root_id: int) -> list[int]:
    by_parent: dict[int | None, list[ProjectModule]] = {}
    for m in modules:
        p = int(m.parent_id) if m.parent_id is not None else None
        by_parent.setdefault(p, []).append(m)
    for k in by_parent:
        by_parent[k].sort(key=lambda x: (x.sort_order, int(x.id)))
    out: list[int] = []
    stack = [root_id]
    while stack:
        cur = stack.pop()
        out.append(cur)
        for ch in by_parent.get(cur, []):
            stack.append(int(ch.id))
    return out


def _would_create_cycle(
    modules_by_id: dict[int, ProjectModule],
    node_id: int,
    new_parent_id: int | None,
) -> bool:
    if new_parent_id is None:
        return False
    if new_parent_id == node_id:
        return True
    cur: int | None = new_parent_id
    seen: set[int] = set()
    while cur is not None:
        if cur == node_id:
            return True
        if cur in seen:
            return True
        seen.add(cur)
        m = modules_by_id.get(cur)
        if not m:
            break
        cur = int(m.parent_id) if m.parent_id is not None else None
    return False


class ProjectModuleService:
    def __init__(self) -> None:
        self._modules = ProjectModuleRepository()
        self._projects = ProjectRepository()

    async def get_tree(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
    ) -> ProjectModuleTreeData:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        rows = await self._modules.list_by_project(db, project_id=project_id)
        return ProjectModuleTreeData(roots=_build_tree(rows))

    async def get_module(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        module_id: int,
    ) -> ProjectModuleOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        row = await self._modules.get_by_id_in_project(
            db, project_id=project_id, module_id=module_id
        )
        if not row:
            raise NotFoundException("模块不存在")
        return _to_out(row)

    async def create_module(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        payload: ProjectModuleCreate,
    ) -> ProjectModuleOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        member = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
        role = member.role if member else None
        if not _can_manage_modules(project=project, uid=uid, member_role=role):
            raise AuthorizationException("仅项目负责人或测试负责人可维护模块")

        name = payload.name.strip()
        if not name:
            raise ValidationException("模块名称不能为空")

        parent_id = payload.parent_id
        if parent_id is not None:
            parent = await self._modules.get_by_id_in_project(
                db, project_id=project_id, module_id=parent_id
            )
            if not parent:
                raise ValidationException("父模块不存在或不属于该项目")

        dup = await self._modules.find_active_by_name_under_parent(
            db,
            project_id=project_id,
            parent_id=parent_id,
            name=name,
        )
        if dup:
            raise ConflictException("同级下已存在同名模块")

        if payload.sort_order is not None:
            sort_order = payload.sort_order
        else:
            mx = await self._modules.max_sort_order_among_siblings(
                db, project_id=project_id, parent_id=parent_id
            )
            sort_order = (mx + 1) if mx is not None else 0

        desc = payload.description.strip() if payload.description else None
        if desc == "":
            desc = None

        data = {
            "project_id": project_id,
            "parent_id": parent_id,
            "name": name,
            "sort_order": sort_order,
            "description": desc,
        }
        try:
            row = await self._modules.create(db, data)
            await db.commit()
            await db.refresh(row)
        except IntegrityError:
            await db.rollback()
            raise ConflictException("同级下已存在同名模块") from None

        return _to_out(row)

    async def update_module(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        module_id: int,
        payload: ProjectModuleUpdate,
    ) -> ProjectModuleOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        member = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
        role = member.role if member else None
        if not _can_manage_modules(project=project, uid=uid, member_role=role):
            raise AuthorizationException("仅项目负责人或测试负责人可维护模块")

        row = await self._modules.get_by_id_in_project(
            db, project_id=project_id, module_id=module_id
        )
        if not row:
            raise NotFoundException("模块不存在")

        raw = payload.model_dump(exclude_unset=True)
        new_parent_id = int(row.parent_id) if row.parent_id is not None else None
        new_name = row.name
        if "parent_id" in raw:
            new_parent_id = raw["parent_id"]
            if new_parent_id is not None:
                parent = await self._modules.get_by_id_in_project(
                    db, project_id=project_id, module_id=new_parent_id
                )
                if not parent:
                    raise ValidationException("父模块不存在或不属于该项目")

        if "name" in raw and raw["name"] is not None:
            n = str(raw["name"]).strip()
            if not n:
                raise ValidationException("模块名称不能为空")
            new_name = n

        if "parent_id" in raw or "name" in raw:
            dup = await self._modules.find_active_by_name_under_parent(
                db,
                project_id=project_id,
                parent_id=new_parent_id,
                name=new_name,
                exclude_module_id=module_id,
            )
            if dup:
                raise ConflictException("同级下已存在同名模块")

        if "parent_id" in raw:
            all_rows = await self._modules.list_by_project(db, project_id=project_id)
            by_id = {int(m.id): m for m in all_rows}
            if _would_create_cycle(by_id, module_id, new_parent_id):
                raise ValidationException("不能将模块移动到自身或其子模块下")

        data: dict = {}
        if "name" in raw:
            data["name"] = new_name
        if "parent_id" in raw:
            data["parent_id"] = new_parent_id
        if "sort_order" in raw and raw["sort_order"] is not None:
            data["sort_order"] = raw["sort_order"]
        if "description" in raw:
            v = raw["description"]
            if v is None:
                data["description"] = None
            else:
                d = str(v).strip()
                data["description"] = d if d else None

        if not data:
            return _to_out(row)

        try:
            fresh = await self._modules.update(db, module_id, data)
            await db.commit()
            await db.refresh(fresh)
        except IntegrityError:
            await db.rollback()
            raise ConflictException("同级下已存在同名模块") from None

        return _to_out(fresh)

    async def delete_module(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        module_id: int,
    ) -> None:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        member = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
        role = member.role if member else None
        if not _can_manage_modules(project=project, uid=uid, member_role=role):
            raise AuthorizationException("仅项目负责人或测试负责人可维护模块")

        row = await self._modules.get_by_id_in_project(
            db, project_id=project_id, module_id=module_id
        )
        if not row:
            raise NotFoundException("模块不存在")

        all_rows = await self._modules.list_by_project(db, project_id=project_id)
        ids = _collect_descendant_ids(all_rows, module_id)
        try:
            for mid in ids:
                await self._modules.soft_delete(db, mid, deleted_by=str(uid))
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ConflictException("删除模块失败，请稍后重试") from None
