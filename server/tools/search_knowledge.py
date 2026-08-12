import requests
from flask import current_app


def search_knowledge(query):
    """Query the AnythingLLM workspace. Returns {"answer", "sources"} or {"error"}."""
    cfg = current_app.config
    url = (
        f"{cfg['ANYTHINGLLM_BASE_URL'].rstrip('/')}"
        f"/api/v1/workspace/{cfg['ANYTHINGLLM_WORKSPACE']}/chat"
    )
    try:
        resp = requests.post(
            url,
            json={"message": query, "mode": "query"},
            headers={
                "Authorization": f"Bearer {cfg['ANYTHINGLLM_API_KEY']}",
                "X-Api-Key": cfg["ANYTHINGLLM_API_KEY"],
            },
            timeout=cfg["TOOL_TIMEOUT_SECONDS"],
        )
    except requests.RequestException as exc:
        return {"error": f"knowledge service unreachable: {exc}"}
    if resp.status_code in (401, 403):
        return {"error": "knowledge service rejected the API key"}
    if resp.status_code != 200:
        return {"error": f"knowledge service returned HTTP {resp.status_code}"}
    data = resp.json()
    sources = [s.get("title") or s.get("url") or "unknown" for s in data.get("sources", [])]
    return {"answer": data.get("textResponse", ""), "sources": sources}
