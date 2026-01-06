import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID


class TestTweetModel:
    """Tests for the Tweet model."""

    def test_tweet_creation(self):
        """Test that Tweet can be instantiated."""
        from src.models import Tweet

        tweet = Tweet(
            "550e8400-e29b-41d4-a716-446655440001",
            "Hello, world!"
        )

        assert str(tweet.user_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert tweet.content == "Hello, world!"

    def test_tweet_default_counts(self):
        """Test that tweet counts default to 0."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")

        assert tweet.num_likes == 0
        assert tweet.num_replys == 0
        assert tweet.num_reposts == 0

    def test_increment_likes(self):
        """Test incrementing like count."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_likes = 5

        result = tweet.increment_likes()

        assert result == 6
        assert tweet.num_likes == 6

    def test_increment_likes_custom_count(self):
        """Test incrementing like count by custom amount."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_likes = 5

        result = tweet.increment_likes(3)

        assert result == 8

    def test_decrement_likes(self):
        """Test decrementing like count."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_likes = 5

        result = tweet.decrement_likes()

        assert result == 4
        assert tweet.num_likes == 4

    def test_increment_replys(self):
        """Test incrementing reply count."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_replys = 2

        result = tweet.increment_replys()

        assert result == 3

    def test_increment_reposts(self):
        """Test incrementing repost count."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_reposts = 10

        result = tweet.increment_reposts()

        assert result == 11

    def test_decrement_reposts(self):
        """Test decrementing repost count."""
        from src.models import Tweet

        tweet = Tweet("user-id", "Test content")
        tweet.num_reposts = 10

        result = tweet.decrement_reposts()

        assert result == 9

    def test_to_dict(self):
        """Test tweet serialization to dictionary."""
        from src.models import Tweet

        tweet = Tweet("550e8400-e29b-41d4-a716-446655440001", "Test content")
        tweet.num_likes = 5
        tweet.num_replys = 3
        tweet.num_reposts = 1

        result = tweet.to_dict()

        assert result["content"] == "Test content"
        assert result["num_likes"] == 5
        assert result["num_replys"] == 3
        assert result["num_reposts"] == 1
        assert "id" in result
        assert "user_id" in result


class TestReplyTweetModel:
    """Tests for the ReplyTweet model."""

    def test_reply_tweet_creation(self):
        """Test that ReplyTweet can be instantiated."""
        from src.models import ReplyTweet

        reply = ReplyTweet(
            "user-id",
            "parent-tweet-id",
            "This is a reply!"
        )

        assert str(reply.user_id) == "user-id"
        assert str(reply.parent_id) == "parent-tweet-id"
        assert reply.content == "This is a reply!"

    def test_reply_to_dict(self):
        """Test reply serialization includes parent_id."""
        from src.models import ReplyTweet

        reply = ReplyTweet("user-id", "parent-id", "Reply content")

        result = reply.to_dict()

        assert "parent_id" in result
        assert result["content"] == "Reply content"


class TestTweetLikeModel:
    """Tests for the TweetLike model."""

    def test_tweet_like_creation(self):
        """Test that TweetLike can be instantiated."""
        from src.models import TweetLike

        like = TweetLike("user-id", "tweet-id")

        assert str(like.user_id) == "user-id"
        assert str(like.tweet_id) == "tweet-id"

    def test_tweet_like_to_dict(self):
        """Test like serialization to dictionary."""
        from src.models import TweetLike

        like = TweetLike("user-id", "tweet-id")

        result = like.to_dict()

        assert "id" in result
        assert "user_id" in result
        assert "tweet_id" in result


class TestTweetRepostModel:
    """Tests for the TweetRepost model."""

    def test_tweet_repost_creation(self):
        """Test that TweetRepost can be instantiated."""
        from src.models import TweetRepost

        repost = TweetRepost("user-id", "tweet-id")

        assert str(repost.user_id) == "user-id"
        assert str(repost.tweet_id) == "tweet-id"

    def test_tweet_repost_to_dict(self):
        """Test repost serialization to dictionary."""
        from src.models import TweetRepost

        repost = TweetRepost("user-id", "tweet-id")

        result = repost.to_dict()

        assert "id" in result
        assert "user_id" in result
        assert "tweet_id" in result
