from fastapi import Query

from app.constants.enums import SortOrderEnum


class Paging:
    """通用分页查询参数。"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        size: int = Query(10, ge=1, le=100, description="每页数量，最大100"),
        sort_by: str = Query("created_at", min_length=1, max_length=50, description="排序字段"),
        order_by: SortOrderEnum = Query(SortOrderEnum.DESC, description="排序方式"),
    ):
        self.page = page
        self.size = size
        self.sort_by = sort_by
        self.order_by = order_by

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
