"""Startup migration behavior for fresh and legacy databases."""

import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from backend.db import migrations


def _configure_database(monkeypatch, tmp_path):
    database_path = tmp_path / "migration-test.db"
    database_engine = create_engine(f"sqlite:///{database_path}")
    monkeypatch.setattr(migrations, "engine", database_engine)
    monkeypatch.setattr(migrations.settings, "database_url", f"sqlite:///{database_path}")
    return database_engine


def test_upgrade_database_creates_schema_on_first_start(monkeypatch, tmp_path):
    database_engine = _configure_database(monkeypatch, tmp_path)
    try:
        migrations.upgrade_database()

        inspector = inspect(database_engine)
        assert "styles" in {column["name"] for column in inspector.get_columns("tables")}
        with database_engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "003_add_browser_scope"
        columns = {column["name"] for column in inspector.get_columns("chats")}
        assert "browser_id" in columns
    finally:
        database_engine.dispose()


@pytest.mark.parametrize("version_table_exists", [True, False])
def test_upgrade_database_adopts_complete_legacy_schema_without_data_loss(
    monkeypatch, tmp_path, version_table_exists
):
    database_engine = _configure_database(monkeypatch, tmp_path)
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    try:
        command.upgrade(config, "001_initial")
        with database_engine.begin() as connection:
            connection.execute(
                text("INSERT INTO chats (title) VALUES ('Legacy chat')")
            )
            connection.execute(
                text(
                    "INSERT INTO tables (chat_id, title, columns, rows, source, version) "
                    "VALUES (1, 'Legacy table', :columns, :rows, 'ai', 1)"
                ),
                {
                    "columns": json.dumps(["Name"]),
                    "rows": json.dumps([["Ali"]]),
                },
            )
            if version_table_exists:
                connection.execute(text("DELETE FROM alembic_version"))
            else:
                connection.execute(text("DROP TABLE alembic_version"))

        migrations.upgrade_database()

        inspector = inspect(database_engine)
        assert "styles" in {column["name"] for column in inspector.get_columns("tables")}
        assert "browser_id" in {
            column["name"] for column in inspector.get_columns("chats")
        }
        with database_engine.connect() as connection:
            assert connection.execute(
                text("SELECT title FROM tables WHERE chat_id = 1")
            ).scalar_one() == "Legacy table"
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "003_add_browser_scope"
    finally:
        database_engine.dispose()


def test_upgrade_database_rejects_partial_unversioned_schema(monkeypatch, tmp_path):
    database_engine = _configure_database(monkeypatch, tmp_path)
    try:
        with database_engine.begin() as connection:
            connection.execute(text("CREATE TABLE chats (id INTEGER PRIMARY KEY)"))

        with pytest.raises(RuntimeError, match="does not match the complete initial schema"):
            migrations.upgrade_database()
    finally:
        database_engine.dispose()
