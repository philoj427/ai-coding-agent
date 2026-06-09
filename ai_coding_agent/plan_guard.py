from __future__ import annotations

from pathlib import Path

from .git_guard import validate_allowed_changes


def validate_plan_allowed_changes(root: Path, allowed_files: set[Path]) -> None:
    validate_allowed_changes(root, {root / path for path in allowed_files})
