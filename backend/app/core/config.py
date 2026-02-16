import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@db:5432/hr_db"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    FITBIT_CLIENT_ID: str = os.getenv("FITBIT_CLIENT_ID", "")
    FITBIT_CLIENT_SECRET: str = os.getenv("FITBIT_CLIENT_SECRET", "")
    FITBIT_REDIRECT_URI: str = os.getenv("FITBIT_REDIRECT_URI", "https://hr.doby.me/oauth/callback")

    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")

    # Google Chat Webhook
    GOOGLE_CHAT_WEBHOOK_URL: str = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "")

    # Google Chat DM (Service Account)
    GOOGLE_CHAT_SA_KEY_FILE: str = os.getenv("GOOGLE_CHAT_SA_KEY_FILE", "")

    class Config:
        env_file = ".env"


settings = Settings()
