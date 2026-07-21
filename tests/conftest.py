"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Route all JSON persistence to a temporary directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    monkeypatch.setattr("config.config.DATA_DIR", str(data_dir))
    monkeypatch.setattr("config.config.COMPLAINTS_FILE", str(data_dir / "complaints.json"))
    monkeypatch.setattr("config.config.LEADS_FILE", str(data_dir / "leads.json"))
    monkeypatch.setattr("config.config.POSTS_FILE", str(data_dir / "posts.json"))
    monkeypatch.setattr("config.config.EMAILS_FILE", str(data_dir / "emails.json"))

    from storage import set_storage
    from storage.json_storage import JsonStorage

    set_storage(JsonStorage())

    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-ci")
