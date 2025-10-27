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

    # ---------- GCS 업로드 Prefix ----------
    PREFIX_TTS: str = "tts_cache"
    PREFIX_FREEVC: str = "freevc"
    PREFIX_W2L: str = "wav2lip"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()