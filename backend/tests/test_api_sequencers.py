"""
Sequencer API Tests

Tests for sequencer management endpoints.
Note: Sequencer write operations require admin role.
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
def admin_user_data() -> dict:
    """Sample admin user registration data."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "AdminPassword123!",
        "roles": ["admin"],
    }


class TestSequencerCreate:
    """Tests for sequencer creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_sequencer_success(self, client: AsyncClient, admin_user_data: dict):
        """Test successful sequencer creation with admin role."""
        # Register and login
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create sequencer
        sequencer_data = {
            "name": "G99-01",
            "model": "G99",
            "platform": "BGI",
            "location": "Lab A",
            "data_dir": "/data/sequencers/g99-01",
        }
        response = await client.post("/api/v1/sequencers/", json=sequencer_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "G99-01"
        assert data["model"] == "G99"
        assert data["platform"] == "BGI"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_sequencer_unauthorized(self, client: AsyncClient):
        """Test sequencer creation without authentication."""
        sequencer_data = {
            "name": "G99-01",
            "model": "G99",
        }
        response = await client.post("/api/v1/sequencers/", json=sequencer_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_sequencer_forbidden(self, client: AsyncClient, sample_user_data: dict):
        """Test sequencer creation with non-admin role."""
        # Register and login as regular user
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to create sequencer
        sequencer_data = {
            "name": "G99-01",
            "model": "G99",
        }
        response = await client.post("/api/v1/sequencers/", json=sequencer_data, headers=headers)

        assert response.status_code == 403


class TestSequencerList:
    """Tests for sequencer listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_sequencers_empty(self, client: AsyncClient, sample_user_data: dict):
        """Test listing sequencers when none exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List sequencers
        response = await client.get("/api/v1/sequencers/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_sequencers_with_data(self, client: AsyncClient, admin_user_data: dict):
        """Test listing sequencers when sequencers exist."""
        # Register and login as admin
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create sequencers
        sequencers = [
            {"name": "G99-01", "model": "G99", "platform": "BGI"},
            {"name": "T7-01", "model": "T7", "platform": "BGI"},
            {"name": "GridION-01", "model": "GridION", "platform": "Nanopore"},
        ]
        for seq in sequencers:
            await client.post("/api/v1/sequencers/", json=seq, headers=headers)

        # List sequencers
        response = await client.get("/api/v1/sequencers/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestSequencerGet:
    """Tests for getting a single sequencer."""

    @pytest.mark.asyncio
    async def test_get_sequencer_success(self, client: AsyncClient, admin_user_data: dict):
        """Test getting a single sequencer by ID."""
        # Register and login as admin
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create sequencer
        sequencer_response = await client.post(
            "/api/v1/sequencers/",
            json={"name": "G99-01", "model": "G99"},
            headers=headers,
        )
        sequencer_id = sequencer_response.json()["id"]

        # Get sequencer
        response = await client.get(f"/api/v1/sequencers/{sequencer_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sequencer_id
        assert data["name"] == "G99-01"

    @pytest.mark.asyncio
    async def test_get_sequencer_not_found(self, client: AsyncClient, admin_user_data: dict):
        """Test getting non-existent sequencer."""
        # Register and login as admin
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/sequencers/non-existent-id", headers=headers)

        assert response.status_code == 404


class TestSequencerDelete:
    """Tests for sequencer deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_sequencer_success(self, client: AsyncClient, admin_user_data: dict):
        """Test successful sequencer deletion."""
        # Register and login as admin
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create sequencer
        sequencer_response = await client.post(
            "/api/v1/sequencers/",
            json={"name": "Delete Me Sequencer", "model": "G99"},
            headers=headers,
        )
        sequencer_id = sequencer_response.json()["id"]

        # Delete sequencer
        response = await client.delete(f"/api/v1/sequencers/{sequencer_id}", headers=headers)

        assert response.status_code == 204

        # Verify sequencer is deleted
        get_response = await client.get(f"/api/v1/sequencers/{sequencer_id}", headers=headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_sequencer_not_found(self, client: AsyncClient, admin_user_data: dict):
        """Test deleting non-existent sequencer."""
        # Register and login as admin
        await client.post("/api/v1/auth/register", json=admin_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": admin_user_data["username"], "password": admin_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/sequencers/non-existent-id", headers=headers)

        assert response.status_code == 404
