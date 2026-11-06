"""Exercise model selection through the real graph without making API calls."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from typer.testing import CliRunner

from agents import graph, sub_agents
from config import config
from core.run import run_agent
from main import app


@pytest.fixture
def stub_models(monkeypatch):
    observed = {"calls": [], "built": [], "barrier": None}

    class StubChatOpenAI:
        def __init__(self, *, model, temperature, api_key):
            self.model = model

        def invoke(self, values):
            observed["calls"].append(("router", self.model))
            if observed["barrier"] is not None:
                observed["barrier"].wait(timeout=5)
            return AIMessage(content=values["user_input"])

    class RouterPrompt:
        def __or__(self, llm):
            return llm

    class StubAgent:
        def __init__(self, model):
            self.model = model

        def invoke(self, state):
            observed["calls"].append(("agent", self.model))
            return {"messages": [AIMessage(content=self.model)]}

    def create_agent(*, model, tools, prompt):
        observed["built"].append(model.model)
        return StubAgent(model.model)

    caches = (graph._get_complaints_agent, graph._get_posting_agent, graph._get_funnel_agent)
    for cache in caches:
        cache.cache_clear()
    monkeypatch.setattr(config, "OPENAI_MODEL", "default-model")
    monkeypatch.setattr(graph, "ChatOpenAI", StubChatOpenAI)
    monkeypatch.setattr(sub_agents, "ChatOpenAI", StubChatOpenAI)
    monkeypatch.setattr(graph, "get_router_prompt", RouterPrompt)
    monkeypatch.setattr(sub_agents, "create_react_agent", create_agent)
    monkeypatch.setattr(graph, "_graph", graph.build_marketing_graph())
    yield observed
    for cache in caches:
        cache.cache_clear()


@pytest.mark.parametrize("intent", ["complaint", "posting", "funnel"])
def test_router_and_agent_use_each_calls_model_and_reuse_matching_cache(stub_models, intent):
    for override, expected in (
        ("override-model", "override-model"),
        (None, "default-model"),
        ("override-model", "override-model"),
    ):
        result = run_agent(intent, model=override)
        assert result.reply == expected
        assert result.intent == intent
        assert config.OPENAI_MODEL == "default-model"

    assert stub_models["calls"] == [
        (node, model)
        for model in ("override-model", "default-model", "override-model")
        for node in ("router", "agent")
    ]
    assert stub_models["built"] == ["override-model", "default-model"]


@pytest.mark.parametrize("intent", ["complaint", "posting", "funnel"])
def test_concurrent_overrides_stay_with_their_own_requests(stub_models, intent):
    stub_models["barrier"] = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run_agent, intent, model="model-a")
        second = pool.submit(run_agent, intent, model="model-b")
        assert first.result(timeout=10).reply == "model-a"
        assert second.result(timeout=10).reply == "model-b"

    assert sorted(stub_models["calls"]) == sorted(
        (node, model) for node in ("router", "agent") for model in ("model-a", "model-b")
    )
    assert config.OPENAI_MODEL == "default-model"


def test_direct_graph_call_without_model_uses_default(stub_models):
    result = graph.get_marketing_graph().invoke({"messages": [HumanMessage(content="posting")]})
    assert result["messages"][-1].content == "default-model"
    assert stub_models["calls"] == [("router", "default-model"), ("agent", "default-model")]


def test_cli_override_does_not_mutate_default(monkeypatch):
    monkeypatch.setattr(config, "OPENAI_MODEL", "default-model")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key-for-ci")
    models = []

    def fake_run(message, history=None, *, model=None):
        models.append(model)
        from core.run import AgentResult

        return AgentResult(reply="Done", intent="posting", messages=[])

    monkeypatch.setattr("core.run.run_agent", fake_run)
    result = CliRunner().invoke(app, ["chat", "--model", "override-model"], input="post\nquit\n")
    assert result.exit_code == 0, result.output
    assert models == ["override-model"]
    assert config.OPENAI_MODEL == "default-model"
