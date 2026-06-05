from __future__ import annotations

import json
from dataclasses import dataclass

from .search_candidates import SearchCandidate


@dataclass(frozen=True)
class CandidateSelection:
    candidate_id: str
    replacement: str
    reason: str


def _strip_code_fences(text: str) -> str:
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].lstrip().startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1])
    return text


def build_candidate_context(candidates: list[SearchCandidate]) -> str:
    sections = ["## Local Search Candidates", "These are exact target-file excerpts available to the local scorer.", ""]
    for candidate in candidates:
        sections.extend([
            f"### Candidate {candidate.candidate_id}",
            f"- Label: {candidate.label}",
            "```text",
            candidate.text,
            "```",
            "",
        ])
    return "\n".join(sections).rstrip() + "\n"


def parse_candidate_selection(text: str) -> CandidateSelection:
    payload = json.loads(_strip_code_fences(text).strip())
    candidate_id = str(payload["candidate_id"]).strip()
    replacement = str(payload["replacement"])
    reason = str(payload.get("reason", "")).strip()
    if not candidate_id:
        raise ValueError("candidate_id is required")
    return CandidateSelection(candidate_id=candidate_id, replacement=replacement, reason=reason)


@dataclass(frozen=True)
class ReplacementSelection:
    replacement: str
    reason: str


def parse_replacement_selection(text: str) -> ReplacementSelection:
    payload = json.loads(_strip_code_fences(text).strip())
    replacement = str(payload["replacement"])
    reason = str(payload.get("reason", "")).strip()
    return ReplacementSelection(replacement=replacement, reason=reason)

