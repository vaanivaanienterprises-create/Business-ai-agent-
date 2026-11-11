import os
import json
import urllib.request
import urllib.error

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")



def ask_openai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": False, "error": "OPENAI_API_KEY not configured"}

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "input": prompt
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode())
        texts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))
        return {"ok": True, "provider": "OpenAI", "text": "\n".join(texts)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def ask_claude(prompt):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY not configured"}

    payload = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode())
        texts = [
            item.get("text", "")
            for item in data.get("content", [])
            if item.get("type") == "text"
        ]
        return {"ok": True, "provider": "Claude", "text": "\n".join(texts)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
