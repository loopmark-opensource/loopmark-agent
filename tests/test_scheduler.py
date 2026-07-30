"""Tests for scheduler queue and integration helpers."""

from __future__ import annotations

from datetime import date

from tools.social_tools import save_post

import scheduler


def test_queue_summary_counts_scheduled_and_due():
    save_post.invoke(
        {
            "platform": "twitter",
            "content": "Due today",
            "scheduled_date": date.today().isoformat(),
        }
    )
    save_post.invoke(
        {
            "platform": "linkedin",
            "content": "Future post",
            "scheduled_date": "2099-01-01",
        }
    )
    summary = scheduler._queue_summary()
    assert "2 scheduled" in summary
    assert "1 due now" in summary


def test_integration_status_reports_missing_by_default(monkeypatch):
    for key in (
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET",
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_PERSON_ID",
        "BUFFER_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)
    status = scheduler._integration_status()
    assert "missing" in status
