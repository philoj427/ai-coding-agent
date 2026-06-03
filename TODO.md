# TODO

## Completed Core Work

- [x] Add a local Gatekeeper step before patch application
- [x] Reject fenced, no-op, malformed, and duplicate-def patches before `apply_search_replace_patch()`
- [x] Retry once after patch-generation or patch-parse failure
- [x] Keep failure cleanup repo-level and deterministic
- [x] Write structured failure reasons to `workspace/test_result.txt`
- [x] Keep `workspace/git_diff.txt` empty on failure
- [x] Add tests for Gatekeeper rejection paths
- [x] Add tests for retry behavior
- [x] Add tests for failure cleanup paths

## Next Phase

- [ ] Run the 50-task pressure test suite
- [ ] Collect failure patterns from all 50 runs
- [ ] Summarize the problems before changing code
- [ ] Revisit the Gatekeeper rules only after evidence is collected

## Non-Goals

- [ ] Multi-file editing
- [ ] Planner / coordinator agents
- [ ] RAG
- [ ] Long-term memory
- [ ] Automatic commit or push
