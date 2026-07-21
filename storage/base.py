"""Storage abstraction for marketing-agent persistence."""

from __future__ import annotations

from typing import Protocol


class StorageProtocol(Protocol):
    """Persistence interface for complaints, leads, posts, and emails."""

    def load_complaints(self) -> list[dict]:
        ...

    def save_complaints(self, data: list[dict]) -> None:
        ...

    def load_leads(self) -> list[dict]:
        ...

    def save_leads(self, data: list[dict]) -> None:
        ...

    def load_posts(self) -> list[dict]:
        ...

    def save_posts(self, data: list[dict]) -> None:
        ...

    def load_emails(self) -> list[dict]:
        ...

    def save_emails(self, data: list[dict]) -> None:
        ...
