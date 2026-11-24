"""JSON data files hold PII and must be owner-only (issue #68)."""

from __future__ import annotations

import os
import stat

import pytest
from typer.testing import CliRunner

from config import config
from storage import get_storage

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits")


def _mode(path: str) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


class _Unserializable:
    def __str__(self) -> str:
        raise TypeError("cannot serialize")


@pytest.mark.parametrize(
    ("save", "path_attr", "data"),
    [
        ("save_leads", "LEADS_FILE", [{"id": "LEAD-1", "email": "a@example.com"}]),
        ("save_crm_segments", "CRM_SEGMENTS_FILE", [{"segment": "smb", "email": "b@example.com"}]),
        ("save_complaints", "COMPLAINTS_FILE", [{"id": "CMP-1", "customer_email": "c@example.com"}]),
        ("save_business_profile", "BUSINESS_PROFILE_FILE", {"product_name": "Acme"}),
    ],
)
def test_saved_files_are_owner_only(save, path_attr, data):
    getattr(get_storage(), save)(data)
    assert _mode(getattr(config, path_attr)) == 0o600


def test_rewrite_tightens_existing_world_readable_file():
    path = config.LEADS_FILE
    with open(path, "w") as f:
        f.write("[]")
    os.chmod(path, 0o644)

    get_storage().save_leads([{"id": "LEAD-2"}])
    assert _mode(path) == 0o600
    assert get_storage().load_leads() == [{"id": "LEAD-2"}]


def test_new_data_dir_is_owner_only(tmp_path, monkeypatch):
    fresh = tmp_path / "fresh-data"
    monkeypatch.setattr(config, "DATA_DIR", str(fresh))
    monkeypatch.setattr(config, "LEADS_FILE", str(fresh / "leads.json"))

    get_storage().save_leads([])
    assert _mode(str(fresh)) == 0o700


def test_failed_write_keeps_previous_file_and_cleans_up():
    storage = get_storage()
    storage.save_leads([{"id": "LEAD-OK"}])

    with pytest.raises(TypeError):
        storage.save_leads([{"bad": _Unserializable()}])
    assert storage.load_leads() == [{"id": "LEAD-OK"}]
    assert not [n for n in os.listdir(config.DATA_DIR) if n.startswith(".tmp-")]


def test_serve_refuses_shared_writable_data_dir(monkeypatch):
    from main import app

    os.chmod(config.DATA_DIR, 0o777)
    monkeypatch.setenv("LOOPMARK_API_KEY", "k")
    result = CliRunner().invoke(app, ["serve"])
    assert result.exit_code == 1
    assert "group/world-writable" in result.output
