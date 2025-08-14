# Backend Testing Guide

This document provides instructions for running and understanding the backend tests for Word Wiz AI.

## Test Overview

The backend test suite provides comprehensive coverage for the FastAPI application, including:

### Authentication Tests (`test_auth.py`)
- **User Registration**: Tests user creation, duplicate email handling
- **Login Functionality**: Tests standard login (30 min token) and "Remember Me" login (30 day token)
- **Token Validation**: Verifies JWT token creation, expiration, and payload
- **Protected Routes**: Tests access control with valid/invalid tokens

### User Management Tests (`test_user.py`)
- **User Profile Access**: Tests getting current user information
- **Settings Management**: Tests user settings updates
- **Authorization**: Tests unauthorized access prevention

### Integration Tests (`test_main.py`)
- **Application Startup**: Verifies FastAPI app initialization
- **Database Connection**: Tests SQLite database connectivity
- **Route Accessibility**: Tests endpoint existence and proper responses
- **CORS Configuration**: Verifies middleware setup

## Test Alignment with Manual Instructions

The authentication tests specifically implement the test cases outlined in `MANUAL_TEST_INSTRUCTIONS.md`:

1. **Standard Login (30 minutes)**: `test_standard_login_without_remember_me`
2. **Remember Me Login (30 days)**: `test_login_with_remember_me`
3. **Token Security Validation**: `test_token_payload_contains_correct_user`
4. **Unauthorized Access Prevention**: `test_access_protected_route_*` tests

## Running Tests

### Prerequisites
```bash
# Install dependencies (from backend directory)
pip install -r requirements.txt
```

### Run All Tests
```bash
# From the backend directory
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Authentication tests only
python -m pytest tests/test_auth.py -v

# User management tests only
python -m pytest tests/test_user.py -v

# Integration tests only
python -m pytest tests/test_main.py -v
```

### Run Individual Tests
```bash
# Run a specific test
python -m pytest tests/test_auth.py::TestAuthentication::test_login_with_remember_me -v
```

### Test with Coverage (Optional)
```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage report
python -m pytest tests/ --cov=. --cov-report=html
```

## Test Configuration

The tests use:
- **SQLite in-memory databases** for isolation
- **Mocked external dependencies** (OpenAI, ML models) for reliability
- **FastAPI TestClient** for HTTP endpoint testing
- **Temporary databases** that are cleaned up after each test

## Environment Variables

Tests automatically set required environment variables:
- `SECRET_KEY`: Used for JWT token signing
- `OPENAI_API_KEY`: Mocked for testing (prevents API calls)

## Test Data

Tests use consistent sample data:
- **Test User**: testuser / test@example.com / Test User
- **Test Password**: testpassword123

## Expected Results

All tests should pass. The test suite includes:
- ✅ 10 Authentication tests
- ✅ 4 User management tests  
- ✅ 6 Integration tests
- **Total: 20 tests**

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed via `pip install -r requirements.txt`
2. **Database Errors**: Tests use temporary databases - no setup required
3. **External Service Errors**: Tests mock external services - no API keys needed

### Warning Messages
Some deprecation warnings from dependencies are expected and don't affect test functionality:
- Pydantic V2 migration warnings
- SQLAlchemy declarative_base warnings
- Passlib crypt deprecation warnings

## Contributing

When adding new features:
1. Add corresponding tests following existing patterns
2. Ensure tests cover both success and failure cases
3. Mock external dependencies to maintain test isolation
4. Update this documentation for new test categories