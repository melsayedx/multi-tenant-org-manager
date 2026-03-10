from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url, pool_pre_ping=True, echo=settings.debug
)

async_session = async_sessionmaker(engine, expire_on_commit=False)
async_read_session = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Read-only session — no transaction, no commit/rollback overhead."""
    async with async_read_session() as session:
        yield session
