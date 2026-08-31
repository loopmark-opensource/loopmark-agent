"""
Shared programmatic entry point for the marketing graph.

Used by the CLI (`main.py`) and future hosted API backends.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from agents.graph import get_marketing_graph


@dataclass
class AgentResult:
    """Structured response from a single agent turn."""

    reply: str
    intent: str
    messages: list[BaseMessage]


def run_agent(
    message: str,
    history: Sequence[BaseMessage] | None = None,
    *,
    model: str | None = None,
) -> AgentResult:
    """
    Run one turn of the marketing agent graph.

    Args:
        message: User input text.
        history: Optional prior conversation messages for multi-turn chat.
        model: Optional OpenAI model override (e.g. gpt-4o-mini).

    Returns:
        AgentResult with reply text, routed intent, and full message history.
    """
    if model:
        from config import config

        config.OPENAI_MODEL = model

    graph = get_marketing_graph()
    conversation: list[BaseMessage] = list(history or [])
    conversation.append(HumanMessage(content=message.strip()))

    result = graph.invoke({"messages": conversation})
    updated_messages: list[BaseMessage] = result["messages"]
    intent = result.get("intent", "unknown")

    ai_messages = [m for m in updated_messages if isinstance(m, AIMessage)]
    reply = ai_messages[-1].content if ai_messages else ""

    return AgentResult(reply=reply, intent=intent, messages=updated_messages)
