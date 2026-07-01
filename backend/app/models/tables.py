"""
SQLAlchemy ORM models for all Phase-0 tables (PRD §9 + FD overrides).

AUTHORITY NOTE
--------------
The Alembic migration (migrations/versions/0001_initial_schema.py) is the
AUTHORITATIVE schema: it carries the things ORM cannot express — Row-Level
Security policies, FORCE ROW LEVEL SECURITY, the append-only NO-UPDATE rules,
and the pgvector index. These ORM classes mirror the same columns so the
application can query with typed objects. Keep the two in sync.

FD overrides applied here (vs. the council PRD):
  • FD-2  — vector columns use STYLE_VECTOR_DIM (768, verified), not 384.
  • FD-7  — persona_capsules stores `capsule_data` (JSONB, source of truth)
            + `yaml_rendered` (derived view), replacing the PRD's `yaml_blob`.
  • FD-6  — no OCEAN columns; OCEAN, if present, lives only as optional
            decorative keys inside capsule_data and never gates anything.
"""
from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import STYLE_VECTOR_DIM
from app.models.base import Base

# Reusable column helpers ------------------------------------------------
_uuid_pk = lambda: mapped_column(  # noqa: E731
    UUID(as_uuid=True),
    primary_key=True,
    server_default=text("gen_random_uuid()"),
)
_created_at = lambda: mapped_column(  # noqa: E731
    DateTime(timezone=True), nullable=False, server_default=func.now()
)


class Org(Base):
    """Root entity for multi-tenancy. One row per business/contestant/customer."""
    __tablename__ = "orgs"

    id: Mapped[str] = _uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'free'"))
    created_at: Mapped[datetime] = _created_at()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class User(Base):
    """A person within an org. A data principal under the DPDP Act."""
    __tablename__ = "users"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'member'"))
    created_at: Mapped[datetime] = _created_at()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Consent(Base):
    """DPDP consent grant — one row per (data_type, purpose). Required before ingest."""
    __tablename__ = "consents"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    data_type: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    granted_at: Mapped[datetime] = _created_at()
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_processed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )


class Persona(Base):
    """A named communication identity. One user may own several."""
    __tablename__ = "personas"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    language_primary: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'hi-en'")
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'warming_up'")
    )
    # Denormalized pointer to the latest persona_capsules.version (FD-4 bands
    # are reflected in `status`, not here).
    current_capsule_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created_at()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PersonaObservation(Base):
    """
    One writing sample per row. THE most important table. APPEND-ONLY:
    enforced at the DB level by a NO-UPDATE rule (see the migration). Only the
    DPDP erasure workflow ever sets `deleted_at`. Raw text is never stored —
    only the SHA-256 `text_hash` of the sanitized text.
    """
    __tablename__ = "persona_observations"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Hinglish / stylometric features (FD-16 expands these in Phase 1/V1).
    cmi: Mapped[float | None] = mapped_column(Float)
    i_index: Mapped[float | None] = mapped_column(Float)
    burstiness: Mapped[float | None] = mapped_column(Float)
    cf: Mapped[float | None] = mapped_column(Float)
    avg_sentence_len: Mapped[float | None] = mapped_column(Float)
    vocab_richness: Mapped[float | None] = mapped_column(Float)
    punctuation_freq: Mapped[float | None] = mapped_column(Float)
    formality_score: Mapped[float | None] = mapped_column(Float)
    merge_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    captured_at: Mapped[datetime] = _created_at()
    # NOT NULL FK — an observation cannot exist without a consent (DPDP).
    consent_ref: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consents.id"), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # NOTE: no updated_at — this table is append-only.


class StyleVector(Base):
    """The style fingerprint per observation (mStyleDistance, dim = STYLE_VECTOR_DIM)."""
    __tablename__ = "style_vectors"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    observation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persona_observations.id"), nullable=False
    )
    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False
    )
    # FD-2: 768, sourced from the verified constant — never a bare literal.
    vector: Mapped[list[float]] = mapped_column(Vector(STYLE_VECTOR_DIM), nullable=False)
    created_at: Mapped[datetime] = _created_at()


class PersonaCapsule(Base):
    """
    Versioned persona snapshot. APPEND-ONLY (NO-UPDATE rule in the migration).

    FD-7: the STRUCTURED record is the source of truth:
      • capsule_data (JSONB)  — typed, queryable, diffable — the real state.
      • yaml_rendered (Text)  — a human-readable VIEW rendered from capsule_data.
    The PRD's single `yaml_blob` is intentionally replaced.
    """
    __tablename__ = "persona_capsules"
    __table_args__ = (UniqueConstraint("persona_id", "version", name="uq_capsule_persona_version"),)

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    capsule_data: Mapped[dict] = mapped_column(JSONB, nullable=False)   # FD-7 source of truth
    yaml_rendered: Mapped[str | None] = mapped_column(Text)             # FD-7 derived view
    fingerprint_vector: Mapped[list[float]] = mapped_column(
        Vector(STYLE_VECTOR_DIM), nullable=False  # FD-2: centroid in style space (768)
    )
    observations_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pfs_last_score: Mapped[float | None] = mapped_column(Float)
    drift_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    consent_ref: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consents.id"), nullable=False
    )
    created_at: Mapped[datetime] = _created_at()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Conversation(Base):
    """Session-level container linking a user, a persona+capsule version, a channel."""
    __tablename__ = "conversations"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False
    )
    capsule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = _created_at()
    last_active_at: Mapped[datetime] = _created_at()
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    avg_pfs_score: Mapped[float | None] = mapped_column(Float)


class Message(Base):
    """One turn in a conversation. `pfs_score` is the most granular fidelity data."""
    __tablename__ = "messages"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    conversation_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    pfs_score: Mapped[float | None] = mapped_column(Float)
    model_used: Mapped[str | None] = mapped_column(Text)            # FD-10: logged per turn
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = _created_at()


class PersonaKBEntry(Base):
    """
    One knowledge "concept" per row (OKF: docs/OKF SPEC — a typed, tagged unit
    of knowledge with a markdown body). Facts, corrections, and stories a
    persona owner adds so the Mirror can draw on them at chat time.

    Unlike persona_observations/persona_capsules this is NOT append-only —
    editable/deletable, matching OKF's model of knowledge as living documents
    rather than an immutable log.
    """
    __tablename__ = "persona_kb_entries"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"), nullable=False)
    persona_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("personas.id"), nullable=False
    )
    # OKF frontmatter fields (§4.1 of the spec) — `type` is the only required one.
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # How the entry originated: 'manual' | 'chat_correction' | 'extraction'.
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'manual'"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _created_at()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    """
    Immutable audit trail. NO UPDATE, NO DELETE ever (enforced in the migration).
    org_id is nullable so system-level events can be recorded.
    """
    __tablename__ = "audit_log"

    id: Mapped[str] = _uuid_pk()
    org_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("orgs.id"))
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(Text)
    entity_id: Mapped[str | None] = mapped_column(UUID(as_uuid=True))
    details: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = _created_at()
