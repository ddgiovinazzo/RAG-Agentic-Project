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

BASE_URL = os.environ.get("ANYTHINGLLM_BASE_URL", "https://anythingllm-service.onrender.com").rstrip("/")
API_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "")
WORKSPACE = os.environ.get("ANYTHINGLLM_WORKSPACE", "apprentice-kb")

if not API_KEY:
    print("❌ Error: ANYTHINGLLM_API_KEY is not set in environment or .env file.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
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
            return False
    except Exception as exc:
        print(f"⚠️ Connection error: {exc}")
        return False

def ensure_workspace():
    """Create workspace if it does not exist."""
    print(f"🔍 Checking workspace '{WORKSPACE}'...")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/workspaces", headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            workspaces = resp.json().get("workspaces", [])
            for w in workspaces:
                if w.get("slug") == WORKSPACE or w.get("name") == WORKSPACE:
                    print(f"✅ Workspace '{WORKSPACE}' exists!")
                    return True

        # Try to create workspace
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/workspace/new",
            json={"name": WORKSPACE},
            headers=HEADERS,
            timeout=10,
        )
        if create_resp.status_code in (200, 201):
            print(f"✅ Created new workspace '{WORKSPACE}'!")
            return True
        else:
            print(f"ℹ️ Workspace setup status: {create_resp.status_code}")
            return True
    except Exception as exc:
        print(f"⚠️ Workspace check error: {exc}")
        return False

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

    for file_path in files:
        print(f"  --> Uploading {file_path.name}...")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Push document as raw-text to AnythingLLM
            raw_resp = requests.post(
                f"{BASE_URL}/api/v1/raw-text",
                json={
                    "textContent": content,
                    "title": file_path.name,
                },
                headers=HEADERS,
                timeout=20,
            )

            if raw_resp.status_code in (200, 201):
                res_data = raw_resp.json()
                location = res_data.get("location") or res_data.get("document", {}).get("location")
                if location:
                    adds.append(location)
                print(f"      ✅ Uploaded {file_path.name}")
            else:
                # Fallback multipart upload
                with open(file_path, "rb") as f_bin:
                    up_headers = {"Authorization": f"Bearer {API_KEY}"}
                    up_resp = requests.post(
                        f"{BASE_URL}/api/v1/document/upload",
                        files={"file": (file_path.name, f_bin)},
                        headers=up_headers,
                        timeout=20,
                    )
                    if up_resp.status_code in (200, 201):
                        res_data = up_resp.json()
                        documents = res_data.get("documents", [])
                        if documents:
                            adds.append(documents[0].get("location"))
                        print(f"      ✅ Uploaded {file_path.name} (multipart)")
                    else:
                        print(f"      ❌ Failed to upload {file_path.name}: HTTP {up_resp.status_code}")
        except Exception as exc:
            print(f"      ❌ Exception uploading {file_path.name}: {exc}")

    if adds:
        print(f"🧠 Indexing and embedding {len(adds)} documents into '{WORKSPACE}'...")
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
                print(f"ℹ️ Update embeddings response: HTTP {update_resp.status_code}")
        except Exception as exc:
            print(f"⚠️ Embedding update error: {exc}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting AnythingLLM RAG Knowledge Base Seeder")
    print("=" * 60)
    check_connection()
    ensure_workspace()
    seed_documents()
    print("=" * 60)
