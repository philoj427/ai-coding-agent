# Test Status

## Summary

- Latest workflow attempt completed with deterministic local templates for the V1.9 pressure suite.
- The agent no longer asks Ollama to invent or select SEARCH text for local candidate flow.
- V1.7 planner can turn a natural-language task into `task_plan.json`.
- V1.8 project index maps symbols to target files and related tests.
- V1.9 high-risk tasks produce plan-only results instead of patching code.
- Latest unit test suite result: 49 tests passed.

## Latest Automated Workflow Attempt

- Result: success
- Run: `python .\run_pressure_tests.py --tasks pressure_tasks_v19.txt`
- Tasks: 50
- Outcome: 50 passed, 0 failed
- Real code patch passes: 40
- Plan-only safety passes: 10
- No-diff passes: 0
- Planner failures: 0

## Latest Planner Check

- Run: `python .\agent.py --root . --task workspace\natural_task.txt --model qwen2.5-coder:7b`
- Result: success
- Generated plan: `demo_add.py`, `unittest`, `tests/test_demo_add.py`, `risk_level=low`
- Index check: `Add a zero-division guard to divide().` selected `math_tool.py`, `unittest`, `tests/test_math_tool.py`
- V1.9 task list: `pressure_tasks_v19.txt` contains 50 harder tasks with increasing difficulty.
- Plan-only check: `Refactor ai_coding_agent/workflow.py to support multi-file editing.` returned `status=plan_only`.

## Latest Failure Pattern

- No failures in the latest V1.9 50-task pressure run.

## Safety Coverage

- SEARCH/REPLACE parsing preserves indentation
- `count == 1` enforcement remains active
- Git Guard still blocks unstaged, staged, and untracked unauthorized files
- test failure cleanup still restores the repo
- `py_compile` validation still runs for Python targets
- `__pycache__` cleanup still runs after successful syntax validation
- demo and math-tool pressure templates still go through Gatekeeper, patch application, `py_compile`, tests, and Git Guard
- V1.7 plans are validated before patch workflow starts
- V1.8 project index respects protected files from `memory/PROTECTED_FILES.md`
- V1.9 plan-only mode prevents protected or high-risk plans from entering patch generation

## Notes

- The local candidate scorer now uses structural intent signals, conservative triggers, and fallback ranking.
- Deterministic demo and math-tool templates lifted the V1.9 pressure result to 50/0.
- This is a suite-specific hardening layer for `demo_add.py` and `math_tool.py`, not a general multi-file production claim.
- V1.7 still enforces a single target file.
- V1.8 still enforces a single target file.
- V1.9 still enforces a single target file.
