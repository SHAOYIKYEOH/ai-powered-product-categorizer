import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables"""
    
    gcp_project_id: str
    gcp_credentials_path: str = None
    bigquery_dataset: str = "raw_data"
    fastapi_debug: bool = False
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
