from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitGuardError(RuntimeError):
    pass


@dataclass
class GitState:
    is_repo: bool
    clean: bool
    changed_files: list[str]


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _git_names(root: Path, *args: str) -> list[str]:
    result = _git(root, *args)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def detect_git_state(root: Path) -> GitState:
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        return GitState(False, False, [])

    changed = []
    changed.extend(_git_names(root, "diff", "--name-only"))
    changed.extend(_git_names(root, "diff", "--name-only", "--cached"))
    changed.extend(_git_names(root, "ls-files", "--others", "--exclude-standard"))
    deduped = sorted(set(changed))
    return GitState(True, len(deduped) == 0, deduped)


def ensure_clean_worktree(root: Path) -> None:
    state = detect_git_state(root)
    if not state.is_repo:
        raise GitGuardError("Git repository not found")
    if not state.clean:
        raise GitGuardError("Working tree must be clean before execution")


def validate_allowed_changes(root: Path, allowed_files: set[Path]) -> None:
    state = detect_git_state(root)
    if not state.is_repo:
        raise GitGuardError("Git repository not found")

    allowed_relative = {path.resolve().relative_to(root.resolve()) for path in allowed_files}
    unauthorized = []
    for changed in state.changed_files:
        changed_path = Path(changed)
        if changed_path not in allowed_relative:
            unauthorized.append(changed)

    if unauthorized:
        raise GitGuardError(f"Unauthorized file changes detected: {', '.join(unauthorized)}")


def git_diff(root: Path, *paths: Path) -> str:
    state = detect_git_state(root)
    if not state.is_repo:
        return ""

    rel_paths = [str(path.resolve().relative_to(root.resolve())) for path in paths]
    args = ["diff", "--"] + rel_paths if rel_paths else ["diff"]
    result = _git(root, *args)
    return result.stdout
