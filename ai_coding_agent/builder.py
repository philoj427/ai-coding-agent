from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """You are Builder Agent for a local-first AI Coding Agent.
Output only a SEARCH/REPLACE patch.
Do not use markdown fences.
Do not explain anything.
The patch must target one file and use exact text matches.
Format:
SEARCH
<exact old text>
END_SEARCH
REPLACE
<new text>
END_REPLACE
"""


def build_prompt(context_pack: str) -> str:
    return f"{SYSTEM_PROMPT}\n\n{context_pack}"


def generate_patch(model: str, prompt: str, ollama_host: str = "http://localhost:11434") -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
    }).encode("utf-8")
    request = Request(
        f"{ollama_host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=600) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body["response"]
    except URLError as exc:
        raise RuntimeError(f"Failed to contact Ollama at {ollama_host}: {exc}") from exc
