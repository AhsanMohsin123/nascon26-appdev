import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://nascon:nascon_pass@localhost:5432/nascon_db"
    redis_url: str = "redis://localhost:6379"
    day1_salt: str = os.environ.get("DAY1_SALT", "")
    day2_salt: str = os.environ.get("DAY2_SALT", "")
    jwt_secret: str = "nascon26-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 2
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"

    class Config:
        env_file = ".env"


settings = Settings()
