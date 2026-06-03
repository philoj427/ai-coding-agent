# AI Coding Agent Project Goals

## Vision

Build a local-first AI Coding Agent running on:

- Ollama
- Qwen2.5-Coder 7B
- RTX 4060
- Python orchestration

The objective is not to maximize model size.

The objective is to maximize reliability through process control.

---

## Core Philosophy

AI should make decisions.

Python should enforce rules.

Git should provide safety.

Tests should validate changes.

---

## Long-Term Architecture

SA / Planner
↓
Context Builder
↓
Builder Agent
↓
Patch Applier
↓
Git Guard
↓
Test Runner
↓
Gatekeeper
↓
Human Approval
↓
Commit

---

## Non-Goals

- Fully autonomous coding
- Automatic commits without review
- Replacing software engineering processes
- Large multi-agent chat systems

---

## Key Design Principles

1. Patch-based editing
2. Strict safety guards
3. Test-first validation
4. Human approval before commit
5. Small-context optimization for 7B models
6. Local-first execution

---

## Planned Roadmap

### V1.35
- Single file editing
- Context Builder
- Git Guard
- Test Runner

### V1.4
- Gatekeeper
- Retry loop
- Error-driven self-correction

### V2
- Planner Agent
- Memory Database
- RAG
- Multi-file editing

### V3
- Full project awareness
- Change history
- Architecture memory
- Long-term project knowledge

---

## Success Criteria

A small coding task should:

1. Be completed by the AI.
2. Pass tests.
3. Produce a clean git diff.
4. Avoid unauthorized file modifications.
5. Require minimal manual intervention.
