"""Path/body ID validation shared by the API routers.

Postgres UUID columns reject a malformed string at the DB layer (a
psycopg DataError), which surfaces as an unhandled 500. Validating the
format in Python first turns that into the normal 404 a missing/garbled
ID should produce.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException


def ensure_uuid(value: str, *, detail: str = "Not found.") -> None:
    """Raise a 404 if `value` isn't a valid UUID string."""
    try:
        UUID(value)
    except ValueError:
        raise HTTPException(status_code=404, detail=detail)
