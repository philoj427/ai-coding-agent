from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChangeStep:
    step_id: str
    target_file: Path
    intent: str
    allowed_change: str
    test_type: str
    test_file: Path | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChangeStep":
        return cls(
            step_id=str(payload["step_id"]),
            target_file=Path(str(payload["target_file"])),
            intent=str(payload["intent"]),
            allowed_change=str(payload.get("allowed_change", "production_code")),
            test_type=str(payload.get("test_type", "none")).lower(),
            test_file=None if not payload.get("test_file") else Path(str(payload["test_file"])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "target_file": self.target_file.as_posix(),
            "intent": self.intent,
            "allowed_change": self.allowed_change,
            "test_type": self.test_type,
            "test_file": self.test_file.as_posix() if self.test_file else None,
        }


@dataclass(frozen=True)
class ChangePlan:
    task: str
    steps: tuple[ChangeStep, ...]
    final_test_type: str
    final_test_file: Path | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChangePlan":
        return cls(
            task=str(payload["task"]),
            steps=tuple(ChangeStep.from_dict(item) for item in payload.get("steps", [])),
            final_test_type=str(payload.get("final_test_type", payload.get("test_type", "unittest"))).lower(),
            final_test_file=None if not payload.get("final_test_file") else Path(str(payload["final_test_file"])),
        )

    @classmethod
    def from_json(cls, text: str) -> "ChangePlan":
        return cls.from_dict(json.loads(text))

    @classmethod
    def from_file(cls, path: Path) -> "ChangePlan":
        return cls.from_json(path.read_text(encoding="utf-8"))

    @property
    def allowed_files(self) -> set[Path]:
        return {step.target_file for step in self.steps}

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "steps": [step.to_dict() for step in self.steps],
            "final_test_type": self.final_test_type,
            "final_test_file": self.final_test_file.as_posix() if self.final_test_file else None,
            "allowed_files": sorted(path.as_posix() for path in self.allowed_files),
        }
