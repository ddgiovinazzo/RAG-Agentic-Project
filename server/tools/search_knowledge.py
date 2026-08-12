import requests
from flask import current_app


def search_knowledge(query):
    """Query the AnythingLLM workspace. Returns {"answer", "sources"} or {"error"}."""
    cfg = current_app.config
    base = cfg['ANYTHINGLLM_BASE_URL'].rstrip('/')
    workspace = cfg['ANYTHINGLLM_WORKSPACE']
    headers = {
        "Authorization": f"Bearer {cfg['ANYTHINGLLM_API_KEY']}",
        "X-Api-Key": cfg["ANYTHINGLLM_API_KEY"],
        "Content-Type": "application/json",
    }
    
    last_error = None
    # Primary RAG endpoint
    url = f"{base}/api/v1/workspace/{workspace}/chat"
    try:
        resp = requests.post(
            url,
            json={"message": query, "mode": "chat"},
            headers=headers,
            timeout=cfg["TOOL_TIMEOUT_SECONDS"],
        )
        if resp.status_code == 200 and resp.text.strip() != "OK":
            try:
                data = resp.json()
                sources = [s.get("title") or s.get("url") or "unknown" for s in data.get("sources", [])]
                answer = data.get("textResponse") or data.get("message") or data.get("response") or str(data)
                if answer and answer.strip() != "OK":
                    return {"answer": answer, "sources": sources}
            except Exception:
                if resp.text and resp.text.strip() != "OK":
                    return {"answer": resp.text, "sources": []}
        elif resp.status_code != 200:
            last_error = f"knowledge service returned HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as exc:
        last_error = f"knowledge service unreachable: {exc}"

    # Fallback RAG vector search endpoint
    sim_url = f"{base}/api/v1/workspace/{workspace}/similarity-search"
    try:
        resp = requests.post(
            sim_url,
            json={"message": query},
            headers=headers,
            timeout=cfg["TOOL_TIMEOUT_SECONDS"],
        )
        if resp.status_code == 200:
            try:
                data = resp.json()
                sources = [s.get("title") or s.get("url") or "unknown" for s in data.get("sources", [])]
                chunks = data.get("chunks", []) or data.get("documents", [])
                text_chunks = [c.get("text") or c.get("content") or str(c) for c in chunks if isinstance(c, dict)]
                answer = "\n".join(text_chunks) if text_chunks else data.get("textResponse", str(data))
                return {"answer": answer, "sources": sources}
            except Exception:
                return {"answer": resp.text, "sources": []}
        elif resp.status_code != 200:
            last_error = f"knowledge service returned HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.RequestException as exc:
        last_error = f"knowledge service unreachable: {exc}"

    if last_error:
        return {"error": last_error}
    return {"answer": "No relevant documents found in knowledge base.", "sources": []}
