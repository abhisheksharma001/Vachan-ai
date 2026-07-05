"""add memory_fragments table for semantic RAG

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-01

This migration adds the Phase-1/V1 semantic memory store:
  • memory_fragments — retrievable text + 1024-dim e5 embedding
  • RLS policy on org_id
  • pgvector ANN index + persona lookup index
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.core.constants import SEMANTIC_VECTOR_DIM

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "vachan_app"


def upgrade() -> None:
    # Ensure pgvector is present (idempotent; already created in 0001).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        f"""
        CREATE TABLE memory_fragments (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id        uuid NOT NULL REFERENCES orgs(id),
            persona_id    uuid NOT NULL REFERENCES personas(id),
            source_type   text NOT NULL,
            source_id     uuid,
            fragment_text text NOT NULL,
            vector        vector({SEMANTIC_VECTOR_DIM}) NOT NULL,
            created_at    timestamptz NOT NULL DEFAULT now(),
            deleted_at    timestamptz
        );
        """
    )

    # Grants to the lower-privilege app role.
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON memory_fragments TO {APP_ROLE}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}"
    )

    # Row-Level Security: tenant isolation by org_id.
    op.execute("ALTER TABLE memory_fragments ENABLE ROW LEVEL SECURITY")
    org_ctx = "NULLIF(current_setting('app.current_org_id', true), '')::uuid"
    op.execute(
        f"""
        CREATE POLICY memory_fragments_org_isolation ON memory_fragments
            USING (org_id = {org_ctx})
            WITH CHECK (org_id = {org_ctx});
        """
    )

    # Indexes: ANN for vector search, B-tree for persona scans/recent lookups.
    op.execute(
        """
        CREATE INDEX memory_fragments_vector_idx
            ON memory_fragments USING ivfflat (vector vector_cosine_ops)
            WITH (lists = 100);
        """
    )
    op.execute(
        "CREATE INDEX memory_fragments_persona_created_idx "
        "ON memory_fragments (persona_id, created_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_fragments CASCADE")
