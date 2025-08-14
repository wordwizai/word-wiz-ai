import pytest
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import status
from auth.auth_handler import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


class TestAuthentication:
    """Test cases for authentication functionality."""

    def test_user_registration(self, client, test_user_data):
        """Test user registration endpoint."""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert data["full_name"] == test_user_data["full_name"]
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_user_registration_duplicate_email(self, client, test_user_data):
        """Test that registering with duplicate email fails."""
        # Register user first time
        client.post("/auth/register", json=test_user_data)
        
        # Try to register again with same email
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_standard_login_without_remember_me(self, client, test_user_data, test_user_login_data):
        """Test standard login without Remember Me (30 minutes token)."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login without remember_me
        response = client.post("/auth/token", data=test_user_login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        
        # Decode token to verify expiration
        token = data["access_token"]
        decoded = jwt.decode(token, "test-secret-key-for-testing-only", algorithms=[ALGORITHM])
        
        # Check token expiration is around 30 minutes (default)
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_diff = exp_time - current_time
        
        # Should be close to ACCESS_TOKEN_EXPIRE_MINUTES (converted to seconds)
        expected_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert abs(time_diff.total_seconds() - expected_seconds) < 60  # Within 1 minute tolerance

    def test_login_with_remember_me(self, client, test_user_data, test_user_login_data):
        """Test login with Remember Me (30 days token)."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login with remember_me=True
        login_data = test_user_login_data.copy()
        response = client.post("/auth/token", data=login_data, params={"remember_me": True})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        
        # Decode token to verify extended expiration
        token = data["access_token"]
        decoded = jwt.decode(token, "test-secret-key-for-testing-only", algorithms=[ALGORITHM])
        
        # Check token expiration is around 30 days
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        current_time = datetime.now(timezone.utc)
        time_diff = exp_time - current_time
        
        # Should be close to 30 days (in seconds)
        expected_seconds = 30 * 24 * 60 * 60  # 30 days in seconds
        assert abs(time_diff.total_seconds() - expected_seconds) < 3600  # Within 1 hour tolerance

    def test_login_invalid_credentials(self, client, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Try login with wrong password
        invalid_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/token", data=invalid_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }
        response = client.post("/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_access_protected_route_with_valid_token(self, client, test_user_data, test_user_login_data):
        """Test accessing protected route with valid token."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data=test_user_login_data)
        token = login_response.json()["access_token"]
        
        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/users/me/", headers=headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user_data["email"]

    def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without token returns 401."""
        response = client.get("/users/me/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me/", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_payload_contains_correct_user(self, client, test_user_data, test_user_login_data):
        """Test that token payload contains correct user information."""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        login_response = client.post("/auth/token", data=test_user_login_data)
        token = login_response.json()["access_token"]
        
        # Decode token
        decoded = jwt.decode(token, "test-secret-key-for-testing-only", algorithms=[ALGORITHM])
        
        # Verify token contains correct user email
        assert decoded["sub"] == test_user_data["email"]
        assert "exp" in decoded  # Expiration should be present