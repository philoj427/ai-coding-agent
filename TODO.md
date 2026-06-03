# TODO

## V1.4 Implementation

- [ ] Add a local Gatekeeper step before patch application
- [ ] Reject fenced, no-op, and malformed patches before `apply_search_replace_patch()`
- [ ] Retry once after patch-generation or patch-parse failure
- [ ] Keep failure cleanup repo-level and deterministic
- [ ] Write failure reasons to `workspace/test_result.txt`
- [ ] Keep `workspace/git_diff.txt` empty on failure
- [ ] Add tests for Gatekeeper rejection paths
- [ ] Add tests for retry behavior
- [ ] Add tests for failure cleanup paths

## Non-Goals

- [ ] Multi-file editing
- [ ] Planner / coordinator agents
- [ ] RAG
- [ ] Long-term memory
- [ ] Automatic commit or push

