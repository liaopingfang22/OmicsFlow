from sqlalchemy import Column, String, DateTime, Integer, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    roles = Column(JSON, default=list)  # ["admin", "bioinformatician", "librarian", "viewer"]
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    pipelines = relationship("Pipeline", back_populates="owner", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(512))
    file_size = Column(Integer)
    file_type = Column(String(50))
    checksum = Column(String(64))
    metadata_json = Column("metadata", JSON)
    owner_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User")
    tasks = relationship("Task", back_populates="dataset")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    pipeline_type = Column(String(50))
    config = Column(JSON)
    nextflow_file = Column(String(255))
    is_public = Column(Boolean, default=False)
    owner_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User")
    tasks = relationship("Task", back_populates="pipeline")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending", index=True)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"))
    dataset_id = Column(String(36), ForeignKey("datasets.id"))
    owner_id = Column(String(36), ForeignKey("users.id"))
    
    input_params = Column(JSON)
    output_path = Column(String(512))
    log_path = Column(String(512))
    
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    pipeline = relationship("Pipeline")
    dataset = relationship("Dataset")
    owner = relationship("User")
    results = relationship("TaskResult", back_populates="task", cascade="all, delete-orphan")


class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    result_type = Column(String(50))
    file_path = Column(String(512))
    file_size = Column(Integer)
    content = Column(Text)
    metadata_json = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    category = Column(String(50))
    description = Column(Text)
    content = Column(Text)
    version = Column(String(20))
    source = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Sequencer(Base):
    __tablename__ = "sequencers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)        # G99, T1Plus, T7
    platform = Column(String(50), default="BGI")
    location = Column(String(255))
    data_dir = Column(String(512))                     # 监控的数据目录
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    runs = relationship("SequencerRun", back_populates="sequencer")


class SequencerRun(Base):
    __tablename__ = "sequencer_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sequencer_id = Column(String(36), ForeignKey("sequencers.id"), nullable=False)
    run_name = Column(String(255), nullable=False)
    run_dir = Column(String(512))
    status = Column(String(20), default="detected")     # detected, importing, ready, failed
    sample_count = Column(Integer)
    total_reads = Column(Integer)
    metadata_json = Column("metadata", JSON)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sequencer = relationship("Sequencer", back_populates="runs")
    samples = relationship("Sample", back_populates="run")


class Sample(Base):
    __tablename__ = "samples"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("sequencer_runs.id"))
    project_id = Column(String(36), ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    species = Column(String(100))
    library_type = Column(String(50))                   # WGS, WES, RNA-seq, 16S, scRNA, etc.
    read1_path = Column(String(512))
    read2_path = Column(String(512))
    file_size = Column(Integer)
    status = Column(String(20), default="pending")       # pending, imported, analyzing, completed
    metadata_json = Column("metadata", JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    run = relationship("SequencerRun", back_populates="samples")
    project = relationship("Project", back_populates="samples")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User")
    samples = relationship("Sample", back_populates="project")
