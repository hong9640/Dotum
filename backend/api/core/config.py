from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    PROJECT_NAME: str = "dotum"
    DEBUG: bool = False
    
    # Database settings
    DB_ID: str
    DB_PW: str
    DB_NAME: str
    DB_NETWORK: str
    DB_PORT: int
    
    # Database Connection Pool Settings
    DB_POOL_SIZE: int = 20  # 기본 커넥션 풀 크기
    DB_MAX_OVERFLOW: int = 10  # 풀이 가득 찼을 때 추가로 생성 가능한 연결 수
    DB_POOL_RECYCLE: int = 3600  # 커넥션 재활용 시간 (초) - 1시간
    DB_POOL_PRE_PING: bool = True  # 커넥션 사용 전 유효성 검사
    DB_ECHO: bool = False  # SQL 쿼리 로깅 (DEBUG 모드에서 자동 활성화)

    # JWT Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION: int = 30  # 분단위

    # Google Cloud Storage Settings
    GCS_BUCKET_NAME: str
    GCS_PROJECT_ID: str
    GCS_CREDENTIALS_PATH: str = ""  # 서비스 계정 키 파일 경로 (선택사항)

    #ML sever URL
    ML_SERVER_URL: str
    STT_SERVER_URL: str

    # ElevenLabs API Key
    ELEVENLABS_API_KEY: str = ""

    # Wav2Lip Processing Control
    ENABLE_WAV2LIP: bool = True  # wav2lip 처리 활성화 여부

    # OPEN_AI_API_KEY
    OPEN_AI_API_KEY: str = ""

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