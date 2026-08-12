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


def _parse_fallback_tool_call(text):
    """
    Provider-agnostic tool call recovery parser.
    Parses raw function call tags (e.g. <function=name{args}>) or stringified tool JSON
    emitted by local Ollama models, open-source LLMs, or API proxies.
    """
    if not text:
        return None
    # Unescape unicode HTML escapes if present (\u003c -> <, \u003e -> >)
    text = text.replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0022", '"')
    import re
    match = re.search(r"<function=(\w+)\s*\(?\s*(\{.*?\})\s*\)?", text, re.DOTALL)
    if not match:
        return None

    t_name = match.group(1)
    t_args_raw = match.group(2).replace('\\"', '"').replace('\\\\', '\\')
    try:
        t_args = json.loads(t_args_raw)
        if isinstance(t_args, dict):
            for k, v in list(t_args.items()):
                if isinstance(v, str) and "{" in v:
                    try:
                        parsed_v = json.loads(v)
                        if isinstance(parsed_v, dict):
                            t_args = parsed_v
                            break
                    except Exception:
                        pass
    except Exception:
        t_args = {"query": t_args_raw}

    return {
        "type": "tool_call",
        "name": t_name,
        "arguments": t_args,
        "call_id": "call_fallback_rescued",
        "usage": {"prompt_tokens": 0, "completion_tokens": 0},
    }


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
        if getattr(exc, "response", None) is not None and exc.response.text:
            fallback = _parse_fallback_tool_call(exc.response.text)
            if fallback:
                return fallback
            raise LLMError(f"model call failed: {exc} - {exc.response.text}") from exc
        raise LLMError(f"model call failed: {exc}") from exc

    data = resp.json()
    message = data["choices"][0]["message"]
    usage_raw = data.get("usage") or {}
    usage = {
        "prompt_tokens": usage_raw.get("prompt_tokens"),
        "completion_tokens": usage_raw.get("completion_tokens"),
    }
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
            "usage": usage,
        }

    content = message.get("content") or ""
    if "{" in content and "}" in content:
        import re
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                raw_str = match.group(0)
                try:
                    parsed = json.loads(raw_str)
                except Exception:
                    import ast
                    parsed = ast.literal_eval(raw_str)

                if isinstance(parsed, dict):
                    tool_name = (
                        parsed.get("name")
                        or parsed.get("tool")
                        or parsed.get("function")
                    )
                    if tool_name in [
                        "search_knowledge",
                        "list_tickets",
                        "create_ticket",
                        "update_ticket",
                        "delete_ticket",
                        "create_draft",
                        "escalate",
                    ]:
                        args = (
                            parsed.get("arguments")
                            or parsed.get("parameters")
                            or {}
                        )
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {"query": args}
                        return {
                            "type": "tool_call",
                            "name": tool_name,
                            "arguments": args if isinstance(args, dict) else {},
                            "call_id": "call_fallback",
                            "usage": usage,
                        }
            except Exception:
                pass


    return {"type": "final", "content": content, "usage": usage}

