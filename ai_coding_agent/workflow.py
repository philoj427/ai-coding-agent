from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

from .builder import build_prompt, generate_patch
from .candidate_selector import parse_replacement_selection
from .candidate_scorer import rank_candidates
from .context_builder import build_context_pack
from .gatekeeper import GatekeeperError, inspect_patch
from .git_guard import GitGuardError, ensure_clean_worktree, git_diff, restore_clean_worktree, validate_allowed_changes
from .local_templates import build_local_template_patch
from .patch_applier import PatchParseError, apply_search_replace_patch
from .patch_parser import parse_search_replace_patch
from .search_candidates import SearchCandidate, build_search_candidates
from .task import TaskSpec
from .test_runner import run_tests


def _classify_failure(exc: Exception) -> str:
    if isinstance(exc, GatekeeperError):
        return "gatekeeper"
    if isinstance(exc, PatchParseError):
        return "patch-parse"
    if isinstance(exc, subprocess.CalledProcessError):
        return "py_compile"
    if isinstance(exc, RuntimeError):
        return "ollama"
    if isinstance(exc, GitGuardError):
        return "git-guard"
    return "workflow"


def _write_failure_report(workspace_dir: Path, *, stage: str, reason: str, details: str | None = None) -> None:
    lines = [
        f"Stage: {stage}",
        f"Reason: {reason}",
    ]
    if details:
        lines.extend(["", details.rstrip("\n")])
    (workspace_dir / "test_result.txt").write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


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


def _compose_patch(candidate: SearchCandidate, replacement: str) -> str:
    return (
        "SEARCH\n"
        f"{candidate.text}\n"
        "END_SEARCH\n"
        "REPLACE\n"
        f"{replacement}\n"
        "END_REPLACE\n"
    )


def _replacement_prompt(prompt: str, candidate: SearchCandidate) -> str:
    return (
        f"{prompt}\n"
        "## Locally Selected Search Candidate\n"
        f"- Candidate id: `{candidate.candidate_id}`\n"
        f"- Label: `{candidate.label}`\n"
        "\n"
        "```text\n"
        f"{candidate.text}\n"
        "```\n"
        "\n"
        "Return only replacement JSON for this candidate.\n"
    )


def _generate_replacement(
    *,
    model: str,
    prompt: str,
    ollama_host: str,
    candidate: SearchCandidate,
) -> str:
    selection_response = generate_patch(model=model, prompt=prompt, ollama_host=ollama_host)
    try:
        return parse_replacement_selection(selection_response).replacement
    except Exception:
        try:
            parsed_pairs = parse_search_replace_patch(selection_response)
        except Exception as exc:
            raise ValueError("Replacement response was not valid JSON or legacy SEARCH/REPLACE") from exc
        if len(parsed_pairs) != 1:
            raise ValueError("Legacy patch response must contain exactly one SEARCH/REPLACE block")
        search_text, replacement_text = parsed_pairs[0]
        if search_text == candidate.text:
            return replacement_text
        raise ValueError("Legacy patch response did not match the locally selected search candidate")


def _generate_and_apply_patch(
    *,
    root: Path,
    target_path: Path,
    model: str,
    prompt: str,
    ollama_host: str,
    patch_path: Path,
    dry_run: bool,
    task_description: str,
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
                    "Retry instruction: use the locally selected SEARCH candidate exactly, keep the replacement minimal, preserve indentation exactly, and return valid JSON only.\n"
                )
            candidates = build_search_candidates(target_path)
            ranked_candidates = rank_candidates(task_description, candidates)
            if not ranked_candidates:
                raise RuntimeError("No local search candidates available")
            for selected_candidate in ranked_candidates:
                try:
                    replacement = _generate_replacement(
                        model=model,
                        prompt=_replacement_prompt(attempt_prompt, selected_candidate),
                        ollama_host=ollama_host,
                        candidate=selected_candidate,
                    )
                    patch_text = _compose_patch(selected_candidate, replacement)
                    patch_path.parent.mkdir(parents=True, exist_ok=True)
                    patch_path.write_text(patch_text, encoding="utf-8")
                    inspect_patch(target_path, patch_text)
                    apply_search_replace_patch(target_path, patch_text)
                    _py_compile_target(target_path)
                    _cleanup_pycache(target_path)
                    return
                except ValueError:
                    raise
                except (GatekeeperError, PatchParseError, subprocess.CalledProcessError, RuntimeError) as exc:
                    last_error = exc
                    restore_clean_worktree(root)
                    patch_path.parent.mkdir(parents=True, exist_ok=True)
                    continue
        except (GatekeeperError, PatchParseError, subprocess.CalledProcessError, RuntimeError, ValueError) as exc:
            last_error = exc
            restore_clean_worktree(root)
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            if attempt + 1 >= attempts:
                raise
        except Exception:
            raise

    if last_error is not None:
        raise last_error


def _failure_details_for_patch_error(exc: Exception) -> str | None:
    if isinstance(exc, GatekeeperError):
        return getattr(exc, "diff_preview", None) or None
    return None


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
        local_patch = build_local_template_patch(root, task)
        if local_patch and not dry_run:
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            patch_path.write_text(local_patch, encoding="utf-8")
            inspect_patch(target_path, local_patch)
            apply_search_replace_patch(target_path, local_patch)
            _py_compile_target(target_path)
            _cleanup_pycache(target_path)
        else:
            _generate_and_apply_patch(
                root=root,
                target_path=target_path,
                model=model,
                prompt=prompt,
                ollama_host=ollama_host,
                patch_path=patch_path,
                dry_run=dry_run,
                task_description=task.description,
            )
        test_result = run_tests(root, task.test_type, task.test_file, workspace_dir)
        if not test_result.passed:
            restore_clean_worktree(root)
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "git_diff.txt").write_text("", encoding="utf-8")
            _write_failure_report(
                workspace_dir,
                stage="tests",
                reason=f"Test command exited with code {test_result.exit_code}",
                details=getattr(test_result, "output", ""),
            )
            return test_result.exit_code

        validate_allowed_changes(root, {target_path})
        diff_text = git_diff(root, target_path)
        (workspace_dir / "git_diff.txt").write_text(diff_text, encoding="utf-8")
        return 0
    except (GitGuardError, GatekeeperError, PatchParseError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        try:
            restore_clean_worktree(root)
        except GitGuardError:
            pass
        except Exception:
            pass
        workspace_dir.mkdir(parents=True, exist_ok=True)
        _write_failure_report(
            workspace_dir,
            stage=_classify_failure(exc),
            reason=str(exc),
            details=_failure_details_for_patch_error(exc),
        )
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
