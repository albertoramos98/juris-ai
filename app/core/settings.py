from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # ✅ Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid",   # mantém seguro
    )

    SECRET_KEY: str = "juris-ai-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # governança
    OFFICE_OVERRIDE_SECRET: str = "change-me"

    # Google OAuth (login do sistema)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/google/callback"

    FRONTEND_LOGIN_REDIRECT: str = "http://127.0.0.1:5500/frontend/index.html"

    # SMTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = ""

    # ✅ OPENAI (IA / RAG)
    openai_api_key: str = Field(
        default="",
        validation_alias="OPENAI_API_KEY",
        description="OpenAI API Key (GPT / RAG)",
    )


settings = Settings()
