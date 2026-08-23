import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# Add backend/ to sys.path so imports resolve from alembic/ subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import Base  # noqa: E402 — after sys.path insert
import db.models  # noqa: F401, E402 — registers all ORM classes with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    # Prefer DATABASE_URL env var, then fall back to pydantic settings.
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        from config import settings
        url = settings.database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Export it or add it to backend/.env before running alembic."
        )
    # asyncpg driver is required for the async engine used by the app.
    # Alembic runs migrations synchronously via run_sync, but still needs
    # the async engine to connect — this is the official recommended pattern.
    return url if "asyncpg" in url else url.replace("postgresql://", "postgresql+asyncpg://")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(get_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
