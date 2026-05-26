from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from services.database import get_db
from services.nextflow import nextflow_service
from models.database import Pipeline, User
from models.schemas import PipelineCreate, PipelineResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = Pipeline(
        name=pipeline_data.name,
        description=pipeline_data.description,
        pipeline_type=pipeline_data.pipeline_type,
        config=pipeline_data.config,
        owner_id=current_user.id,
    )
    
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    
    return pipeline


@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pipeline).where(
            (Pipeline.owner_id == current_user.id) | (Pipeline.is_public == True)
        )
    )
    pipelines = result.scalars().all()
    return pipelines


@router.get("/available")
async def list_available_pipelines():
    workflows = nextflow_service.list_workflows()
    return workflows


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline_id)
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    
    if not pipeline.is_public and pipeline.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Pipeline).where(
            Pipeline.id == pipeline_id,
            Pipeline.owner_id == current_user.id,
        )
    )
    pipeline = result.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    
    await db.delete(pipeline)
    await db.commit()
