"""JSON file-backed storage (default for self-hosted OSS usage)."""

from __future__ import annotations

import json
import os

from config import config


class JsonStorage:
    """Read and write entity lists as JSON files under config.DATA_DIR."""

    def _read(self, path: str) -> list[dict]:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return json.load(f)

    def _write(self, path: str, data: list[dict]) -> None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_complaints(self) -> list[dict]:
        return self._read(config.COMPLAINTS_FILE)

    def save_complaints(self, data: list[dict]) -> None:
        self._write(config.COMPLAINTS_FILE, data)

    def load_leads(self) -> list[dict]:
        return self._read(config.LEADS_FILE)

    def save_leads(self, data: list[dict]) -> None:
        self._write(config.LEADS_FILE, data)

    def load_posts(self) -> list[dict]:
        return self._read(config.POSTS_FILE)

    def save_posts(self, data: list[dict]) -> None:
        self._write(config.POSTS_FILE, data)

    def load_emails(self) -> list[dict]:
        return self._read(config.EMAILS_FILE)

    def save_emails(self, data: list[dict]) -> None:
        self._write(config.EMAILS_FILE, data)

    def load_business_profile(self) -> dict | None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        if not os.path.exists(config.BUSINESS_PROFILE_FILE):
            return None
        with open(config.BUSINESS_PROFILE_FILE) as f:
            return json.load(f)

    def save_business_profile(self, data: dict) -> None:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(config.BUSINESS_PROFILE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_audience_personas(self) -> list[dict]:
        return self._read(config.AUDIENCE_PERSONAS_FILE)

    def save_audience_personas(self, data: list[dict]) -> None:
        self._write(config.AUDIENCE_PERSONAS_FILE, data)

    def load_crm_segments(self) -> list[dict]:
        return self._read(config.CRM_SEGMENTS_FILE)

    def save_crm_segments(self, data: list[dict]) -> None:
        self._write(config.CRM_SEGMENTS_FILE, data)
