"""
Authentication API Tests

Tests for user registration, login, and authentication endpoints.
"""
import pytest
from httpx import AsyncClient


class TestAuthRegister:
    """Tests for user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data  # Password should not be returned

    @pytest.mark.asyncio
    async def test_register_user_duplicate_username(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with duplicate username fails."""
        # Register first user
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Try to register with same username
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response = await client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Try to register with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "differentuser"

        response = await client.post("/api/v1/auth/register", json=duplicate_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with invalid email format."""
        invalid_data = sample_user_data.copy()
        invalid_data["email"] = "invalid-email"

        response = await client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_user_short_password(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with password too short."""
        invalid_data = sample_user_data.copy()
        invalid_data["password"] = "short"

        response = await client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error


class TestAuthLogin:
    """Tests for user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful login."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "username": sample_user_data["username"],
            "password": sample_user_data["password"],
        }
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data: dict):
        """Test login with wrong password."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Login with wrong password
        login_data = {
            "username": sample_user_data["username"],
            "password": "WrongPassword123!",
        }
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistentuser",
            "password": "Password123!",
        }
        response = await client.post(
            "/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient, sample_user_data: dict):
        """Test get current user with valid token."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["email"] == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test get current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test get current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestAuthUnauthorizedAccess:
    """Tests for unauthorized access to protected endpoints."""

    @pytest.mark.asyncio
    async def test_tasks_unauthorized(self, client: AsyncClient):
        """Test accessing tasks endpoint without authentication."""
        response = await client.get("/api/v1/tasks/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_pipelines_unauthorized(self, client: AsyncClient):
        """Test accessing pipelines endpoint without authentication."""
        response = await client.get("/api/v1/pipelines/")
        assert response.status_code == 401
