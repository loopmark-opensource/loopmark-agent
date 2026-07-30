"""Tests for the credentials abstraction."""

from __future__ import annotations

from credentials import get_credentials, set_credentials
from credentials.env_credentials import EnvCredentials


class _StubCredentials:
    def twitter(self):
        return {
            "TWITTER_API_KEY": "k",
            "TWITTER_API_SECRET": "s",
            "TWITTER_ACCESS_TOKEN": "t",
            "TWITTER_ACCESS_SECRET": "ts",
        }

    def linkedin(self):
        return None

    def buffer(self):
        return {"token": "buf"}


def test_env_credentials_twitter(monkeypatch):
    monkeypatch.setenv("TWITTER_API_KEY", "k")
    monkeypatch.setenv("TWITTER_API_SECRET", "s")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "t")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "ts")
    creds = EnvCredentials()
    assert creds.twitter() is not None
    assert creds.linkedin() is None


def test_env_credentials_partial_twitter_returns_none(monkeypatch):
    monkeypatch.delenv("TWITTER_API_KEY", raising=False)
    monkeypatch.setenv("TWITTER_API_SECRET", "s")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "t")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "ts")
    assert EnvCredentials().twitter() is None


def test_set_credentials_override():
    set_credentials(_StubCredentials())
    creds = get_credentials()
    assert creds.twitter() is not None
    assert creds.buffer() == {"token": "buf"}
    set_credentials(EnvCredentials())
