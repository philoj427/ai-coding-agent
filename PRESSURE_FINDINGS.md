# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 27
- Failed: 23

## What Changed

- The workflow now scores local exact SEARCH candidates deterministically.
- Ollama provides replacement text only for the locally selected candidate.
- The model no longer owns SEARCH generation or candidate ranking.

## Main Failure Types

- `SEARCH block must match exactly one location, found 0`
- `py_compile` syntax failures
- test failures from real behavior regressions
- malformed or incomplete patch output

## Read

- The local scorer improves determinism, but it did not improve the pressure pass rate yet.
- The remaining failures are still split across syntax and semantic issues.
- The next candidate-ranking improvement should be based on the recorded failure classes.

## Next Direction

- Tighten local candidate ranking.
- Keep Ollama on replacement wording only.
- Avoid pushing SEARCH generation back to the model.
