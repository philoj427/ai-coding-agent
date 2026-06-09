from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
RESULTS_DIR = WORKSPACE / "pressure_v20_results"
REPORT_PATH = WORKSPACE / "pressure_v20_report.md"


@dataclass(frozen=True)
class PressureCase:
    name: str
    mode: str
    expected: str
    payload: str | dict[str, Any]


def _single_tasks() -> list[str]:
    return [
        "Rewrite the module docstring for the add helper in a concise style while keeping behavior unchanged.",
        "Update add() function docstring to mention non-numeric inputs raise TypeError.",
        "Add a short comment above add() validation explaining both inputs must be numeric.",
        "Add a short comment above add() return statement explaining it returns the computed sum.",
        "Introduce a local variable named total inside add() and return it.",
        "Rename the local total variable in add() to result.",
        "Change the TypeError message in add() to be shorter and direct.",
        "Split add() validation across multiple readable lines.",
        "Rewrite add() validation using all(...) over the two inputs.",
        "Refactor add() to assign validation result to a variable before raising TypeError.",
        "Add a module-level NUMERIC_TYPES constant for add() validation.",
        "Introduce a Numeric type alias and use it in add() signature.",
        "Add a module-level __all__ declaration that exports add.",
        "Add a module-level __version__ string.",
        "Extract add() numeric check into _is_numeric(value).",
        "Rename _is_numeric(value) to _is_number(value).",
        "Extract add() validation into _validate_numbers(a, b).",
        "Add a docstring to _validate_numbers().",
        "Add type annotations to _validate_numbers().",
        "Extract add() addition expression into _sum(a, b).",
        "Add a docstring to _sum().",
        "Add type annotations to _sum().",
        "Replace inline add() validation with a bool-returning helper.",
        "Introduce _raise_numeric_type_error() and call it from add().",
        "Add a zero-division guard to divide().",
        "Add a docstring to divide() explaining it divides a by b.",
        "Add type annotations to divide().",
        "Introduce a local quotient variable in divide() and return it.",
        "Add a module-level __all__ declaration that exports divide.",
        "Extract divide() divisor validation into _validate_divisor(b) and call it from divide().",
    ]


def _change_plan(task: str, steps: list[dict[str, Any]], final_test_type: str = "unittest") -> dict[str, Any]:
    return {
        "task": task,
        "steps": steps,
        "final_test_type": final_test_type,
        "final_test_file": "tests/test_math_tool.py" if final_test_type == "unittest" else None,
    }


def _source_step(step_id: str, intent: str) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "target_file": "math_tool.py",
        "intent": intent,
        "allowed_change": "production_code",
        "test_type": "unittest",
        "test_file": "tests/test_math_tool.py",
    }


def _test_step(step_id: str, intent: str) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "target_file": "tests/test_math_tool.py",
        "intent": intent,
        "allowed_change": "test_code",
        "test_type": "unittest",
        "test_file": "tests/test_math_tool.py",
    }


