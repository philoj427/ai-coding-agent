from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

from .patch_parser import PatchParseError, parse_search_replace_patch


@dataclass
class PatchResult:
    applied: bool
    before_text: str
    after_text: str
    diff_text: str


def apply_search_replace_patch(target_file: Path, patch_text: str) -> PatchResult:
    original_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    updated_text = original_text

    for search_text, replace_text in parse_search_replace_patch(patch_text):
        if search_text != replace_text and search_text.strip() == replace_text.strip():
            raise PatchParseError("SEARCH/REPLACE cannot be indentation-only changes")
        occurrences = updated_text.count(search_text)
        if occurrences != 1:
            raise PatchParseError(
                f"SEARCH block must match exactly one location, found {occurrences}"
            )
        updated_text = updated_text.replace(search_text, replace_text, 1)

    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(updated_text, encoding="utf-8")

    diff_text = "".join(
        difflib.unified_diff(
            original_text.splitlines(True),
            updated_text.splitlines(True),
            fromfile=str(target_file),
            tofile=str(target_file),
        )
    )
    return PatchResult(True, original_text, updated_text, diff_text)


def restore_text(target_file: Path, text: str) -> None:
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(text, encoding="utf-8")
