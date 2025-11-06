from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# serving-server 디렉토리를 BASE_DIR로 설정 (현재 파일 기준 3단계 상위)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "serving-server"
    DEBUG: bool = False

    # ---------- GCP ----------
    GCP_PROJECT_ID: str
    GCS_BUCKET: str
    GCS_CREDENTIAL_PATH: str | None

    # ---------- 로컬 모델 경로 ----------
    # 상대 경로로 설정하되 환경 변수로 덮어쓰기 가능
    LOCAL_MODEL_BASE_PATH: str = str(BASE_DIR / "models")
    LOCAL_WAV2LIP_PATH: str = str(BASE_DIR / "models" / "Wav2Lip")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
