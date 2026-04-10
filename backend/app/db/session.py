from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _is_mysql_url(url: str) -> bool:
    return url.startswith("mysql+") or "+aiomysql" in url or "+asyncmy" in url


_async_connect_args = {"charset": "utf8mb4"} if _is_mysql_url(settings.database_url) else {}

async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    echo_pool=settings.debug,
    pool_size=5,
    max_overflow=5,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args=_async_connect_args,
)

session_factory = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_database() -> None:
    await async_engine.dispose()


def get_sync_engine():
    sync_url = (
        settings.database_url.replace("+aiomysql", "+pymysql")
        .replace("+asyncmy", "+pymysql")
        .replace("+asyncpg", "+psycopg")
    )
    sync_connect_args = {"charset": "utf8mb4"} if _is_mysql_url(sync_url) else {}
    return create_engine(
        sync_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=sync_connect_args,
    )
