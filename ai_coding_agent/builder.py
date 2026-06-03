from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """Output only one SEARCH/REPLACE patch.
No markdown fences.
No explanations.
Preserve exact indentation and whitespace.
Do not output indentation-only changes.
Patch must change the target file contents.
Do not output a no-op patch.
Do not change indentation on a line unless the line content also changes.
Target one file only.
Use this exact format:
SEARCH
<exact old text>
END_SEARCH
REPLACE
<replacement text>
END_REPLACE
"""


def build_prompt(context_pack: str) -> str:
    return f"{SYSTEM_PROMPT}\n\n{context_pack}\n"


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
