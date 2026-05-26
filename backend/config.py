from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "OmicsFlow Backend"
    debug: bool = True
    
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/omicsflow"
    
    redis_url: str = "redis://localhost:6379/0"
    
    nextflow_path: str = "/opt/omicsflow/bin/nextflow"
    workflow_dir: str = "/public/xalab/liaopingfang/pipeline_test/OmicsFlow/workflows"
    output_dir: str = "/data/output"
    storage_path: str = "/data/storage"
    
    singularity_cache: str = "/data/singularity"
    singularity_enabled: bool = True
    
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    
    max_upload_size: int = 10 * 1024 * 1024 * 1024

    # AI model settings
    ai_model: str = "claude-sonnet-4-20250514"
    ai_max_tokens: int = 1024
    ai_timeout: float = 30.0

    # Database pool settings
    pool_size: int = 20
    max_overflow: int = 10

    # Production settings
    log_level: str = "INFO"
    log_json: bool = False
    cors_origins: str = ""  # comma-separated, empty = allow all in debug
    rate_limit_rpm: int = 120  # requests per minute


@lru_cache()
def get_settings() -> Settings:
    return Settings()
