"""Storage layer — swap JsonStorage for Postgres in hosted deployments."""

from __future__ import annotations

from storage.base import StorageProtocol
from storage.json_storage import JsonStorage

_default_storage: StorageProtocol | None = None


def get_storage() -> StorageProtocol:
    """Return the active storage backend (JSON files by default)."""
    global _default_storage
    if _default_storage is None:
        _default_storage = JsonStorage()
    return _default_storage


def set_storage(storage: StorageProtocol) -> None:
    """Replace the default storage backend (useful for tests or hosted adapters)."""
    global _default_storage
    _default_storage = storage
