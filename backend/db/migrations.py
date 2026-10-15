"""Safe Alembic startup migrations, including databases created before Alembic."""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from backend.config import settings
from backend.db.session import engine


logger = logging.getLogger(__name__)

INITIAL_COLUMNS = {
    "chats": {"id", "title", "created_at", "updated_at"},
    "messages": {"id", "chat_id", "role", "content", "created_at"},
    "tables": {
        "id",
        "chat_id",
        "title",
        "columns",
        "rows",
        "source",
        "version",
        "created_at",
        "updated_at",
    },
}


def upgrade_database() -> None:
    """Upgrade to the latest revision without recreating legacy application tables."""
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    existing_app_tables = table_names.intersection(INITIAL_COLUMNS)
    if existing_app_tables:
        revision = _current_revision(inspector)
        if revision is None:
            _stamp_legacy_schema(config, inspector, existing_app_tables)
        else:
            logger.info("Database Alembic revision: %s", revision)

    command.upgrade(config, "head")
    logger.info("Database migrations are up to date.")


def _current_revision(inspector) -> str | None:
    if "alembic_version" not in inspector.get_table_names():
        return None

    with engine.connect() as connection:
        return connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version LIMIT 1"
        ).scalar_one_or_none()


def _stamp_legacy_schema(config: Config, inspector, existing_tables: set[str]) -> None:
    missing_tables = set(INITIAL_COLUMNS).difference(existing_tables)
    missing_columns = {
        table: sorted(required.difference(
            column["name"] for column in inspector.get_columns(table)
        ))
        for table, required in INITIAL_COLUMNS.items()
        if table in existing_tables
    }
    missing_columns = {
        table: columns for table, columns in missing_columns.items() if columns
    }
    if missing_tables or missing_columns:
        raise RuntimeError(
            "Alembic revision is missing and the existing database does not match "
            "the complete initial schema. No migration was applied. "
            f"Missing tables: {sorted(missing_tables)}; missing columns: {missing_columns}."
        )

    table_columns = {
        column["name"] for column in inspector.get_columns("tables")
    }
    revision = "002_add_styles" if "styles" in table_columns else "001_initial"
    logger.warning(
        "Legacy database detected without an Alembic revision; "
        "stamping verified schema as %s before upgrading.",
        revision,
    )
    command.stamp(config, revision)
