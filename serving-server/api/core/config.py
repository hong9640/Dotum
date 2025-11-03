from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "serving-server"
    DEBUG: bool = False

    # ---------- GCP ----------
    GCP_PROJECT_ID: str
    GCS_BUCKET: str
    GCS_CREDENTIAL_PATH: str | None

    # ---------- 모델 SDK ----------
    FREEVC_SDK_PATH: str | None = None
    W2L_SDK_PATH: str | None = None

    # ---------- 로컬 모델 경로 ----------
    LOCAL_MODEL_BASE_PATH: str = "/app/models"
    LOCAL_FREEVC_PATH: str = "/app/models/FreeVC"
    LOCAL_WAV2LIP_PATH: str = "/app/models/Wav2Lip"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()