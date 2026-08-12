#!/usr/bin/env python3
"""
RAG Knowledge Base Seeder Script for AnythingLLM

Reads text/markdown documents from sample-data/ and populates the
AnythingLLM workspace vector database via its developer REST API.
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("ANYTHINGLLM_BASE_URL", "http://localhost:3001").rstrip("/")
PORT = os.environ.get("ANYTHINGLLM_PORT", "")
if PORT and ":" not in BASE_URL.split("://")[-1]:
    BASE_URL = f"{BASE_URL}:{PORT}"
API_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "")
WORKSPACE = os.environ.get("ANYTHINGLLM_WORKSPACE", "apprentice-kb")

if not BASE_URL:
    print("❌ Error: ANYTHINGLLM_BASE_URL is not set in environment or .env file.")
    sys.exit(1)

if not API_KEY:
    print("❌ Error: ANYTHINGLLM_API_KEY is not set in environment or .env file.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "X-Api-Key": API_KEY,
    "Content-Type": "application/json",
}

def check_connection():
    """Verify API Key & connection to AnythingLLM."""
    print(f"📡 Connecting to AnythingLLM at {BASE_URL}...")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/auth", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            print("✅ AnythingLLM API Key verified successfully!")
            return True
        else:
            print(f"⚠️ API Ping returned HTTP {resp.status_code}: {resp.text}")
            print("👉 Check that API_KEY on Render matches ANYTHINGLLM_API_KEY in your .env file!")
            return False
    except Exception as exc:
        print(f"⚠️ Connection error: {exc}")
        return False

def ensure_workspace():
    """Create workspace if it does not exist."""
    print(f"🔍 Checking workspace '{WORKSPACE}'...")
    try:
        # Try to create workspace directly if missing
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/workspace/new",
            json={"name": WORKSPACE},
            headers=HEADERS,
            timeout=10,
        )
        if create_resp.status_code in (200, 201):
            print(f"✅ Workspace '{WORKSPACE}' ready!")
            return True
        elif create_resp.status_code == 400 and "already exists" in create_resp.text.lower():
            print(f"✅ Workspace '{WORKSPACE}' already exists!")
            return True
        else:
            print(f"ℹ️ Workspace setup status: HTTP {create_resp.status_code}")
            return True
    except Exception as exc:
        print(f"⚠️ Workspace check info: {exc}")
        return True

def seed_documents():
    """Upload documents from sample-data/ to AnythingLLM."""
    sample_dir = Path(__file__).resolve().parent.parent / "sample-data"
    files = list(sample_dir.glob("*.txt")) + list(sample_dir.glob("*.md"))
    files = [f for f in files if f.name.lower() != "readme.md"]

    if not files:
        print("⚠️ No document files (.txt, .md) found in sample-data/")
        return

    print(f"📄 Found {len(files)} knowledge base files to index...")
    adds = []
    auth_headers = {"Authorization": f"Bearer {API_KEY}", "X-Api-Key": API_KEY}

    for file_path in files:
        print(f"  --> Uploading {file_path.name}...")
        try:
            with open(file_path, "rb") as f_bin:
                up_resp = requests.post(
                    f"{BASE_URL}/api/v1/document/upload",
                    files={"file": (file_path.name, f_bin, "text/plain")},
                    headers=auth_headers,
                    timeout=30,
                )
                if up_resp.status_code in (200, 201):
                    try:
                        res_data = up_resp.json()
                        documents = res_data.get("documents", [])
                        loc = None
                        if isinstance(documents, list) and documents:
                            loc = documents[0].get("location") if isinstance(documents[0], dict) else str(documents[0])
                        elif isinstance(documents, dict):
                            loc = documents.get("location")
                        if not loc and "location" in res_data:
                            loc = res_data["location"]
                        if not loc:
                            loc = f"custom-documents/{file_path.name}"
                        adds.append(loc)
                        print(f"      ✅ Uploaded {file_path.name} (location: {loc})")
                    except Exception as parse_exc:
                        loc = f"custom-documents/{file_path.name}"
                        adds.append(loc)
                        print(f"      ✅ Uploaded {file_path.name} (fallback location: {loc}, body: {up_resp.text[:150]})")
                else:
                    print(f"      ❌ Upload returned HTTP {up_resp.status_code}: {up_resp.text[:150]}")
        except Exception as exc:
            print(f"      ❌ Exception uploading {file_path.name}: {exc}")

    if adds:
        adds = list(set(adds))
        print(f"🧠 Indexing and embedding {len(adds)} document(s) into '{WORKSPACE}'...")
        try:
            update_resp = requests.post(
                f"{BASE_URL}/api/v1/workspace/{WORKSPACE}/update-embeddings",
                json={"adds": adds},
                headers=HEADERS,
                timeout=30,
            )
            if update_resp.status_code in (200, 201):
                print("🎉 SUCCESS! Knowledge base successfully seeded and embedded!")
            else:
                print(f"ℹ️ Update embeddings response: HTTP {update_resp.status_code} - {update_resp.text[:150]}")
        except Exception as exc:
            print(f"⚠️ Embedding update error: {exc}")
    else:
        print("⚠️ No document locations were extracted from upload responses.")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting AnythingLLM RAG Knowledge Base Seeder")
    print("=" * 60)
    check_connection()
    ensure_workspace()
    seed_documents()
    print("=" * 60)
