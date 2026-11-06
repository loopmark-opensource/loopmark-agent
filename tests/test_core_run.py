"""Tests for core.run programmatic entry point."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from core.run import AgentResult, run_agent
from config import config


class _FakeGraph:
    def invoke(self, state):
        messages = list(state["messages"])
        messages.append(AIMessage(content="Test reply"))
        return {"messages": messages, "intent": "posting"}


def test_run_agent_returns_structured_result(monkeypatch):
    monkeypatch.setattr("core.run.get_marketing_graph", lambda: _FakeGraph())

    result = run_agent("Write a LinkedIn post", history=[HumanMessage(content="Hi")])

    assert isinstance(result, AgentResult)
    assert result.reply == "Test reply"
    assert result.intent == "posting"
    assert len(result.messages) == 3


def test_run_agent_empty_reply_when_no_ai_message(monkeypatch):
    class _EmptyGraph:
        def invoke(self, state):
            return {"messages": state["messages"], "intent": "unknown"}

    monkeypatch.setattr("core.run.get_marketing_graph", lambda: _EmptyGraph())
    result = run_agent("hello")
    assert result.reply == ""
    assert result.intent == "unknown"


def test_model_override_is_local_to_one_call(monkeypatch):
    models = []

    class RecordingGraph(_FakeGraph):
        def invoke(self, state):
            models.append(state.get("model"))
            return super().invoke(state)

    monkeypatch.setattr(config, "OPENAI_MODEL", "default-model")
    monkeypatch.setattr("core.run.get_marketing_graph", lambda: RecordingGraph())

    run_agent("Write a post", model="override-model")
    assert config.OPENAI_MODEL == "default-model"
    run_agent("Write another post")
    assert models == ["override-model", "default-model"]
