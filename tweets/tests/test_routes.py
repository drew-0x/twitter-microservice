import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self):
        """Test health check returns 200 OK."""
        with patch("src.routes.DB"), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")

            assert response.status_code == 200

    def test_health_check_returns_correct_body(self):
        """Test health check returns expected JSON body."""
        with patch("src.routes.DB"), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/health")
            data = response.json()

            assert data["status"] == "healthy"
            assert data["service"] == "tweets-service"


class TestCreateTweetEndpoint:
    """Tests for the tweet creation endpoint."""

    def test_create_tweet_success(self):
        """Test successful tweet creation."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.to_dict.return_value = {
            "id": "tweet-1",
            "user_id": "user-1",
            "content": "Test tweet"
        }

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.Tweet", return_value=mock_tweet), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.post("/tweet", json={"content": "Test tweet"})

            assert response.status_code == 200
            assert response.json()["message"] == "tweet created"

    def test_create_tweet_missing_content(self):
        """Test tweet creation fails without content."""
        with patch("src.routes.DB"), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            mock_user_token = MagicMock()
            mock_user_token.id = "user-1"

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.post("/tweet", json={})

            assert response.status_code == 422  # Validation error

    def test_create_tweet_publishes_to_queues(self):
        """Test that creating a tweet publishes to message queues."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.to_dict.return_value = {"id": "tweet-1", "content": "Test"}
        mock_produce = MagicMock()

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.Tweet", return_value=mock_tweet), \
             patch("src.routes.produce_message", mock_produce), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            client.post("/tweet", json={"content": "Test tweet"})

            # Should be called twice: once for feed, once for search
            assert mock_produce.call_count == 2


class TestGetTweetEndpoint:
    """Tests for getting tweets."""

    def test_get_tweets_by_user(self):
        """Test getting user's tweets."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.to_dict.return_value = {"id": "tweet-1", "content": "Test"}
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_tweet]

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.get("/tweet")

            assert response.status_code == 200
            assert "result" in response.json()

    def test_get_tweet_by_id(self):
        """Test getting a specific tweet by ID."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.id = "tweet-1"
        mock_tweet.to_dict.return_value = {"id": "tweet-1", "content": "Test"}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tweet
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/tweet/tweet-1")

            assert response.status_code == 200
            assert "tweet" in response.json()

    def test_get_tweet_not_found(self):
        """Test getting non-existent tweet returns 404."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)

            response = client.get("/tweet/nonexistent-id")

            assert response.status_code == 404


class TestDeleteTweetEndpoint:
    """Tests for deleting tweets."""

    def test_delete_tweet_success(self):
        """Test successful tweet deletion."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.user_id = "user-1"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tweet

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.delete("/tweet/tweet-1")

            assert response.status_code == 200
            assert response.json()["message"] == "tweet deleted"

    def test_delete_tweet_unauthorized(self):
        """Test deleting another user's tweet returns 403."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_tweet.user_id = "other-user"  # Different user
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tweet

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.delete("/tweet/tweet-1")

            assert response.status_code == 403


class TestLikeEndpoints:
    """Tests for like-related endpoints."""

    def test_create_like_success(self):
        """Test successful like creation."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tweet

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.TweetLike"), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.post("/tweet/like/tweet-1")

            assert response.status_code == 200
            mock_tweet.increment_likes.assert_called_once()

    def test_create_like_tweet_not_found(self):
        """Test liking non-existent tweet returns 404."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.post("/tweet/like/nonexistent")

            assert response.status_code == 404


class TestRepostEndpoints:
    """Tests for repost-related endpoints."""

    def test_create_repost_success(self):
        """Test successful repost creation."""
        mock_db = MagicMock()
        mock_tweet = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tweet

        mock_user_token = MagicMock()
        mock_user_token.id = "user-1"

        with patch("src.routes.DB", mock_db), \
             patch("src.routes.TweetRepost"), \
             patch("src.routes.produce_message"), \
             patch("src.routes.IncrementTweets"):
            from src.routes import router
            from src.dependencies.auth import VerifyToken

            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[VerifyToken] = lambda: mock_user_token
            client = TestClient(app)

            response = client.post("/tweet/repost/tweet-1")

            assert response.status_code == 200
            mock_tweet.increment_reposts.assert_called_once()
