import os
import pytest
from typing import Generator
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.dependencies.db import Base, get_db
from src.dependencies.auth import VerifyToken, UserToken


# Set test environment variables before any imports
os.environ.setdefault("DB_USERNAME", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_DATABASE", "test_db")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")
os.environ.setdefault("JAEGER", "localhost:4317")


# Test database setup - SQLite in-memory for fast tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def override_get_db(test_db):
    """Override get_db dependency for testing."""
    def _override_get_db():
        try:
            yield test_db
        finally:
            pass  # Session cleanup handled by test_db fixture
    return _override_get_db


@pytest.fixture
def mock_user_token():
    """Create a mock user token for authenticated requests."""
    return UserToken(
        id="550e8400-e29b-41d4-a716-446655440000",
        username="testuser"
    )


@pytest.fixture
def override_verify_token(mock_user_token):
    """Override VerifyToken dependency for testing."""
    def _override_verify_token():
        return mock_user_token
    return _override_verify_token


@pytest.fixture
def test_client(override_get_db, override_verify_token) -> Generator[TestClient, None, None]:
    """
    Create a test client with overridden dependencies.

    Usage:
        def test_something(test_client):
            response = test_client.get("/some-endpoint")
            assert response.status_code == 200
    """
    from src import App

    app = App()
    app.api.dependency_overrides[get_db] = override_get_db
    app.api.dependency_overrides[VerifyToken] = override_verify_token

    with TestClient(app.api) as client:
        yield client

    # Clean up overrides
    app.api.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth(override_get_db) -> Generator[TestClient, None, None]:
    """
    Create a test client without auth override (for testing auth failures).
    """
    from src import App

    app = App()
    app.api.dependency_overrides[get_db] = override_get_db

    with TestClient(app.api) as client:
        yield client

    app.api.dependency_overrides.clear()


@pytest.fixture
def mock_db_session():
    """Create a mock database session for unit testing without DB."""
    mock_session = MagicMock(spec=Session)
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.rollback = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.delete = MagicMock()
    mock_session.query = MagicMock()
    mock_session.close = MagicMock()
    return mock_session


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    }


@pytest.fixture
def sample_user_dict():
    """Sample user dict as returned by User.to_dict()."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "username": "testuser",
        "num_tweets": 0,
        "num_followers": 0,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def mock_jwt_token():
    """Sample JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAwIiwidXNlcm5hbWUiOiJ0ZXN0dXNlciJ9.test"


@pytest.fixture
def auth_headers(mock_jwt_token):
    """Authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}
