# AI Coding Agent

Local-first AI coding agent prototype based on the V1.35 architecture review.

## Goals

- Keep code changes small and patch-based.
- Use Python to enforce safety rules.
- Validate changes with tests before review.
- Keep the workflow local-first and easy to inspect.

## Workflow

The agent reads `workspace/task.txt`, builds a context pack, sends it to a local Ollama model, applies a strict `SEARCH` / `REPLACE` patch, runs the selected tests, and records the result under `workspace/`.

If patching or tests fail, it rolls back the target file and restores a clean worktree.

## Task Format

`target_file | test_type | test_file | task_description`

Example:

`app.py | pytest | tests/test_app.py | Implement divide(a, b) with divide-by-zero protection`

Supported `test_type` values:

- `pytest`
- `npm test`
- `none`

## Usage

```powershell
python .\agent.py --root . --task workspace\task.txt --model qwen2.5-coder:7b
```

Optional flags:

- `--workspace workspace`
- `--ollama-host http://localhost:11434`
- `--dry-run`

## Output Files

- `workspace/context_pack.md`
- `workspace/search_replace.patch`
- `workspace/test_result.txt`
- `workspace/git_diff.txt`

## Safety Rules

- The repository must be clean before execution.
- `workspace/` is ignored by git.
- Only one target file is supported in V1.35.
- SEARCH blocks must match exactly one location.
- Failed tests trigger rollback of the target file.
- No automatic commit is performed.

## Repository Status

This repository includes:

- the agent prototype implementation
- a demo task and demo tests
- the three original architecture documents

## Current Status

- Latest workflow run: success, with a real diff applied to `demo_add.py`
- Latest validation: `python -m unittest discover -s tests` passed with 22 tests
- Safety gates: no-op patch rejection, strict SEARCH/REPLACE matching, Git Guard, rollback, and `py_compile`

See [TEST_STATUS.md](TEST_STATUS.md) for the latest run details and failure coverage.
