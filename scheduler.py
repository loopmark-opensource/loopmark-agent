#!/usr/bin/env python3
"""
Auto-posting scheduler.

Runs as a background daemon that checks the posts queue every N minutes
and publishes anything whose scheduled_date has arrived.

Usage:
    python scheduler.py                  # runs every 30 minutes (default)
    python scheduler.py --interval 60    # runs every 60 minutes
    python scheduler.py --once           # run once and exit (useful for cron)
    python scheduler.py --dry-run        # check what's due without posting

Cron alternative (post once an hour):
    0 * * * * cd /path/to/marketing-agent && .venv/bin/python scheduler.py --once
"""

from __future__ import annotations

import sys
import os
import time
import signal

import typer
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(__file__))

from config import config

if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith("sk-..."):
    print("ERROR: Set OPENAI_API_KEY in your .env file.")
    sys.exit(1)

from tools.publisher_tools import publish_scheduled_posts

console = Console()
app = typer.Typer(add_completion=False, help="Marketing Agent — Auto-posting Scheduler")

_running = True


def _handle_signal(sig, frame):
    global _running
    console.print("\n[yellow]Scheduler stopping...[/yellow]")
    _running = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def _run_once(dry_run: bool = False) -> None:
    now = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    console.print(f"\n[dim]Checking queue at {now}...[/dim]")
    try:
        result = publish_scheduled_posts.invoke({"dry_run": dry_run})
        console.print(
            Panel(
                result,
                title="[green]Scheduler[/green]" if not dry_run else "[yellow]Dry Run[/yellow]",
                border_style="green" if not dry_run else "yellow",
            )
        )
    except Exception as exc:
        console.print(f"[red]Scheduler error:[/red] {exc}")


@app.command()
def run(
    interval: int = typer.Option(30, help="How often to check the queue, in minutes."),
    once: bool = typer.Option(False, "--once", help="Run once and exit (for cron use)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Report due posts without publishing."),
):
    """Start the auto-posting scheduler."""
    if once:
        _run_once(dry_run=dry_run)
        return

    console.print(
        f"[bold green]Auto-posting scheduler started.[/bold green] "
        f"Checking every [bold]{interval}[/bold] minutes. "
        f"Press Ctrl+C to stop."
    )

    _run_once(dry_run=dry_run)  # immediate first run

    sleep_seconds = interval * 60
    elapsed = 0

    while _running:
        time.sleep(5)
        elapsed += 5
        if elapsed >= sleep_seconds:
            _run_once(dry_run=dry_run)
            elapsed = 0

    console.print("[dim]Scheduler stopped.[/dim]")


if __name__ == "__main__":
    app()
