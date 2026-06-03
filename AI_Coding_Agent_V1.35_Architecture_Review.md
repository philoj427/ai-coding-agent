# AI Coding Agent V1.35 Architecture Review

# Executive Summary

This project aims to build a local-first AI Coding Agent running on:

- Ollama
- Qwen2.5-Coder 7B
- RTX 4060
- Python Orchestration

The primary goal is reliability rather than maximum model intelligence.

The design assumes a 7B model has limited context handling and therefore relies on:
- Context control
- Patch-based editing
- Git safety guards
- Automated testing
- Human approval

---

# Problem Statement

Direct AI code generation frequently causes:

- Regression bugs
- Accidental file modification
- Loss of existing functionality
- Context overload
- Unreliable behavior from smaller models

The system is designed to reduce these risks.

---

# Design Principles

1. AI makes decisions.
2. Python enforces rules.
3. Git provides safety.
4. Tests validate behavior.
5. Humans approve final changes.

---

# Why Patch-Based Editing

Rejected approach:

AI generates entire file
→ overwrite source code

Problems:

- Deletes existing logic
- Removes imports
- Breaks edge cases
- High regression risk

Chosen approach:

SEARCH/REPLACE patch
→ Python validates
→ Git verifies changes

Benefits:

- Minimal modification scope
- Easier review
- Safer rollback

---

# Why Not LangChain / LangGraph (V1)

Reasons:

- Additional complexity
- Harder debugging
- More moving parts
- Slower iteration

V1 prioritizes:

- Plain Python
- Transparent workflow
- Easy debugging

Future versions may evaluate LangGraph.

---

# V1.35 Architecture

User Task
↓
Context Builder
↓
Builder Agent (Qwen)
↓
SEARCH/REPLACE Patch
↓
Patch Applier
↓
Git Guard
↓
Test Runner
↓
Human Review
↓
Manual Commit

---

# Context Builder

Purpose:

Provide only relevant information.

Sources:

- Target source file
- Task description
- CODING_RULES.md
- Related test file

Output:

workspace/context_pack.md

Goal:

Reduce context size while increasing relevance.

---

# Git Guard

Responsibilities:

- Verify clean working tree
- Detect unauthorized modifications
- Limit changes to approved files
- Support rollback

Current strategy:

- allowed_files whitelist
- git diff --name-only validation

---

# Test Runner

Purpose:

Prevent broken code from surviving.

Supported:

- pytest
- npm test

Behavior:

Pass:
- show git diff

Fail:
- rollback changes

---

# Current Limitations

1. Single-file modification only
2. No retry loop
3. No architecture memory
4. No semantic search
5. No automatic debugging

These are intentional V1 constraints.

---

# V1.4 Proposal

Add:

- Gatekeeper Agent
- Retry Loop
- Self-correction

Flow:

Builder
↓
Tests
↓
Failure
↓
Gatekeeper
↓
Retry

---

# V2 Proposal

Add:

- Planner Agent
- Memory Database
- RAG
- Multi-file support

Flow:

Planner
↓
Context Builder
↓
Builder
↓
Gatekeeper

---

# Open Questions For Review

1. Is SEARCH/REPLACE the correct patch format?
2. Should rollback be file-level or repository-level?
3. How should multi-file permissions be managed?
4. What information should Context Builder prioritize?
5. When should RAG be introduced?
6. What metrics should define task success?

---

# Success Metrics

A successful task:

- Modifies only approved files
- Passes automated tests
- Produces clean git diff
- Requires minimal manual intervention
- Avoids regressions

