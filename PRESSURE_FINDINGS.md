# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 27
- Failed: 23

## What Changed

- The workflow now scores local exact SEARCH candidates deterministically.
- Ollama provides replacement text only for the locally selected candidate.
- The model no longer owns SEARCH generation or candidate ranking.
- Candidate generation now includes function docstring, validation block, and return statement candidates.
- The scorer now uses structural intent signals with conservative trigger words.

## Main Failure Types

- `SEARCH block must match exactly one location, found 0`
- `py_compile` syntax failures
- test failures from real behavior regressions
- malformed or incomplete patch output

## Read

- The local scorer improves determinism, but it did not improve the pressure pass rate yet.
- The remaining failures are still split across syntax and semantic issues.
- Aggressive structural matching regressed to 25/25, so scorer changes need confidence gates.
- The useful compare-tool lesson is to prefer stable, unique hunks when intent confidence is low.

## Next Direction

- Tighten local candidate ranking.
- Add confidence thresholds and fallback candidate ordering.
- Use failure data to learn which candidate classes fail by task type.
- Keep Ollama on replacement wording only.
- Avoid pushing SEARCH generation back to the model.
