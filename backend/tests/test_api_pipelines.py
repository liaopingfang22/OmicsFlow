"""
Pipeline API Tests

Tests for pipeline CRUD operations and listing endpoints.
"""
import pytest
from httpx import AsyncClient


class TestPipelineCreate:
    """Tests for pipeline creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_pipeline_success(self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict):
        """Test successful pipeline creation."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline
        response = await client.post("/api/v1/pipelines/", json=sample_pipeline_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Pipeline"
        assert data["pipeline_type"] == "rnaseq"
        assert "id" in data
        assert "owner_id" in data

    @pytest.mark.asyncio
    async def test_create_pipeline_with_config(self, client: AsyncClient, sample_user_data: dict):
        """Test pipeline creation with configuration."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline with config
        pipeline_data = {
            "name": "Configured Pipeline",
            "description": "Pipeline with custom config",
            "pipeline_type": "wgs",
            "config": {"threads": 8, "memory": "16GB"},
        }
        response = await client.post("/api/v1/pipelines/", json=pipeline_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["config"] == {"threads": 8, "memory": "16GB"}

    @pytest.mark.asyncio
    async def test_create_pipeline_unauthorized(self, client: AsyncClient, sample_pipeline_data: dict):
        """Test pipeline creation without authentication."""
        response = await client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        assert response.status_code == 401


class TestPipelineList:
    """Tests for pipeline listing endpoints."""

    @pytest.mark.asyncio
    async def test_list_pipelines_empty(self, client: AsyncClient, sample_user_data: dict):
        """Test listing pipelines when none exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List pipelines
        response = await client.get("/api/v1/pipelines/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_pipelines_with_data(self, client: AsyncClient, sample_user_data: dict):
        """Test listing pipelines when pipelines exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create multiple pipelines
        for i in range(3):
            pipeline_data = {"name": f"Pipeline {i}", "pipeline_type": "rnaseq"}
            await client.post("/api/v1/pipelines/", json=pipeline_data, headers=headers)

        # List pipelines
        response = await client.get("/api/v1/pipelines/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_pipelines_only_own_and_public(
        self, client: AsyncClient
    ):
        """Test that users see their own pipelines and public ones."""
        # Create two users
        user1 = {"username": "user1", "email": "user1@test.com", "password": "Password123!"}
        user2 = {"username": "user2", "email": "user2@test.com", "password": "Password123!"}

        await client.post("/api/v1/auth/register", json=user1)
        await client.post("/api/v1/auth/register", json=user2)

        # Login as user1
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": user1["username"], "password": user1["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Create private pipeline as user1
        await client.post(
            "/api/v1/pipelines/",
            json={"name": "User1 Private Pipeline"},
            headers=headers1,
        )

        # Login as user2
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": user2["username"], "password": user2["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # User2 should not see user1's private pipeline
        response = await client.get("/api/v1/pipelines/", headers=headers2)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestPipelineGet:
    """Tests for getting a single pipeline."""

    @pytest.mark.asyncio
    async def test_get_pipeline_success(self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict):
        """Test getting a single pipeline by ID."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline
        create_response = await client.post("/api/v1/pipelines/", json=sample_pipeline_data, headers=headers)
        pipeline_id = create_response.json()["id"]

        # Get pipeline
        response = await client.get(f"/api/v1/pipelines/{pipeline_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pipeline_id
        assert data["name"] == "Test Pipeline"

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test getting non-existent pipeline."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/pipelines/non-existent-id", headers=headers)

        assert response.status_code == 404


class TestPipelineDelete:
    """Tests for pipeline deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_pipeline_success(
        self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict
    ):
        """Test successful pipeline deletion."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline
        create_response = await client.post("/api/v1/pipelines/", json=sample_pipeline_data, headers=headers)
        pipeline_id = create_response.json()["id"]

        # Delete pipeline
        response = await client.delete(f"/api/v1/pipelines/{pipeline_id}", headers=headers)

        assert response.status_code == 204

        # Verify pipeline is deleted
        get_response = await client.get(f"/api/v1/pipelines/{pipeline_id}", headers=headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_pipeline_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test deleting non-existent pipeline."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/pipelines/non-existent-id", headers=headers)

        assert response.status_code == 404


class TestPipelineAvailable:
    """Tests for available pipelines endpoint."""

    @pytest.mark.asyncio
    async def test_list_available_pipelines(self, client: AsyncClient):
        """Test listing available pipelines."""
        response = await client.get("/api/v1/pipelines/available")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))  # Could be list or dict depending on implementation
