"""Tests for the optional FastAPI REST layer."""

from __future__ import annotations

import socket

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from api import app as api_module
from core.run import AgentResult

SAMPLE_CSV = """segment,name,email,company,industry,job_title,tags
Enterprise,Sarah Lee,s@bigco.com,BigCo,SaaS,CTO,automation;content
SMB,John Doe,j@shop.com,ShopCo,Retail,Owner,local;instagram
Enterprise,Mike Chen,m@bigco.com,BigCo,SaaS,VP Marketing,automation
"""


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv(api_module.API_KEY_ENV, raising=False)
    return TestClient(api_module.create_app())


def _fake_dns(ip: str):
    return lambda host, port, *a, **kw: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_openapi_docs_served(client):
    assert client.get("/docs").status_code == 200
    assert "/personas" in client.get("/openapi.json").json()["paths"]


def test_profile_roundtrip(client):
    assert client.get("/profile").status_code == 404

    resp = client.put("/profile", json={"product_name": "Acme", "brand_tone": "friendly"})
    assert resp.status_code == 200

    profile = client.get("/profile").json()
    assert profile["product_name"] == "Acme"
    assert profile["brand_tone"] == "friendly"


def test_personas_create_and_list(client):
    resp = client.post(
        "/personas",
        json={"name": "Busy Founder", "preferred_platforms": ["linkedin"]},
    )
    assert resp.status_code == 201
    assert resp.json()["id"].startswith("PERSONA-")

    personas = client.get("/personas").json()
    assert [p["name"] for p in personas] == ["Busy Founder"]
    assert personas[0]["source"] == "api"


def test_crm_import_csv(client):
    resp = client.post("/crm/import", json={"data": SAMPLE_CSV, "format": "csv"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] == 3
    assert body["segments"] == {"Enterprise": 2, "SMB": 1}

    again = client.post("/crm/import", json={"data": SAMPLE_CSV, "merge": True}).json()
    assert again["total"] == 6


def test_crm_import_rejects_bad_json(client):
    resp = client.post("/crm/import", json={"data": "{not json", "format": "json"})
    assert resp.status_code == 422


def test_analyze_website_blocks_private_addresses(client, monkeypatch):
    monkeypatch.setattr(api_module.socket, "getaddrinfo", _fake_dns("169.254.169.254"))
    called = []
    monkeypatch.setattr(api_module, "fetch_site_summary", lambda url: called.append(url))

    resp = client.post("/analyze/website", json={"url": "http://metadata.internal/latest"})
    assert resp.status_code == 422
    assert not called


def test_analyze_website_public_url(client, monkeypatch):
    monkeypatch.setattr(api_module.socket, "getaddrinfo", _fake_dns("93.184.216.34"))
    site = {
        "url": "https://example.com",
        "title": "Loopmark | AI Marketing for Small Teams",
        "description": "Automate social posts and email for SMB marketers.",
        "snippet": "Save time on content and grow your audience with AI.",
    }
    monkeypatch.setattr(api_module, "fetch_site_summary", lambda url: site)

    resp = client.post("/analyze/website", json={"url": "example.com"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["site"]["url"] == "https://example.com"
    assert body["research"]["personas"]


def test_chat_wraps_run_agent(client, monkeypatch):
    seen = {}

    def fake_run_agent(message, history=None, model=None):
        seen.update(message=message, history=history, model=model)
        return AgentResult(reply="Here are 3 posts", intent="posting", messages=[])

    monkeypatch.setattr("core.run.run_agent", fake_run_agent)

    resp = client.post(
        "/chat",
        json={
            "message": "Write posts",
            "history": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        },
    )
    assert resp.json() == {"reply": "Here are 3 posts", "intent": "posting"}
    assert seen["message"] == "Write posts"
    assert [m.content for m in seen["history"]] == ["hi", "hello"]


def test_api_key_required_when_configured(monkeypatch):
    monkeypatch.setenv(api_module.API_KEY_ENV, "s3cret")
    client = TestClient(api_module.create_app())

    assert client.get("/health").status_code == 200
    assert client.get("/personas").status_code == 401
    assert client.get("/personas", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/personas", headers={"X-API-Key": "s3cret"}).status_code == 200
