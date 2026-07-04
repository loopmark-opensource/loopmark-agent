#!/usr/bin/env python3
"""
Marketing Agent — CLI entry point.

Usage:
    python main.py                  # interactive chat mode
    python main.py --help
"""

from __future__ import annotations

import sys
import os

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme
from langchain_core.messages import HumanMessage, AIMessage

# ─── Bootstrap ───────────────────────────────────────────────────────────────

# Ensure workspace root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from config import config

if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith("sk-..."):
    print("ERROR: Set OPENAI_API_KEY in your .env file (copy .env.example → .env).")
    sys.exit(1)

from agents.graph import get_marketing_graph

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

app = typer.Typer(add_completion=False, help="Marketing Agent CLI")


@app.command()
def chat(
    model: str = typer.Option(None, help="Override the OpenAI model (e.g. gpt-4o-mini)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show routing intent labels"),
):
    """Start an interactive marketing agent session."""
    if model:
        config.OPENAI_MODEL = model

    console.print(BANNER, style="bold blue")

    graph = get_marketing_graph()
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

        conversation_messages.append(HumanMessage(content=user_text))

        try:
            result = graph.invoke({"messages": conversation_messages})
        except Exception as exc:
            console.print(f"[error]Agent error:[/error] {exc}")
            continue

        # Update conversation history
        conversation_messages = result["messages"]

        # Extract the last AI message
        ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if not ai_messages:
            continue
        reply = ai_messages[-1].content

        intent = result.get("intent", "unknown")
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
