"""
Task API Tests

Tests for task CRUD operations and management endpoints.
"""
import pytest
from httpx import AsyncClient


class TestTaskCreate:
    """Tests for task creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict
    ):
        """Test successful task creation."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a pipeline first
        pipeline_response = await client.post(
            "/api/v1/pipelines/", json=sample_pipeline_data, headers=headers
        )
        assert pipeline_response.status_code == 201
        pipeline_id = pipeline_response.json()["id"]

        # Create task
        task_data = {
            "name": "Test Task",
            "pipeline_id": pipeline_id,
            "input_params": {"param1": "value1"},
        }
        response = await client.post("/api/v1/tasks/", json=task_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Task"
        assert data["pipeline_id"] == pipeline_id
        assert data["status"] == "pending"
        assert data["progress"] == 0

    @pytest.mark.asyncio
    async def test_create_task_pipeline_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test task creation with non-existent pipeline."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create task with non-existent pipeline
        task_data = {
            "name": "Test Task",
            "pipeline_id": "non-existent-pipeline-id",
        }
        response = await client.post("/api/v1/tasks/", json=task_data, headers=headers)

        assert response.status_code == 404
        assert "Pipeline not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, client: AsyncClient, sample_task_data: dict):
        """Test task creation without authentication."""
        response = await client.post("/api/v1/tasks/", json=sample_task_data)
        assert response.status_code == 401


class TestTaskList:
    """Tests for task listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(
        self, client: AsyncClient, sample_user_data: dict
    ):
        """Test listing tasks when none exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List tasks
        response = await client.get("/api/v1/tasks/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_tasks_with_data(
        self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict
    ):
        """Test listing tasks when tasks exist."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a pipeline
        pipeline_response = await client.post(
            "/api/v1/pipelines/", json=sample_pipeline_data, headers=headers
        )
        pipeline_id = pipeline_response.json()["id"]

        # Create tasks
        for i in range(3):
            task_data = {"name": f"Task {i}", "pipeline_id": pipeline_id}
            await client.post("/api/v1/tasks/", json=task_data, headers=headers)

        # List tasks
        response = await client.get("/api/v1/tasks/", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_tasks_only_own_tasks(
        self, client: AsyncClient, sample_pipeline_data: dict
    ):
        """Test that users can only see their own tasks."""
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

        # Create pipeline and task as user1
        pipeline_response = await client.post(
            "/api/v1/pipelines/", json=sample_pipeline_data, headers=headers1
        )
        pipeline_id = pipeline_response.json()["id"]

        await client.post(
            "/api/v1/tasks/",
            json={"name": "User1 Task", "pipeline_id": pipeline_id},
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

        # User2 should not see user1's tasks
        response = await client.get("/api/v1/tasks/", headers=headers2)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestTaskGet:
    """Tests for getting a single task."""

    @pytest.mark.asyncio
    async def test_get_task_success(
        self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict
    ):
        """Test getting a single task by ID."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline and task
        pipeline_response = await client.post(
            "/api/v1/pipelines/", json=sample_pipeline_data, headers=headers
        )
        pipeline_id = pipeline_response.json()["id"]

        task_response = await client.post(
            "/api/v1/tasks/",
            json={"name": "Get Me Task", "pipeline_id": pipeline_id},
            headers=headers,
        )
        task_id = task_response.json()["id"]

        # Get task
        response = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == "Get Me Task"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test getting non-existent task."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get("/api/v1/tasks/non-existent-id", headers=headers)

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


class TestTaskDelete:
    """Tests for task deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_task_success(
        self, client: AsyncClient, sample_user_data: dict, sample_pipeline_data: dict
    ):
        """Test successful task cancellation."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create pipeline and task
        pipeline_response = await client.post(
            "/api/v1/pipelines/", json=sample_pipeline_data, headers=headers
        )
        pipeline_id = pipeline_response.json()["id"]

        task_response = await client.post(
            "/api/v1/tasks/",
            json={"name": "Delete Me Task", "pipeline_id": pipeline_id},
            headers=headers,
        )
        task_id = task_response.json()["id"]

        # Cancel task (delete endpoint sets status to cancelled)
        response = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)

        assert response.status_code == 204

        # Verify task exists but status is cancelled
        get_response = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, client: AsyncClient, sample_user_data: dict):
        """Test deleting non-existent task."""
        # Register and login
        await client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            data={"username": sample_user_data["username"], "password": sample_user_data["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete("/api/v1/tasks/non-existent-id", headers=headers)

        assert response.status_code == 404
