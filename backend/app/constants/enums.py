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
