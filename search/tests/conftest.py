import os
import pytest
from typing import Generator
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.dependencies.auth import VerifyToken, UserToken
from src.dependencies.elasticsearch import get_search_client, SearchClient


# Set test environment variables
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")
os.environ.setdefault("JAEGER", "localhost:4317")
os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")


class MockTestSearchClient:
    """Mock search client for testing."""

    def __init__(self, results: list[dict] | None = None):
        self.results = results or []

    def search(self, query: str, limit: int = 20, offset: int = 0) -> list[dict]:
        """Return mock results."""
        return self.results


@pytest.fixture
def mock_search_client():
    """Create a mock search client for testing."""
    return MockTestSearchClient()


@pytest.fixture
def override_get_search_client(mock_search_client):
    """Override get_search_client dependency for testing."""
    def _override_get_search_client():
        yield mock_search_client
    return _override_get_search_client


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
    override_get_search_client,
    override_verify_token,
) -> Generator[TestClient, None, None]:
    """Create a test client with overridden dependencies."""
    from src import App

    app = App()
    app.api.dependency_overrides[get_search_client] = override_get_search_client
    app.api.dependency_overrides[VerifyToken] = override_verify_token

    with TestClient(app.api) as client:
        yield client

    app.api.dependency_overrides.clear()


@pytest.fixture
def test_client_no_auth(override_get_search_client) -> Generator[TestClient, None, None]:
    """Create a test client without auth override."""
    from src import App

    app = App()
    app.api.dependency_overrides[get_search_client] = override_get_search_client

    with TestClient(app.api) as client:
        yield client

    app.api.dependency_overrides.clear()


@pytest.fixture
def sample_search_results():
    """Sample search results from Elasticsearch."""
    return [
        {
            "id": "tweet-1",
            "user_id": "user-1",
            "content": "Hello world",
            "score": 1.5
        },
        {
            "id": "tweet-2",
            "user_id": "user-2",
            "content": "Hello there",
            "score": 1.2
        }
    ]
