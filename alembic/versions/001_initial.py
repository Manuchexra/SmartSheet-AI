"""Initial schema: chats, messages, tables

Revision ID: 001_initial
Revises:
Create Date: 2026-10-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Jadvallarni yaratish."""

    # ============================================
    # 1. CHATS
    # ============================================
    op.create_table(
        "chats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chats_title", "chats", ["title"], unique=False)
    op.create_index("ix_chats_updated_at", "chats", ["updated_at"], unique=False)

    # ============================================
    # 2. MESSAGES
    # ============================================
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"], unique=False)
    op.create_index("ix_messages_role", "messages", ["role"], unique=False)
    op.create_index(
        "ix_messages_chat_created",
        "messages",
        ["chat_id", "created_at"],
        unique=False,
    )

    # ============================================
    # 3. TABLES
    # ============================================
    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("columns", sa.JSON(), nullable=False),
        sa.Column("rows", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", name="uq_tables_chat_id"),
    )
    op.create_index("ix_tables_chat_id", "tables", ["chat_id"], unique=False)
    op.create_index("ix_tables_updated_at", "tables", ["updated_at"], unique=False)


def downgrade() -> None:
    """Jadvallarni o'chirish (teskari tartibda)."""

    op.drop_index("ix_tables_updated_at", table_name="tables")
    op.drop_index("ix_tables_chat_id", table_name="tables")
    op.drop_table("tables")

    op.drop_index("ix_messages_chat_created", table_name="messages")
    op.drop_index("ix_messages_role", table_name="messages")
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_chats_updated_at", table_name="chats")
    op.drop_index("ix_chats_title", table_name="chats")
    op.drop_table("chats")