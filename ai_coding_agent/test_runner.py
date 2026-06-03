from __future__ import annotations

import subprocess
import sys
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    test_type: str
    exit_code: int
    output: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def run_tests(root: Path, test_type: str, test_file: Path | None, workspace_dir: Path) -> TestResult:
    test_type = test_type.lower()
    if test_type == "none":
        result = TestResult(test_type, 0, "No tests configured.\n")
        (workspace_dir / "test_result.txt").write_text(result.output, encoding="utf-8")
        return result

    if test_type == "pytest":
        if shutil.which("pytest") is not None:
            cmd = [sys.executable, "-m", "pytest"]
            if test_file is not None:
                cmd.append(str((root / test_file).resolve()))
        else:
            cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
            if test_file is not None:
                cmd.extend(["-p", Path(test_file).name])
    elif test_type == "npm test":
        cmd = ["npm", "test"]
    else:
        raise ValueError(f"Unsupported test type: {test_type}")

    proc = subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    result = TestResult(test_type, proc.returncode, output)
    (workspace_dir / "test_result.txt").write_text(output, encoding="utf-8")
    return result
