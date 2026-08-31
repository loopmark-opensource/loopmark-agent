"""
Publisher tools — real automatic posting to social platforms.

Supported channels:
  - Twitter/X      via Tweepy (OAuth 1.0a)
  - LinkedIn       via LinkedIn REST API v2
  - Buffer         via Buffer API v1  (schedules to Twitter, LinkedIn,
                   Instagram, Facebook from one place)

All credentials are read via `credentials.get_credentials()` (default: `.env` BYOK).
Each tool degrades gracefully: if credentials are missing it returns
a clear error rather than crashing the agent.
"""

from __future__ import annotations

import os
from datetime import datetime

import httpx
from langchain_core.tools import tool

from credentials import get_credentials
from storage import get_storage


def _twitter_creds() -> dict | None:
    return get_credentials().twitter()


def _linkedin_creds() -> dict | None:
    return get_credentials().linkedin()


def _buffer_creds() -> dict | None:
    return get_credentials().buffer()


# ─── post-status tracking ──────────────────────────────────────────────────

def _load_posts() -> list[dict]:
    return get_storage().load_posts()


def _save_posts(data: list[dict]) -> None:
    get_storage().save_posts(data)


def _mark_published(post_id: str, platform_post_id: str = "", error: str = "") -> None:
    posts = _load_posts()
    for p in posts:
        if p["id"] == post_id:
            p["status"] = "failed" if error else "published"
            p["published_at"] = datetime.utcnow().isoformat()
            if platform_post_id:
                p["platform_post_id"] = platform_post_id
            if error:
                p["error"] = error
    _save_posts(posts)


# ─── tools ─────────────────────────────────────────────────────────────────

@tool
def post_to_twitter(content: str, post_id: str = "") -> str:
    """
    Publish a tweet via the Twitter/X API v2.

    Requires these env vars: TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET.

    Args:
        content: Tweet text (max 280 characters).
        post_id: Optional saved post ID to mark as published.

    Returns:
        Success message with tweet URL, or error details.
    """
    creds = _twitter_creds()
    if not creds:
        return (
            "Twitter credentials not set. Add to .env:\n"
            "  TWITTER_API_KEY=...\n"
            "  TWITTER_API_SECRET=...\n"
            "  TWITTER_ACCESS_TOKEN=...\n"
            "  TWITTER_ACCESS_SECRET=..."
        )

    if len(content) > 280:
        return f"Tweet exceeds 280 characters ({len(content)}). Please shorten it."

    try:
        import tweepy  # type: ignore

        client = tweepy.Client(
            consumer_key=creds["TWITTER_API_KEY"],
            consumer_secret=creds["TWITTER_API_SECRET"],
            access_token=creds["TWITTER_ACCESS_TOKEN"],
            access_token_secret=creds["TWITTER_ACCESS_SECRET"],
        )
        response = client.create_tweet(text=content)
        tweet_id = response.data["id"]
        tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"

        if post_id:
            _mark_published(post_id, platform_post_id=tweet_id)

        return f"Tweet published successfully!\nURL: {tweet_url}\nTweet ID: {tweet_id}"

    except ImportError:
        return "tweepy not installed. Run: pip install tweepy"
    except Exception as e:
        if post_id:
            _mark_published(post_id, error=str(e))
        return f"Twitter posting failed: {e}"


@tool
def post_to_linkedin(content: str, post_id: str = "") -> str:
    """
    Publish a post to LinkedIn via the LinkedIn REST API v2.

    Requires these env vars: LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_ID.
    Get your Person ID by calling: GET https://api.linkedin.com/v2/me

    Args:
        content: Post text (max 3,000 characters).
        post_id: Optional saved post ID to mark as published.

    Returns:
        Success message with post URN, or error details.
    """
    creds = _linkedin_creds()
    if not creds:
        return (
            "LinkedIn credentials not set. Add to .env:\n"
            "  LINKEDIN_ACCESS_TOKEN=...   (OAuth 2.0 token)\n"
            "  LINKEDIN_PERSON_ID=...      (your LinkedIn member ID, e.g. 'urn:li:person:XXXXXXX')"
        )

    if len(content) > 3000:
        return f"LinkedIn post exceeds 3,000 characters ({len(content)}). Please shorten it."

    person_urn = creds["person_id"]
    if not person_urn.startswith("urn:li:person:"):
        person_urn = f"urn:li:person:{person_urn}"

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        resp = httpx.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {creds['token']}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        post_urn = resp.headers.get("x-restli-id", "unknown")

        if post_id:
            _mark_published(post_id, platform_post_id=post_urn)

        return f"LinkedIn post published!\nPost URN: {post_urn}"

    except httpx.HTTPStatusError as e:
        err = f"LinkedIn API error {e.response.status_code}: {e.response.text}"
        if post_id:
            _mark_published(post_id, error=err)
        return err
    except Exception as e:
        if post_id:
            _mark_published(post_id, error=str(e))
        return f"LinkedIn posting failed: {e}"


