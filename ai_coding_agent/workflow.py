from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from .builder import build_prompt, generate_patch
from .context_builder import build_context_pack
from .git_guard import GitGuardError, ensure_clean_worktree, git_diff, restore_clean_worktree, validate_allowed_changes
from .patch_applier import PatchParseError, apply_search_replace_patch
from .task import TaskSpec
from .test_runner import run_tests


def _py_compile_target(target_path: Path) -> None:
    if target_path.suffix != ".py":
        return
    subprocess.run([sys.executable, "-m", "py_compile", str(target_path)], check=True, capture_output=True, text=True)


def _cleanup_pycache(target_path: Path) -> None:
    if target_path.suffix != ".py":
        return
    pyc_path = Path(importlib.util.cache_from_source(str(target_path)))
    if pyc_path.exists():
        pyc_path.unlink()
    pycache_dir = pyc_path.parent
    try:
        pycache_dir.rmdir()
    except OSError:
        pass


def _generate_and_apply_patch(
    *,
    root: Path,
    target_path: Path,
    model: str,
    prompt: str,
    ollama_host: str,
    patch_path: Path,
    dry_run: bool,
    retry_on_failure: bool = True,
) -> None:
    attempts = 2 if retry_on_failure else 1
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            if dry_run:
                return

            attempt_prompt = prompt
            if attempt > 0:
                attempt_prompt = (
                    f"{prompt}\n"
                    "Retry instruction: preserve indentation exactly and output only a valid SEARCH/REPLACE patch.\n"
                )
            patch_text = generate_patch(model=model, prompt=attempt_prompt, ollama_host=ollama_host)
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            patch_path.write_text(patch_text, encoding="utf-8")
            apply_search_replace_patch(target_path, patch_text)
            _py_compile_target(target_path)
            _cleanup_pycache(target_path)
            return
        except (PatchParseError, subprocess.CalledProcessError) as exc:
            last_error = exc
            restore_clean_worktree(root)
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            if attempt + 1 >= attempts:
                raise
        except Exception:
            raise

    if last_error is not None:
        raise last_error


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

    try:
        target_path = (root / task.target_file).resolve()
        _generate_and_apply_patch(
            root=root,
            target_path=target_path,
            model=model,
            prompt=prompt,
            ollama_host=ollama_host,
            patch_path=patch_path,
            dry_run=dry_run,
        )
        test_result = run_tests(root, task.test_type, task.test_file, workspace_dir)
        if not test_result.passed:
            restore_clean_worktree(root)
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "git_diff.txt").write_text("", encoding="utf-8")
            return test_result.exit_code

        validate_allowed_changes(root, {target_path})
        diff_text = git_diff(root, target_path)
        (workspace_dir / "git_diff.txt").write_text(diff_text, encoding="utf-8")
        return 0
    except (GitGuardError, PatchParseError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        try:
            restore_clean_worktree(root)
        except GitGuardError:
            pass
        except Exception:
            pass
        workspace_dir.mkdir(parents=True, exist_ok=True)
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
