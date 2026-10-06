from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import Document, Chunk, UsageLog  # noqa: F401

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.sql_echo)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def initialize_database() -> None:
    url = make_url(settings.database_url)
    if url.get_backend_name() == "sqlite" and url.database not in (None, ":memory:"):
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
