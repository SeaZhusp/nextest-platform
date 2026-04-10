import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.api.v2.router import router as v2_router
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware import setup_middleware
from app.db.session import close_database

app_logger = logging.getLogger("nextest.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    app_logger.info("Application startup complete")
    yield
    await close_database()
    app_logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NexTest Platform API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    setup_middleware(app)
    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")
    app.include_router(v2_router, prefix="/api/v2")
    return app


app = create_app()
