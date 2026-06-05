from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .task import TaskSpec


@dataclass(frozen=True)
class TaskPlan:
    target_file: Path
    test_type: str
    test_file: Path | None
    risk_level: str
    reason: str
    allowed_files: tuple[Path, ...]
    forbidden_files: tuple[str, ...]
    description: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], description: str) -> "TaskPlan":
        return cls(
            target_file=Path(str(payload["target_file"])),
            test_type=str(payload["test_type"]).lower(),
            test_file=None if not payload.get("test_file") else Path(str(payload["test_file"])),
            risk_level=str(payload["risk_level"]).lower(),
            reason=str(payload.get("reason", "")),
            allowed_files=tuple(Path(str(path)) for path in payload.get("allowed_files", [])),
            forbidden_files=tuple(str(path) for path in payload.get("forbidden_files", [])),
            description=description,
        )

    @classmethod
    def from_json(cls, text: str, description: str) -> "TaskPlan":
        return cls.from_dict(json.loads(text), description)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_file": self.target_file.as_posix(),
            "test_type": self.test_type,
            "test_file": self.test_file.as_posix() if self.test_file else None,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "allowed_files": [path.as_posix() for path in self.allowed_files],
            "forbidden_files": list(self.forbidden_files),
        }

    def to_task_spec(self) -> TaskSpec:
        return TaskSpec(
            target_file=self.target_file,
            test_type=self.test_type,
            test_file=self.test_file,
            description=self.description,
        )

