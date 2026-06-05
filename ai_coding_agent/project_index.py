from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IndexedFile:
    path: str
    type: str
    symbols: tuple[str, ...]
    summary: str
    tests: tuple[str, ...]
    risk: str


@dataclass(frozen=True)
class ProjectIndex:
    files: tuple[IndexedFile, ...]
    protected_files: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectIndex":
        return cls(
            files=tuple(
                IndexedFile(
                    path=str(item["path"]),
                    type=str(item["type"]),
                    symbols=tuple(str(symbol) for symbol in item.get("symbols", [])),
                    summary=str(item.get("summary", "")),
                    tests=tuple(str(test) for test in item.get("tests", [])),
                    risk=str(item.get("risk", "medium")),
                )
                for item in payload.get("files", [])
            ),
            protected_files=tuple(str(path) for path in payload.get("protected_files", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": [
                {
                    "path": item.path,
                    "type": item.type,
                    "symbols": list(item.symbols),
                    "summary": item.summary,
                    "tests": list(item.tests),
                    "risk": item.risk,
                }
                for item in self.files
            ],
            "protected_files": list(self.protected_files),
        }

    @classmethod
    def from_file(cls, path: Path) -> "ProjectIndex":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


DEFAULT_PROTECTED_FILES = (
    ".gitignore",
    "README.md",
    "ai_coding_agent/git_guard.py",
    "ai_coding_agent/workflow.py",
)


def _read_protected_files(root: Path) -> tuple[str, ...]:
    path = root / "memory" / "PROTECTED_FILES.md"
    if not path.exists():
        return DEFAULT_PROTECTED_FILES
    protected: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            protected.append(line)
    return tuple(protected) or DEFAULT_PROTECTED_FILES


def _python_symbols(path: Path) -> tuple[str, ...]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return ()
    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
    return tuple(symbols)


def _js_symbols(text: str) -> tuple[str, ...]:
    names = re.findall(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", text)
    names.extend(re.findall(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", text))
    names.extend(re.findall(r"export\s+const\s+([A-Za-z_][A-Za-z0-9_]*)", text))
    return tuple(dict.fromkeys(names))


def _test_candidates(path: Path) -> list[str]:
    stem = path.stem
    return [
        f"tests/test_{stem}.py",
        f"test_{stem}.py",
        f"tests/{stem}.test.js",
        f"tests/{stem}.spec.js",
    ]


def _file_type(path: Path) -> str:
    if path.suffix == ".py":
        return "python_test" if path.name.startswith("test_") or "tests" in path.parts else "python"
    if path.suffix in {".js", ".ts", ".jsx", ".tsx"}:
        return "javascript_test" if "test" in path.name or "spec" in path.name or "tests" in path.parts else "javascript"
    if path.name.lower().startswith("readme") or path.suffix == ".md":
        return "documentation"
    return path.suffix.lstrip(".") or "file"


def _summary(path: Path, file_type: str, symbols: tuple[str, ...]) -> str:
    if symbols:
        return f"Contains symbols: {', '.join(symbols)}."
    if "test" in file_type:
        return "Contains tests."
    if file_type == "documentation":
        return "Contains documentation."
    return "Project file."


def scan_project(root: Path) -> ProjectIndex:
    protected_files = _read_protected_files(root)
    indexed: list[IndexedFile] = []
    all_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts and "workspace" not in path.parts and "__pycache__" not in path.parts
    }
    for path_text in sorted(all_paths):
        path = root / path_text
        file_type = _file_type(path)
        if file_type == "python":
            symbols = _python_symbols(path)
        elif file_type == "javascript":
            symbols = _js_symbols(path.read_text(encoding="utf-8", errors="ignore"))
        else:
            symbols = ()
        tests = tuple(candidate for candidate in _test_candidates(path) if candidate in all_paths)
        risk = "high" if path_text in protected_files or path_text.startswith("ai_coding_agent/") else "low"
        indexed.append(
            IndexedFile(
                path=path_text,
                type=file_type,
                symbols=symbols,
                summary=_summary(path, file_type, symbols),
                tests=tests,
                risk=risk,
            )
        )
    return ProjectIndex(files=tuple(indexed), protected_files=protected_files)

