"""add chat lifecycle columns

Revision ID: 9c4e7a1b2d6f
Revises: 8a5d8d9f4e2c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c4e7a1b2d6f"
down_revision: Union[str, Sequence[str], None] = "8a5d8d9f4e2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_chat_messages_role",
        "chat_messages",
        "role IN ('user', 'assistant')",
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "deleted_at")
    op.drop_column("chat_sessions", "archived_at")
    op.drop_constraint(
        "ck_chat_messages_role", "chat_messages", type_="check"
    )