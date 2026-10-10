from typing import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

logger = logging.getLogger("f1_predictor.database")

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=(settings.log_level.upper() == "DEBUG"),
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    # Deferred import: register ORM metadata before create_all.
    # Importing eagerly at module level would create a circular import
    # (app.models.* models import Base from this module).
    import app.models  # noqa: F401

    # create_all() issues DDL, i.e. writes. Against a managed Postgres instance
    # that must not happen on every cold start: the schema is created once by
    # scripts/seed_postgres.py, and attempting DDL here would either fail on a
    # read-only role or race across concurrent invocations. SQLite dev/CI keeps
    # the convenience of automatic schema creation.
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        logger.info(
            "Skipping create_all on non-sqlite DATABASE_URL; "
            "run scripts/seed_postgres.py to create and hydrate the schema."
        )
