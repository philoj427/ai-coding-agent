# AI Coding Agent

Local-first AI coding agent skeleton based on the V1.35 architecture review.

## What it does

- Reads a `task.txt` file.
- Builds a focused `workspace/context_pack.md`.
- Sends the context to a local Ollama model.
- Expects a strict `SEARCH` / `REPLACE` patch.
- Applies the patch to one target file.
- Runs tests.
- Writes `workspace/test_result.txt` and `workspace/git_diff.txt`.
- Rolls back if tests fail.

## Task format

`task.txt` must contain one line:

`target_file | test_type | test_file | task_description`

Example:

`app.py | pytest | tests/test_app.py | Implement divide(a, b) with divide-by-zero protection`

## Usage

```powershell
python .\agent.py --root . --task task.txt --model qwen2.5-coder:7b
```

Optional:

- `--workspace workspace`
- `--ollama-host http://localhost:11434`
- `--dry-run`

## Files written

- `workspace/context_pack.md`
- `workspace/search_replace.patch`
- `workspace/test_result.txt`
- `workspace/git_diff.txt`

## Notes

- The tool expects to run inside a git repository for Git Guard and diff validation.
- `workspace/` is ignored by git.
- This is a V1.35 prototype, so it only supports single-file editing.