def _cases() -> list[PressureCase]:
    cases: list[PressureCase] = [
        PressureCase(f"single-file {index:02d}", "single", "PASS_PATCH", task)
        for index, task in enumerate(_single_tasks(), start=1)
    ]
    change_plans = [
        _change_plan("Add divide zero guard and tests", [_source_step("S1", "Add a zero-division guard to divide()."), _test_step("S2", "Add a test for divide by zero.")]),
        _change_plan("Add divide type hints and zero-divisor test", [_source_step("S1", "Add type annotations and a zero-division guard to divide()."), _test_step("S2", "Add a test for divide by zero.")]),
        _change_plan("Add divide docstring guard and zero-divisor test", [_source_step("S1", "Add a docstring and a zero-division guard to divide()."), _test_step("S2", "Add a test for divide by zero.")]),
        _change_plan("Extract divisor validation and test zero divisor", [_source_step("S1", "Extract divide() divisor validation into _validate_divisor(b) and call it from divide()."), _test_step("S2", "Add a test for divide by zero.")]),
        _change_plan("Add source export guard and import-oriented test", [_source_step("S1", "Add a module-level __all__ declaration and a zero-division guard for divide."), _test_step("S2", "Add a test for divide by zero.")]),
        _change_plan("Three-step guard docstring and test", [_source_step("S1", "Add a zero-division guard to divide()."), _source_step("S2", "Rewrite divide() docstring to mention b must not be zero."), _test_step("S3", "Add a test for divide by zero.")]),
        _change_plan("Three-step type hints quotient and test", [_source_step("S1", "Add type annotations and a zero-division guard to divide()."), _source_step("S2", "Introduce a local quotient variable in divide() and return it."), _test_step("S3", "Add a test for divide by zero.")]),
        _change_plan("Three-step helper extraction and test", [_source_step("S1", "Extract divide() divisor validation into _validate_divisor(b) and call it from divide()."), _source_step("S2", "Add a docstring to divide() explaining it divides a by b."), _test_step("S3", "Add a test for divide by zero.")]),
        _change_plan("Three-step two-file guard export and test", [_source_step("S1", "Add a zero-division guard to divide()."), _source_step("S2", "Add a module-level __all__ declaration that exports divide."), _test_step("S3", "Add a test for divide by zero.")]),
        _change_plan("Three-step single-file steps across source and test", [_source_step("S1", "Add type annotations and a zero-division guard to divide()."), _source_step("S2", "Rewrite divide() docstring to mention b must not be zero."), _test_step("S3", "Add a test for divide by zero.")]),
    ]
    cases.extend(
        PressureCase(f"change-plan {index:02d}", "change_plan", "PASS_CHANGE_PLAN", plan)
        for index, plan in enumerate(change_plans, start=31)
    )
    plan_only_tasks = [
        "Modify README.md to document the whole planner workflow.",
        "Refactor ai_coding_agent/workflow.py to support multi-file editing.",
        "Change ai_coding_agent/git_guard.py to loosen protected-file checks.",
        "Plan a repository-wide rename from add to add_numbers.",
        "Plan a feature that needs both math_tool.py and demo_add.py to change.",
    ]
    cases.extend(
        PressureCase(f"plan-only {index:02d}", "single", "PASS_PLAN_ONLY", task)
        for index, task in enumerate(plan_only_tasks, start=41)
    )
    reject_plans = [
        _change_plan("Reject protected file", [{**_source_step("S1", "Change workflow"), "target_file": "ai_coding_agent/workflow.py"}], "none"),
        _change_plan("Reject four steps", [_source_step("S1", "Add a zero-division guard to divide()."), _source_step("S2", "Add type annotations to divide()."), _source_step("S3", "Introduce a local quotient variable in divide()."), _test_step("S4", "Add a test for divide by zero.")]),
        _change_plan(
            "Reject four files",
            [
                {**_source_step("S1", "Change app"), "target_file": "demo_add.py"},
                _source_step("S2", "Add a zero-division guard to divide()."),
                _test_step("S3", "Add a test for divide by zero."),
                {**_test_step("S4", "Change demo test"), "target_file": "tests/test_demo_add.py", "test_file": "tests/test_demo_add.py"},
            ],
        ),
        _change_plan("Reject test file marked production", [{**_test_step("S1", "Add a test for divide by zero."), "allowed_change": "production_code"}]),
    ]
    cases.extend(
        PressureCase(f"reject {index:02d}", "change_plan", "PASS_REJECT", plan)
        for index, plan in enumerate(reject_plans, start=46)
    )
    rollback_plan = _change_plan(
        "Rollback after valid step then invalid final test",
        [_source_step("S1", "Add a zero-division guard to divide().")],
        final_test_type="npm",
    )
    cases.append(PressureCase("rollback 50", "change_plan", "PASS_ROLLBACK", rollback_plan))
    return cases


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def _git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True, check=check)


