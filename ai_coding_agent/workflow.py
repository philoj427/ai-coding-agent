from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build_prompt, generate_patch
from .context_builder import build_context_pack
from .git_guard import GitGuardError, ensure_clean_worktree, git_diff, validate_allowed_changes
from .patch_applier import PatchParseError, apply_search_replace_patch, restore_text
from .task import TaskSpec
from .test_runner import run_tests


def run_workflow(root: Path, task_path: Path, workspace_dir: Path, model: str, ollama_host: str, dry_run: bool = False) -> int:
    task = TaskSpec.from_file(task_path)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    ensure_clean_worktree(root)

    context_path = build_context_pack(root, task, workspace_dir)
    context_text = context_path.read_text(encoding="utf-8")
    prompt = build_prompt(context_text)

    patch_text = ""
    patch_path = workspace_dir / "search_replace.patch"
    patch_path.write_text("", encoding="utf-8")

    if not dry_run:
        patch_text = generate_patch(model=model, prompt=prompt, ollama_host=ollama_host)
        patch_path.write_text(patch_text, encoding="utf-8")

    target_path = (root / task.target_file).resolve()
    original_text = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    try:
        if not dry_run:
            apply_search_replace_patch(target_path, patch_text)
        test_result = run_tests(root, task.test_type, task.test_file, workspace_dir)
        if not test_result.passed:
            restore_text(target_path, original_text)
            (workspace_dir / "git_diff.txt").write_text("", encoding="utf-8")
            return test_result.exit_code

        validate_allowed_changes(root, {target_path})
        diff_text = git_diff(root, target_path)
        (workspace_dir / "git_diff.txt").write_text(diff_text, encoding="utf-8")
        return 0
    except (GitGuardError, PatchParseError, RuntimeError, ValueError) as exc:
        restore_text(target_path, original_text)
        (workspace_dir / "test_result.txt").write_text(f"{exc}\n", encoding="utf-8")
        (workspace_dir / "git_diff.txt").write_text("", encoding="utf-8")
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Coding Agent V1.35 prototype")
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", default="task.txt")
    parser.add_argument("--workspace", default="workspace")
    parser.add_argument("--model", default="qwen2.5-coder:7b")
    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    task_path = (root / args.task).resolve()
    workspace_dir = (root / args.workspace).resolve()
    return run_workflow(root, task_path, workspace_dir, args.model, args.ollama_host, args.dry_run)
