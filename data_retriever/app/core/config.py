from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., env="POSTGRES_DB")
    postgres_host: str = Field(..., env="POSTGRES_HOST")
    postgres_port: int = Field(..., env="POSTGRES_PORT", default=5432)
    postgres_schema: str = Field(..., env="POSTGRES_SCHEMA", default="public")


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

