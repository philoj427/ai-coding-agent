# Pressure Test Findings

Run summary:

- Tasks: 50
- Passed: 29
- Failed: 21

## Main Failure Buckets

1. `SEARCH block must match exactly one location, found 0`
- The model often proposed a patch whose search text did not exist in the current file state.
- This points to weak task grounding and search-text drift, not just a patch-format problem.

2. `py_compile` failures
- A small number of patches produced invalid Python syntax.
- These are usually malformed multiline edits or incomplete structural rewrites.

3. Test failures
- A few patches compiled but changed behavior in ways the existing tests caught.
- These are the most important because they represent real semantic regressions.

4. Malformed patch output
- One task produced a missing `END_REPLACE`.
- This is a format failure and should continue to be retried or rejected.

## What Improved

- The Gatekeeper spacing rule was tightened and no longer false-fires on normal module docstrings.
- Structured failure reports now make it clear which stage failed and why.
- The 50-task runner successfully reset the repo between tasks, so failures were isolated.

## Likely Fixes to Research Next

- Add exact current-file snippets to the context pack so the model anchors search text better.
- Make docstring-only tasks and code-refactor tasks use slightly different prompts.
- Add a syntax-oriented retry instruction when the first attempt hits `py_compile`.
- Consider an AST-based preflight for helper-extraction tasks before letting tests run.
- Add a stronger reminder in the prompt that replacements must preserve all existing behavior unless the task says otherwise.

