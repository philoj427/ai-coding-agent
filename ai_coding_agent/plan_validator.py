from __future__ import annotations

from pathlib import Path

from .change_plan import ChangePlan
from .task_plan import TaskPlan


class PlanValidationError(ValueError):
    pass


VALID_TEST_TYPES = {"pytest", "unittest", "npm", "none"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}
ALLOWED_CHANGE_TYPES = {"production_code", "test_code", "documentation"}
MAX_CHANGE_STEPS = 3
MAX_CHANGE_FILES = 3


def _inside_root(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_plan(root: Path, plan: TaskPlan) -> None:
    target_path = root / plan.target_file
    if not _inside_root(root, target_path):
        raise PlanValidationError("target_file must stay inside repo root")
    if not target_path.exists():
        raise PlanValidationError(f"target_file does not exist: {plan.target_file.as_posix()}")
    if not target_path.is_file():
        raise PlanValidationError(f"target_file is not a file: {plan.target_file.as_posix()}")
    if plan.test_type not in VALID_TEST_TYPES:
        raise PlanValidationError(f"test_type is not supported: {plan.test_type}")
    if plan.test_file is not None:
        test_path = root / plan.test_file
        if not _inside_root(root, test_path):
            raise PlanValidationError("test_file must stay inside repo root")
        if not test_path.exists():
            raise PlanValidationError(f"test_file does not exist: {plan.test_file.as_posix()}")
    if not plan.allowed_files:
        raise PlanValidationError("allowed_files must not be empty")
    if plan.target_file not in plan.allowed_files:
        raise PlanValidationError("target_file must be listed in allowed_files")
    if len(plan.allowed_files) != 1:
        raise PlanValidationError("V1.9 supports exactly one allowed file")
    if plan.risk_level not in ALLOWED_RISK_LEVELS:
        raise PlanValidationError(f"risk_level is not supported: {plan.risk_level}")


def requires_plan_only(plan: TaskPlan) -> bool:
    return plan.risk_level == "high"


def _is_protected_path(path: Path) -> bool:
    normalized = path.as_posix()
    return normalized in {
        ".gitignore",
        "README.md",
        "ai_coding_agent/git_guard.py",
        "ai_coding_agent/workflow.py",
    } or normalized.startswith("ai_coding_agent/")


def _is_test_path(path: Path) -> bool:
    return path.name.startswith("test_") or "tests" in path.parts


def validate_change_plan(root: Path, plan: ChangePlan) -> None:
    if not plan.steps:
        raise PlanValidationError("change_plan must contain at least one step")
    if len(plan.steps) > MAX_CHANGE_STEPS:
        raise PlanValidationError(f"V2.0 supports at most {MAX_CHANGE_STEPS} steps")
    if len(plan.allowed_files) > MAX_CHANGE_FILES:
        raise PlanValidationError(f"V2.0 supports at most {MAX_CHANGE_FILES} files")
    if plan.final_test_type not in VALID_TEST_TYPES:
        raise PlanValidationError(f"final_test_type is not supported: {plan.final_test_type}")
    if plan.final_test_file is not None:
        final_test_path = root / plan.final_test_file
        if not _inside_root(root, final_test_path):
            raise PlanValidationError("final_test_file must stay inside repo root")
        if not final_test_path.exists():
            raise PlanValidationError(f"final_test_file does not exist: {plan.final_test_file.as_posix()}")

    seen_ids: set[str] = set()
    for step in plan.steps:
        if not step.step_id:
            raise PlanValidationError("step_id must not be empty")
        if step.step_id in seen_ids:
            raise PlanValidationError(f"duplicate step_id: {step.step_id}")
        seen_ids.add(step.step_id)

        target_path = root / step.target_file
        if not _inside_root(root, target_path):
            raise PlanValidationError("step target_file must stay inside repo root")
        if not target_path.exists():
            raise PlanValidationError(f"step target_file does not exist: {step.target_file.as_posix()}")
        if not target_path.is_file():
            raise PlanValidationError(f"step target_file is not a file: {step.target_file.as_posix()}")
        if _is_protected_path(step.target_file):
            raise PlanValidationError(f"protected file is not allowed in V2.0 change_plan: {step.target_file.as_posix()}")
        if step.allowed_change not in ALLOWED_CHANGE_TYPES:
            raise PlanValidationError(f"allowed_change is not supported: {step.allowed_change}")
        if step.allowed_change == "test_code" and not _is_test_path(step.target_file):
            raise PlanValidationError("test_code steps must target a test file")
        if step.allowed_change == "production_code" and _is_test_path(step.target_file):
            raise PlanValidationError("production_code steps must not target a test file")
        if step.test_type not in VALID_TEST_TYPES:
            raise PlanValidationError(f"step test_type is not supported: {step.test_type}")
        if step.test_file is not None:
            test_path = root / step.test_file
            if not _inside_root(root, test_path):
                raise PlanValidationError("step test_file must stay inside repo root")
            if not test_path.exists():
                raise PlanValidationError(f"step test_file does not exist: {step.test_file.as_posix()}")
