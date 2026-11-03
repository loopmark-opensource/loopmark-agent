"""Time helpers.

``datetime.utcnow()`` is deprecated since Python 3.12 and returns a naive
datetime. Use :func:`utcnow` instead, which returns a timezone-aware UTC value.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 string, treating naive values (legacy data) as UTC.

    Older JSON files store naive timestamps; this keeps them comparable with
    the aware values produced by :func:`utcnow`.
    """
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
