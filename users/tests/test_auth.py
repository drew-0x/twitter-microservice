import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import jwt


class TestSignJWT:
    """Tests for JWT signing functionality."""

    def test_sign_jwt_returns_string(self):
        """Test that sign_jwt returns a string token."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            # Re-import to pick up the patched env
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            token = auth_module.sign_jwt("user-123", "testuser")

            assert isinstance(token, str)
            assert len(token) > 0

    def test_sign_jwt_contains_user_data(self):
        """Test that signed JWT contains correct user data."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            token = auth_module.sign_jwt("user-123", "testuser")
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

            assert decoded["user_id"] == "user-123"
            assert decoded["username"] == "testuser"

    def test_sign_jwt_has_expiration(self):
        """Test that signed JWT has expiration claim."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            token = auth_module.sign_jwt("user-123", "testuser")
            decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])

            assert "exp" in decoded
            assert "iat" in decoded


class TestDecodeJWT:
    """Tests for JWT decoding functionality."""

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            # Create a valid token
            token = auth_module.sign_jwt("user-123", "testuser")

            # Decode it
            result = auth_module.decode_jwt(token)

            assert result["user_id"] == "user-123"
            assert result["username"] == "testuser"

    def test_decode_expired_token_raises(self):
        """Test that decoding expired token raises ExpiredSignatureError."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            # Create an expired token manually
            expired_payload = {
                "user_id": "user-123",
                "username": "testuser",
                "exp": datetime.utcnow() - timedelta(hours=1),
                "iat": datetime.utcnow() - timedelta(hours=2)
            }
            expired_token = jwt.encode(expired_payload, "test-secret-key", algorithm="HS256")

            with pytest.raises(jwt.ExpiredSignatureError):
                auth_module.decode_jwt(expired_token)

    def test_decode_invalid_token_raises(self):
        """Test that decoding invalid token raises InvalidTokenError."""
        with patch.dict("os.environ", {"JWT_SECRET": "test-secret-key"}):
            import importlib
            import src.dependencies.auth as auth_module
            importlib.reload(auth_module)

            with pytest.raises(jwt.InvalidTokenError):
                auth_module.decode_jwt("invalid.token.here")


class TestUserToken:
    """Tests for UserToken dataclass."""

    def test_user_token_creation(self):
        """Test UserToken dataclass creation."""
        from src.dependencies.auth import UserToken

        user_token = UserToken(id="user-123", username="testuser")

        assert user_token.id == "user-123"
        assert user_token.username == "testuser"
