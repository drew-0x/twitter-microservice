import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self):
        """Test that User can be instantiated with required fields."""
        with patch("src.models.hashpw") as mock_hashpw:
            mock_hashpw.return_value = b"hashed_password"

            from src.models import User
            user = User("test@example.com", "password123", "testuser")

            assert user.email == "test@example.com"
            assert user.username == "testuser"
            assert user.password is not None

    def test_user_password_hashing(self):
        """Test that password is hashed on creation."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.gensalt") as mock_gensalt:
            mock_gensalt.return_value = b"salt"
            mock_hashpw.return_value = b"hashed_password"

            from src.models import User
            user = User("test@example.com", "plaintext", "testuser")

            mock_hashpw.assert_called_once()
            assert user.password == b"hashed_password"

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.checkpw") as mock_checkpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"$2b$12$hashedpassword"
            mock_checkpw.return_value = True

            from src.models import User
            user = User("test@example.com", "password123", "testuser")

            result = user.verify_password("password123")

            assert result is True
            mock_checkpw.assert_called_once()

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.checkpw") as mock_checkpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"$2b$12$hashedpassword"
            mock_checkpw.return_value = False

            from src.models import User
            user = User("test@example.com", "password123", "testuser")

            result = user.verify_password("wrongpassword")

            assert result is False

    def test_increment_followers(self):
        """Test incrementing follower count."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"hashed"

            from src.models import User
            user = User("test@example.com", "pass", "testuser")
            user.num_followers = 5

            result = user.increment_followers()

            assert result == 6
            assert user.num_followers == 6

    def test_increment_followers_custom_count(self):
        """Test incrementing follower count by custom amount."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"hashed"

            from src.models import User
            user = User("test@example.com", "pass", "testuser")
            user.num_followers = 5

            result = user.increment_followers(3)

            assert result == 8

    def test_increment_tweets(self):
        """Test incrementing tweet count."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"hashed"

            from src.models import User
            user = User("test@example.com", "pass", "testuser")
            user.num_tweets = 10

            result = user.increment_tweets()

            assert result == 11

    def test_to_dict(self):
        """Test user serialization to dictionary."""
        with patch("src.models.hashpw") as mock_hashpw, \
             patch("src.models.gensalt"):
            mock_hashpw.return_value = b"hashed"

            from src.models import User
            user = User("test@example.com", "pass", "testuser")
            user.num_tweets = 5
            user.num_followers = 10

            result = user.to_dict()

            assert result["email"] == "test@example.com"
            assert result["username"] == "testuser"
            assert result["num_tweets"] == 5
            assert result["num_followers"] == 10
            assert "password" not in result  # Password should not be in dict


class TestFollowModel:
    """Tests for the Follow model."""

    def test_follow_creation(self):
        """Test that Follow can be instantiated."""
        from src.models import Follow

        follow = Follow(
            "550e8400-e29b-41d4-a716-446655440001",
            "550e8400-e29b-41d4-a716-446655440002"
        )

        assert str(follow.follower_id) == "550e8400-e29b-41d4-a716-446655440001"
        assert str(follow.following_id) == "550e8400-e29b-41d4-a716-446655440002"

    def test_follow_to_dict(self):
        """Test follow serialization to dictionary."""
        from src.models import Follow

        follow = Follow(
            "550e8400-e29b-41d4-a716-446655440001",
            "550e8400-e29b-41d4-a716-446655440002"
        )

        result = follow.to_dict()

        assert "id" in result
        assert result["follower_id"] == "550e8400-e29b-41d4-a716-446655440001"
        assert result["following_id"] == "550e8400-e29b-41d4-a716-446655440002"
