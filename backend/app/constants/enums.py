from enum import Enum


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class TokenTypeEnum(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class SortOrderEnum(str, Enum):
    ASC = "asc"
    DESC = "desc"
