"""JSON file-backed storage (default for self-hosted OSS usage)."""

from __future__ import annotations

import json
import os
import tempfile

from config import config

# Data files hold PII (leads, CRM contacts, complaints): owner-only access.
DATA_DIR_MODE = 0o700
DATA_FILE_MODE = 0o600


class JsonStorage:
    """Read and write entity lists as JSON files under config.DATA_DIR."""

    def _ensure_dir(self) -> None:
        # Only a newly created DATA_DIR gets 0700; an existing one may be a deliberately shared volume.
        os.makedirs(config.DATA_DIR, mode=DATA_DIR_MODE, exist_ok=True)

    def _read(self, path: str) -> list[dict]:
        self._ensure_dir()
        if not os.path.exists(path):
            return []
        with open(path) as f:
            return json.load(f)

    def _write(self, path: str, data: list[dict] | dict) -> None:
        """Write atomically via an owner-only temp file, so files are never briefly world-readable or half-written."""
        self._ensure_dir()
        fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".tmp-", suffix=".json")
        try:
            os.chmod(tmp_path, DATA_FILE_MODE)
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, path)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

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
        self._ensure_dir()
        if not os.path.exists(config.BUSINESS_PROFILE_FILE):
            return None
        with open(config.BUSINESS_PROFILE_FILE) as f:
            return json.load(f)

    def save_business_profile(self, data: dict) -> None:
        self._write(config.BUSINESS_PROFILE_FILE, data)

    def load_audience_personas(self) -> list[dict]:
        return self._read(config.AUDIENCE_PERSONAS_FILE)

    def save_audience_personas(self, data: list[dict]) -> None:
        self._write(config.AUDIENCE_PERSONAS_FILE, data)

    def load_crm_segments(self) -> list[dict]:
        return self._read(config.CRM_SEGMENTS_FILE)

    def save_crm_segments(self, data: list[dict]) -> None:
        self._write(config.CRM_SEGMENTS_FILE, data)
