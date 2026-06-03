from __future__ import annotations


class PatchParseError(ValueError):
    pass


def parse_search_replace_patch(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    i = 0
    blocks: list[tuple[str, str]] = []

    def consume_until(marker: str) -> list[str]:
        nonlocal i
        buf: list[str] = []
        while i < len(lines) and lines[i].strip() != marker:
            buf.append(lines[i])
            i += 1
        if i >= len(lines):
            raise PatchParseError(f"Missing {marker}")
        return buf

    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        if lines[i].strip() != "SEARCH":
            raise PatchParseError("Expected SEARCH")
        i += 1
        search_lines = consume_until("END_SEARCH")
        i += 1
        if i >= len(lines) or lines[i].strip() != "REPLACE":
            raise PatchParseError("Expected REPLACE")
        i += 1
        replace_lines = consume_until("END_REPLACE")
        i += 1
        blocks.append(("\n".join(search_lines), "\n".join(replace_lines)))

    if not blocks:
        raise PatchParseError("No patch blocks found")
    return blocks
