from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Apply any pending Alembic migrations at startup (idempotent — no-op if already at head)."""
    import asyncio
    import os
    from alembic.config import Config
    from alembic import command

    alembic_ini = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    cfg = Config(alembic_ini)
    await asyncio.get_event_loop().run_in_executor(None, command.upgrade, cfg, "head")
