from fastapi import Query


class Paging:
    """通用分页查询参数；排序由 service / repository 按业务决定，不在此声明。"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        size: int = Query(10, ge=1, le=100, description="每页数量，最大100"),
    ):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
