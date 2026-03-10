import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.infrastructure.database import get_db, get_read_db
from app.main import app
from app.models import Base


@pytest.fixture
async def db_engine(postgres_url):
    engine = create_async_engine(postgres_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_get_read_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_read_db] = override_get_read_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    await client.post(
        "/auth/register",
        json={
            "email": "admin@test.com",
            "password": "StrongPass123!",
            "full_name": "Admin User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "StrongPass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
