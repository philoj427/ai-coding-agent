from __future__ import annotations

from pathlib import Path

from .task import TaskSpec


DEFAULT_RULES = """# Coding Rules

- Use patch-based editing.
- Keep the change minimal.
- Do not overwrite whole files.
- Preserve existing behavior unless the task requires a change.
- Prefer exact SEARCH/REPLACE patches.
"""


def _read_text(path: Path) -> str:
    if not path.exists():
        return "<missing file>"
    return path.read_text(encoding="utf-8")


def build_context_pack(root: Path, task: TaskSpec, workspace_dir: Path) -> Path:
    workspace_dir.mkdir(parents=True, exist_ok=True)

    target_path = root / task.target_file
    rules_path = root / "CODING_RULES.md"

    sections = [
        "# Context Pack",
        "",
        "## Task",
        f"- Target file: `{task.target_file.as_posix()}`",
        f"- Test type: `{task.test_type}`",
        f"- Test file: `{task.test_file.as_posix() if task.test_file else 'none'}`",
        f"- Description: {task.description}",
        "",
        "## Coding Rules",
        _read_text(rules_path) if rules_path.exists() else DEFAULT_RULES,
        "",
        "## Target File",
        f"Path: `{task.target_file.as_posix()}`",
        "",
        "```text",
        _read_text(target_path),
        "```",
    ]

    if task.test_file is not None:
        test_path = root / task.test_file
        sections.extend([
            "",
            "## Related Test File",
            f"Path: `{task.test_file.as_posix()}`",
            "",
            "```text",
            _read_text(test_path),
            "```",
        ])

    sections.extend([
        "",
        "## Expected Patch Format",
        "```text",
        "SEARCH",
        "<exact old text>",
        "END_SEARCH",
        "REPLACE",
        "<new text>",
        "END_REPLACE",
        "```",
    ])

    context_path = workspace_dir / "context_pack.md"
    context_path.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    return context_path
