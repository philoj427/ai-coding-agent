# AI Coding Agent

Local-first AI coding agent for safe, single-file patching with local Ollama.

## Workflow

Read `workspace/task.txt`, build or load a project index, plan the task when needed, build a context pack, select an exact local SEARCH candidate, ask local Ollama for replacement text, run the patch through Gatekeeper, apply a strict `SEARCH` / `REPLACE` patch, run tests, and record the result under `workspace/`.

V2.0 can also run a bounded `change_plan.json` as multiple single-file steps. Each step still uses the same single-file safety workflow.

If patching or tests fail, the agent rolls back the target file and restores a clean worktree.

## Usage

```powershell
python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b
```

V2.0 change plan:

```powershell
python .\agent.py --root . --change-plan workspace\change_plan.json --model qwen2.5-coder:7b
```

Optional flags:

- `--workspace workspace`
- `--ollama-host http://localhost:11434`
- `--dry-run`

## Safety Rules

- Repo must be clean before execution.
- `workspace/` is ignored by git.
- V1.9 supports one target file only.
- V2.0 supports bounded multi-step change plans, with one target file per step.
- Planner output is validated before patching.
- Project index guides target and test-file selection.
- High-risk tasks are plan-only and do not patch code.
- SEARCH blocks must match exactly one location.
- Failed tests trigger rollback.
- No automatic commit is performed.

## Current Status

- Latest V1.9 50-task pressure run: `50 passed, 0 failed`
- Pressure run classification: 40 real code patch passes, 10 plan-only safety passes, 0 no-diff passes
- Latest V2.0 mixed pressure run: 100 cases passed, 0 failed
- V2.0 pressure classification: 55 single-file patch passes, 18 change-plan passes, 9 plan-only passes, 13 reject passes, 5 rollback passes
- Latest validation: `python -m unittest discover -s tests` passed with 66 tests
- General programming benchmark coverage includes string parsing, data transforms, coupon/invoice logic, config loading, CSV output, state transitions, and rate limiting
- V1.8 Project Index lets Planner map symbols to target and test files
- V1.9 adds plan-only output for high-risk tasks
- V2.0 adds safe multi-step change plans for small source + test changes
- Safety gates: plan validation, Gatekeeper, retry once, structured failure reports, no-op patch rejection, duplicate top-level function rejection, module docstring spacing rejection, line-level indentation rejection, strict SEARCH/REPLACE matching, Git Guard, rollback, and `py_compile`

See [TEST_STATUS.md](TEST_STATUS.md) for the latest run details and failure coverage.

## Roadmap

- [V1.4.md](V1.4.md)
- [V1.7.md](V1.7.md)
- [V1.8.md](V1.8.md)
- [V1.9.md](V1.9.md)
- [V2.0.md](V2.0.md)
- [TODO.md](TODO.md)

## Task Format

Either a natural-language task:

```text
Rewrite the module docstring for the add helper.
```

Or the explicit legacy format:

```text
target_file | test_type | test_file | task_description
```

Supported `test_type` values: `pytest`, `unittest`, `npm test`, `none`
