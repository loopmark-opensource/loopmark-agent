"""Shared identifiers for persisted records."""

from uuid import uuid4


def new_id(prefix: str) -> str:
    """Keep record types readable without depending on clock resolution."""
    return f"{prefix}-{uuid4().hex}"
