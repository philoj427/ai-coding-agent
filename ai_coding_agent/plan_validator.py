from __future__ import annotations

from pathlib import Path

from .task_plan import TaskPlan


class PlanValidationError(ValueError):
    pass


VALID_TEST_TYPES = {"pytest", "unittest", "npm", "none"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


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
