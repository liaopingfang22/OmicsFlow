from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone
import uuid

from services.database import get_db, async_session_maker
from services.nextflow import nextflow_service
from services.task_queue import enqueue_pipeline_task, get_task_status, get_task_logs, cancel_task as queue_cancel_task
from services.websocket import ws_manager
from models.database import Task, Pipeline, User
from models.schemas import TaskCreate, TaskResponse, TaskUpdate
from api.deps import get_current_active_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pipeline).where(Pipeline.id == task_data.pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    
    task = Task(
        name=task_data.name,
        pipeline_id=task_data.pipeline_id,
        dataset_id=task_data.dataset_id,
        input_params=task_data.input_params,
        owner_id=current_user.id,
        status="pending",
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(Task.owner_id == current_user.id).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return task


@router.post("/{task_id}/run", response_model=TaskResponse)
async def run_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    pipeline_result = await db.execute(
        select(Pipeline).where(Pipeline.id == task.pipeline_id)
    )
    pipeline = pipeline_result.scalar_one_or_none()
    
    task.status = "queued"
    task.started_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    
    await enqueue_pipeline_task(
        task_id=task.id,
        pipeline_type=pipeline.pipeline_type or "main",
        params=task.input_params or {},
        db_session_factory=async_session_maker,
    )
    
    await ws_manager.send_global_update("task_queued", {"task_id": task.id, "name": task.name})
    
    return task


@router.get("/{task_id}/status")
async def get_task_live_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Get real-time task status from task queue."""
    status_info = get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found in queue")
    return status_info


@router.get("/{task_id}/logs")
async def get_task_live_logs(
    task_id: str,
    since: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    """Get streaming task logs."""
    logs = get_task_logs(task_id, since_line=since)
    return {"task_id": task_id, "logs": logs, "count": len(logs)}


@router.websocket("/ws/{task_id}")
async def websocket_task(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time task updates."""
    await ws_manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, task_id)


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard real-time updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if task.status in ("running", "queued"):
        await queue_cancel_task(task.id)
    
    task.status = "cancelled"
    await db.commit()