@tool
def schedule_via_buffer(
    content: str,
    platform_profile_id: str,
    scheduled_at: str = "",
    post_id: str = "",
) -> str:
    """
    Schedule a post via Buffer (supports Twitter, LinkedIn, Instagram, Facebook).

    Buffer handles one API → posts to all your connected platforms.
    Get your profile IDs from: GET https://api.bufferapp.com/1/profiles.json

    Requires env var: BUFFER_ACCESS_TOKEN

    Args:
        content: Post text.
        platform_profile_id: Buffer profile ID for the target channel.
        scheduled_at: ISO datetime string to schedule (e.g. '2026-07-10T09:00:00').
                      Leave empty to add to the next available slot in your Buffer queue.
        post_id: Optional saved post ID to mark as scheduled.

    Returns:
        Success message with Buffer update ID, or error details.
    """
    creds = _buffer_creds()
    if not creds:
        return (
            "Buffer credentials not set. Add to .env:\n"
            "  BUFFER_ACCESS_TOKEN=...   (get from buffer.com/developers)\n\n"
            "Buffer lets you post to Twitter, LinkedIn, Instagram, and Facebook\n"
            "from a single API. Get profile IDs with the 'get_buffer_profiles' tool."
        )

    payload: dict = {
        "text": content,
        "profile_ids[]": platform_profile_id,
    }
    if scheduled_at:
        try:
            dt = datetime.fromisoformat(scheduled_at)
            payload["scheduled_at"] = dt.isoformat() + "Z"
            payload["now"] = "false"
        except ValueError:
            return f"Invalid scheduled_at format. Use ISO 8601, e.g. '2026-07-10T09:00:00'."
    else:
        payload["now"] = "false"  # adds to queue

    try:
        resp = httpx.post(
            "https://api.bufferapp.com/1/updates/create.json",
            headers={"Authorization": f"Bearer {creds['token']}"},
            data=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        update_id = data.get("updates", [{}])[0].get("id", "unknown")
        status = data.get("updates", [{}])[0].get("status", "buffer")

        if post_id:
            _mark_published(post_id, platform_post_id=update_id)

        scheduled_info = f" at {scheduled_at}" if scheduled_at else " (added to queue)"
        return f"Post scheduled via Buffer{scheduled_info}.\nBuffer Update ID: {update_id}  |  Status: {status}"

    except httpx.HTTPStatusError as e:
        err = f"Buffer API error {e.response.status_code}: {e.response.text}"
        if post_id:
            _mark_published(post_id, error=err)
        return err
    except Exception as e:
        if post_id:
            _mark_published(post_id, error=str(e))
        return f"Buffer posting failed: {e}"


@tool
def get_buffer_profiles() -> str:
    """
    List all social media profiles connected to your Buffer account.
    Use the returned profile IDs with the 'schedule_via_buffer' tool.

    Requires env var: BUFFER_ACCESS_TOKEN

    Returns:
        A list of connected profiles with their IDs and platform names.
    """
    creds = _buffer_creds()
    if not creds:
        return "BUFFER_ACCESS_TOKEN not set in .env."

    try:
        resp = httpx.get(
            "https://api.bufferapp.com/1/profiles.json",
            headers={"Authorization": f"Bearer {creds['token']}"},
            timeout=15,
        )
        resp.raise_for_status()
        profiles = resp.json()

        if not profiles:
            return "No profiles connected to your Buffer account."

        lines = ["Buffer connected profiles:", ""]
        for p in profiles:
            lines.append(
                f"  ID: {p.get('id')}  |  "
                f"Platform: {p.get('service', 'unknown').upper()}  |  "
                f"Handle: @{p.get('service_username', 'unknown')}"
            )
        lines.append("\nUse these IDs with the 'schedule_via_buffer' tool.")
        return "\n".join(lines)

    except Exception as e:
        return f"Failed to fetch Buffer profiles: {e}"


@tool
def publish_scheduled_posts(dry_run: bool = False) -> str:
    """
    Scan the posts queue and publish any posts whose scheduled_date is today or past.

    This tool is called automatically by the scheduler, but can also be
    triggered manually.

    Args:
        dry_run: If True, only report what would be published without actually posting.

    Returns:
        A summary of posts published (or that would be published in dry-run mode).
    """
    posts = _load_posts()
    today = datetime.utcnow().date()

    due = [
        p for p in posts
        if p.get("status") == "scheduled"
        and p.get("scheduled_date")
        and datetime.fromisoformat(p["scheduled_date"]).date() <= today
    ]

    if not due:
        return "No posts due for publishing today."

    lines = [f"{'[DRY RUN] ' if dry_run else ''}Posts due for publishing: {len(due)}", ""]

    for p in due:
        platform = p.get("platform", "unknown")
        lines.append(f"  [{p['id']}] {platform.upper()} — {p['content'][:60]}...")

        if not dry_run:
            if platform == "twitter":
                result = post_to_twitter.invoke({"content": p["content"], "post_id": p["id"]})
            elif platform == "linkedin":
                result = post_to_linkedin.invoke({"content": p["content"], "post_id": p["id"]})
            else:
                result = f"Platform '{platform}' not wired for auto-posting. Use Buffer."
                _mark_published(p["id"], error=result)
            lines.append(f"    → {result}")

    return "\n".join(lines)


@tool
def get_posting_status() -> str:
    """
    Show a summary of all posts by status: draft, scheduled, published, failed.

    Returns:
        A formatted status report.
    """
    posts = _load_posts()
    if not posts:
        return "No posts in the library yet."

    counts: dict[str, int] = {}
    for p in posts:
        s = p.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    lines = ["Post Library Status", "=" * 40]
    for status, count in sorted(counts.items()):
        emoji = {"draft": "📝", "scheduled": "🕐", "published": "✅", "failed": "❌"}.get(status, "•")
        lines.append(f"  {emoji} {status.capitalize():<12} {count}")
    lines.append(f"\n  Total: {len(posts)}")
    return "\n".join(lines)


PUBLISHER_TOOLS = [
    post_to_twitter,
    post_to_linkedin,
    schedule_via_buffer,
    get_buffer_profiles,
    publish_scheduled_posts,
    get_posting_status,
]
