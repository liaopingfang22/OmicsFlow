from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ==================== User & Auth ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    roles: Optional[List[str]] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None


class UserResponse(UserBase):
    id: str
    is_active: bool
    roles: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ==================== Dataset ====================

class DatasetBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: str
    file_path: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    owner_id: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Pipeline ====================

class PipelineBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    pipeline_type: Optional[str] = None


class PipelineCreate(PipelineBase):
    config: Optional[dict] = None


class PipelineResponse(PipelineBase):
    id: str
    owner_id: Optional[str]
    is_public: bool
    config: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Task ====================

class TaskBase(BaseModel):
    name: str = Field(..., max_length=255)


class TaskCreate(TaskBase):
    pipeline_id: str
    dataset_id: Optional[str] = None
    input_params: Optional[dict] = None


class TaskResponse(TaskBase):
    id: str
    status: str
    pipeline_id: Optional[str]
    dataset_id: Optional[str]
    owner_id: Optional[str]
    progress: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


# ==================== TaskResult ====================

class TaskResultBase(BaseModel):
    result_type: str


class TaskResultResponse(TaskResultBase):
    id: str
    task_id: str
    file_path: Optional[str]
    file_size: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Skill ====================

class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class SkillCreate(SkillBase):
    content: str
    version: Optional[str] = None
    source: Optional[str] = None


class SkillResponse(SkillBase):
    id: str
    version: Optional[str]
    source: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Sequencer ====================

class SequencerBase(BaseModel):
    name: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    platform: str = Field(default="BGI", max_length=50)
    location: Optional[str] = None
    data_dir: Optional[str] = None


class SequencerCreate(SequencerBase):
    pass


class SequencerResponse(SequencerBase):
    id: str
    is_active: bool
    last_seen: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SequencerRunBase(BaseModel):
    run_name: str
    run_dir: str


class SequencerRunResponse(SequencerRunBase):
    id: str
    sequencer_id: str
    status: str
    sample_count: Optional[int]
    total_reads: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Project ====================

class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str
    owner_id: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)