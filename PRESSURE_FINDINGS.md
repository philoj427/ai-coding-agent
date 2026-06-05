# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 34
- Failed: 16

## What Changed

- The workflow now scores local exact SEARCH candidates deterministically.
- Ollama provides replacement text only for the locally selected candidate.
- The model no longer owns SEARCH generation or candidate ranking.
- Candidate generation now includes function docstring, validation block, and return statement candidates.
- The scorer now uses structural intent signals with conservative trigger words.
- The workflow now tries a small fallback order of ranked candidates instead of only the top candidate.

## Main Failure Types

- `SEARCH block must match exactly one location, found 0`
- `py_compile` syntax failures
- test failures from real behavior regressions
- malformed or incomplete patch output

## Read

- Fallback ranking improved the pressure pass rate from 27/23 to 34/16.
- The remaining failures are still split across syntax and semantic issues.
- Aggressive structural matching regressed to 25/25, so scorer changes need confidence gates.
- The useful compare-tool lesson is to prefer stable, unique hunks when intent confidence is low.

## Next Direction

- Tighten local candidate ranking.
- Use failure data to tune fallback candidate ordering.
- Use failure data to learn which candidate classes fail by task type.
- Keep Ollama on replacement wording only.
- Avoid pushing SEARCH generation back to the model.
