#!/usr/bin/env python3
"""
Marketing Agent — CLI entry point.

Usage:
    loopmark-agent chat             # interactive chat (after pip install)
    loopmark-agent stats
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

    if model:
        config.OPENAI_MODEL = model

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


if __name__ == "__main__":
    app()
