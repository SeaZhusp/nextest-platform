from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import SortOrderEnum
from app.core.exceptions import NotFoundException, ValidationException
from app.models.base import ModelBase

ModelType = TypeVar("ModelType", bound=ModelBase)


class BaseRepository(Generic[ModelType]):
    """轻量通用仓储：CRUD、分页、排序、软删除。"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def _base_query(self) -> Select[tuple[ModelType]]:
        return select(self.model).where(self.model.deleted_at.is_(None))

    def _resolve_sort_field(self, sort_by: str):
        if not hasattr(self.model, sort_by):
            raise ValidationException(f"排序字段不存在: {sort_by}")
        return getattr(self.model, sort_by)

    async def get_by_id(self, db: AsyncSession, record_id: int) -> ModelType | None:
        result = await db.execute(
            self._base_query().where(self.model.id == record_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def require_by_id(self, db: AsyncSession, record_id: int) -> ModelType:
        record = await self.get_by_id(db, record_id)
        if not record:
            raise NotFoundException(f"{self.model.__name__}({record_id}) 不存在")
        return record

    async def list_paginated(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        sort_by: str = "created_at",
        order_by: SortOrderEnum = SortOrderEnum.DESC,
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[ModelType], int]:
        query = self._base_query()
        if filters:
            for key, value in filters.items():
                if not hasattr(self.model, key):
                    raise ValidationException(f"过滤字段不存在: {key}")
                field = getattr(self.model, key)
                query = query.where(field == value)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        sort_field = self._resolve_sort_field(sort_by)
        query = query.order_by(
            sort_field.desc() if order_by == SortOrderEnum.DESC else sort_field.asc()
        )
        query = query.offset((page - 1) * size).limit(size)

        records = (await db.execute(query)).scalars().all()
        return list(records), int(total)

    async def create(self, db: AsyncSession, data: dict[str, Any]) -> ModelType:
        record = self.model(**data)
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def update(
        self,
        db: AsyncSession,
        record_id: int,
        data: dict[str, Any],
    ) -> ModelType:
        record = await self.require_by_id(db, record_id)
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        await db.flush()
        await db.refresh(record)
        return record

    async def soft_delete(
        self,
        db: AsyncSession,
        record_id: int,
        deleted_by: str | None = None,
    ) -> None:
        record = await self.require_by_id(db, record_id)
        record.deleted_at = datetime.now(timezone.utc)
        record.deleted_by = deleted_by
        await db.flush()

    async def hard_delete(self, db: AsyncSession, record_id: int) -> None:
        record = await self.require_by_id(db, record_id)
        await db.delete(record)
        await db.flush()
