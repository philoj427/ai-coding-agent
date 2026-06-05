# Test Status

## Summary

- Latest workflow attempt completed with local exact SEARCH candidates and deterministic local scoring.
- The agent no longer asks Ollama to invent or select SEARCH text.
- Latest unit test suite result: 38 tests passed.

## Latest Automated Workflow Attempt

- Result: failed
- Run: `python .\run_pressure_tests.py`
- Tasks: 50
- Outcome: 34 passed, 16 failed

## Latest Failure Pattern

- `SEARCH block must match exactly one location, found 0`
- `py_compile` syntax validation failures
- test failures from real regressions
- malformed or incomplete patch output

## Safety Coverage

- SEARCH/REPLACE parsing preserves indentation
- `count == 1` enforcement remains active
- Git Guard still blocks unstaged, staged, and untracked unauthorized files
- test failure cleanup still restores the repo
- `py_compile` validation still runs for Python targets
- `__pycache__` cleanup still runs after successful syntax validation

## Notes

- The local candidate scorer now uses structural intent signals, conservative triggers, and fallback ranking.
- Fallback ranking improved the pressure result from 27/23 to 34/16.
