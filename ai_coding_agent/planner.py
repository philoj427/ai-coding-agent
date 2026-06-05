from __future__ import annotations

import json
from pathlib import Path

from .builder import generate_patch
from .candidate_selector import _strip_code_fences
from .task_plan import TaskPlan


def _project_summary(root: Path) -> str:
    paths: list[str] = []
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or "workspace" in path.parts or "__pycache__" in path.parts:
            continue
        if path.is_file() and path.suffix in {".py", ".md", ".txt", ".json"}:
            paths.append(path.relative_to(root).as_posix())
        if len(paths) >= 80:
            break
    return "\n".join(paths)


def _fallback_plan(root: Path, description: str) -> TaskPlan | None:
    lowered = description.lower()
    if "add" in lowered and (root / "demo_add.py").exists():
        test_type = "unittest" if (root / "tests" / "test_demo_add.py").exists() else "none"
        test_file = "tests/test_demo_add.py" if test_type == "unittest" else None
        return TaskPlan.from_dict(
            {
                "target_file": "demo_add.py",
                "test_type": test_type,
                "test_file": test_file,
                "risk_level": "low",
                "reason": "The request refers to add(), which is implemented in demo_add.py.",
                "allowed_files": ["demo_add.py"],
                "forbidden_files": ["ai_coding_agent/", ".gitignore", "README.md"],
            },
            description,
        )
    return None


def _planner_prompt(root: Path, description: str) -> str:
    return (
        "Create a single-file task plan as JSON only.\n"
        "No markdown fences. No explanations outside JSON.\n"
        "V1.7 supports exactly one target file and one allowed file.\n"
        "Use test_type one of: pytest, unittest, npm, none.\n"
        "Use risk_level one of: low, medium, high.\n"
        "Required JSON keys: target_file, test_type, test_file, risk_level, reason, allowed_files, forbidden_files.\n"
        "\n"
        "Project files:\n"
        f"{_project_summary(root)}\n"
        "\n"
        f"User task: {description}\n"
    )


def _extract_json(text: str) -> str:
    stripped = _strip_code_fences(text).strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return stripped[start : end + 1]
    raise ValueError("Planner response did not contain a JSON object")


def plan_task(root: Path, description: str, model: str, ollama_host: str) -> TaskPlan:
    fallback = _fallback_plan(root, description)
    if fallback is not None:
        return fallback
    try:
        response = generate_patch(model=model, prompt=_planner_prompt(root, description), ollama_host=ollama_host)
        payload = json.loads(_extract_json(response))
        return TaskPlan.from_dict(payload, description)
    except Exception:
        raise