def _reset_repo() -> None:
    _git(["reset", "--hard", "HEAD"])
    _git(["clean", "-fd"])


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _run_case(case: PressureCase) -> tuple[subprocess.CompletedProcess[str], dict[str, Any], str]:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    if case.mode == "single":
        task_path = WORKSPACE / "task.txt"
        task_path.write_text(str(case.payload) + "\n", encoding="utf-8")
        proc = _run(["python", ".\\agent.py", "--root", ".", "--task", "workspace\\task.txt", "--model", "qwen2.5-coder:7b"])
    else:
        plan_path = WORKSPACE / "change_plan.json"
        plan_path.write_text(json.dumps(case.payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        proc = _run(["python", ".\\agent.py", "--root", ".", "--change-plan", "workspace\\change_plan.json", "--model", "qwen2.5-coder:7b"])
    result = _read_json(WORKSPACE / "result.json")
    diff_text = (WORKSPACE / "git_diff.txt").read_text(encoding="utf-8") if (WORKSPACE / "git_diff.txt").exists() else ""
    return proc, result, diff_text


def _classify(case: PressureCase, proc: subprocess.CompletedProcess[str], result: dict[str, Any], diff_text: str) -> str:
    status = str(result.get("status", ""))
    if case.expected == "PASS_PATCH":
        return "PASS_PATCH" if proc.returncode == 0 and status == "patch_applied" and diff_text.strip() else "FAIL"
    if case.expected == "PASS_CHANGE_PLAN":
        return "PASS_CHANGE_PLAN" if proc.returncode == 0 and status == "change_plan_applied" and diff_text.strip() else "FAIL"
    if case.expected == "PASS_PLAN_ONLY":
        return "PASS_PLAN_ONLY" if proc.returncode == 0 and status == "plan_only" and not diff_text.strip() else "FAIL"
    if case.expected == "PASS_REJECT":
        return "PASS_REJECT" if proc.returncode != 0 and status == "change_plan_failed" and not _git(["diff", "--name-only"]).stdout.strip() else "FAIL"
    if case.expected == "PASS_ROLLBACK":
        return "PASS_ROLLBACK" if proc.returncode != 0 and status == "change_plan_failed" and not _git(["diff", "--name-only"]).stdout.strip() else "FAIL"
    return "FAIL"


def main() -> int:
    original_head = _git(["rev-parse", "HEAD"]).stdout.strip()
    cases = _cases()
    report_lines = ["# V2.0 Pressure Test Report", "", f"Total cases: {len(cases)}", ""]
    counts: dict[str, int] = {
        "PASS_PATCH": 0,
        "PASS_CHANGE_PLAN": 0,
        "PASS_PLAN_ONLY": 0,
        "PASS_REJECT": 0,
        "PASS_ROLLBACK": 0,
        "FAIL": 0,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for index, case in enumerate(cases, start=1):
        case_dir = RESULTS_DIR / f"case_{index:02d}"
        case_dir.mkdir(parents=True, exist_ok=True)
        proc, result, diff_text = _run_case(case)
        actual = _classify(case, proc, result, diff_text)
        counts[actual] = counts.get(actual, 0) + 1

        for filename in ("result.json", "git_diff.txt", "test_result.txt", "task_plan.json", "change_plan.json"):
            src = WORKSPACE / filename
            if src.exists():
                (case_dir / filename).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        (case_dir / "stdout.txt").write_text(proc.stdout or "", encoding="utf-8")
        (case_dir / "stderr.txt").write_text(proc.stderr or "", encoding="utf-8")

        report_lines.extend(
            [
                f"## Case {index}",
                "",
                f"- Name: {case.name}",
                f"- Mode: {case.mode}",
                f"- Expected: {case.expected}",
                f"- Actual: {actual}",
                f"- Exit code: {proc.returncode}",
                f"- Result status: {result.get('status', '')}",
                f"- Code diff: {'yes' if diff_text.strip() else 'no'}",
                "",
            ]
        )
        _reset_repo()

    report_lines.extend(["## Summary", ""])
    for key in ("PASS_PATCH", "PASS_CHANGE_PLAN", "PASS_PLAN_ONLY", "PASS_REJECT", "PASS_ROLLBACK", "FAIL"):
        report_lines.append(f"- {key}: {counts.get(key, 0)}")
    report_lines.append("")
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    _git(["reset", "--hard", original_head])
    _git(["clean", "-fd"])
    print(f"Wrote {REPORT_PATH}")
    for key in ("PASS_PATCH", "PASS_CHANGE_PLAN", "PASS_PLAN_ONLY", "PASS_REJECT", "PASS_ROLLBACK", "FAIL"):
        print(f"{key}: {counts.get(key, 0)}")
    return 0 if counts.get("FAIL", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
