"""Results API endpoints for task results and visualization."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from services.database import get_db
from services.rbac import check_permission
from models.database import TaskResult, Task, User
from models.schemas import TaskResultResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("/{task_id}", response_model=List[TaskResultResponse])
async def get_task_results(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get results for a specific task."""
    # Check if task exists and user has access
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permission - users can only see their own task results
    if task.owner_id != current_user.id:
        check_permission(current_user, "results:read")

    # Get results
    results_query = await db.execute(
        select(TaskResult).where(TaskResult.task_id == task_id)
    )
    return results_query.scalars().all()


@router.get("/result/{result_id}", response_model=TaskResultResponse)
async def get_result(
    result_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific result by ID."""
    result = await db.execute(select(TaskResult).where(TaskResult.id == result_id))
    task_result = result.scalar_one_or_none()

    if not task_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found",
        )

    # Check permission
    task_query = await db.execute(select(Task).where(Task.id == task_result.task_id))
    task = task_query.scalar_one_or_none()

    if task and task.owner_id != current_user.id:
        check_permission(current_user, "results:read")

    return task_result
