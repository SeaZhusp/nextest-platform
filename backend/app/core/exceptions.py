from typing import Any

from fastapi import status

from app.constants.error_codes import ErrorCode


class BaseCustomException(Exception):
    """基础自定义异常"""

    def __init__(
        self,
        message: str,
        code: int = 400,
        status_code: int = 400,
        details: Any = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class AuthenticationException(BaseCustomException):
    """认证异常"""

    def __init__(self, message: str = "认证失败", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class AuthorizationException(BaseCustomException):
    """授权异常"""

    def __init__(self, message: str = "权限不足", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationException(BaseCustomException):
    """验证异常"""

    def __init__(self, message: str = "数据验证失败", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.BAD_REQUEST,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ConflictException(BaseCustomException):
    """冲突异常"""

    def __init__(self, message: str = "数据冲突", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class NotFoundException(BaseCustomException):
    """未找到异常"""

    def __init__(self, message: str = "资源未找到", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class RateLimitException(BaseCustomException):
    """速率限制异常"""

    def __init__(self, message: str = "请求过于频繁", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.TOO_MANY_REQUESTS,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class ServerException(BaseCustomException):
    """服务器异常"""

    def __init__(self, message: str = "服务器内部错误", details: Any = None):
        super().__init__(
            message=message,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class BusinessException(BaseCustomException):
    """业务异常"""

    def __init__(
        self,
        message: str = "业务处理失败",
        code: int = ErrorCode.BUSINESS_ERROR,
        details: Any = None,
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )
