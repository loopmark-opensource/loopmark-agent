"""
Complaints, Posting, and Funnel sub-agents.

Each agent is a LangChain ReAct agent (create_react_agent) wrapped in a
thin helper that returns a plain string response.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import config
from prompts.templates import (
    get_complaints_prompt,
    get_posting_prompt,
    get_funnel_prompt,
)
from tools.complaint_tools import COMPLAINT_TOOLS
from tools.social_tools import POSTING_TOOLS
from tools.email_tools import EMAIL_TOOLS
from tools.publisher_tools import PUBLISHER_TOOLS
from tools.funnel_tools import FUNNEL_TOOLS


def _make_llm(temperature: float | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=temperature if temperature is not None else config.OPENAI_TEMPERATURE,
        api_key=config.OPENAI_API_KEY,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Complaints Agent
# ──────────────────────────────────────────────────────────────────────────────

def build_complaints_agent():
    """Return a compiled LangGraph ReAct agent for complaint management."""
    llm = _make_llm(temperature=0.3)
    prompt = get_complaints_prompt()
    return create_react_agent(
        model=llm,
        tools=COMPLAINT_TOOLS,
        prompt=prompt,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Posting / Content Agent
# ──────────────────────────────────────────────────────────────────────────────

def build_posting_agent():
    """Return a compiled LangGraph ReAct agent for content creation, posting, and email marketing."""
    llm = _make_llm(temperature=0.8)
    prompt = get_posting_prompt()
    return create_react_agent(
        model=llm,
        tools=POSTING_TOOLS + EMAIL_TOOLS + PUBLISHER_TOOLS,
        prompt=prompt,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Funnel Agent
# ──────────────────────────────────────────────────────────────────────────────

def build_funnel_agent():
    """Return a compiled LangGraph ReAct agent for funnel / lead management."""
    llm = _make_llm(temperature=0.2)
    prompt = get_funnel_prompt()
    return create_react_agent(
        model=llm,
        tools=FUNNEL_TOOLS,
        prompt=prompt,
    )
