"""Live publishing needs the kill-switch on and a human approval (issue #69)."""

from __future__ import annotations

import httpx
import pytest
from typer.testing import CliRunner

from storage import get_storage
from tools import publish_guard, publisher_tools
from tools.publisher_tools import post_to_linkedin, post_to_twitter, publish_scheduled_posts, schedule_via_buffer


@pytest.fixture
def creds(monkeypatch):
    for key, value in {
        "TWITTER_API_KEY": "k", "TWITTER_API_SECRET": "s", "TWITTER_ACCESS_TOKEN": "t",
        "TWITTER_ACCESS_SECRET": "ts", "LINKEDIN_ACCESS_TOKEN": "li", "LINKEDIN_PERSON_ID": "123",
        "BUFFER_ACCESS_TOKEN": "buf",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def http(monkeypatch):
    """Record outgoing posts; any call here means something was published."""
    sent = []

    def fake_post(url, **kwargs):
        sent.append(url)
        body = {"data": {"id": "1"}} if "twitter" in url else {"success": True, "updates": [{"id": "u1"}]}
        return httpx.Response(201, json=body, headers={"x-restli-id": "urn:li:share:1"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(publisher_tools.httpx, "post", fake_post)
    return sent


@pytest.fixture
def human(monkeypatch):
    answers = {"value": False, "asked": 0}

    def ask(platform, content):
        answers["asked"] += 1
        return answers["value"]

    monkeypatch.setattr(publish_guard, "_ask_human", ask)
    return answers


def _save(content="Launch day!", platform="twitter", status="draft", **extra):
    post = {"id": f"POST-{abs(hash(content))}", "platform": platform, "content": content, "status": status, **extra}
    storage = get_storage()
    storage.save_posts(storage.load_posts() + [post])
    return post


def _publish(tool, content, post_id=""):
    args = {"content": content, "post_id": post_id}
    if tool is schedule_via_buffer:
        args["platform_profile_id"] = "p1"
    return tool.invoke(args)


@pytest.mark.parametrize("tool", [post_to_twitter, post_to_linkedin, schedule_via_buffer])
def test_kill_switch_off_blocks_every_live_tool(tool, creds, http, human, monkeypatch):
    monkeypatch.delenv(publish_guard.ALLOW_ENV, raising=False)
    human["value"] = True

    result = _publish(tool, "Hello")
    assert "Live publishing is disabled" in result
    assert http == [] and human["asked"] == 0


@pytest.mark.parametrize("tool", [post_to_twitter, post_to_linkedin, schedule_via_buffer])
def test_enabled_but_unapproved_and_human_declines_blocks(tool, creds, http, human, monkeypatch):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")

    result = _publish(tool, "Hello")
    assert "a human must approve" in result
    assert http == [] and human["asked"] == 1


@pytest.mark.parametrize("tool", [post_to_twitter, post_to_linkedin, schedule_via_buffer])
def test_enabled_and_human_confirms_publishes(tool, creds, http, human, monkeypatch):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")
    human["value"] = True

    _publish(tool, "Hello")
    assert len(http) == 1


def test_prior_approval_publishes_without_prompt(creds, http, human, monkeypatch):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")
    post = _save("Approved tweet")
    publish_guard.approve_post(post["id"])

    post_to_twitter.invoke({"content": "Approved tweet", "post_id": post["id"]})
    assert len(http) == 1 and human["asked"] == 0


def test_approval_does_not_cover_changed_content(creds, http, human, monkeypatch):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")
    post = _save("Original text")
    publish_guard.approve_post(post["id"])

    result = post_to_twitter.invoke({"content": "Injected text", "post_id": post["id"]})
    assert "a human must approve" in result
    assert http == []


def test_no_prompt_without_terminal_or_when_disabled(monkeypatch):
    monkeypatch.setattr(publish_guard.sys.stdin, "isatty", lambda: False, raising=False)
    assert publish_guard._ask_human("Twitter", "x") is False


def test_api_app_disables_prompts(monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setattr(publish_guard, "_prompts_enabled", True)
    from api.app import create_app

    create_app()
    assert publish_guard._prompts_enabled is False


def test_scheduler_skips_unapproved_and_publishes_approved(creds, http, human, monkeypatch):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")
    pending = _save("Needs approval", status="scheduled", scheduled_date="2020-01-01")
    approved = _save("Good to go", status="scheduled", scheduled_date="2020-01-01")
    publish_guard.approve_post(approved["id"])

    result = publish_scheduled_posts.invoke({"dry_run": False})
    assert f"awaiting approval (`loopmark-agent approve {pending['id']}`)" in result
    assert len(http) == 1 and human["asked"] == 0
    statuses = {p["id"]: p["status"] for p in get_storage().load_posts()}
    assert statuses == {pending["id"]: "scheduled", approved["id"]: "published"}


def test_publish_attempts_are_logged_with_content_hash(creds, http, human, monkeypatch, caplog):
    monkeypatch.setenv(publish_guard.ALLOW_ENV, "true")
    human["value"] = True
    caplog.set_level("INFO", logger="loopmark.publish")

    post_to_twitter.invoke({"content": "Logged"})
    assert publish_guard.content_hash("Logged") in caplog.text
    assert "Publishing to Twitter" in caplog.text


def test_approve_cli_records_hash(monkeypatch):
    from main import app

    post = _save("CLI approved")
    result = CliRunner().invoke(app, ["approve", post["id"], "--yes"])
    assert result.exit_code == 0, result.output
    assert publish_guard.is_approved(post["id"], "CLI approved")

    missing = CliRunner().invoke(app, ["approve", "POST-nope", "--yes"])
    assert missing.exit_code == 1
