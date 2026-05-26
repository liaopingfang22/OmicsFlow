from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from services.database import get_db
from models.database import Skill, User
from models.schemas import SkillCreate, SkillResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=List[SkillResponse])
async def list_skills(
    category: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Skill).where(Skill.is_active == True)
    
    if category:
        query = query.where(Skill.category == category)
    
    result = await db.execute(query.order_by(Skill.name))
    skills = result.scalars().all()
    return skills


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    
    return skill


@router.get("/by-name/{name}")
async def get_skill_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    
    return {"id": skill.id, "name": skill.name, "content": skill.content}


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    
    skill = Skill(
        name=skill_data.name,
        category=skill_data.category,
        description=skill_data.description,
        content=skill_data.content,
        version=skill_data.version,
        source=skill_data.source,
    )
    
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    
    return skill
