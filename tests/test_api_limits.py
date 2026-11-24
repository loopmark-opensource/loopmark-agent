"""Body size, rate limits, and field caps on the REST API (issue #70)."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api import app as api_module
from api import limits
from core.run import AgentResult


@pytest.fixture
def make_client(monkeypatch):
    monkeypatch.delenv(api_module.API_KEY_ENV, raising=False)
    monkeypatch.setattr(
        "core.run.run_agent", lambda message, history=None, model=None: AgentResult("ok", "posting", [])
    )

    def build(**env):
        for name, value in env.items():
            monkeypatch.setenv(name, str(value))
        return TestClient(api_module.create_app())

    return build


def test_oversized_body_by_content_length_is_413(make_client):
    client = make_client(LOOPMARK_API_MAX_BODY_BYTES=200)
    resp = client.post("/crm/import", json={"data": "x" * 500})
    assert resp.status_code == 413
    assert "too large" in resp.json()["detail"]


def test_oversized_chunked_body_is_413(make_client):
    client = make_client(LOOPMARK_API_MAX_BODY_BYTES=200)
    chunks = (b'{"data": "' + b"x" * 100 for _ in range(5))  # no Content-Length: sent chunked
    resp = client.post("/crm/import", content=chunks, headers={"content-type": "application/json"})
    assert resp.status_code == 413


def test_body_under_limit_is_accepted(make_client):
    client = make_client(LOOPMARK_API_MAX_BODY_BYTES=10_000)
    assert client.post("/chat", json={"message": "hi"}).status_code == 200


def test_chat_burst_is_throttled_with_retry_after(make_client):
    client = make_client(LOOPMARK_API_CHAT_PER_MIN=3)
    codes = [client.post("/chat", json={"message": "hi"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]

    resp = client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 429
    assert 1 <= int(resp.headers["Retry-After"]) <= 60


def test_rate_limit_buckets_are_per_client(make_client):
    client = make_client(LOOPMARK_API_CHAT_PER_MIN=1)
    assert client.post("/chat", json={"message": "a"}, headers={"X-API-Key": "one"}).status_code == 200
    assert client.post("/chat", json={"message": "a"}, headers={"X-API-Key": "one"}).status_code == 429
    assert client.post("/chat", json={"message": "a"}, headers={"X-API-Key": "two"}).status_code == 200


def test_analyze_website_is_rate_limited(make_client, monkeypatch):
    def reject(url):
        raise api_module.UnsafeURLError("blocked for test")

    monkeypatch.setattr(api_module, "assert_public_http_url", reject)
    client = make_client(LOOPMARK_API_ANALYZE_PER_MIN=2)
    codes = [client.post("/analyze/website", json={"url": "https://example.com"}).status_code for _ in range(3)]
    assert codes == [422, 422, 429]


def test_other_endpoints_are_not_rate_limited(make_client):
    client = make_client(LOOPMARK_API_CHAT_PER_MIN=1, LOOPMARK_API_ANALYZE_PER_MIN=1)
    assert all(client.get("/personas").status_code == 200 for _ in range(5))


def test_unauthenticated_requests_do_not_consume_quota(make_client, monkeypatch):
    monkeypatch.setenv(api_module.API_KEY_ENV, "secret")
    client = make_client(LOOPMARK_API_CHAT_PER_MIN=1)
    for _ in range(3):
        assert client.post("/chat", json={"message": "hi"}).status_code == 401
    assert client.post("/chat", json={"message": "hi"}, headers={"X-API-Key": "secret"}).status_code == 200


def test_chat_history_and_message_caps(make_client):
    client = make_client()
    turns = [{"role": "user", "content": "x"}] * (api_module.MAX_CHAT_HISTORY + 1)
    assert client.post("/chat", json={"message": "hi", "history": turns}).status_code == 422
    too_long = "x" * (api_module.MAX_TEXT_CHARS + 1)
    assert client.post("/chat", json={"message": too_long}).status_code == 422


def test_crm_import_row_caps(make_client, monkeypatch):
    client = make_client()
    monkeypatch.setattr(api_module, "MAX_CRM_ROWS_PER_IMPORT", 2)
    monkeypatch.setattr(api_module, "MAX_CRM_ROWS_TOTAL", 3)
    csv = "segment,name\na,1\nb,2\n"
    three = csv + "c,3\n"

    assert client.post("/crm/import", json={"data": three}).status_code == 413
    assert client.post("/crm/import", json={"data": csv}).status_code == 200
    assert client.post("/crm/import", json={"data": csv, "merge": True}).status_code == 413
    assert client.post("/crm/import", json={"data": csv, "merge": False}).status_code == 200


def test_limits_documented_in_openapi(make_client):
    description = make_client().get("/openapi.json").json()["info"]["description"]
    assert "413" in description and "429" in description


def test_rate_limiter_window_expires(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(limits.time, "monotonic", lambda: now[0])
    limiter = limits.RateLimiter(limit=2, window_seconds=60)

    limiter.check("c")
    limiter.check("c")
    with pytest.raises(HTTPException) as exc:
        limiter.check("c")
    assert exc.value.status_code == 429

    now[0] += 61
    limiter.check("c")


@pytest.mark.parametrize(("raw", "expected"), [("", 7), ("abc", 7), ("0", 7), ("-5", 7), ("42", 42)])
def test_env_int_falls_back_on_bad_values(monkeypatch, raw, expected):
    monkeypatch.setenv("X_LIMIT", raw)
    assert limits.env_int("X_LIMIT", 7) == expected
