def scripted(*responses):
    it = iter(responses)

    def fake_generate(messages, tools):
        return next(it)

    return fake_generate


def test_single_tool_then_final_answer(app, run, monkeypatch):
    from server.agent import run_agent
    from server.tools import TOOLS

    monkeypatch.setattr(
        "server.agent.generate",
        scripted(
            {"type": "tool_call", "name": "search_knowledge", "arguments": {"query": "vpn"}, "call_id": "c1"},
            {"type": "final", "content": "Reset it in Settings."},
        ),
    )
    monkeypatch.setitem(
        TOOLS["search_knowledge"], "handler", lambda query: {"answer": "kb says reset", "sources": []}
    )

    outcome = run_agent(run, "How do I reset my VPN?")
    assert outcome["status"] == "completed"
    assert outcome["answer"] == "Reset it in Settings."
    assert [s.kind for s in run.steps] == ["llm_call", "tool_call", "llm_call"]
    from server.models import Message

    saved = Message.query.filter_by(conversation_id=run.conversation_id, role="assistant").one()
    assert saved.content == "Reset it in Settings."


def test_loop_terminates_at_max_steps(app, run, monkeypatch):
    from server.agent import run_agent
    from server.tools import TOOLS

    monkeypatch.setattr(
        "server.agent.generate",
        lambda m, t: {
            "type": "tool_call",
            "name": "search_knowledge",
            "arguments": {"query": "again"},
            "call_id": "c",
        },
    )
    monkeypatch.setitem(TOOLS["search_knowledge"], "handler", lambda query: {"answer": "a", "sources": []})

    outcome = run_agent(run, "loop forever")
    assert outcome["status"] == "failed"
    assert len(run.steps) <= app.config["MAX_AGENT_STEPS"]


def test_invalid_arguments_retry_once_then_fail(app, run, monkeypatch):
    from server.agent import run_agent

    monkeypatch.setattr(
        "server.agent.generate",
        lambda m, t: {"type": "tool_call", "name": "search_knowledge", "arguments": {}, "call_id": "c"},
    )
    outcome = run_agent(run, "bad args forever")
    assert outcome["status"] == "failed"
    # two llm_calls (original + one retry), no tool ever executed
    assert [s.kind for s in run.steps] == ["llm_call", "llm_call"]


def test_llm_failure_fails_gracefully(app, run, monkeypatch):
    from server.agent import run_agent
    from server.llm import LLMError

    def dead(messages, tools):
        raise LLMError("connection refused")

    monkeypatch.setattr("server.agent.generate", dead)
    outcome = run_agent(run, "anything")
    assert outcome["status"] == "failed"
    assert outcome["answer"]  # a human-readable apology, not empty


def test_confirmation_gated_tool_pauses_run(app, run, monkeypatch):
    from server.agent import run_agent
    from server.models import PendingAction

    monkeypatch.setattr(
        "server.agent.generate",
        scripted(
            {
                "type": "tool_call",
                "name": "escalate",
                "arguments": {"ticket_id": "T-1", "priority": "high", "reason": "outage"},
                "call_id": "c1",
            }
        ),
    )
    outcome = run_agent(run, "Escalate ticket T-1")
    assert outcome["status"] == "needs_confirmation"
    assert outcome["pending_action"]["tool"] == "escalate"
    action = PendingAction.query.filter_by(run_id=run.id).one()
    assert action.status == "pending"
    assert run.status == "needs_confirmation"
    # only the llm_call is recorded — the tool has NOT run
    assert [s.kind for s in run.steps] == ["llm_call"]
