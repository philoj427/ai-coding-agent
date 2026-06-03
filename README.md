# AI Coding Agent

Local-first AI coding agent for safe, single-file patching with local Ollama.

## Workflow

Read `workspace/task.txt`, build a context pack, send it to local Ollama, run the patch through Gatekeeper, apply a strict `SEARCH` / `REPLACE` patch, run tests, and record the result under `workspace/`.

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
- V1.35 supports one target file only.
- SEARCH blocks must match exactly one location.
- Failed tests trigger rollback.
- No automatic commit is performed.

## Current Status

- Latest workflow run: success, with a real diff applied to `demo_add.py`
- Gatekeeper is wired into the workflow before patch application
- Latest validation: `python -m unittest discover -s tests` passed with 27 tests
- Safety gates: Gatekeeper, retry once, structured failure reports, no-op patch rejection, duplicate top-level function rejection, line-level indentation rejection, strict SEARCH/REPLACE matching, Git Guard, rollback, and `py_compile`

See [TEST_STATUS.md](TEST_STATUS.md) for the latest run details and failure coverage.

## Roadmap

- [V1.4.md](V1.4.md)
- [TODO.md](TODO.md)

## Task Format

`target_file | test_type | test_file | task_description`

Supported `test_type` values: `pytest`, `npm test`, `none`
