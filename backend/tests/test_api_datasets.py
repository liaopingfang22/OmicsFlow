"""
Dataset API Tests

Tests for dataset CRUD operations and management endpoints.
Note: Dataset creation requires file upload, so we test other endpoints.
"""
import pytest
from httpx import AsyncClient


class TestDatasetList:
    """Tests for dataset listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_datasets_empty(self, client: AsyncClient, sample_user_data: dict):
        """Test listing datasets when none exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List datasets
        response = await client.get("/api/v1/datasets/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_datasets_unauthorized(self, client: AsyncClient):
        """Test listing datasets without authentication."""
        response = await client.get("/api/v1/datasets/")
        assert response.status_code == 401


class TestDatasetGet:
    """Tests for getting a single dataset."""

    @pytest.mark.asyncio
    async def test_get_dataset_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test getting non-existent dataset."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/datasets/non-existent-id", headers=headers)

        assert response.status_code == 404


class TestDatasetDelete:
    """Tests for dataset deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_dataset_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test deleting non-existent dataset."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/datasets/non-existent-id", headers=headers)

        assert response.status_code == 404
