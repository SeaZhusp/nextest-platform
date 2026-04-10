import logging
import sys
import time
import uuid
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

try:
    from loguru import logger
except ImportError:  # pragma: no cover - runtime fallback
    logger = None


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        if logger is None:
            return
        level = record.levelname
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(log_level: str | None = None, log_dir: str = "logs") -> None:
    level = (log_level or "DEBUG" if settings.environment == "dev" else "INFO").upper()
    if logger is None:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
        return

    is_dev = settings.environment == "dev"
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.configure(extra={"request_id": "-"})
    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        enqueue=True,
        backtrace=is_dev,
        diagnose=is_dev,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "rid={extra[request_id]} | "
            "{name}:{function}:{line} - <level>{message}</level>"
        ),
    )
    logger.add(
        log_path / "app.log",
        level=level,
        enqueue=True,
        rotation="20 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | rid={extra[request_id]} | {name}:{function}:{line} - {message}",
    )
    logger.add(
        log_path / "error.log",
        level="ERROR",
        enqueue=True,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        backtrace=False,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | rid={extra[request_id]} | {name}:{function}:{line} - {message}",
    )

    intercept_handler = InterceptHandler()
    logging.root.handlers = [intercept_handler]
    logging.root.setLevel(level)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        named_logger = logging.getLogger(name)
        named_logger.handlers = [intercept_handler]
        named_logger.propagate = False


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()

        if logger is not None:
            request_logger = logger.bind(request_id=request_id)
        else:
            request_logger = logging.getLogger("nextest.api")

        try:
            response = await call_next(request)
        except Exception:
            if logger is not None:
                request_logger.exception(
                    "Unhandled error while processing {} {}",
                    request.method,
                    request.url.path,
                )
            else:
                request_logger.exception(
                    "Unhandled error while processing %s %s",
                    request.method,
                    request.url.path,
                )
            raise

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        if logger is not None:
            request_logger.info(
                "HTTP {} {} status={} elapsed_ms={}",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
        else:
            request_logger.info(
                "HTTP %s %s status=%s elapsed_ms=%s request_id=%s",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                request_id,
            )
        return response
