"""
Ma'lumotlar bazasi sessiyasi.

Bu modul:
1. SQLAlchemy engine'ni yaratadi.
2. SessionLocal klassini beradi.
3. FastAPI uchun `get_db()` dependency.
"""

import logging
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings
from backend.db.base import Base


logger = logging.getLogger(__name__)


# ============================================
# SQLITE PAPKASINI YARATISH
# ============================================
# sqlite:///./data/smartsheet.db → ./data/ papkasi kerak
if settings.database_url.startswith("sqlite"):
    # URL dan fayl yo'lini ajratib olish
    db_path = settings.database_url.replace("sqlite:///", "")
    db_file = Path(db_path)

    # Papkani yaratish (agar mavjud bo'lmasa)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"📁 SQLite papkasi: {db_file.parent}")


# ============================================
# SQLALCHEMY ENGINE
# ============================================
# SQLite uchun maxsus sozlamalar
connect_args = {}
if settings.database_url.startswith("sqlite"):
    # SQLite bir vaqtda faqat 1 ta thread'ni qo'llab-quvvatlaydi
    # Shuning uchun `check_same_thread=False`
    connect_args = {"check_same_thread": False}


engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.app_env == "development",  # Development'da SQL log
    future=True,
)


# ============================================
# SQLITE UCHUN PRAGMA SOZLAMALARI
# ============================================
# Foreign key'lar va WAL rejimini yoqish
if settings.database_url.startswith("sqlite"):
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """SQLite uchun pragma sozlamalari."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")  # FK cheklovlarini yoqish
        cursor.execute("PRAGMA journal_mode=WAL")  # Tezroq yozish
        cursor.close()


# ============================================
# SESSION FACTORY
# ============================================
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


# ============================================
# FASTAPI DEPENDENCY
# ============================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: ma'lumotlar bazasi sessiyasi.

    Ishlatish:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# JADVALLARNI YARATISH (development)
# ============================================
def init_db() -> None:
    """
    Barcha jadvallarni yaratish.

    Diqqat: bu faqat development uchun.
    Production'da Alembic migratsiyalaridan foydalaning.
    """
    # Modellarni import qilish kerak (Base.metadata'ga qo'shilishi uchun)
    from backend.models import chat, message, table  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("✅ Ma'lumotlar bazasi jadvallari yaratildi")