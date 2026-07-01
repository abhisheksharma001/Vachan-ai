"""add persona_kb_entries (per-persona OKF knowledge base)

Revision ID: a1c9f2e6b7d4
Revises: fd0ae06e8499
Create Date: 2026-07-02 00:00:00.000000

One row per knowledge "concept" (docs/OKF format: a typed, tagged unit of
knowledge with a markdown body) — facts, corrections, and stories a persona
owner adds so the Mirror can draw on them at chat time. Unlike
persona_observations/persona_capsules this table is NOT append-only: a
correction or fact is user-editable/deletable, matching OKF's own model of
knowledge as living, diffable documents rather than an immutable log.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "a1c9f2e6b7d4"
down_revision: str | None = "fd0ae06e8499"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE persona_kb_entries (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id      uuid NOT NULL REFERENCES orgs(id),
            persona_id  uuid NOT NULL REFERENCES personas(id),
            type        text NOT NULL,
            title       text,
            description text,
            tags        jsonb NOT NULL DEFAULT '[]'::jsonb,
            body        text NOT NULL,
            source      text NOT NULL DEFAULT 'manual',
            created_at  timestamptz NOT NULL DEFAULT now(),
            updated_at  timestamptz NOT NULL DEFAULT now(),
            deleted_at  timestamptz
        );
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON persona_kb_entries TO vachan_app")

    org_ctx = "NULLIF(current_setting('app.current_org_id', true), '')::uuid"
    op.execute("ALTER TABLE persona_kb_entries ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY persona_kb_entries_org_isolation ON persona_kb_entries
            USING (org_id = {org_ctx})
            WITH CHECK (org_id = {org_ctx});
        """
    )
    op.execute("CREATE INDEX persona_kb_entries_persona_idx ON persona_kb_entries (persona_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS persona_kb_entries CASCADE")
