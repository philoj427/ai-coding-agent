from __future__ import annotations

import json
from pathlib import Path

from .builder import generate_patch
from .candidate_selector import _strip_code_fences
from .project_index import ProjectIndex, scan_project
from .task_plan import TaskPlan


def load_or_build_project_index(root: Path, workspace_dir: Path) -> ProjectIndex:
    index_path = workspace_dir / "project_index.json"
    if index_path.exists():
        return ProjectIndex.from_file(index_path)
    index = scan_project(root)
    index.write(index_path)
    return index


def _rule_based_plan(index: ProjectIndex, description: str) -> TaskPlan | None:
    lowered = description.lower()
    protected = set(index.protected_files)
    for item in index.files:
        path_stem = Path(item.path).stem.lower()
        if item.path in protected or item.risk == "high":
            if item.path.lower() in lowered or path_stem in lowered:
                return TaskPlan.from_dict(
                    {
                        "target_file": item.path,
                        "test_type": "none",
                        "test_file": None,
                        "risk_level": "high",
                        "reason": f"Task targets protected or high-risk file {item.path}. Plan-only mode required.",
                        "allowed_files": [item.path],
                        "forbidden_files": list(index.protected_files),
                    },
                    description,
                )
    candidates = [
        item
        for item in index.files
        if item.risk != "high"
        and item.path not in protected
        and not item.type.endswith("_test")
        and item.type not in {"documentation"}
    ]

    scored: list[tuple[int, object]] = []
    for item in candidates:
        score = 0
        for symbol in item.symbols:
            if symbol.lower() in lowered:
                score += 10
        if item.path.lower() in lowered or Path(item.path).stem.lower() in lowered:
            score += 6
        for word in lowered.replace("_", " ").split():
            if len(word) > 2 and word in item.summary.lower():
                score += 1
        if score:
            scored.append((score, item))

    if not scored:
        return None

    scored.sort(key=lambda pair: (-pair[0], pair[1].path))
    best = scored[0][1]
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None

    test_file = best.tests[0] if best.tests else None
    test_type = "unittest" if test_file and test_file.endswith(".py") else "none"
    if test_file and test_file.endswith((".js", ".ts", ".jsx", ".tsx")):
        test_type = "npm"
    return TaskPlan.from_dict(
        {
            "target_file": best.path,
            "test_type": test_type,
            "test_file": test_file,
            "risk_level": best.risk,
            "reason": f"Task matched indexed symbols or path for {best.path}.",
            "allowed_files": [best.path],
            "forbidden_files": list(index.protected_files),
        },
        description,
    )


def _fallback_plan(root: Path, index: ProjectIndex, description: str) -> TaskPlan | None:
    plan = _rule_based_plan(index, description)
    if plan is not None:
        return plan
    lowered = description.lower()
    if "add" in lowered and (root / "demo_add.py").exists():
        test_match = next((item.tests[0] for item in index.files if item.path == "demo_add.py" and item.tests), None)
        test_type = "unittest" if test_match else "none"
        return TaskPlan.from_dict(
            {
                "target_file": "demo_add.py",
                "test_type": test_type,
                "test_file": test_match,
                "risk_level": "low",
                "reason": "The request refers to add(), which is implemented in demo_add.py.",
                "allowed_files": ["demo_add.py"],
                "forbidden_files": list(index.protected_files),
            },
            description,
        )
    return None


def _planner_prompt(index: ProjectIndex, description: str) -> str:
    return (
        "Create a single-file task plan as JSON only.\n"
        "No markdown fences. No explanations outside JSON.\n"
        "V1.8 supports exactly one target file and one allowed file.\n"
        "Use test_type one of: pytest, unittest, npm, none.\n"
        "Use risk_level one of: low, medium, high.\n"
        "Required JSON keys: target_file, test_type, test_file, risk_level, reason, allowed_files, forbidden_files.\n"
        "Only choose target_file from project_index.files.\n"
        "Do not choose protected files.\n"
        "\n"
        "Project index:\n"
        f"{json.dumps(index.to_dict(), indent=2, sort_keys=True)}\n"
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


def plan_task(root: Path, description: str, model: str, ollama_host: str, workspace_dir: Path | None = None) -> TaskPlan:
    workspace = workspace_dir if workspace_dir is not None else root / "workspace"
    index = load_or_build_project_index(root, workspace)
    fallback = _fallback_plan(root, index, description)
    if fallback is not None:
        return fallback
    try:
        response = generate_patch(model=model, prompt=_planner_prompt(index, description), ollama_host=ollama_host)
        payload = json.loads(_extract_json(response))
        return TaskPlan.from_dict(payload, description)
    except Exception:
        raise
