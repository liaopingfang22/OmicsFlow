"""
Project management API.
Projects group samples, datasets, and tasks for organized analysis.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from services.database import get_db
from services.rbac import check_permission
from models.database import Project, Sample, User
from models.schemas import ProjectCreate, ProjectResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "projects:write")
    project = Project(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "projects:read")
    result = await db.execute(select(Project).where(Project.is_active == True).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "projects:read")
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "projects:delete")
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.is_active = False
    await db.commit()


@router.get("/{project_id}/samples")
async def list_project_samples(
    project_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    check_permission(current_user, "samples:read")
    result = await db.execute(
        select(Sample).where(Sample.project_id == project_id).order_by(Sample.created_at.desc())
    )
    samples = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "species": s.species,
            "library_type": s.library_type,
            "file_size": s.file_size,
            "status": s.status,
            "created_at": s.created_at,
        }
        for s in samples
    ]