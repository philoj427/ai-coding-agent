# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 21
- Failed: 29

## What Changed

- The workflow now uses local exact SEARCH candidates.
- Ollama selects a candidate and provides replacement text instead of inventing SEARCH text.
- The model no longer owns the most fragile part of the patch.

## Main Failure Types

- `SEARCH block must match exactly one location, found 0`
- `py_compile` syntax failures
- test failures from real behavior regressions
- malformed or incomplete patch output

## Read

- The local candidate layer helps, but it did not move the pressure result up yet.
- `SEARCH=0` is still the dominant failure mode.
- The remaining failures are more spread across syntax and semantic issues.

## Next Direction

- Tighten local candidate ranking.
- Add a deterministic local candidate scorer.
- Keep Ollama on ranking and replacement wording only.
- Avoid pushing SEARCH generation back to the model.
