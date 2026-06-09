from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
TASK_FILE = WORKSPACE / "task.txt"
RESULTS_DIR = WORKSPACE / "pressure_results"
REPORT_PATH = WORKSPACE / "pressure_test_report.md"


def read_tasks(tasks_path: Path) -> list[str]:
    tasks: list[str] = []
    for raw_line in tasks_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tasks.append(raw_line)
    return tasks


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, **kwargs)


def reset_repo() -> None:
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=str(ROOT), check=True, capture_output=True, text=True)
    subprocess.run(["git", "clean", "-fd"], cwd=str(ROOT), check=True, capture_output=True, text=True)


def git_stdout(args: list[str]) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT), check=True, capture_output=True, text=True).stdout.strip()


def checkpoint(index: int) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(ROOT), check=True, capture_output=True, text=True)
    status = git_stdout(["status", "--porcelain"])
    if status:
        subprocess.run(
            ["git", "commit", "-m", f"pressure checkpoint {index:02d}"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        )


def parse_failure_report(text: str) -> tuple[str, str]:
    stage = ""
    reason = ""
    for line in text.splitlines():
        if line.startswith("Stage:"):
            stage = line.split(":", 1)[1].strip()
        elif line.startswith("Reason:"):
            reason = line.split(":", 1)[1].strip()
    return stage, reason


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run pressure tasks.")
    parser.add_argument("--tasks", default="pressure_tasks.txt", help="Task list file to run.")
    parser.add_argument("--sequence", action="store_true", help="Keep successful task changes as temporary checkpoints.")
    args = parser.parse_args(argv)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    tasks_path = (ROOT / args.tasks).resolve()
    tasks = read_tasks(tasks_path)
    original_head = git_stdout(["rev-parse", "HEAD"])

    report_lines = [
        "# Pressure Test Report",
        "",
        f"Total tasks: {len(tasks)}",
        f"Tasks file: {tasks_path.relative_to(ROOT).as_posix()}",
        "",
    ]

    pass_count = 0
    fail_count = 0

    for index, task in enumerate(tasks, start=1):
        task_dir = RESULTS_DIR / f"task_{index:02d}"
        task_dir.mkdir(parents=True, exist_ok=True)

        TASK_FILE.write_text(task + "\n", encoding="utf-8")

        proc = run(["python", ".\\agent.py", "--root", ".", "--task", "workspace\\task.txt", "--model", "qwen2.5-coder:7b"])
        exit_code = proc.returncode

        test_result_path = WORKSPACE / "test_result.txt"
        git_diff_path = WORKSPACE / "git_diff.txt"
        patch_path = WORKSPACE / "search_replace.patch"

        if test_result_path.exists():
            (task_dir / "test_result.txt").write_text(test_result_path.read_text(encoding="utf-8"), encoding="utf-8")
        if git_diff_path.exists():
            (task_dir / "git_diff.txt").write_text(git_diff_path.read_text(encoding="utf-8"), encoding="utf-8")
        if patch_path.exists():
            (task_dir / "search_replace.patch").write_text(patch_path.read_text(encoding="utf-8"), encoding="utf-8")

        stage = ""
        reason = ""
        if test_result_path.exists():
            stage, reason = parse_failure_report(test_result_path.read_text(encoding="utf-8"))

        status = "PASS" if exit_code == 0 else "FAIL"
        if status == "PASS":
            pass_count += 1
        else:
            fail_count += 1

        report_lines.extend(
            [
                f"## Task {index}",
                "",
                f"- Status: {status}",
                f"- Exit code: {exit_code}",
                f"- Task: {task}",
            ]
        )
        if stage:
            report_lines.append(f"- Stage: {stage}")
        if reason:
            report_lines.append(f"- Reason: {reason}")
        if proc.stdout or proc.stderr:
            combined = (proc.stdout or "") + (proc.stderr or "")
            report_lines.append(f"- Agent output: {combined.strip()}")
        report_lines.append("")

        if args.sequence:
            if status == "PASS":
                checkpoint(index)
            else:
                reset_repo()
        else:
            reset_repo()

    report_lines.extend(
        [
            "## Summary",
            "",
            f"- Passed: {pass_count}",
            f"- Failed: {fail_count}",
            "",
        ]
    )

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    if args.sequence:
        subprocess.run(["git", "reset", "--hard", original_head], cwd=str(ROOT), check=True, capture_output=True, text=True)
        subprocess.run(["git", "clean", "-fd"], cwd=str(ROOT), check=True, capture_output=True, text=True)
    print(f"Wrote {REPORT_PATH}")
    print(f"Passed: {pass_count}, Failed: {fail_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
