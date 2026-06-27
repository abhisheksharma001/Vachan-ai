"""initial schema — all 10 tables, RLS, append-only triggers, immutable audit

Revision ID: 0001
Revises:
Create Date: 2026-06-27

This migration is the AUTHORITATIVE Phase-0 schema. It runs as the OWNER role
(DATABASE_URL_SYNC) and applies, in order:

  1. the pgvector extension (needed for VECTOR columns);
  2. the lower-privilege application role `vachan_app` (see RLS note below);
  3. all 10 tables (PRD §9 + FD overrides);
  4. privilege grants to `vachan_app`;
  5. Row-Level Security policies (org isolation);
  6. append-only triggers (persona_observations, persona_capsules);
  7. immutable triggers (audit_log);
  8. indexes (the pgvector ANN index + helpful FK indexes).

WHY TWO ROLES (the RLS subtlety the PRD missed)
-----------------------------------------------
In Postgres, the role that OWNS a table BYPASSES that table's RLS policies
unless RLS is FORCED. Our migrations/provisioning run as the owner (so we can
create orgs/users before any org-context exists). If the running app ALSO used
the owner role, RLS would never actually filter anything — the isolation test
would be a no-op. So the app connects as `vachan_app` (a non-owner LOGIN role),
which IS subject to RLS. Owner = provisioning/migrations; app role = requests.

WHY TRIGGERS, NOT `CREATE RULE ... DO INSTEAD NOTHING` (the append-only fix)
---------------------------------------------------------------------------
The PRD's blunt no-update RULE would silently swallow ALL updates — including
the DPDP erasure workflow, which legitimately sets `deleted_at`. That makes the
PRD self-contradictory. Instead we use a BEFORE UPDATE trigger that RAISES on
any normal update, but PERMITS the update when the session has explicitly opted
in via `SET app.allow_erasure = 'on'` (only the V1 erasure workflow does this).
Append-only is preserved AND erasure stays possible.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# The verified style-vector dimension (FD-2). Imported, never hardcoded, so the
# schema dimension and the application constant can never silently disagree.
from app.core.constants import STYLE_VECTOR_DIM

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Name of the lower-privilege role the running app uses (RLS applies to it).
APP_ROLE = "vachan_app"
APP_ROLE_PASSWORD = "vachan_app"  # local dev only; production manages this externally

# Tenant tables whose isolation key is `org_id`.
ORG_SCOPED_TABLES = [
    "users",
    "consents",
    "personas",
    "persona_observations",
    "style_vectors",
    "persona_capsules",
    "conversations",
    "messages",
]


def upgrade() -> None:
    # ── 1. Extension ────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── 2. Application role (idempotent) ────────────────────────────
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PASSWORD}';
            END IF;
        END$$;
        """
    )

    # ── 3. Tables (FK-safe creation order) ──────────────────────────
    op.execute(
        """
        CREATE TABLE orgs (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name        text NOT NULL,
            plan        text NOT NULL DEFAULT 'free',
            created_at  timestamptz NOT NULL DEFAULT now(),
            deleted_at  timestamptz
        );
        """
    )
    op.execute(
        """
        CREATE TABLE users (
            id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id       uuid NOT NULL REFERENCES orgs(id),
            email        text UNIQUE NOT NULL,
            display_name text,
            role         text NOT NULL DEFAULT 'member',
            created_at   timestamptz NOT NULL DEFAULT now(),
            deleted_at   timestamptz
        );
        """
    )
    op.execute(
        """
        CREATE TABLE consents (
            id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id               uuid NOT NULL REFERENCES orgs(id),
            user_id              uuid NOT NULL REFERENCES users(id),
            data_type            text NOT NULL,
            purpose              text NOT NULL,
            retention_days       int  NOT NULL,
            granted_at           timestamptz NOT NULL DEFAULT now(),
            expires_at           timestamptz,
            revoked_at           timestamptz,
            revocation_processed boolean NOT NULL DEFAULT false
        );
        """
    )
    op.execute(
        """
        CREATE TABLE personas (
            id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id                  uuid NOT NULL REFERENCES orgs(id),
            user_id                 uuid NOT NULL REFERENCES users(id),
            name                    text NOT NULL,
            language_primary        text NOT NULL DEFAULT 'hi-en',
            status                  text NOT NULL DEFAULT 'warming_up',
            current_capsule_version int,
            created_at              timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE persona_observations (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id           uuid NOT NULL REFERENCES orgs(id),
            persona_id       uuid NOT NULL REFERENCES personas(id),
            source_type      text NOT NULL,
            text_hash        text NOT NULL,
            token_count      int  NOT NULL,
            cmi              float,
            i_index          float,
            burstiness       float,
            cf               float,
            avg_sentence_len float,
            vocab_richness   float,
            punctuation_freq float,
            formality_score  float,
            merge_status     text NOT NULL DEFAULT 'pending',
            captured_at      timestamptz NOT NULL DEFAULT now(),
            consent_ref      uuid NOT NULL REFERENCES consents(id),
            deleted_at       timestamptz
        );
        """
    )
    # FD-2: vector dimension comes from the verified constant, never a literal.
    op.execute(
        f"""
        CREATE TABLE style_vectors (
            id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id         uuid NOT NULL REFERENCES orgs(id),
            observation_id uuid NOT NULL REFERENCES persona_observations(id),
            persona_id     uuid NOT NULL REFERENCES personas(id),
            vector         vector({STYLE_VECTOR_DIM}) NOT NULL,
            created_at     timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    # FD-7: capsule_data (JSONB) is the source of truth; yaml_rendered is a view.
    op.execute(
        f"""
        CREATE TABLE persona_capsules (
            id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id             uuid NOT NULL REFERENCES orgs(id),
            persona_id         uuid NOT NULL REFERENCES personas(id),
            version            int  NOT NULL,
            capsule_data       jsonb NOT NULL,
            yaml_rendered      text,
            fingerprint_vector vector({STYLE_VECTOR_DIM}) NOT NULL,
            observations_count int  NOT NULL,
            pfs_last_score     float,
            drift_flag         boolean NOT NULL DEFAULT false,
            consent_ref        uuid NOT NULL REFERENCES consents(id),
            created_at         timestamptz NOT NULL DEFAULT now(),
            deleted_at         timestamptz,
            CONSTRAINT uq_capsule_persona_version UNIQUE (persona_id, version)
        );
        """
    )
    op.execute(
        """
        CREATE TABLE conversations (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id          uuid NOT NULL REFERENCES orgs(id),
            user_id         uuid NOT NULL REFERENCES users(id),
            persona_id      uuid NOT NULL REFERENCES personas(id),
            capsule_version int  NOT NULL,
            channel         text NOT NULL,
            started_at      timestamptz NOT NULL DEFAULT now(),
            last_active_at  timestamptz NOT NULL DEFAULT now(),
            turn_count      int  NOT NULL DEFAULT 0,
            avg_pfs_score   float
        );
        """
    )
    op.execute(
        """
        CREATE TABLE messages (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id          uuid NOT NULL REFERENCES orgs(id),
            conversation_id uuid NOT NULL REFERENCES conversations(id),
            turn_number     int  NOT NULL,
            role            text NOT NULL,
            content         text NOT NULL,
            pfs_score       float,
            model_used      text,
            escalated       boolean NOT NULL DEFAULT false,
            created_at      timestamptz NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        """
        CREATE TABLE audit_log (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id      uuid REFERENCES orgs(id),
            user_id     uuid REFERENCES users(id),
            event_type  text NOT NULL,
            entity_type text,
            entity_id   uuid,
            details     jsonb,
            ip_address  inet,
            created_at  timestamptz NOT NULL DEFAULT now()
        );
        """
    )

    # ── 4. Grants to the app role ───────────────────────────────────
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}"
    )
    # Future tables created by the owner are auto-granted too.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}"
    )

    # ── 5. Row-Level Security ───────────────────────────────────────
    # `orgs` keys on its own id; every other tenant table keys on org_id.
    # RLS is ENABLED but not FORCED: the owner bypasses it for provisioning;
    # the app role is subject to it.
    #
    # Fail-closed detail: NULLIF(current_setting(..., true), '') maps BOTH
    # "never set" (NULL) AND "reset to empty after a SET LOCAL on this pooled
    # connection" ('') to NULL. `org_id = NULL` is NULL → no rows. Without the
    # NULLIF, a stale '' would hit `''::uuid` and raise instead of returning
    # zero rows — i.e. fail-open-ish errors instead of clean fail-closed.
    org_ctx = "NULLIF(current_setting('app.current_org_id', true), '')::uuid"

    op.execute("ALTER TABLE orgs ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY orgs_isolation ON orgs
            USING (id = {org_ctx})
            WITH CHECK (id = {org_ctx});
        """
    )
    for table in ORG_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_org_isolation ON {table}
                USING (org_id = {org_ctx})
                WITH CHECK (org_id = {org_ctx});
            """
        )

    # ── 6. Append-only triggers ─────────────────────────────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION vachan_block_update_append_only()
        RETURNS trigger AS $$
        BEGIN
            -- DPDP erasure (V1) opts in with: SET LOCAL app.allow_erasure = 'on';
            IF current_setting('app.allow_erasure', true) = 'on' THEN
                RETURN NEW;
            END IF;
            RAISE EXCEPTION
                'Table % is append-only; UPDATE is not permitted '
                '(gate app.allow_erasure for DPDP erasure).', TG_TABLE_NAME
                USING ERRCODE = 'check_violation';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in ("persona_observations", "persona_capsules"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_append_only
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION vachan_block_update_append_only();
            """
        )

    # ── 7. Immutable audit_log (no UPDATE, no DELETE, ever) ─────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION vachan_block_modify_immutable()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Table % is immutable; % is not permitted.',
                TG_TABLE_NAME, TG_OP
                USING ERRCODE = 'check_violation';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION vachan_block_modify_immutable();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log
            FOR EACH ROW EXECUTE FUNCTION vachan_block_modify_immutable();
        """
    )

    # ── 8. Indexes ──────────────────────────────────────────────────
    # pgvector ANN index for style similarity (PRD §9). IVFFlat is fine for
    # Phase-1 volumes; switch to HNSW at Phase-2 scale.
    op.execute(
        """
        CREATE INDEX style_vectors_vector_idx
            ON style_vectors USING ivfflat (vector vector_cosine_ops)
            WITH (lists = 100);
        """
    )
    # Helpful B-tree indexes on hot foreign keys (cheap, used from Phase 1).
    op.execute("CREATE INDEX persona_observations_persona_idx ON persona_observations (persona_id)")
    op.execute("CREATE INDEX style_vectors_persona_idx ON style_vectors (persona_id)")
    op.execute("CREATE INDEX persona_capsules_persona_idx ON persona_capsules (persona_id)")
    op.execute("CREATE INDEX conversations_persona_idx ON conversations (persona_id)")
    op.execute("CREATE INDEX messages_conversation_idx ON messages (conversation_id)")
    op.execute("CREATE INDEX consents_user_idx ON consents (user_id)")


def downgrade() -> None:
    # Drop tables (reverse FK order); CASCADE clears policies, triggers, indexes.
    for table in (
        "audit_log",
        "messages",
        "conversations",
        "persona_capsules",
        "style_vectors",
        "persona_observations",
        "personas",
        "consents",
        "users",
        "orgs",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    op.execute("DROP FUNCTION IF EXISTS vachan_block_update_append_only()")
    op.execute("DROP FUNCTION IF EXISTS vachan_block_modify_immutable()")

    # Remove the app role's grants, then the role itself.
    op.execute(f"DROP OWNED BY {APP_ROLE}")
    op.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
