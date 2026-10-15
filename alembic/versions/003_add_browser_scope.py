"""Associate chats with a browser identity.

Revision ID: 003_add_browser_scope
Revises: 002_add_styles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_add_browser_scope"
down_revision: Union[str, None] = "002_add_styles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chats", sa.Column("browser_id", sa.String(length=36), nullable=True))
    op.create_index("ix_chats_browser_id", "chats", ["browser_id"])


def downgrade() -> None:
    op.drop_index("ix_chats_browser_id", table_name="chats")
    op.drop_column("chats", "browser_id")
