from __future__ import annotations

import json
from pathlib import Path

from .change_plan import ChangePlan
from .git_guard import GitGuardError, git_diff, restore_clean_worktree
from .plan_guard import validate_plan_allowed_changes
from .plan_validator import PlanValidationError, validate_change_plan
from .test_runner import run_tests
from .workflow import run_workflow


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_failure(workspace_dir: Path, stage: str, reason: str) -> None:
    (workspace_dir / "test_result.txt").write_text(f"Stage: {stage}\nReason: {reason}\n", encoding="utf-8")
    _write_json(workspace_dir / "result.json", {"status": "change_plan_failed", "stage": stage, "reason": reason})


def _step_task_text(step) -> str:
    test_file = step.test_file.as_posix() if step.test_file else "none"
    return f"{step.target_file.as_posix()} | {step.test_type} | {test_file} | {step.intent}\n"


def _cleanup_repo_pycache(root: Path) -> None:
    for pycache_dir in root.rglob("__pycache__"):
        for pyc_path in pycache_dir.glob("*.pyc"):
            pyc_path.unlink()
        try:
            pycache_dir.rmdir()
        except OSError:
            pass


def run_change_plan(
    root: Path,
    plan_path: Path,
    workspace_dir: Path,
    model: str,
    ollama_host: str,
    dry_run: bool = False,
) -> int:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    try:
        plan = ChangePlan.from_file(plan_path)
        validate_change_plan(root, plan)
    except (OSError, json.JSONDecodeError, KeyError, PlanValidationError, ValueError) as exc:
        _write_failure(workspace_dir, "change-plan", str(exc))
        return 1

    (workspace_dir / "change_plan.json").write_text(
        json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    completed_files: set[Path] = set()
    step_results: list[dict[str, object]] = []
    try:
        for step in plan.steps:
            step_workspace = workspace_dir / "steps" / step.step_id
            step_workspace.mkdir(parents=True, exist_ok=True)
            step_task_path = step_workspace / "task.txt"
            step_task_path.write_text(_step_task_text(step), encoding="utf-8")

            exit_code = run_workflow(
                root=root,
                task_path=step_task_path,
                workspace_dir=step_workspace,
                model=model,
                ollama_host=ollama_host,
                dry_run=dry_run,
                base_allowed_files=completed_files,
            )
            step_results.append(
                {
                    "step_id": step.step_id,
                    "target_file": step.target_file.as_posix(),
                    "exit_code": exit_code,
                    "status": "passed" if exit_code == 0 else "failed",
                }
            )
            if exit_code != 0:
                restore_clean_worktree(root)
                _write_json(
                    workspace_dir / "result.json",
                    {"status": "change_plan_failed", "stage": step.step_id, "steps": step_results},
                )
                return exit_code
            completed_files.add(step.target_file)

        final_result = run_tests(root, plan.final_test_type, plan.final_test_file, workspace_dir)
        if not final_result.passed:
            restore_clean_worktree(root)
            _write_json(
                workspace_dir / "result.json",
                {
                    "status": "change_plan_failed",
                    "stage": "full-tests",
                    "exit_code": final_result.exit_code,
                    "steps": step_results,
                },
            )
            return final_result.exit_code

        _cleanup_repo_pycache(root)
        validate_plan_allowed_changes(root, plan.allowed_files)
        diff_text = git_diff(root, *[root / path for path in sorted(plan.allowed_files)])
        (workspace_dir / "git_diff.txt").write_text(diff_text, encoding="utf-8")
        _write_json(
            workspace_dir / "result.json",
            {
                "status": "change_plan_applied",
                "changed_files": sorted(path.as_posix() for path in plan.allowed_files),
                "steps": step_results,
            },
        )
        return 0
    except (GitGuardError, RuntimeError, ValueError) as exc:
        try:
            restore_clean_worktree(root)
        except Exception:
            pass
        _write_failure(workspace_dir, "change-plan-runner", str(exc))
        return 1
