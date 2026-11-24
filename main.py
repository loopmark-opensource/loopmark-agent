#!/usr/bin/env python3
"""
Marketing Agent — CLI entry point.

Usage:
    loopmark-agent chat             # interactive chat (after pip install)
    loopmark-agent stats
    loopmark-agent approve POST-ID  # allow a saved post to be published live
    loopmark-agent serve            # REST API (needs `pip install loopmark-agent[api]`)
    python main.py chat             # from a local clone
"""

from __future__ import annotations

import os
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

# Allow running from a source checkout without installing the package.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from config import config

# ─── Rich theme ──────────────────────────────────────────────────────────────

theme = Theme({
    "user": "bold cyan",
    "agent": "bold green",
    "intent": "dim yellow",
    "error": "bold red",
    "info": "dim white",
})

console = Console(theme=theme)

BANNER = """
╔══════════════════════════════════════════════════════════╗
║          🚀  MARKETING AGENT  v1.0                       ║
║  Complaints · Content Posting · Funnel Management        ║
╚══════════════════════════════════════════════════════════╝
Type your request in plain English. Type 'exit' to quit.
"""

INTENT_LABELS = {
    "complaint": "🗣️  Complaints Agent",
    "posting": "📣  Posting Agent",
    "funnel": "📊  Funnel Agent",
    "unknown": "🤖  General",
}

# ─── CLI app ─────────────────────────────────────────────────────────────────

app = typer.Typer(
    add_completion=False,
    help="Loopmark Agent — open-source LangGraph marketing CLI",
    no_args_is_help=True,
)


def _require_api_key() -> None:
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith("sk-..."):
        console.print(
            "[error]ERROR:[/error] Set OPENAI_API_KEY in your .env file "
            "(copy .env.example → .env), or export it in your shell."
        )
        raise typer.Exit(code=1)


@app.command()
def chat(
    model: str = typer.Option(None, help="Override the OpenAI model (e.g. gpt-4o-mini)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show routing intent labels"),
):
    """Start an interactive marketing agent session."""
    _require_api_key()

    from core.run import run_agent

    console.print(BANNER, style="bold blue")

    conversation_messages: list = []

    while True:
        try:
            user_text = Prompt.ask("\n[user]You[/user]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[info]Goodbye![/info]")
            break

        user_text = user_text.strip()
        if not user_text:
            continue
        if user_text.lower() in ("exit", "quit", "bye"):
            console.print("[info]Goodbye![/info]")
            break

        try:
            result = run_agent(user_text, history=conversation_messages, model=model)
        except Exception as exc:
            console.print(f"[error]Agent error:[/error] {exc}")
            continue

        conversation_messages = result.messages
        reply = result.reply
        intent = result.intent
        label = INTENT_LABELS.get(intent, "🤖  Agent")

        if verbose:
            console.print(f"[intent]  ↳ Routed to: {label}[/intent]")

        console.print(
            Panel(
                Markdown(reply),
                title=f"[agent]{label}[/agent]",
                border_style="green",
                padding=(1, 2),
            )
        )


@app.command()
def stats():
    """Print a quick summary of complaints, posts, and funnel leads."""
    import json

    console.print("\n[bold]Marketing Agent — Quick Stats[/bold]\n")

    for label, path in [
        ("Complaints", config.COMPLAINTS_FILE),
        ("Posts", config.POSTS_FILE),
        ("Leads", config.LEADS_FILE),
    ]:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            console.print(f"  {label}: [bold]{len(data)}[/bold] records")
        else:
            console.print(f"  {label}: [dim]no data yet[/dim]")

    console.print()


def _data_dir_is_shared_writable() -> bool:
    """True when DATA_DIR exists and other users could plant or replace data files (POSIX only)."""
    if os.name != "posix" or not os.path.isdir(config.DATA_DIR):
        return False
    return bool(os.stat(config.DATA_DIR).st_mode & 0o022)


@app.command()
def approve(
    post_id: str = typer.Argument(..., help="Saved post ID, e.g. POST-1a2b..."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt"),
):
    """Approve a saved post for live publishing (the agent cannot do this itself)."""
    from rich.prompt import Confirm

    from tools.publish_guard import approve_post, find_post, live_publish_enabled

    post = find_post(post_id)
    if not post:
        console.print(f"[error]ERROR:[/error] No saved post with ID {post_id}.")
        raise typer.Exit(code=1)

    console.print(
        Panel(post.get("content", ""), title=f"{post.get('platform', '?')} · {post_id}", border_style="yellow")
    )
    if not yes and not Confirm.ask("Approve this exact text for live publishing?", default=False):
        console.print("[info]Not approved.[/info]")
        raise typer.Exit(code=1)

    approve_post(post_id)
    console.print(f"[agent]Approved {post_id}.[/agent] Editing the text later requires approving again.")
    if not live_publish_enabled():
        console.print("[info]Live publishing is still off: set LOOPMARK_ALLOW_LIVE_PUBLISH=true in .env.[/info]")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind address. Set LOOPMARK_API_KEY before exposing beyond localhost."),
    port: int = typer.Option(8000, help="Port to listen on"),
):
    """Run the REST API (OpenAPI docs at /docs)."""
    if host not in ("127.0.0.1", "localhost") and not os.getenv("LOOPMARK_API_KEY"):
        console.print("[error]ERROR:[/error] Set LOOPMARK_API_KEY before binding to a non-local address.")
        raise typer.Exit(code=1)

    if os.getenv("LOOPMARK_API_KEY") and _data_dir_is_shared_writable():
        console.print(
            f"[error]ERROR:[/error] DATA_DIR {config.DATA_DIR} is group/world-writable and holds PII. "
            f"Run: chmod 700 {config.DATA_DIR}"
        )
        raise typer.Exit(code=1)

    try:
        import uvicorn
    except ImportError:
        console.print("[error]ERROR:[/error] Install the API extra: pip install 'loopmark-agent[api]'")
        raise typer.Exit(code=1)

    uvicorn.run("api.app:app", host=host, port=port)


if __name__ == "__main__":
    app()
