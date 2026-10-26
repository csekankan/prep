"""Router heuristics — no network required."""

from rag_chatbot.graph.nodes import _heuristic_analysis


def test_greeting_routes_to_chat():
    a = _heuristic_analysis("hello")
    assert a.route == "chat"


def test_policy_keyword_routes_to_rag():
    a = _heuristic_analysis("What is the refund policy for $150?")
    assert a.route == "rag"
    assert a.sub_questions
