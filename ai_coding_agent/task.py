from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TaskSpec:
    target_file: Path
    test_type: str
    test_file: Path | None
    description: str

    @classmethod
    def from_text(cls, text: str) -> "TaskSpec":
        parts = [part.strip() for part in text.strip().split("|", 3)]
        if len(parts) != 4:
            raise ValueError("task.txt must use: target_file | test_type | test_file | task_description")

        target_file, test_type, test_file, description = parts
        return cls(
            target_file=Path(target_file),
            test_type=test_type.lower(),
            test_file=None if test_file.lower() in {"", "none", "null"} else Path(test_file),
            description=description,
        )

    @classmethod
    def from_file(cls, path: Path) -> "TaskSpec":
        return cls.from_text(path.read_text(encoding="utf-8"))
