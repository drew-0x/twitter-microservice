import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.dependencies.db import get_db
from src.dependencies.auth import VerifyToken, UserToken


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Test health check returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_body(self, test_client):
        """Test health check returns expected JSON body."""
        response = test_client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "users-service"


class TestRegisterEndpoint:
    """Tests for the user registration endpoint."""

    def test_register_success(self, test_client_no_auth, test_db):
        """Test successful user registration with real DB."""
        response = test_client_no_auth.post("/users/register", json={
            "email": "newuser@example.com",
            "password": "password123",
            "username": "newuser"
        })

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"

    def test_register_missing_fields(self, test_client_no_auth):
        """Test registration fails with missing fields."""
        response = test_client_no_auth.post("/users/register", json={
            "email": "test@example.com"
        })

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, test_client_no_auth):
        """Test registration fails with invalid email format."""
        response = test_client_no_auth.post("/users/register", json={
            "email": "not-an-email",
            "password": "password123",
            "username": "testuser"
        })

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for the user login endpoint."""

    def test_login_success(self, test_client_no_auth, test_db):
        """Test successful login with real DB."""
        # First register a user
        test_client_no_auth.post("/users/register", json={
            "email": "login@example.com",
            "password": "password123",
            "username": "loginuser"
        })

        # Then try to login
        response = test_client_no_auth.post("/users/login", json={
            "email": "login@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data

    def test_login_user_not_found(self, test_client_no_auth):
        """Test login with non-existent user."""
        response = test_client_no_auth.post("/users/login", json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })

        assert response.status_code == 400
        assert "Invalid Login" in response.json()["detail"]

    def test_login_wrong_password(self, test_client_no_auth, test_db):
        """Test login with incorrect password."""
        # First register a user
        test_client_no_auth.post("/users/register", json={
            "email": "wrongpw@example.com",
            "password": "correctpassword",
            "username": "wrongpwuser"
        })

        # Try to login with wrong password
        response = test_client_no_auth.post("/users/login", json={
            "email": "wrongpw@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 400
        assert "Incorrect Password" in response.json()["detail"]


class TestHelloEndpoint:
    """Tests for the authenticated hello endpoint."""

    def test_hello_authenticated(self, test_client):
        """Test hello endpoint returns user greeting when authenticated."""
        response = test_client.get("/hello")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Hello" in data["message"]

    def test_hello_unauthenticated(self, test_client_no_auth):
        """Test hello endpoint requires authentication."""
        response = test_client_no_auth.get("/hello")

        assert response.status_code == 403


class TestFollowEndpoints:
    """Tests for follow-related endpoints."""

    def test_create_follow_success(self, test_client, test_db):
        """Test successful follow creation."""
        from src.models import User

        # Create a user to follow
        user_to_follow = User("target@example.com", "password123", "targetuser")
        test_db.add(user_to_follow)
        test_db.commit()
        test_db.refresh(user_to_follow)

        response = test_client.post("/follow", json={
            "following_id": str(user_to_follow.id)
        })

        assert response.status_code == 200
        assert response.json()["message"] == "User Followed"

    def test_cannot_follow_self(self, test_client, mock_user_token):
        """Test that user cannot follow themselves."""
        response = test_client.post("/follow", json={
            "following_id": mock_user_token.id  # Same as authenticated user's ID
        })

        assert response.status_code == 400
        assert "can not follow self" in response.json()["detail"]

    def test_follow_nonexistent_user(self, test_client):
        """Test following a user that doesn't exist."""
        response = test_client.post("/follow", json={
            "following_id": "00000000-0000-0000-0000-000000000000"
        })

        assert response.status_code == 404
        assert "user not found" in response.json()["detail"]

    def test_get_followers_empty(self, test_client):
        """Test getting followers when user has none."""
        response = test_client.get("/follow")

        assert response.status_code == 200
        assert response.json()["result"] == []

    def test_get_following_empty(self, test_client):
        """Test getting following list when empty."""
        response = test_client.get("/following")

        assert response.status_code == 200
        assert response.json()["result"] == []

    def test_get_following_returns_list(self, test_client, test_db):
        """Test getting list of users being followed."""
        from src.models import User, Follow

        # Create a user to follow
        user_to_follow = User("followed@example.com", "password123", "followeduser")
        test_db.add(user_to_follow)
        test_db.commit()
        test_db.refresh(user_to_follow)

        # Create the follow relationship
        response = test_client.post("/follow", json={
            "following_id": str(user_to_follow.id)
        })
        assert response.status_code == 200

        # Get the following list
        response = test_client.get("/following")

        assert response.status_code == 200
        result = response.json()["result"]
        assert len(result) >= 1

    def test_delete_follow(self, test_client, test_db):
        """Test unfollowing a user."""
        from src.models import User

        # Create a user to follow
        user_to_follow = User("unfollow@example.com", "password123", "unfollowuser")
        test_db.add(user_to_follow)
        test_db.commit()
        test_db.refresh(user_to_follow)

        # Follow the user
        test_client.post("/follow", json={
            "following_id": str(user_to_follow.id)
        })

        # Unfollow
        response = test_client.delete(f"/follow/{user_to_follow.id}")

        assert response.status_code == 204

    def test_delete_follow_not_found(self, test_client):
        """Test unfollowing when follow relationship doesn't exist."""
        response = test_client.delete("/follow/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert "follow not found" in response.json()["detail"]


class TestFollowByIdEndpoint:
    """Tests for getting follow by ID."""

    def test_get_follow_by_id_not_found(self, test_client):
        """Test getting a follow that doesn't exist."""
        response = test_client.get("/follow/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert "could not find follow" in response.json()["detail"]
