import json
from datetime import date

import httpx

from config import config
from tools import publisher_tools
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


def test_oauth1_signature_matches_twitter_reference_example():
    # Worked example from Twitter's "Creating a signature" docs.
    params = {
        "status": "Hello Ladies + Gentlemen, a signed OAuth request!",
        "include_entities": "true",
        "oauth_consumer_key": "xvz1evFS4wEEPTGEFPHBog",
        "oauth_nonce": "kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg",
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": "1318622958",
        "oauth_token": "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
        "oauth_version": "1.0",
    }
    signature = publisher_tools._oauth1_signature(
        "POST",
        "https://api.twitter.com/1.1/statuses/update.json",
        params,
        "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
        "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE",
    )
    assert signature == "hCtSmYh+iHYCEqBWrE7C7hYmtUk="


def test_post_to_twitter_sends_signed_request(monkeypatch):
    monkeypatch.setenv("TWITTER_API_KEY", "key")
    monkeypatch.setenv("TWITTER_API_SECRET", "secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "token-secret")
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json)
        return httpx.Response(
            201, json={"data": {"id": "123", "text": json["text"]}}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(publisher_tools.httpx, "post", fake_post)

    result = post_to_twitter.invoke({"content": "Hello world"})
    assert "Tweet ID: 123" in result
    assert captured["url"] == publisher_tools.TWITTER_TWEETS_URL
    assert captured["json"] == {"text": "Hello world"}
    auth = captured["headers"]["Authorization"]
    assert auth.startswith("OAuth ")
    assert 'oauth_consumer_key="key"' in auth and 'oauth_token="token"' in auth
    assert "oauth_signature=" in auth


def test_post_to_twitter_api_error(monkeypatch):
    monkeypatch.setenv("TWITTER_API_KEY", "key")
    monkeypatch.setenv("TWITTER_API_SECRET", "secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "token-secret")
    monkeypatch.setattr(
        publisher_tools.httpx,
        "post",
        lambda url, **kw: httpx.Response(401, text="Unauthorized", request=httpx.Request("POST", url)),
    )

    result = post_to_twitter.invoke({"content": "Hello world"})
    assert result == "Twitter API error 401: Unauthorized"


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
