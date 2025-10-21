from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "init"
    DB_URL: str
    DEBUG: bool = False
    DB_ID: str
    DB_PW: str
    DB_NAME: str

    # JWT Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30  # 분단위

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()