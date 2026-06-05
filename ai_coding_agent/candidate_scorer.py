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
    prefers_module_docstring = "docstring" in task_tokens and "module" in task_tokens
    prefers_function_docstring = "docstring" in task_tokens and ("function" in task_tokens or "add" in task_tokens)
    prefers_module_level = (
        {"module", "level"}.issubset(task_tokens)
        or any(word in task_tokens for word in {"__all__", "__version__", "constant", "alias"})
    )
    prefers_helper = any(word in task_tokens for word in {"helper", "extract", "factor", "reusable"})
    prefers_validation = any(word in task_tokens for word in {"validation", "validate", "typeerror", "guard", "check"})
    prefers_return = any(word in task_tokens for word in {"return", "sum", "total", "result"})
    prefers_typing = any(word in task_tokens for word in {"type", "typing", "signature", "annotations"})
    scored: list[ScoredCandidate] = []

    for candidate in candidates:
        label_tokens = _tokenize(candidate.label)
        text_tokens = _tokenize(candidate.text)
        overlap = len(task_tokens & (label_tokens | text_tokens))
        ratio = SequenceMatcher(None, task_description.lower(), candidate.label.lower()).ratio()
        score = (overlap * 3.0) + ratio
        reasons: list[str] = []
        label = candidate.label

        if overlap:
            reasons.append(f"token_overlap={overlap}")
        if "docstring" in label:
            score += 1.5
            reasons.append("docstring_match")
        if "function" in label:
            score += 1.0
            reasons.append("function_match")
        if "class" in label:
            score += 0.5
            reasons.append("class_match")
        if prefers_module_docstring and "module_docstring" in label:
            score += 8.0
            reasons.append("task_prefers_module_docstring")
        if prefers_function_docstring and "function_docstring" in label:
            score += 8.0
            reasons.append("task_prefers_function_docstring")
        if prefers_module_level and "module_docstring" in label:
            score += 4.0
            reasons.append("module_level_uses_module_anchor")
        if prefers_helper and "top_level_function" in label:
            score += 5.0
            reasons.append("helper_prefers_function_block")
        if prefers_validation and "if_block" in label:
            score += 7.0
            reasons.append("validation_prefers_if_block")
        if prefers_validation and "top_level_function" in label:
            score += 3.0
            reasons.append("validation_allows_function_block")
        if prefers_return and "return" in label:
            score += 7.0
            reasons.append("return_prefers_return_block")
        if prefers_typing and "top_level_function" in label:
            score += 5.0
            reasons.append("typing_prefers_function_block")
        if "_line_" in candidate.candidate_id and not (
            prefers_module_docstring
            or prefers_function_docstring
            or prefers_helper
            or prefers_validation
            or prefers_return
            or prefers_typing
        ):
            score += 2.0
            reasons.append("small_change_prefers_line")

        scored.append(ScoredCandidate(candidate=candidate, score=score, reasons=tuple(reasons)))

    scored.sort(key=lambda item: (-item.score, item.candidate.candidate_id))
    return scored


def rank_candidates(task_description: str, candidates: list[SearchCandidate], max_candidates: int = 3) -> list[SearchCandidate]:
    scored = score_candidates(task_description, candidates)
    if not scored:
        return []

    ranked: list[SearchCandidate] = []
    seen: set[str] = set()

    def add(candidate: SearchCandidate) -> None:
        if candidate.candidate_id in seen:
            return
        seen.add(candidate.candidate_id)
        ranked.append(candidate)

    best = scored[0]
    add(best.candidate)

    # If confidence is low, prefer stable structural fallbacks before tiny line hunks.
    strong_reason = any(reason.startswith("task_prefers_") or reason.endswith("_prefers_function_block") for reason in best.reasons)
    if not strong_reason:
        for item in scored:
            label = item.candidate.label
            if "top_level_function" in label or "module_docstring" in label:
                add(item.candidate)
                if len(ranked) >= max_candidates:
                    return ranked

    for item in scored:
        add(item.candidate)
        if len(ranked) >= max_candidates:
            return ranked

    return ranked
