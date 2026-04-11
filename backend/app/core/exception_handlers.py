import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.constants.error_codes import ErrorCode
from app.core.exceptions import BaseCustomException

logger = logging.getLogger(__name__)


def error_json_response(
    msg: str = "error",
    *,
    code: int = 400,
    status: int = 400,
    message: str | None = None,
    **extra: Any,
) -> JSONResponse:
    if message is not None:
        msg = message
    body: dict[str, Any] = {"code": code, "message": msg, "data": None, **extra}
    return JSONResponse(content=body, status_code=status)


def _friendly_validation_message(exc: RequestValidationError) -> str:
    if not exc.errors():
        return "请求数据验证失败"

    first_error = exc.errors()[0]
    error_type = first_error.get("type", "")
    fallback = first_error.get("msg", "请求数据验证失败")
    type_map = {
        "missing": "请求失败，缺少必填项",
        "list_type": "类型错误，输入应该是一个有效的列表",
        "int_parsing": "类型错误，输入应该是一个整数",
        "bool_parsing": "类型错误，输入应该是一个布尔值",
    }
    return type_map.get(error_type, fallback)


def _http_status_to_code(status_code: int) -> int:
    mapping = {
        status.HTTP_400_BAD_REQUEST: ErrorCode.BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED: ErrorCode.UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN: ErrorCode.FORBIDDEN,
        status.HTTP_404_NOT_FOUND: ErrorCode.NOT_FOUND,
        status.HTTP_409_CONFLICT: ErrorCode.CONFLICT,
        status.HTTP_422_UNPROCESSABLE_ENTITY: ErrorCode.VALIDATION_FAILED,
        status.HTTP_429_TOO_MANY_REQUESTS: ErrorCode.TOO_MANY_REQUESTS,
        status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorCode.INTERNAL_SERVER_ERROR,
    }
    return mapping.get(status_code, status_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(
        request: Request, exc: BaseCustomException
    ) -> JSONResponse:
        logger.error("CustomException path=%s message=%s", request.url.path, exc.message)
        return error_json_response(
            exc.message,
            code=exc.code,
            status=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.error(
            "HTTPException path=%s status=%s detail=%s",
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return error_json_response(
            str(exc.detail),
            code=_http_status_to_code(exc.status_code),
            status=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.error("ValidationError path=%s errors=%s", request.url.path, exc.errors())
        return error_json_response(
            _friendly_validation_message(exc),
            code=ErrorCode.VALIDATION_FAILED,
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.errors(),
        )

    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.error("ValueError path=%s error=%s", request.url.path, str(exc))
        return error_json_response(
            str(exc),
            code=ErrorCode.BAD_REQUEST,
            status=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("UnhandledException path=%s", request.url.path, exc_info=exc)
        return error_json_response(
            "服务器内部错误，请稍后重试",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
