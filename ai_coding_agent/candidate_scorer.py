from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .search_candidates import SearchCandidate


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: SearchCandidate
    score: float
    reasons: tuple[str, ...]


def _tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    current: list[str] = []
    for char in text.lower():
        if char.isalnum() or char == "_":
            current.append(char)
        else:
            if current:
                token = "".join(current)
                if len(token) > 1:
                    tokens.add(token)
                current.clear()
    if current:
        token = "".join(current)
        if len(token) > 1:
            tokens.add(token)
    return tokens


def score_candidates(task_description: str, candidates: list[SearchCandidate]) -> list[ScoredCandidate]:
    task_tokens = _tokenize(task_description)
    prefers_docstring = any(word in task_tokens for word in {"docstring", "comment", "text", "docs", "documentation"})
    prefers_function = any(word in task_tokens for word in {"refactor", "function", "type", "typing", "signature"})
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        label_tokens = _tokenize(candidate.label)
        text_tokens = _tokenize(candidate.text)
        overlap = len(task_tokens & (label_tokens | text_tokens))
        ratio = SequenceMatcher(None, task_description.lower(), candidate.label.lower()).ratio()
        score = (overlap * 3.0) + ratio
        reasons: list[str] = []

        if overlap:
            reasons.append(f"token_overlap={overlap}")
        if "docstring" in candidate.label:
            score += 1.5
            reasons.append("docstring_match")
        if "function" in candidate.label:
            score += 1.0
            reasons.append("function_match")
        if "class" in candidate.label:
            score += 0.5
            reasons.append("class_match")
        if prefers_docstring and "docstring" in candidate.label:
            score += 4.0
            reasons.append("task_prefers_docstring")
        if prefers_function and "function" in candidate.label:
            score += 2.0
            reasons.append("task_prefers_function")
        if "_line_" in candidate.candidate_id and not prefers_docstring and not prefers_function:
            score += 2.0
            reasons.append("small_change_prefers_line")

        scored.append(ScoredCandidate(candidate=candidate, score=score, reasons=tuple(reasons)))

    scored.sort(key=lambda item: (-item.score, item.candidate.candidate_id))
    return scored

