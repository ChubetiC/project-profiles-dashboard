from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Project Profiles Dashboard"
    environment: str = "local"
    secret_key: str = "change-me-for-local-development"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/project_profiles"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "project-documents"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    max_project_storage_bytes: int = 50 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

