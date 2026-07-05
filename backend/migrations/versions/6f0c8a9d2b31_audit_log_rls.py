"""enable RLS on audit_log (it was omitted from ORG_SCOPED_TABLES in 0001)

Revision ID: 6f0c8a9d2b31
Revises: fd0ae06e8499
Create Date: 2026-07-06

SECURITY: audit_log has an org_id column and is actively written to
(app.workers.echo_worker) but 0001_initial_schema.py's ORG_SCOPED_TABLES
list — the loop that ENABLEs RLS + creates the org-isolation policy for
every tenant table — did not include it. Every other tenant table is
protected at the Postgres level from cross-org reads; this one silently
was not. Nothing currently SELECTs from audit_log, so there is no known
exploited path yet, but any future audit/reporting endpoint using the
normal org_scoped_session would get every org's audit rows back, not just
its own — the opposite of what this codebase's RLS model promises.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "6f0c8a9d2b31"
down_revision: str | None = "fd0ae06e8499"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORG_CTX = "NULLIF(current_setting('app.current_org_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY audit_log_org_isolation ON audit_log
            USING (org_id = {_ORG_CTX})
            WITH CHECK (org_id = {_ORG_CTX});
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_log_org_isolation ON audit_log")
    op.execute("ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY")
