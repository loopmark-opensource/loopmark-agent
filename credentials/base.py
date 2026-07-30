"""Credential access abstraction for OSS (.env) and future hosted vault adapters."""

from __future__ import annotations

from typing import Protocol


class CredentialsProtocol(Protocol):
    """
    Extension point for credential providers.

    OSS: EnvCredentials reads from environment variables (BYOK).
    Hosted (future, not in this repo): vault-backed per-org credentials.
    """

    def twitter(self) -> dict[str, str] | None:
        """Return Twitter OAuth 1.0a keys or None if not configured."""
        ...

    def linkedin(self) -> dict[str, str] | None:
        """Return LinkedIn token + person_id or None if not configured."""
        ...

    def buffer(self) -> dict[str, str] | None:
        """Return Buffer access token or None if not configured."""
        ...
