from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ProjectMemberRoleEnum, SortOrderEnum
from app.core.exceptions import AuthorizationException, ConflictException, NotFoundException, ValidationException
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import Participation, ProjectMemberRepository, ProjectRepository
from app.repositories.user import UserRepository
from app.schemas.project import (
    ProjectCreate,
    ProjectListData,
    ProjectMemberAdd,
    ProjectMemberListData,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdate,
)


def _parse_user_id(user_id: str) -> int:
    try:
        return int(user_id)
    except (TypeError, ValueError) as e:
        raise ValidationException("无效的用户身份") from e


def _owner_display_name(user: User | None) -> str:
    if user is None:
        return "—"
    nick = (user.nickname or "").strip()
    return nick or user.username or "—"


def _project_to_out(project: Project, *, uid: int, my_role: str) -> ProjectOut:
    return ProjectOut(
        id=int(project.id),
        name=project.name,
        description=project.description,
        owner_id=int(project.owner_id),
        owner_name=_owner_display_name(project.owner),
        my_role=my_role,
        created_at=project.created_at.isoformat() if project.created_at else "",
        updated_at=project.updated_at.isoformat() if project.updated_at else "",
    )


def _resolve_my_role(project: Project, uid: int, member_role: str | None) -> str:
    if int(project.owner_id) == uid:
        return ProjectMemberRoleEnum.OWNER.value
    if member_role:
        return member_role
    return ProjectMemberRoleEnum.TESTER.value


class ProjectService:
    def __init__(self) -> None:
        self._projects = ProjectRepository()
        self._members = ProjectMemberRepository()
        self._users = UserRepository()

    async def list_projects(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        page: int,
        size: int,
        participation: Participation = "all",
    ) -> ProjectListData:
        uid = _parse_user_id(user_id)
        records, total = await self._projects.list_for_user(
            db,
            user_id=uid,
            page=page,
            size=size,
            participation=participation,
            sort_by="updated_at",
            order_by=SortOrderEnum.DESC,
        )
        items: list[ProjectOut] = []
        for p in records:
            row = await self._projects.get_member_row(db, project_id=int(p.id), user_id=uid)
            member_role = row.role if row else None
            role_str = _resolve_my_role(p, uid, member_role)
            items.append(_project_to_out(p, uid=uid, my_role=role_str))

        return ProjectListData(items=items, total=total, page=page, size=size)

    async def get_project(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
    ) -> ProjectOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        row = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
        member_role = row.role if row else None
        role_str = _resolve_my_role(project, uid, member_role)
        return _project_to_out(project, uid=uid, my_role=role_str)

    async def create_project(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        payload: ProjectCreate,
    ) -> ProjectOut:
        uid = _parse_user_id(user_id)
        name = payload.name.strip()
        if not name:
            raise ValidationException("项目名称不能为空")
        desc = payload.description.strip() if payload.description else None
        if desc == "":
            desc = None

        project = await self._projects.create(
            db,
            {"name": name, "description": desc, "owner_id": uid},
        )
        await self._members.create(
            db,
            {
                "project_id": int(project.id),
                "user_id": uid,
                "role": ProjectMemberRoleEnum.OWNER.value,
            },
        )
        await db.commit()
        reloaded = await self._projects.get_accessible_by_id(db, int(project.id), uid)
        if not reloaded:
            raise NotFoundException("项目创建后加载失败")
        return _project_to_out(
            reloaded,
            uid=uid,
            my_role=ProjectMemberRoleEnum.OWNER.value,
        )

    async def update_project(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        payload: ProjectUpdate,
    ) -> ProjectOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        if int(project.owner_id) != uid:
            raise AuthorizationException("仅项目负责人可编辑项目")

        raw = payload.model_dump(exclude_unset=True)
        data: dict = {}
        if "name" in raw:
            n = (raw["name"] or "").strip()
            if not n:
                raise ValidationException("项目名称不能为空")
            data["name"] = n
        if "description" in raw:
            v = raw["description"]
            if v is None:
                data["description"] = None
            else:
                d = str(v).strip()
                data["description"] = d if d else None

        if not data:
            row = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
            member_role = row.role if row else None
            role_str = _resolve_my_role(project, uid, member_role)
            return _project_to_out(project, uid=uid, my_role=role_str)

        await self._projects.update(db, project_id, data)
        await db.commit()
        fresh = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not fresh:
            raise NotFoundException("项目不存在或无权访问")
        row = await self._projects.get_member_row(db, project_id=project_id, user_id=uid)
        member_role = row.role if row else None
        role_str = _resolve_my_role(fresh, uid, member_role)
        return _project_to_out(fresh, uid=uid, my_role=role_str)

    async def delete_project(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
    ) -> None:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        if int(project.owner_id) != uid:
            raise AuthorizationException("仅项目负责人可删除项目")

        await self._projects.soft_delete(db, project_id, deleted_by=str(uid))
        await self._projects.soft_delete_members_by_project(
            db,
            project_id=project_id,
            deleted_by=str(uid),
        )
        await db.commit()

    async def list_project_members(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
    ) -> ProjectMemberListData:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        rows = await self._members.list_active_with_users(db, project_id)
        items = [
            ProjectMemberOut(
                user_id=int(u.id),
                username=u.username,
                nickname=u.nickname,
                role=m.role,
            )
            for m, u in rows
        ]
        return ProjectMemberListData(items=items)

    async def add_project_member(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        payload: ProjectMemberAdd,
    ) -> ProjectMemberOut:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        if int(project.owner_id) != uid:
            raise AuthorizationException("仅项目负责人可添加成员")

        uname = payload.username.strip()
        if not uname:
            raise ValidationException("用户名不能为空")

        target = await self._users.get_by_username(db, uname)
        if not target:
            raise NotFoundException("用户不存在")

        tid = int(target.id)
        if tid == int(project.owner_id):
            raise ConflictException("负责人已在项目中")

        existing = await self._members.get_active_by_project_and_user(
            db, project_id=project_id, user_id=tid
        )
        if existing:
            raise ConflictException("该用户已是项目成员")

        await self._members.create(
            db,
            {
                "project_id": project_id,
                "user_id": tid,
                "role": payload.role,
            },
        )
        await db.commit()
        return ProjectMemberOut(
            user_id=tid,
            username=target.username,
            nickname=target.nickname,
            role=payload.role,
        )

    async def remove_project_member(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: int,
        member_user_id: int,
    ) -> None:
        uid = _parse_user_id(user_id)
        project = await self._projects.get_accessible_by_id(db, project_id, uid)
        if not project:
            raise NotFoundException("项目不存在或无权访问")
        if int(project.owner_id) != uid:
            raise AuthorizationException("仅项目负责人可移除成员")

        if member_user_id == int(project.owner_id):
            raise ValidationException("不能移除项目负责人")

        row = await self._members.soft_delete_one(
            db,
            project_id=project_id,
            member_user_id=member_user_id,
            deleted_by=str(uid),
        )
        if not row:
            raise NotFoundException("成员不存在或已移除")
        await db.commit()
