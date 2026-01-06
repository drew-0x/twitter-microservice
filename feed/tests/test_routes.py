import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self):
        """Test health check returns 200 OK."""
        with patch("src.routes.get_feed_tweet_ids"), \
             patch("src.routes.GetTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")

            assert response.status_code == 200

    def test_health_check_returns_correct_body(self):
        """Test health check returns expected JSON body."""
        with patch("src.routes.get_feed_tweet_ids"), \
             patch("src.routes.GetTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")
            data = response.json()

            assert data["status"] == "healthy"
            assert data["service"] == "feed-service"


class TestFeedEndpoint:
    """Tests for the feed endpoint."""

    def test_get_feed_success(self):
        """Test successful feed retrieval."""
        mock_tweet_ids = ["tweet-1", "tweet-2"]
        mock_tweets = [
            {"id": "tweet-1", "content": "First"},
            {"id": "tweet-2", "content": "Second"}
        ]

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=mock_tweet_ids), \
             patch("src.routes.GetTweets", return_value=mock_tweets):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed")

            assert response.status_code == 200
            data = response.json()
            assert "tweets" in data
            assert len(data["tweets"]) == 2
            assert data["count"] == 2

    def test_get_feed_empty(self):
        """Test feed returns empty when no tweets."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=[]), \
             patch("src.routes.GetTweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed")

            assert response.status_code == 200
            data = response.json()
            assert data["tweets"] == []
            assert data["count"] == 0

    def test_get_feed_respects_limit(self):
        """Test that limit query parameter is passed correctly."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        mock_get_feed = MagicMock(return_value=[])

        with patch("src.routes.get_feed_tweet_ids", mock_get_feed), \
             patch("src.routes.GetTweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed?limit=25")

            assert response.status_code == 200
            mock_get_feed.assert_called_once()
            # Check limit was passed
            call_kwargs = mock_get_feed.call_args
            assert call_kwargs[1]["limit"] == 25

    def test_get_feed_respects_offset(self):
        """Test that offset query parameter is passed correctly."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        mock_get_feed = MagicMock(return_value=[])

        with patch("src.routes.get_feed_tweet_ids", mock_get_feed), \
             patch("src.routes.GetTweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed?offset=10")

            assert response.status_code == 200
            call_kwargs = mock_get_feed.call_args
            assert call_kwargs[1]["offset"] == 10

    def test_get_feed_limit_validation(self):
        """Test that limit has proper validation."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=[]), \
             patch("src.routes.GetTweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            # Test limit > 100 (should fail validation)
            response = client.get("/feed?limit=200")
            assert response.status_code == 422

            # Test limit < 1 (should fail validation)
            response = client.get("/feed?limit=0")
            assert response.status_code == 422

    def test_get_feed_requires_auth(self):
        """Test that feed endpoint requires authentication."""
        with patch("src.routes.get_feed_tweet_ids"), \
             patch("src.routes.GetTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            # No auth header
            response = client.get("/feed")

            assert response.status_code == 403

    def test_get_feed_includes_pagination_info(self):
        """Test that response includes pagination metadata."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=["t1"]), \
             patch("src.routes.GetTweets", return_value=[{"id": "t1"}]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed?limit=25&offset=10")

            data = response.json()
            assert data["limit"] == 25
            assert data["offset"] == 10


class TestGRPCIntegration:
    """Tests for gRPC client integration."""

    def test_feed_calls_grpc_with_tweet_ids(self):
        """Test that feed calls GetTweets with correct IDs."""
        mock_tweet_ids = ["tweet-1", "tweet-2", "tweet-3"]
        mock_get_tweets = MagicMock(return_value=[])

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=mock_tweet_ids), \
             patch("src.routes.GetTweets", mock_get_tweets):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            client.get("/feed")

            mock_get_tweets.assert_called_once_with(mock_tweet_ids)

    def test_feed_handles_grpc_returning_empty(self):
        """Test that feed handles empty gRPC response."""
        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.get_feed_tweet_ids", return_value=["t1"]), \
             patch("src.routes.GetTweets", return_value=[]):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/feed")

            assert response.status_code == 200
            assert response.json()["tweets"] == []
