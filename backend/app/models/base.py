"""SQLAlchemy declarative base. All ORM models inherit from this."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata for every table. Alembic reads Base.metadata."""
    pass
