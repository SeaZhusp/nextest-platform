import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware import setup_middleware
from app.db.session import close_database
from app.services.skill.registry import get_skill_registry

app_logger = logging.getLogger("nextest.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    get_skill_registry().reload(settings.skills_dir)
    app_logger.info(
        "技能注册完成: %s (目录=%s)",
        get_skill_registry().list_skill_ids(),
        settings.skills_dir,
    )
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
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
