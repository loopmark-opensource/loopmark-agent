"""
Human gate for live social publishing (issue #69).

The agent can draft and schedule freely, but nothing reaches a real account unless:

1. the operator enabled live publishing with LOOPMARK_ALLOW_LIVE_PUBLISH=true, and
2. a human confirmed this exact content, either beforehand with
   `loopmark-agent approve POST-ID` (stored as a content hash on the post) or by
   answering a y/N prompt in an interactive terminal.

A tool argument like `confirm=True` would not be a gate: the model can set it itself.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import threading

from storage import get_storage

ALLOW_ENV = "LOOPMARK_ALLOW_LIVE_PUBLISH"

log = logging.getLogger("loopmark.publish")
_prompt_lock = threading.Lock()
_prompts_enabled = True


def disable_prompts() -> None:
    """For server processes: never block a request on a terminal prompt; require prior approval."""
    global _prompts_enabled
    _prompts_enabled = False


def live_publish_enabled() -> bool:
    return os.getenv(ALLOW_ENV, "").strip().lower() in ("1", "true", "yes")


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_post(post_id: str) -> dict | None:
    return next((p for p in get_storage().load_posts() if p.get("id") == post_id), None)


def is_approved(post_id: str, content: str) -> bool:
    """True when a human approved this post ID with exactly this content."""
    post = find_post(post_id) if post_id else None
    return bool(post and post.get("approved_content_sha256") == content_hash(content))


def approve_post(post_id: str) -> dict:
    """Record human approval of a saved post's current content. Raises KeyError if missing."""
    storage = get_storage()
    posts = storage.load_posts()
    for post in posts:
        if post.get("id") == post_id:
            from utils.clock import utcnow

            post["approved_content_sha256"] = content_hash(post.get("content", ""))
            post["approved_at"] = utcnow().isoformat()
            storage.save_posts(posts)
            return post
    raise KeyError(post_id)


def _ask_human(platform: str, content: str) -> bool:
    """Ask on the controlling terminal; never possible for the API server or cron."""
    if not _prompts_enabled or not sys.stdin.isatty():
        return False
    from rich.console import Console
    from rich.prompt import Confirm

    with _prompt_lock:
        console = Console()
        console.print(f"\n[bold yellow]Publish to {platform}?[/bold yellow]\n{content}\n")
        return Confirm.ask("Post this now to your real account?", default=False)


def check_live_publish(platform: str, content: str, post_id: str = "", *, interactive: bool = True) -> str | None:
    """
    Return None if publishing may proceed, otherwise a message explaining why nothing was sent.
    """
    digest = content_hash(content)
    if not live_publish_enabled():
        log.info("Blocked %s publish (kill-switch off), post=%s sha256=%s", platform, post_id or "-", digest)
        return (
            f"Live publishing is disabled, so nothing was posted to {platform}. "
            f"To enable it, set {ALLOW_ENV}=true in .env. The draft is still saved locally."
        )

    if not is_approved(post_id, content) and not (interactive and _ask_human(platform, content)):
        log.info("Blocked %s publish (no human approval), post=%s sha256=%s", platform, post_id or "-", digest)
        how = f"`loopmark-agent approve {post_id}`" if post_id else "save it with save_post, then `loopmark-agent approve <post_id>`"
        return (
            f"Not posted to {platform}: a human must approve this exact content first. "
            f"Ask the user to run {how} in their terminal, then try again."
        )

    log.warning("Publishing to %s, post=%s sha256=%s", platform, post_id or "-", digest)
    return None
