"""
Tools for the Content / Posting Agent.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from langchain_core.tools import tool

from models.schemas import GeneratedPost, Platform
from storage import get_storage


# ─── helpers ───────────────────────────────────────────────────────────────

_PLATFORM_LIMITS = {
    Platform.TWITTER: 280,
    Platform.LINKEDIN: 3000,
    Platform.INSTAGRAM: 2200,
    Platform.FACEBOOK: 63206,
    Platform.BLOG: 10000,
    Platform.EMAIL: 5000,
}

_BEST_TIMES = {
    Platform.TWITTER: "Tuesday–Thursday, 9 AM or 3 PM",
    Platform.LINKEDIN: "Tuesday–Thursday, 8–10 AM",
    Platform.INSTAGRAM: "Monday–Friday, 11 AM–1 PM",
    Platform.FACEBOOK: "Wednesday, 11 AM–1 PM",
    Platform.BLOG: "Monday or Thursday morning",
    Platform.EMAIL: "Tuesday or Thursday, 10 AM",
}


def _load_posts() -> list[dict]:
    return get_storage().load_posts()


def _save_posts(data: list[dict]) -> None:
    get_storage().save_posts(data)


# ─── tools ─────────────────────────────────────────────────────────────────

@tool
def get_platform_guidelines(platform: str) -> str:
    """
    Return character limits, best practices, and optimal posting times for a
    social media platform.

    Args:
        platform: One of twitter, linkedin, instagram, facebook, blog, email.

    Returns:
        Formatted guidelines string.
    """
    try:
        p = Platform(platform.lower())
    except ValueError:
        return f"Unknown platform '{platform}'. Supported: twitter, linkedin, instagram, facebook, blog, email."

    limit = _PLATFORM_LIMITS[p]
    best_time = _BEST_TIMES[p]

    tips = {
        Platform.TWITTER: "Use 1-3 hashtags max. Threads get more reach. Media boosts engagement ~150%.",
        Platform.LINKEDIN: "Lead with a hook sentence. Use line breaks. Avoid external links in the post body.",
        Platform.INSTAGRAM: "First 125 chars must hook — rest is truncated. Use 5-15 hashtags in comments.",
        Platform.FACEBOOK: "Video performs best. Keep text under 80 chars for full display. Ask questions.",
        Platform.BLOG: "Target 1,500–2,500 words for SEO. Use H2/H3 headers. Include internal links.",
        Platform.EMAIL: "Subject line ≤50 chars. Personalise the greeting. Single, clear CTA.",
    }

    return (
        f"Platform: {p.value.upper()}\n"
        f"Character limit: {limit}\n"
        f"Best posting time: {best_time}\n"
        f"Tips: {tips[p]}"
    )


@tool
def save_post(
    platform: str,
    content: str,
    hashtags: str = "",
    scheduled_date: str = "",
) -> str:
    """
    Save a generated post to the content library.

    Args:
        platform: Target platform (twitter, linkedin, instagram, facebook, blog, email).
        content: The post text.
        hashtags: Comma-separated hashtags (without #).
        scheduled_date: ISO date string for scheduling (e.g. 2026-07-10).

    Returns:
        Confirmation with post ID.
    """
    post = {
        "id": f"POST-{int(datetime.utcnow().timestamp())}",
        "platform": platform,
        "content": content,
        "hashtags": [h.strip() for h in hashtags.split(",") if h.strip()],
        "character_count": len(content),
        "scheduled_date": scheduled_date or datetime.utcnow().date().isoformat(),
        "status": "scheduled" if scheduled_date else "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    posts = _load_posts()
    posts.append(post)
    _save_posts(posts)
    return f"Post saved. ID: {post['id']}  |  Status: {post['status']}"


@tool
def list_posts(platform: str = "all", status: str = "all", limit: int = 10) -> str:
    """
    List saved posts from the content library.

    Args:
        platform: Filter by platform or 'all'.
        status: Filter by status ('draft', 'scheduled', 'published') or 'all'.
        limit: Maximum number of posts to return.

    Returns:
        A formatted list of posts.
    """
    posts = _load_posts()

    if platform != "all":
        posts = [p for p in posts if p.get("platform") == platform.lower()]
    if status != "all":
        posts = [p for p in posts if p.get("status") == status.lower()]

    posts = posts[:limit]
    if not posts:
        return "No posts found matching the criteria."

    lines = []
    for p in posts:
        tags = " ".join(f"#{t}" for t in p.get("hashtags", []))
        lines.append(
            f"[{p['id']}] [{p['platform'].upper()}] [{p['status']}] "
            f"{p['content'][:60]}... | {tags}"
        )
    return "\n".join(lines)


@tool
def generate_content_calendar(
    topics: str,
    platforms: str,
    weeks: int = 2,
) -> str:
    """
    Generate a content calendar outline for the specified topics and platforms.

    Args:
        topics: Comma-separated list of content topics.
        platforms: Comma-separated list of platforms (twitter, linkedin, etc.).
        weeks: Number of weeks to plan (1–4).

    Returns:
        A formatted content calendar table.
    """
    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    weeks = max(1, min(4, weeks))

    today = datetime.utcnow().date()
    calendar: list[str] = ["Content Calendar", "=" * 60]

    posting_days = [0, 2, 4]  # Mon, Wed, Fri
    entry_idx = 0

    for week in range(weeks):
        calendar.append(f"\nWeek {week + 1}")
        calendar.append("-" * 40)
        for day_offset in posting_days:
            post_date = today + timedelta(days=week * 7 + day_offset)
            platform = platform_list[entry_idx % len(platform_list)]
            topic = topic_list[entry_idx % len(topic_list)]
            calendar.append(f"  {post_date}  [{platform.upper()}]  Topic: {topic}")
            entry_idx += 1

    calendar.append("\nUse the 'save_post' tool to draft content for each entry.")
    return "\n".join(calendar)


@tool
def get_hashtag_suggestions(topic: str, platform: str = "twitter") -> str:
    """
    Return hashtag suggestions for a topic on a given platform.

    Args:
        topic: The content topic or niche.
        platform: Target platform.

    Returns:
        Suggested hashtags grouped by type.
    """
    topic_lower = topic.lower()

    # Simple keyword-based suggestions — the LLM can augment these
    base_tags = [topic_lower.replace(" ", ""), "marketing", "digitalmarketing", "growth"]
    niche_tags: list[str] = []

    if any(k in topic_lower for k in ["product", "launch", "new"]):
        niche_tags += ["productlaunch", "newproduct", "innovation"]
    if any(k in topic_lower for k in ["sale", "discount", "offer", "promo"]):
        niche_tags += ["sale", "deal", "limitedoffer", "promo"]
    if any(k in topic_lower for k in ["content", "blog", "article"]):
        niche_tags += ["contentmarketing", "blogging", "seo"]
    if any(k in topic_lower for k in ["social", "media", "post"]):
        niche_tags += ["socialmedia", "smm", "socialmediamarketing"]

    platform_tags = {
        "twitter": ["trending", "viral"],
        "linkedin": ["b2b", "thoughtleadership", "leadership"],
        "instagram": ["instagood", "reels", "explore"],
        "facebook": ["community", "engagement"],
    }

    extra = platform_tags.get(platform.lower(), [])

    all_tags = list(dict.fromkeys(base_tags + niche_tags + extra))
    formatted = "  ".join(f"#{t}" for t in all_tags)

    limit_note = "(Instagram: add in comments, Twitter: use max 2-3)" if platform in ("instagram", "twitter") else ""
    return f"Suggested hashtags for '{topic}' on {platform.upper()}:\n{formatted}\n{limit_note}"


POSTING_TOOLS = [
    get_platform_guidelines,
    save_post,
    list_posts,
    generate_content_calendar,
    get_hashtag_suggestions,
]
