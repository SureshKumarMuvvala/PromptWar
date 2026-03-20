"""
Application configuration — env-driven via Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """All configuration is loaded from environment variables / .env file."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Emergency Health Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "*"

    # ── Google Gemini ────────────────────────────────────────────
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_TIMEOUT: int = 30

    # ── RAG / FAISS ──────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "app/rag/faiss_index"
    KNOWLEDGE_BASE_PATH: str = "app/rag/knowledge_base"
    RAG_TOP_K: int = 5
    RAG_CONFIDENCE_THRESHOLD: float = 0.7

    # ── Google Maps / Places ─────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""
    HOSPITAL_SEARCH_RADIUS_KM: int = 10
    HOSPITAL_MAX_RESULTS: int = 10

    # ── External Services (optional) ─────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    EMERGENCY_PHONE_NUMBER: str = ""

    SENDGRID_API_KEY: str = ""
    ALERT_EMAIL_FROM: str = ""
    ALERT_EMAIL_TO: str = ""

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
