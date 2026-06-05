from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """Write a replacement for the already-selected exact SEARCH candidate.
Return JSON only.
No markdown fences.
No explanations.
Do not invent SEARCH text.
Do not paraphrase the selected candidate.
Use this exact JSON shape:
{"replacement":"<new text>","reason":"<short reason>"}
"""


def build_prompt(context_pack: str) -> str:
    return f"{SYSTEM_PROMPT}\n\n{context_pack}\n"


def _strip_code_fences(text: str) -> str:
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].lstrip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


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
            return _strip_code_fences(body["response"].strip())
    except URLError as exc:
        raise RuntimeError(f"Failed to contact Ollama at {ollama_host}: {exc}") from exc
