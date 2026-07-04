import json
from datetime import date

from config import config
from tools.publisher_tools import (
    post_to_twitter,
    post_to_linkedin,
    schedule_via_buffer,
    get_buffer_profiles,
    publish_scheduled_posts,
    get_posting_status,
)
from tools.social_tools import save_post


def test_post_to_twitter_missing_credentials(monkeypatch):
    monkeypatch.delenv("TWITTER_API_KEY", raising=False)
    monkeypatch.delenv("TWITTER_API_SECRET", raising=False)
    monkeypatch.delenv("TWITTER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TWITTER_ACCESS_SECRET", raising=False)

    result = post_to_twitter.invoke({"content": "Hello world"})
    assert "Twitter credentials not set" in result


def test_post_to_twitter_too_long(monkeypatch):
    monkeypatch.setenv("TWITTER_API_KEY", "key")
    monkeypatch.setenv("TWITTER_API_SECRET", "secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "token-secret")

    result = post_to_twitter.invoke({"content": "x" * 281})
    assert "280 characters" in result


def test_post_to_linkedin_missing_credentials(monkeypatch):
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINKEDIN_PERSON_ID", raising=False)

    result = post_to_linkedin.invoke({"content": "Hello LinkedIn"})
    assert "LinkedIn credentials not set" in result


def test_schedule_via_buffer_missing_credentials(monkeypatch):
    monkeypatch.delenv("BUFFER_ACCESS_TOKEN", raising=False)

    result = schedule_via_buffer.invoke(
        {"content": "Scheduled post", "platform_profile_id": "12345"}
    )
    assert "Buffer credentials not set" in result


def test_get_buffer_profiles_missing_credentials(monkeypatch):
    monkeypatch.delenv("BUFFER_ACCESS_TOKEN", raising=False)

    result = get_buffer_profiles.invoke({})
    assert "BUFFER_ACCESS_TOKEN not set" in result


def test_publish_scheduled_posts_dry_run():
    save_post.invoke(
        {
            "platform": "twitter",
            "content": "Due post",
            "scheduled_date": date.today().isoformat(),
        }
    )

    # Mark as scheduled (save_post sets scheduled when date provided)
    with open(config.POSTS_FILE) as f:
        posts = json.load(f)
    posts[0]["status"] = "scheduled"
    with open(config.POSTS_FILE, "w") as f:
        json.dump(posts, f)

    result = publish_scheduled_posts.invoke({"dry_run": True})
    assert "DRY RUN" in result
    assert "Due post" in result


def test_publish_scheduled_posts_none_due():
    result = publish_scheduled_posts.invoke({"dry_run": False})
    assert "No posts due" in result


def test_get_posting_status_empty():
    result = get_posting_status.invoke({})
    assert "No posts in the library" in result


def test_get_posting_status_with_posts():
    save_post.invoke({"platform": "twitter", "content": "Draft post"})
    result = get_posting_status.invoke({})
    assert "Total: 1" in result
