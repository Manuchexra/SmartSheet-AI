"""
Konfiguratsiya moduli.

.env faylidan sozlamalarni o'qib, butun ilova bo'ylab
ishlatiladigan yagona Settings obyektini yaratadi.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ilova sozlamalari."""

    # --- Ilova ---
    app_name: str = "SmartSheet AI"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- AI provayderi ---
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_api_url: str = ""

    # --- Ma'lumotlar bazasi (12-bosqich) ---
    database_url: str = "sqlite:///./data/smartsheet.db"

    # --- Cheklovlar ---
    max_rows: int = Field(default=200, ge=1, le=200)
    max_columns: int = 20
    max_prompt_length: int = 2000

    # --- Undo tarixi ---
    max_history_size: int = 20

    # --- Chat sozlamalari (12-bosqich) ---
    max_chats: int = 100  # Foydalanuvchi uchun maksimal chatlar
    max_messages_per_chat: int = 50

    # Pydantic sozlamalari
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Yagona global Settings obyekti
settings = Settings()