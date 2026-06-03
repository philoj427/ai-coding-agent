from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchCandidate:
    candidate_id: str
    label: str
    text: str


def _line_window(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start:end]).rstrip("\n")


def _dedupe(candidates: list[SearchCandidate]) -> list[SearchCandidate]:
    seen: set[str] = set()
    unique: list[SearchCandidate] = []
    for candidate in candidates:
        if candidate.text in seen or not candidate.text.strip():
            continue
        seen.add(candidate.text)
        unique.append(candidate)
    return unique


def _python_candidates(source: str) -> list[SearchCandidate]:
    candidates: list[SearchCandidate] = []
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    docstring = ast.get_docstring(tree, clean=False)
    if docstring and getattr(tree, "body", None):
        first_node = tree.body[0]
        doc_segment = ast.get_source_segment(source, first_node)
        if doc_segment:
            candidates.append(
                SearchCandidate(
                    candidate_id="docstring",
                    label="module_docstring",
                    text=doc_segment.rstrip("\n"),
                )
            )

    for index, node in enumerate(tree.body):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = ast.get_source_segment(source, node)
            if segment:
                kind = "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class"
                candidates.append(
                    SearchCandidate(
                        candidate_id=f"{kind}_{index}",
                        label=f"top_level_{kind}:{node.name}",
                        text=segment.rstrip("\n"),
                    )
                )
            if getattr(node, "lineno", None) and getattr(node, "end_lineno", None):
                for line_no in range(node.lineno, node.end_lineno):
                    if 0 <= line_no < len(lines):
                        line_text = lines[line_no].rstrip("\n")
                        if line_text.strip():
                            candidates.append(
                                SearchCandidate(
                                    candidate_id=f"{kind}_{index}_line_{line_no + 1}",
                                    label=f"{kind}_line:{node.name}:{line_no + 1}",
                                    text=line_text,
                                )
                            )

    if not candidates and lines:
        candidates.append(
            SearchCandidate(
                candidate_id="file_head",
                label="file_head",
                text=_line_window(lines, 0, min(len(lines), 40)),
            )
        )

    return _dedupe(candidates)


def _generic_candidates(source: str) -> list[SearchCandidate]:
    lines = source.splitlines()
    candidates: list[SearchCandidate] = []
    if lines:
        candidates.append(
            SearchCandidate(
                candidate_id="file_head",
                label="file_head",
                text=_line_window(lines, 0, min(len(lines), 40)),
            )
        )
        if len(lines) > 40:
            candidates.append(
                SearchCandidate(
                    candidate_id="file_tail",
                    label="file_tail",
                    text=_line_window(lines, max(0, len(lines) - 40), len(lines)),
                )
            )
    return _dedupe(candidates)


def build_search_candidates(target_path: Path) -> list[SearchCandidate]:
    source = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    if target_path.suffix == ".py":
        candidates = _python_candidates(source)
    else:
        candidates = _generic_candidates(source)
    if not candidates and source.strip():
        candidates = _generic_candidates(source)
    return candidates

