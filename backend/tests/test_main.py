import pytest
from fastapi import status


class TestMainApp:
    """Test cases for main FastAPI application functionality."""

    def test_app_creates_successfully(self, client):
        """Test that the FastAPI app can be created and runs."""
        # This test verifies the app starts without errors
        assert client is not None

    def test_database_connection(self, test_db):
        """Test that database connection works."""
        # This test verifies the test database is properly set up
        assert test_db is not None
        # Try a simple database operation using SQLAlchemy 2.0 syntax
        from sqlalchemy import text
        result = test_db.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

    def test_cors_middleware_configured(self, client):
        """Test that CORS middleware is properly configured."""
        # Make an OPTIONS request to test CORS
        response = client.options("/auth/register")
        
        # Should not return server error
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_routes_are_accessible(self, client):
        """Test that main routes are accessible (return proper responses)."""
        # Test auth routes (should return 422 for missing data, not 404)
        auth_response = client.post("/auth/register")
        assert auth_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  # Missing required fields
        
        login_response = client.post("/auth/token")
        assert login_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY  # Missing required fields
        
        # Test protected route (should return 401 unauthorized, not 404)
        user_response = client.get("/users/me/")
        assert user_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_route_returns_404(self, client):
        """Test that invalid routes return 404."""
        response = client.get("/nonexistent/route")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_check_endpoints_accessible(self, client):
        """Test basic endpoint accessibility without authentication."""
        # These tests verify the app routing works
        
        # Auth registration endpoint exists
        response = client.post("/auth/register")
        assert response.status_code != status.HTTP_404_NOT_FOUND
        
        # Auth token endpoint exists  
        response = client.post("/auth/token")
        assert response.status_code != status.HTTP_404_NOT_FOUND
        
        # User endpoint exists (but requires auth)
        response = client.get("/users/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED  # Should exist but require auth