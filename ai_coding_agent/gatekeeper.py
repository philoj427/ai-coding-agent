from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

from .patch_parser import PatchParseError, parse_search_replace_patch


class GatekeeperError(ValueError):
    pass


@dataclass
class GatekeeperResult:
    approved: bool
    reason: str
    diff_preview: str


def inspect_patch(target_file: Path, patch_text: str) -> GatekeeperResult:
    original_text = target_file.read_text(encoding="utf-8") if target_file.exists() else ""
    updated_text = original_text

    try:
        blocks = parse_search_replace_patch(patch_text)
    except PatchParseError as exc:
        raise GatekeeperError(str(exc)) from exc

    for search_text, replace_text in blocks:
        if search_text != replace_text and search_text.strip() == replace_text.strip():
            raise GatekeeperError("SEARCH/REPLACE cannot be indentation-only changes")

        search_lines = search_text.splitlines()
        replace_lines = replace_text.splitlines()
        if len(search_lines) == len(replace_lines):
            for search_line, replace_line in zip(search_lines, replace_lines):
                if search_line != replace_line and search_line.lstrip() == replace_line.lstrip():
                    raise GatekeeperError(
                        "SEARCH/REPLACE cannot change indentation without changing line content"
                    )

        occurrences = updated_text.count(search_text)
        if occurrences != 1:
            raise GatekeeperError(
                f"SEARCH block must match exactly one location, found {occurrences}"
            )

        updated_text = updated_text.replace(search_text, replace_text, 1)

    diff_text = "".join(
        difflib.unified_diff(
            original_text.splitlines(True),
            updated_text.splitlines(True),
            fromfile=str(target_file),
            tofile=str(target_file),
        )
    )
    if not diff_text.strip():
        raise GatekeeperError("SEARCH/REPLACE patch must change target file")

    if target_file.suffix == ".py":
        top_level_defs: set[str] = set()
        for line in updated_text.splitlines():
            if line.startswith("def "):
                name = line[4:].split("(", 1)[0].strip()
                if name in top_level_defs:
                    raise GatekeeperError(f"Duplicate top-level function definition: {name}")
                top_level_defs.add(name)

        if updated_text.startswith('"""'):
            docstring_end = updated_text.find('"""', 3)
            if docstring_end != -1:
                tail = updated_text[docstring_end + 3 :]
                if tail.startswith("\ndef ") or tail.startswith("\n\ndef "):
                    raise GatekeeperError("Module docstring must be separated from top-level defs by a blank line")

    return GatekeeperResult(True, "ok", diff_text)
