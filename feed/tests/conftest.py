import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.dependencies.auth import VerifyToken, UserToken
from src.dependencies.redis import get_redis_client


# Set test environment variables
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")
os.environ.setdefault("JAEGER", "localhost:4317")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("TWEET_SERVICE_GRPC_TARGET", "localhost:50052")


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    mock_client = MagicMock()
    mock_client.lrange = MagicMock(return_value=[])
    mock_client.lpush = MagicMock()
    mock_client.ltrim = MagicMock()
    return mock_client


@pytest.fixture
def override_get_redis(mock_redis_client):
    """Override get_redis_client dependency for testing."""
    def _override_get_redis():
        yield mock_redis_client
    return _override_get_redis


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
def test_client(
    override_get_redis,
    override_verify_token,
    mock_redis_client,
) -> Generator[TestClient, None, None]:
    """Create a test client with overridden dependencies."""
    with patch("src.routes.GetTweets", return_value=[]):
        from src import App

        app = App()
        app.api.dependency_overrides[get_redis_client] = override_get_redis
        app.api.dependency_overrides[VerifyToken] = override_verify_token

        with TestClient(app.api) as client:
            yield client

        app.api.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth(override_get_redis) -> Generator[TestClient, None, None]:
    """Create a test client without auth override."""
    with patch("src.routes.GetTweets", return_value=[]):
        from src import App

        app = App()
        app.api.dependency_overrides[get_redis_client] = override_get_redis

        with TestClient(app.api) as client:
            yield client

        app.api.dependency_overrides.clear()


@pytest.fixture
def sample_tweet_ids():
    """Sample list of tweet IDs from Redis."""
    return [
        "tweet-1",
        "tweet-2",
        "tweet-3",
        "tweet-4",
        "tweet-5"
    ]


@pytest.fixture
def sample_tweets():
    """Sample hydrated tweets from gRPC."""
    return [
        {
            "id": "tweet-1",
            "user_id": "user-1",
            "content": "First tweet",
            "num_likes": 10,
            "num_replys": 2,
            "num_reposts": 1,
            "created_at": "2024-01-01T12:00:00"
        },
        {
            "id": "tweet-2",
            "user_id": "user-2",
            "content": "Second tweet",
            "num_likes": 5,
            "num_replys": 0,
            "num_reposts": 0,
            "created_at": "2024-01-01T11:00:00"
        }
    ]
