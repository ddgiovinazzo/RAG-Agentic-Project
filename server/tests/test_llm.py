import pytest
import requests


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _message_payload(message):
    return {"choices": [{"message": message}]}


def test_generate_final_answer(app, monkeypatch):
    calls = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls["url"] = url
        return FakeResponse(_message_payload({"content": "hi there"}))

    monkeypatch.setattr("server.llm.requests.post", fake_post)
    from server.llm import generate

    result = generate([{"role": "user", "content": "hello"}], [])
    assert result == {
        "type": "final",
        "content": "hi there",
        "usage": {"prompt_tokens": None, "completion_tokens": None},
    }
    assert calls["url"] == "http://localhost:11434/v1/chat/completions"


def test_generate_parses_tool_call(app, monkeypatch):
    payload = _message_payload(
        {
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_knowledge",
                        "arguments": '{"query": "vpn reset"}',
                    },
                }
            ],
        }
    )
    monkeypatch.setattr("server.llm.requests.post", lambda *a, **k: FakeResponse(payload))
    from server.llm import generate

    result = generate([{"role": "user", "content": "x"}], [])
    assert result == {
        "type": "tool_call",
        "name": "search_knowledge",
        "arguments": {"query": "vpn reset"},
        "call_id": "call_1",
        "usage": {"prompt_tokens": None, "completion_tokens": None},
    }


def test_generate_marks_malformed_arguments(app, monkeypatch):
    payload = _message_payload(
        {
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "escalate", "arguments": "{not json"},
                }
            ]
        }
    )
    monkeypatch.setattr("server.llm.requests.post", lambda *a, **k: FakeResponse(payload))
    from server.llm import generate

    result = generate([], [])
    assert result["arguments"] == {"__parse_error__": "{not json"}


def test_generate_uses_hosted_endpoint_when_configured(app, monkeypatch):
    app.config["AGENT_API_BASE_URL"] = "https://api.example.com/v1"
    app.config["AGENT_API_KEY"] = "sk-test"
    seen = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        seen["url"] = url
        seen["headers"] = headers
        return FakeResponse(_message_payload({"content": "ok"}))

    monkeypatch.setattr("server.llm.requests.post", fake_post)
    from server.llm import generate

    generate([], [])
    assert seen["url"] == "https://api.example.com/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer sk-test"


def test_generate_raises_llm_error_on_connection_failure(app, monkeypatch):
    def fake_post(*a, **k):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr("server.llm.requests.post", fake_post)
    from server.llm import LLMError, generate

    with pytest.raises(LLMError):
        generate([], [])


def test_generate_rescues_groq_tool_use_failed(app, monkeypatch):
    import json as _json
    err_json = _json.dumps({
        "error": {
            "message": "Failed to call a function.",
            "type": "invalid_request_error",
            "code": "tool_use_failed",
            "failed_generation": '<function=search_knowledge{"query": "company remote work policy"}></function>'
        }
    })

    class Groq400Response:
        status_code = 400
        text = err_json
        def raise_for_status(self):
            exc = requests.HTTPError("400 Client Error")
            exc.response = self
            raise exc

    monkeypatch.setattr("server.llm.requests.post", lambda *a, **k: Groq400Response())
    from server.llm import generate

    result = generate([{"role": "user", "content": "x"}], [])
    assert result["type"] == "tool_call"
    assert result["name"] == "search_knowledge"
    assert result["arguments"] == {"query": "company remote work policy"}


def test_generate_parses_usage(app, monkeypatch):
    payload = {
        "choices": [{"message": {"content": "hi"}}],
        "usage": {"prompt_tokens": 150, "completion_tokens": 20},
    }
    monkeypatch.setattr("server.llm.requests.post", lambda *a, **k: FakeResponse(payload))
    from server.llm import generate

    result = generate([], [])
    assert result["usage"] == {"prompt_tokens": 150, "completion_tokens": 20}
