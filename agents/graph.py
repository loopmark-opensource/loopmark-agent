"""
LangGraph orchestrator: routes user input to the correct sub-agent.

Graph topology
──────────────
  START
    │
    ▼
  route_intent          ← classifies user intent via a lightweight LLM call
    │
    ├──[complaint]──► complaints_node ──► END
    ├──[posting]────► posting_node    ──► END
    ├──[funnel]─────► funnel_node     ──► END
    └──[unknown]────► fallback_node   ──► END
"""

from __future__ import annotations

from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated

from config import config
from prompts.templates import get_router_prompt
from agents.sub_agents import (
    build_complaints_agent,
    build_posting_agent,
    build_funnel_agent,
)


# ─── Graph state ──────────────────────────────────────────────────────────────

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str


# ─── Lazy-loaded sub-agents (avoid rebuilding on every call) ─────────────────

_complaints_agent = None
_posting_agent = None
_funnel_agent = None


def _get_complaints_agent():
    global _complaints_agent
    if _complaints_agent is None:
        _complaints_agent = build_complaints_agent()
    return _complaints_agent


def _get_posting_agent():
    global _posting_agent
    if _posting_agent is None:
        _posting_agent = build_posting_agent()
    return _posting_agent


def _get_funnel_agent():
    global _funnel_agent
    if _funnel_agent is None:
        _funnel_agent = build_funnel_agent()
    return _funnel_agent


# ─── Nodes ───────────────────────────────────────────────────────────────────

def route_intent(state: GraphState) -> GraphState:
    """Classify the latest user message into an intent label."""
    user_input = state["messages"][-1].content if state["messages"] else ""
    router_prompt = get_router_prompt()
    llm = ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=0,
        api_key=config.OPENAI_API_KEY,
    )
    chain = router_prompt | llm
    result = chain.invoke({"user_input": user_input})
    intent = result.content.strip().lower()
    if intent not in ("complaint", "posting", "funnel"):
        intent = "unknown"
    return {"intent": intent, "messages": state["messages"]}


def complaints_node(state: GraphState) -> GraphState:
    agent = _get_complaints_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"], "intent": state["intent"]}


def posting_node(state: GraphState) -> GraphState:
    agent = _get_posting_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"], "intent": state["intent"]}


def funnel_node(state: GraphState) -> GraphState:
    agent = _get_funnel_agent()
    result = agent.invoke({"messages": state["messages"]})
    return {"messages": result["messages"], "intent": state["intent"]}


def fallback_node(state: GraphState) -> GraphState:
    from langchain_core.messages import AIMessage
    msg = AIMessage(
        content=(
            "I'm your Marketing Agent. I can help you with:\n\n"
            "  🗣️  **Complaints** — log, triage, and respond to customer complaints\n"
            "  📣  **Posting** — define your target audience, create platform-optimised content,\n"
            "       engage your audience, and build content calendars\n"
            "  📊  **Funnel** — manage leads, score prospects, grow conversions, and plan nurture sequences\n\n"
            "How can I help you today?"
        )
    )
    return {"messages": [msg], "intent": "unknown"}


# ─── Conditional edge ────────────────────────────────────────────────────────

def select_agent(state: GraphState) -> Literal["complaints_node", "posting_node", "funnel_node", "fallback_node"]:
    mapping = {
        "complaint": "complaints_node",
        "posting": "posting_node",
        "funnel": "funnel_node",
        "unknown": "fallback_node",
    }
    return mapping.get(state["intent"], "fallback_node")


# ─── Build graph ─────────────────────────────────────────────────────────────

def build_marketing_graph():
    """Compile and return the full marketing agent LangGraph."""
    builder = StateGraph(GraphState)

    builder.add_node("route_intent", route_intent)
    builder.add_node("complaints_node", complaints_node)
    builder.add_node("posting_node", posting_node)
    builder.add_node("funnel_node", funnel_node)
    builder.add_node("fallback_node", fallback_node)

    builder.add_edge(START, "route_intent")
    builder.add_conditional_edges("route_intent", select_agent)
    builder.add_edge("complaints_node", END)
    builder.add_edge("posting_node", END)
    builder.add_edge("funnel_node", END)
    builder.add_edge("fallback_node", END)

    return builder.compile()


# Singleton compiled graph
_graph = None


def get_marketing_graph():
    global _graph
    if _graph is None:
        _graph = build_marketing_graph()
    return _graph
