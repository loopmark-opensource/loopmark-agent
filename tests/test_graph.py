from langchain_core.messages import HumanMessage

from agents.graph import (
    build_marketing_graph,
    select_agent,
    fallback_node,
)


def test_select_agent_routes_correctly():
    assert select_agent({"intent": "complaint", "messages": []}) == "complaints_node"
    assert select_agent({"intent": "posting", "messages": []}) == "posting_node"
    assert select_agent({"intent": "funnel", "messages": []}) == "funnel_node"
    assert select_agent({"intent": "unknown", "messages": []}) == "fallback_node"
    assert select_agent({"intent": "invalid", "messages": []}) == "fallback_node"


def test_fallback_node_returns_help_message():
    state = fallback_node({"messages": [HumanMessage(content="hello")], "intent": "unknown"})
    assert state["intent"] == "unknown"
    assert "Complaints" in state["messages"][0].content
    assert "Posting" in state["messages"][0].content
    assert "Funnel" in state["messages"][0].content


def test_build_marketing_graph_compiles():
    graph = build_marketing_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")
