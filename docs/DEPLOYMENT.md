# Free Cloud Deployment & Security Guide

This document provides step-by-step instructions for deploying the **RAG Agentic Project** to free cloud hosting platforms (Vercel + Render + Groq API + AnythingLLM) along with production security controls and automated CI/CD pipelines.

---

## Architecture Overview

```
                       ┌──────────────────────────────────────────────┐
                       │           Vercel Static Hosting              │
                       │   React + Vite Frontend (Chat UI & Trace)    │
                       └──────────────────────┬───────────────────────┘
                                              │ HTTPS (CORS Restricted)
                                              ▼
                       ┌──────────────────────────────────────────────┐
                       │          Render Free Web Service             │
                       │ Flask + Gunicorn + Rate Limiting + SQLite/PG │
                       └──────────────┬────────────────┬──────────────┘
                                      │                │
            ┌─────────────────────────┘                └─────────────────────────┐
            │ OpenAI-compatible REST                                             │ REST API (Bearer Key)
            ▼                                                                    ▼
┌───────────────────────────────┐                             ┌─────────────────────────────────────┐
│           Groq API            │                             │   AnythingLLM RAG Service           │
│ Llama 3.3 70B (Free / Fast)   │                             │ (Hugging Face Space / CF Tunnel)    │
└───────────────────────────────┘                             └─────────────────────────────────────┘
```

---

## 1. LLM Engine Setup (Groq API — Free & Fast)

Instead of running Ollama locally (which requires a GPU and 8GB RAM), the backend natively supports OpenAI-compatible cloud endpoints.

1. Sign up for a free account at [console.groq.com](https://console.groq.com/).
2. Create an API Key.
3. Configure these environment variables on your backend service:
   ```env
   AGENT_API_BASE_URL=https://api.groq.com/openai/v1
   AGENT_API_KEY=gsk_your_groq_api_key_here
   AGENT_MODEL=llama-3.3-70b-versatile
   ```

---

## 2. AnythingLLM RAG Knowledge Base Setup

For a free public live demo, choose one of these two options for AnythingLLM:

### Option A: Cloudflare Tunnel (Recommended for Live Demo Sessions)
Run AnythingLLM locally on your laptop in Docker, then expose it via a free public tunnel:
```bash
npx cloudflared tunnel --url http://localhost:3001
```
Copy the generated `https://<random-id>.trycloudflare.com` URL and set it as `ANYTHINGLLM_BASE_URL` on your backend.

### Option B: Deploy AnythingLLM on Render (Docker Web Service with Persistent Storage)
1. Deploy `mintplexlabs/anythingllm` as a Web Service on Render.
2. Attach a **Persistent Disk** on Render mounted at `/app/server/storage` (1 GB+).
3. Set Environment Variable `PORT=3001` (this exposes the AnythingLLM web UI at `https://anythingllm-service.onrender.com`).
4. Set Environment Variable `STORAGE_DIR=/app/server/storage`.
5. Open `https://anythingllm-service.onrender.com` in your browser.
6. Go to **Settings → API Keys → Generate Key**, copy the generated key, and set it as `ANYTHINGLLM_API_KEY` on your `RAG-Agentic-Project` backend.
7. Run `.venv/bin/python3 scripts/seed_rag.py` once to seed and embed the knowledge base files. Because persistent storage is attached, documents, embeddings, and API keys are saved permanently across container restarts!

---

## 3. Backend Deployment (Render Free Tier)

1. Connect your GitHub repository to [Render.com](https://render.com).
2. Create a **New Web Service** using the committed `render.yaml` blueprint or manual settings:
   - **Environment:** Python
   - **Build Command:** `pip install -r server/requirements.txt`
   - **Start Command:** `gunicorn --workers 2 --bind 0.0.0.0:$PORT server.app:app`
3. Set the required Environment Variables:
   - `SECRET_KEY` = (random 32-character string)
   - `DATABASE_URL` = `sqlite:///agent.db`
   - `AGENT_API_BASE_URL` = `https://api.groq.com/openai/v1`
   - `AGENT_API_KEY` = `gsk_...`
   - `AGENT_MODEL` = `llama-3.3-70b-versatile`
   - `ALLOWED_ORIGINS` = `https://your-app.vercel.app`
   - `MAX_AGENT_STEPS` = `5`
   - `MAX_PROMPT_LENGTH` = `1000`

---

## 4. Frontend Deployment (Vercel)

1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Select the **`client`** folder as the Root Directory.
3. Framework Preset: **Vite**.
4. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://your-backend.onrender.com`
5. Click **Deploy**.

---

## 5. Security & Anti-Abuse Controls

The app includes built-in security features to prevent bad actors from spamming your API, exhausting quotas, or abusing LLM endpoints:

- **In-Memory Rate Limiting:**
  - `/api/auth/register` & `/api/auth/login`: 10 requests / minute per IP.
  - `/api/conversations/<id>/messages` (Agent loop): 5 executions / minute per IP or authenticated user ID.
  - Exceeding limit returns HTTP `429 Too Many Requests`.
- **CORS Lock Down:** `ALLOWED_ORIGINS` restricts API requests strictly to your Vercel frontend.
- **Prompt Length Bounds:** Rejects prompts longer than `MAX_PROMPT_LENGTH` (1,000 chars) with HTTP `400 Bad Request`.
- **Read-Only RAG Ingestion:** AnythingLLM API keys remain strictly on the backend. Public users can only issue read-only search queries (`mode: "query"`); document upload/embedding endpoints are isolated.

---

## 6. Automated Production CI/CD Pipeline

The repository includes a GitHub Actions pipeline in `.github/workflows/deploy.yml`.

### Setting Up CD Secrets in GitHub:
Go to **Repository Settings → Secrets and variables → Actions** and add:
- `RENDER_DEPLOY_HOOK_URL`: Deploy Hook URL from Render Web Service settings.
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`: From your Vercel Account & Project settings.

### Pipeline Workflow:
1. On **Pull Request**: Runs `pytest` backend tests and `vitest` frontend tests.
2. On **Push / Merge to `main`**: Runs all unit tests, verifies frontend build, and automatically triggers production deployment on Render and Vercel.
