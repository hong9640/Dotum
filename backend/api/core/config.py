from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "init"
    DEBUG: bool = False
    
    # Database settings
    DB_ID: str
    DB_PW: str
    DB_NAME: str
    DB_NETWORK: str
    DB_PORT: int

    # JWT Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30  # 분단위

    # Google Cloud Storage Settings
    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str
    GCS_CREDENTIALS_PATH: str = ""  # 서비스 계정 키 파일 경로 (선택사항)

    # CORS Settings
    CORS_ORIGINS: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        """CORS 허용 origin 리스트"""
        if self.CORS_ORIGINS is None:
            return ["http://localhost:5173"]
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @computed_field
    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_ID}:{self.DB_PW}@{self.DB_NETWORK}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()