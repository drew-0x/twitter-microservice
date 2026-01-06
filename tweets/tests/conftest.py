import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.dependencies.db import Base, get_db
from src.dependencies.auth import VerifyToken, UserToken


# Set test environment variables
os.environ.setdefault("DB_USERNAME", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_DATABASE", "test_db")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")
os.environ.setdefault("JAEGER", "localhost:4317")
os.environ.setdefault("RABBITMQ_URL", "amqp://test:test@localhost:5672")
os.environ.setdefault("USER_SERVICE_GRPC_TARGET", "localhost:50051")


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
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def override_get_db(test_db):
    """Override get_db dependency for testing."""
    def _override_get_db():
        try:
            yield test_db
        finally:
            pass
    return _override_get_db


@pytest.fixture
def mock_user_token():
    """Create a mock user token for authenticated requests."""
    return UserToken(
        id="550e8400-e29b-41d4-a716-446655440001",
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
    """Create a test client with overridden dependencies."""
    # Mock external dependencies (RabbitMQ, gRPC)
    with patch("src.routes.produce_message"), \
         patch("src.routes.IncrementTweets"):
        from src import App

        app = App()
        app.api.dependency_overrides[get_db] = override_get_db
        app.api.dependency_overrides[VerifyToken] = override_verify_token

        with TestClient(app.api) as client:
            yield client

        app.api.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth(override_get_db) -> Generator[TestClient, None, None]:
    """Create a test client without auth override."""
    with patch("src.routes.produce_message"), \
         patch("src.routes.IncrementTweets"):
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
def sample_tweet_data():
    """Sample tweet data for testing."""
    return {
        "content": "This is a test tweet!"
    }


@pytest.fixture
def sample_tweet_dict():
    """Sample tweet dict as returned by Tweet.to_dict()."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "content": "This is a test tweet!",
        "num_likes": 0,
        "num_replys": 0,
        "num_reposts": 0,
        "created_at": "2024-01-01T00:00:00"
    }


@pytest.fixture
def auth_headers():
    """Authorization headers with Bearer token."""
    return {"Authorization": "Bearer mock-jwt-token"}
