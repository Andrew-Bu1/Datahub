from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aihub_url: str
    identity_url: str
    identity_user: str
    identity_secret: str

    database_url: str

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
