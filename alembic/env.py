"""
Alembic environment.

Bu fayl:
1. .env dan DATABASE_URL ni o'qiydi.
2. Barcha modellarni import qiladi (Base.metadata uchun).
3. Online va offline migratsiyalarni boshqaradi.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ============================================
# LOYIHA PAPKASINI PYTHON PATH'GA QO'SHISH
# ============================================
# Bu — `from backend.config import settings` ishlashi uchun
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# ============================================
# MODELLARNI IMPORT QILISH
# ============================================
# Base.metadata'ga barcha modellar qo'shilishi kerak
from backend.config import settings
from backend.db.base import Base

# Barcha modellarni import qilish (Base.metadata'ga qo'shiladi)
from backend.models import Chat, Message, Table  # noqa: F401


# ============================================
# ALEMBIC CONFIG
# ============================================
config = context.config

# .env dan DATABASE_URL ni o'rnatish
config.set_main_option("sqlalchemy.url", settings.database_url)

# Logging sozlash
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic avtomatik migratsiya uchun metadata
target_metadata = Base.metadata


# ============================================
# OFFLINE MIGRATSIYA
# ============================================
def run_migrations_offline() -> None:
    """
    Offline migratsiya (SQL skript sifatida).

    Ishlatish:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================
# ONLINE MIGRATSIYA
# ============================================
def run_migrations_online() -> None:
    """
    Online migratsiya (haqiqiy baza bilan).

    Ishlatish:
        alembic upgrade head
    """
    # Engine yaratish
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # SQLite uchun batch mode (ALTER TABLE cheklovi)
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================
# ISHGA TUSHIRISH
# ============================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()