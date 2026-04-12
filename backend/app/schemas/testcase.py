"""测试用例结构（阶段一 2.2.2 / F1.6）。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


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

    @staticmethod
    def _join_if_list(v: Any, *, sep: str = "\n") -> str:
        if isinstance(v, list):
            return sep.join(str(x).strip() for x in v if str(x).strip())
        return str(v) if v is not None else ""

    @model_validator(mode="before")
    @classmethod
    def normalize_llm_shape(cls, data: Any) -> Any:
        """兼容常见模型输出：仅有 id、steps 为数组、编号为数字等。"""
        if not isinstance(data, dict):
            return data
        d: dict[str, Any] = dict(data)

        cid = d.get("case_no")
        id_v = d.get("id")
        if cid is None or (isinstance(cid, str) and not cid.strip()):
            if id_v is not None and str(id_v).strip():
                d["case_no"] = str(id_v).strip()
        elif isinstance(cid, (int, float)):
            d["case_no"] = str(int(cid)) if float(cid) == int(cid) else str(cid)

        if isinstance(d.get("steps"), list):
            d["steps"] = cls._join_if_list(d["steps"])
        if isinstance(d.get("expected"), list):
            d["expected"] = cls._join_if_list(d["expected"])

        pr = d.get("priority")
        if pr is not None and not isinstance(pr, str):
            d["priority"] = str(pr).strip() or "P2"

        for key, fallback in (("module", "未指定模块"), ("title", "未命名用例")):
            v = d.get(key)
            if v is None or (isinstance(v, str) and not v.strip()):
                d[key] = fallback

        return d
