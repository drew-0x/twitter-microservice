import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self):
        """Test health check returns 200 OK."""
        with patch("src.routes.search_tweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")

            assert response.status_code == 200

    def test_health_check_returns_correct_body(self):
        """Test health check returns expected JSON body."""
        with patch("src.routes.search_tweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")
            data = response.json()

            assert data["status"] == "healthy"
            assert data["service"] == "search-service"


class TestSearchEndpoint:
    """Tests for the search endpoint."""

    def test_search_success(self):
        """Test successful search."""
        mock_results = [
            {"id": "tweet-1", "content": "Hello world", "score": 1.0},
            {"id": "tweet-2", "content": "Hello there", "score": 0.8}
        ]

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets", return_value=mock_results):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/search?q=hello")

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            assert data["query"] == "hello"

    def test_search_empty_results(self):
        """Test search with no results."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/search?q=nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == []
            assert data["count"] == 0

    def test_search_requires_query(self):
        """Test that search requires q parameter."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            # No query parameter
            response = client.get("/search")

            assert response.status_code == 422  # Validation error

    def test_search_respects_limit(self):
        """Test that limit query parameter is passed correctly."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"
        mock_search = MagicMock(return_value=[])

        with patch("src.routes.search_tweets", mock_search):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/search?q=test&limit=10")

            assert response.status_code == 200
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["limit"] == 10

    def test_search_respects_offset(self):
        """Test that offset query parameter is passed correctly."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"
        mock_search = MagicMock(return_value=[])

        with patch("src.routes.search_tweets", mock_search):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/search?q=test&offset=20")

            assert response.status_code == 200
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs["offset"] == 20

    def test_search_limit_validation(self):
        """Test that limit has proper validation."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            # Test limit > 100 (should fail)
            response = client.get("/search?q=test&limit=200")
            assert response.status_code == 422

            # Test limit < 1 (should fail)
            response = client.get("/search?q=test&limit=0")
            assert response.status_code == 422

    def test_search_query_min_length(self):
        """Test that query has minimum length validation."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            # Empty query should fail (min_length=1)
            response = client.get("/search?q=")
            assert response.status_code == 422

    def test_search_requires_auth(self):
        """Test that search endpoint requires authentication."""
        with patch("src.routes.search_tweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # No auth header
            response = client.get("/search?q=test")

            assert response.status_code == 403

    def test_search_includes_pagination_info(self):
        """Test that response includes pagination metadata."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.search_tweets", return_value=[{"id": "1"}]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/search?q=test&limit=15&offset=5")

            data = response.json()
            assert data["limit"] == 15
            assert data["offset"] == 5
            assert data["count"] == 1
