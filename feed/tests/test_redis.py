import pytest
from unittest.mock import patch, MagicMock


class TestGetFeedTweetIds:
    """Tests for Redis feed operations."""

    def test_get_feed_tweet_ids_returns_list(self):
        """Test that get_feed_tweet_ids returns a list."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = ["tweet-1", "tweet-2", "tweet-3"]

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            result = get_feed_tweet_ids("user-123")

            assert isinstance(result, list)
            assert len(result) == 3

    def test_get_feed_tweet_ids_uses_correct_key(self):
        """Test that the correct Redis key pattern is used."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            get_feed_tweet_ids("user-123")

            mock_redis.lrange.assert_called_once()
            call_args = mock_redis.lrange.call_args[0]
            assert call_args[0] == "feed:user-123"

    def test_get_feed_tweet_ids_respects_limit(self):
        """Test that limit parameter is respected."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = ["tweet-1", "tweet-2"]

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            get_feed_tweet_ids("user-123", limit=10)

            call_args = mock_redis.lrange.call_args[0]
            # Should be lrange(key, offset, offset + limit - 1)
            assert call_args[1] == 0  # offset
            assert call_args[2] == 9  # limit - 1

    def test_get_feed_tweet_ids_respects_offset(self):
        """Test that offset parameter is respected."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            get_feed_tweet_ids("user-123", limit=10, offset=5)

            call_args = mock_redis.lrange.call_args[0]
            assert call_args[1] == 5  # offset
            assert call_args[2] == 14  # offset + limit - 1

    def test_get_feed_tweet_ids_empty_feed(self):
        """Test handling of empty feed."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            result = get_feed_tweet_ids("user-with-no-feed")

            assert result == []

    def test_get_feed_tweet_ids_default_params(self):
        """Test default limit and offset values."""
        mock_redis = MagicMock()
        mock_redis.lrange.return_value = []

        with patch("src.dependencies.redis.redis_client", mock_redis):
            from src.dependencies.redis import get_feed_tweet_ids

            get_feed_tweet_ids("user-123")

            call_args = mock_redis.lrange.call_args[0]
            # Default: limit=50, offset=0
            assert call_args[1] == 0
            assert call_args[2] == 49
