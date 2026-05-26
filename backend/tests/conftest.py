"""
OmicsFlow Test Configuration and Fixtures

Provides test fixtures for database sessions, API clients, and test data.
Uses SQLite in-memory database for fast, isolated tests.
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set test environment variables to disable rate limiting
os.environ["RATE_LIMIT_RPM"] = "10000"

# Test database URL (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create a test database engine with fresh tables for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Import and create all tables
        from models.database import Base
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        from models.database import Base
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with mocked database dependencies."""
    from api.main import app
    from services.database import get_db

    # Override database dependency
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
    }


@pytest.fixture
def sample_pipeline_data() -> dict:
    """Sample pipeline creation data."""
    return {
        "name": "Test Pipeline",
        "description": "A test bioinformatics pipeline",
        "pipeline_type": "rnaseq",
    }


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task creation data."""
    return {
        "name": "Test Task",
        "pipeline_id": "",  # Must be set in test
    }
