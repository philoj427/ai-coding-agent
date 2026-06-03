# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 27
- Failed: 23

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

- The local candidate layer improves control, but it did not yet eliminate `SEARCH=0`.
- The remaining failures are still split across syntax and semantic issues.
- A deterministic local candidate scorer is the next thing to try.

## Next Direction

- Tighten local candidate ranking.
- Keep Ollama on ranking and replacement wording only.
- Avoid pushing SEARCH generation back to the model.
