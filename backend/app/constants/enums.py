from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"


class TokenTypeEnum(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class SortOrderEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ProjectMemberRoleEnum(str, Enum):
    OWNER = "owner"
    LEADER = "leader"
    TESTER = "tester"


class TestCaseTypeEnum(str, Enum):
    """用例类型（与接口层校验一致）。"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    COMPATIBILITY = "compatibility"
    SCENARIO = "scenario"


class TestCaseSourceEnum(str, Enum):
    AI = "ai"
    MANUAL = "manual"
