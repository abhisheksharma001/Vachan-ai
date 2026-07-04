"""add unique index on conversations(persona_id, user_id)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04

Without this, two concurrent chat requests (e.g. two open tabs) both find no
existing conversation and each insert a new row — forking turn/PFS history
into two conversations instead of one. CTO review, item 3. Paired with the
ON CONFLICT DO UPDATE upsert in app.api.personas._record_turn.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX uq_conversations_persona_user "
        "ON conversations (persona_id, user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_conversations_persona_user")
