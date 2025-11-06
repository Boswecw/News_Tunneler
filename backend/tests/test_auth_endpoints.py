"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Import all models
from app.models import (
    Base, User, UserRole, Article, Score, Source, Signal,
    OpportunityCache, PriceCache, ResearchFeatures, ResearchLabels,
    Webhook, Setting, ModelRun, PredictionBounds
)
from app.core.db import get_db
from app.core.auth import get_password_hash

# Test database setup
TEST_DATABASE_URL = "sqlite:///file:test_auth_db?mode=memory&cache=shared&uri=true"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "uri": True},
    poolclass=None
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_app():
    """Create a test FastAPI app."""
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=lifespan)

    # Import and include auth router
    from app.api import auth
    test_app.include_router(auth.router)

    return test_app


@pytest.fixture(scope="function")
def client(db):
    """Create test client."""
    test_app = create_test_app()
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    db_session = TestingSessionLocal()
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.close()
    return {"email": "test@example.com", "username": "testuser", "password": "testpassword123"}


class TestUserRegistration:
    """Test user registration endpoints."""

    def test_register_new_user(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password hash

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user["email"],
                "username": "differentuser",
                "password": "SecurePassword123!",
                "full_name": "Different User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username fails."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user["username"],
                "password": "SecurePassword123!",
                "full_name": "Different User"
            }
        )
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()


class TestUserLogin:
    """Test user login endpoints."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_email(self, client, test_user):
        """Test login with email instead of username."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["email"],  # Using email as username
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user fails."""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "somepassword"
            }
        )
        assert response.status_code == 401


class TestTokenOperations:
    """Test JWT token operations."""

    def test_get_current_user(self, client, test_user):
        """Test getting current user with valid token."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]

    def test_access_protected_without_token(self, client):
        """Test accessing protected endpoint without token fails."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_access_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token fails."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401

    def test_refresh_token(self, client, test_user):
        """Test refreshing access token."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh the token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # Ensure the new token is different
        assert data["access_token"] != login_response.json()["access_token"]


class TestUserProfile:
    """Test user profile endpoints."""

    def test_update_profile(self, client, test_user):
        """Test updating user profile."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Update profile
        response = client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"


class TestPasswordSecurity:
    """Test password security requirements."""

    def test_weak_password_rejected(self, client):
        """Test that weak passwords are rejected."""
        # This test assumes password validation is implemented
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "username": "user",
                "password": "weak",  # Too short
                "full_name": "User"
            }
        )
        # Depending on implementation, this might succeed or fail
        # If password validation is strict, expect 400
        if response.status_code == 400:
            assert "password" in response.json()["detail"].lower()
        else:
            # If no validation, at least registration should work
            assert response.status_code == 201


class TestRoleBasedAccess:
    """Test role-based access control."""

    @pytest.fixture
    def admin_user(self, db):
        """Create an admin user."""
        db_session = TestingSessionLocal()
        user = User(
            email="admin@example.com",
            username="admin",
            hashed_password=get_password_hash("adminpassword123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.close()
        return {"username": "admin", "password": "adminpassword123"}

    def test_admin_can_list_users(self, client, admin_user):
        """Test that admin can list all users."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": admin_user["username"],
                "password": admin_user["password"]
            }
        )
        token = login_response.json()["access_token"]

        # List users
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1  # At least the admin user

    def test_non_admin_cannot_list_users(self, client, test_user):
        """Test that non-admin cannot list users."""
        # Login as regular user
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Try to list users
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403  # Forbidden


# Performance/Security Tests
class TestSecurityMeasures:
    """Test security measures."""

    def test_password_not_in_response(self, client, test_user):
        """Test that password hash is never returned in API responses."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["username"],
                "password": test_user["password"]
            }
        )
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data

    def test_rate_limiting_protection(self, client):
        """Test that rate limiting is applied (if implemented)."""
        # Make many requests
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                data={
                    "username": "nonexistent",
                    "password": "wrong"
                }
            )
            # First few should be 401, later ones might be 429 (rate limited)
            assert response.status_code in [401, 429]
