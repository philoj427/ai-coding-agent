# AI Coding Agent

Local-first AI coding agent prototype based on the V1.35 architecture review.

## Goals

- Keep code changes small and patch-based.
- Use Python to enforce safety rules.
- Validate changes with tests before review.
- Keep the workflow local-first and easy to inspect.

## Workflow

1. Read `workspace/task.txt`.
2. Build `workspace/context_pack.md` from the target file, rules, and optional test file.
3. Send the context to a local Ollama model.
4. Receive a strict `SEARCH` / `REPLACE` patch.
5. Apply the patch to the target file.
6. Run the selected test command.
7. Record test output and git diff under `workspace/`.
8. Roll back the target file if patching or tests fail.

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

The latest validated state is:

- one end-to-end workflow run that produced a real diff in `demo_add.py`
- no-op patches are rejected before test execution
- SEARCH/REPLACE parsing preserves indentation and rejects ambiguous matches
- Git Guard blocks unauthorized staged, untracked, and diff-visible files
- repo cleanup restores the worktree to `HEAD` on failure
- Python target files are syntax-checked with `py_compile`
- the current test suite passes with `unittest`

See [TEST_STATUS.md](TEST_STATUS.md) for the latest run details.
