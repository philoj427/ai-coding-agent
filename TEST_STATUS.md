# Test Status

Last updated: 2026-06-03

## Summary

- Latest workflow run completed successfully.
- The run produced a real diff in `demo_add.py`.
- The current test suite passes with 22 tests.

## Workflow Result

- Command: `python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b`
- Result: success
- Patch: applied a real diff to `demo_add.py`
- Change: `def add(a, b):` -> `def add(a: int | float, b: int | float) -> int | float:`

## Verification

- Command: `python -m unittest discover -s tests`
- Result: success
- Runner: `unittest` fallback
- Outcome: 22 tests passed

## Safety Coverage

The core suite covers:

- SEARCH blocks that match multiple locations
- SEARCH blocks that do not exist in the target file
- No-op patch rejection
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
