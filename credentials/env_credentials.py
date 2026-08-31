"""Environment-variable credential provider (default for self-hosted OSS)."""

from __future__ import annotations

import os


class EnvCredentials:
    """Read social publishing credentials from process environment / .env."""

    def twitter(self) -> dict[str, str] | None:
        keys = [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_SECRET",
        ]
        vals = {k: os.getenv(k, "") for k in keys}
        return vals if all(vals.values()) else None

    def linkedin(self) -> dict[str, str] | None:
        token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        person_id = os.getenv("LINKEDIN_PERSON_ID", "")
        return {"token": token, "person_id": person_id} if token and person_id else None

    def buffer(self) -> dict[str, str] | None:
        token = os.getenv("BUFFER_ACCESS_TOKEN", "")
        return {"token": token} if token else None
