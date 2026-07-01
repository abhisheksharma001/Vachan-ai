"""ORM models package. Importing this registers every table on Base.metadata."""
from app.models.base import Base
from app.models.tables import (
    AuditLog,
    Consent,
    Conversation,
    MemoryFragment,
    Message,
    Org,
    Persona,
    PersonaCapsule,
    PersonaObservation,
    StyleVector,
    User,
)

__all__ = [
    "Base",
    "Org",
    "User",
    "Consent",
    "Persona",
    "PersonaObservation",
    "StyleVector",
    "PersonaCapsule",
    "MemoryFragment",
    "Conversation",
    "Message",
    "AuditLog",
]
