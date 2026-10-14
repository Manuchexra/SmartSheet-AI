"""
Konfiguratsiya moduli.

.env faylidan sozlamalarni o'qib, butun ilova bo'ylab
ishlatiladigan yagona Settings obyektini yaratadi.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Ilova sozlamalari.

    Har bir maydon .env faylidagi kalitga mos keladi.
    Masalan: app_name <-> APP_NAME
    """

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

    # --- Cheklovlar ---
    max_rows: int = 100
    max_columns: int = 20
    max_prompt_length: int = 2000

    # --- Undo tarixi ---
    max_history_size: int = 20

    # Pydantic sozlamalari
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Yagona global Settings obyekti
settings = Settings()