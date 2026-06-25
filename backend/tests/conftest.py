"""Test fixtures and configuration."""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models import User, Tag, post_tags

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a fresh database for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    """Return an async HTTP client with test DB override."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession):
    """Create and return a test user."""
    user = User(
        username="lg鹿铭",
        email="test@test.com",
        hashed_password=hash_password("password123"),
        nickname="TestUser",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_user2(db_session: AsyncSession):
    """Create a second test user for permission tests."""
    user = User(
        username="otheruser",
        email="other@test.com",
        hashed_password=hash_password("password123"),
        nickname="OtherUser",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(async_client: AsyncClient, test_user: User):
    """Login and return auth headers for test_user."""
    resp = await async_client.post("/api/v1/auth/login", json={
        "username": "lg鹿铭", "password": "password123"
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def auth_headers2(async_client: AsyncClient, test_user2: User):
    """Login and return auth headers for test_user2."""
    resp = await async_client.post("/api/v1/auth/login", json={
        "username": "otheruser", "password": "password123"
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
