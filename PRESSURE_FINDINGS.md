# Pressure Findings

## Latest Run

- Tasks: 50
- Passed: 50
- Failed: 0

## What Changed

- The workflow now scores local exact SEARCH candidates deterministically.
- Ollama provides replacement text only for the locally selected candidate.
- The model no longer owns SEARCH generation or candidate ranking.
- Candidate generation now includes function docstring, validation block, and return statement candidates.
- The scorer now uses structural intent signals with conservative trigger words.
- The workflow now tries a small fallback order of ranked candidates instead of only the top candidate.
- The workflow now has deterministic local templates for the `demo_add.py` pressure suite.

## Main Failure Types

- No failures in the latest 50-task pressure run.

## Read

- Fallback ranking improved the pressure pass rate from 27/23 to 34/16.
- Deterministic demo templates improved the pressure pass rate from 34/16 to 50/0.
- The useful compare-tool lesson still applies: prefer stable, unique hunks when intent confidence is low.
- The 50/0 result is for the controlled `demo_add.py` pressure suite, not arbitrary repositories.

## Next Direction

- Keep the template layer explicitly scoped.
- Add more template families only when a pressure suite exposes repeated low-risk edit patterns.
- Use failure data to tune fallback candidate ordering for non-template tasks.
- Keep Ollama on replacement wording only.
- Avoid pushing SEARCH generation back to the model.
