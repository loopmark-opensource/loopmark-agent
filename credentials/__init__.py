"""Credential providers — swap EnvCredentials for a vault adapter in hosted deployments."""

from __future__ import annotations

from credentials.base import CredentialsProtocol
from credentials.env_credentials import EnvCredentials

_default_credentials: CredentialsProtocol | None = None


def get_credentials() -> CredentialsProtocol:
    """Return the active credentials backend (.env by default)."""
    global _default_credentials
    if _default_credentials is None:
        _default_credentials = EnvCredentials()
    return _default_credentials


def set_credentials(credentials: CredentialsProtocol) -> None:
    """Replace the default credentials backend (useful for tests or hosted adapters)."""
    global _default_credentials
    _default_credentials = credentials
