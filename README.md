# AI Coding Agent

Local-first AI coding agent for safe, single-file patching with local Ollama.

## Workflow

Read `workspace/task.txt`, build or load a project index, plan the task when needed, build a context pack, select an exact local SEARCH candidate, ask local Ollama for replacement text, run the patch through Gatekeeper, apply a strict `SEARCH` / `REPLACE` patch, run tests, and record the result under `workspace/`.

If patching or tests fail, the agent rolls back the target file and restores a clean worktree.

## Usage

```powershell
python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b
```

Optional flags:

- `--workspace workspace`
- `--ollama-host http://localhost:11434`
- `--dry-run`

## Safety Rules

- Repo must be clean before execution.
- `workspace/` is ignored by git.
- V1.9 supports one target file only.
- Planner output is validated before patching.
- Project index guides target and test-file selection.
- High-risk tasks are plan-only and do not patch code.
- SEARCH blocks must match exactly one location.
- Failed tests trigger rollback.
- No automatic commit is performed.

## Current Status

- Latest 50-task pressure run: `50 passed, 0 failed`
- Latest validation: `python -m unittest discover -s tests` passed with 49 tests
- V1.8 Project Index lets Planner map symbols to target and test files
- V1.9 adds plan-only output for high-risk tasks
- Safety gates: plan validation, Gatekeeper, retry once, structured failure reports, no-op patch rejection, duplicate top-level function rejection, module docstring spacing rejection, line-level indentation rejection, strict SEARCH/REPLACE matching, Git Guard, rollback, and `py_compile`

See [TEST_STATUS.md](TEST_STATUS.md) for the latest run details and failure coverage.

## Roadmap

- [V1.4.md](V1.4.md)
- [V1.7.md](V1.7.md)
- [V1.8.md](V1.8.md)
- [V1.9.md](V1.9.md)
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
