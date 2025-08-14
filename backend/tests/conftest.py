import os
import tempfile
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Set up environment before importing app modules
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["OPENAI_API_KEY"] = "test-openai-key"

# Mock problematic imports that require external resources
with patch('core.phoneme_assistant.PhonemeAssistant') as mock_assistant:
    mock_assistant.return_value = Mock()
    with patch('openai.OpenAI') as mock_openai:
        mock_openai.return_value = Mock()
        from database import Base, get_db
        from main import app


# Create a test database
@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp()
    test_database_url = f"sqlite:///{db_path}"
    
    # Create engine and session
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture(scope="function") 
def client(test_db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com", 
        "full_name": "Test User",
        "password": "testpassword123"
    }


@pytest.fixture
def test_user_login_data():
    """Sample login data for testing."""
    return {
        "username": "test@example.com",  # Username is email in this app
        "password": "testpassword123"
    }


# Set environment variables for testing
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing-only")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")  # Mock for testing