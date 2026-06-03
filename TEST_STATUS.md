# Test Status

Last updated: 2026-06-03

## Summary

- Latest workflow run failed because Gatekeeper rejected a malformed docstring patch.
- The latest failure report includes stage and reason.
- The current test suite passes with 29 tests.

## Workflow Result

- Command: `python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b`
- Result: failed
- Stage: gatekeeper
- Reason: Module docstring must be separated from top-level defs by a blank line
- Patch: malformed docstring spacing patch

## Verification

- Command: `python -m unittest discover -s tests`
- Result: success
- Runner: `unittest` fallback
- Outcome: 29 tests passed

## Safety Coverage

The core suite covers:

- SEARCH blocks that match multiple locations
- SEARCH blocks that do not exist in the target file
- No-op patch rejection
- Line-level indentation-only rejection
- Gatekeeper pre-application rejection
- Retry once after malformed patch output
- Structured failure reports with stage and reason
- Duplicate top-level function rejection
- Module docstring spacing rejection
- Git Guard blocking unauthorized staged files
- Git Guard blocking unauthorized untracked files
- Workflow rollback when tests fail
- Workflow repo cleanup after test failure
- Builder prompt hardening
- Patch parse retry once
- Python syntax validation with `py_compile`
- Cleanup of `__pycache__` artifacts

## Notes

- `workspace/` is ignored by git, so runtime artifacts stay local.
- Failure cleanup restores the repo to `HEAD` and removes stray untracked files.
- Python target files are syntax-checked, and generated `__pycache__` artifacts are removed.
