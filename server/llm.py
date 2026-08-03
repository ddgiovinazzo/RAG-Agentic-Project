import json

import requests
from flask import current_app


class LLMError(Exception):
    """The model endpoint could not be reached or returned an error."""


def _endpoint_and_headers():
    cfg = current_app.config
    if cfg.get("AGENT_API_BASE_URL"):
        base = cfg["AGENT_API_BASE_URL"].rstrip("/")
        headers = {"Authorization": f"Bearer {cfg['AGENT_API_KEY']}"}
    else:
        base = cfg["OLLAMA_BASE_URL"].rstrip("/") + "/v1"
        headers = {}
    return f"{base}/chat/completions", headers


def generate(messages, tools):
    """One model call. Returns {"type": "final", "content": str} or
    {"type": "tool_call", "name": str, "arguments": dict, "call_id": str}."""
    url, headers = _endpoint_and_headers()
    payload = {"model": current_app.config["AGENT_MODEL"], "messages": messages}
    if tools:
        payload["tools"] = tools
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise LLMError(f"model call failed: {exc}") from exc

    message = resp.json()["choices"][0]["message"]
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        call = tool_calls[0]
        raw = call["function"].get("arguments") or "{}"
        try:
            arguments = json.loads(raw)
        except json.JSONDecodeError:
            arguments = {"__parse_error__": raw}
        return {
            "type": "tool_call",
            "name": call["function"]["name"],
            "arguments": arguments,
            "call_id": call.get("id", "call_0"),
        }
    return {"type": "final", "content": message.get("content") or ""}
