"""测试用例结构（阶段一 2.2.2 / F1.6）。"""

from pydantic import BaseModel, ConfigDict, Field


class TestCaseItem(BaseModel):
    """单条用例；`case_no` 与 `id` 二选一展示时优先 `case_no`。"""

    # LLM 可能多字段；入库前可再收紧校验
    model_config = ConfigDict(extra="ignore")

    id: str | None = Field(default=None, description="可选业务 ID")
    case_no: str = Field(..., min_length=1, description="用例编号")
    module: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    preconditions: str = ""
    steps: str = ""
    expected: str = ""
    priority: str = Field(default="P2", description="如 P0 / P1 / P2")
