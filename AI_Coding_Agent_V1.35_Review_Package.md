# AI Coding Agent V1.35 Review Package

## Current Architecture

User Task
→ Context Builder
→ Ollama (Qwen2.5-Coder 7B)
→ SEARCH/REPLACE Patch
→ Patch Applier
→ Git Guard
→ Test Runner
→ Human Review (git diff)

## Core Components

### 1. Builder Agent
- Model: qwen2.5-coder:7b
- Output format: SEARCH/REPLACE only
- No markdown code fences
- No explanations

### 2. Context Builder
Inputs:
- Target source file
- Task description
- CODING_RULES.md
- Related test file

Output:
- workspace/context_pack.md

### 3. Patch Applier
Rules:
- SEARCH block must exist
- SEARCH block must be unique
- Preserve indentation
- Use SEARCH/REPLACE instead of whole-file overwrite

### 4. Git Guard
Rules:
- Repository must be clean before execution
- workspace/ added to .gitignore
- Only allowed files may be modified
- Unauthorized changes cause failure

### 5. Test Runner
Supported:
- pytest
- npm test
- none

Output:
- workspace/test_result.txt

## task.txt Format

target_file | test_type | test_file | task_description

Example:

math_tool.py | pytest | tests/test_math.py | Implement divide(a,b) with divide-by-zero protection

## Workspace Files

workspace/
- task.txt
- context_pack.md
- search_replace.patch
- test_result.txt
- git_diff.txt

## Safety Rules

1. Git working tree must be clean.
2. workspace/ must be ignored by Git.
3. SEARCH block must match exactly one location.
4. Unauthorized file modifications are rejected.
5. Failed tests trigger rollback.
6. No automatic commit in V1.35.
7. Human reviews git diff before commit.

## Known Future Improvements

V1.4
- Gatekeeper Agent
- Retry Loop
- Self-correction

V2
- Planner Agent
- Memory DB
- RAG
- Multi-file editing

## Review Focus

Please review:
1. Security of patch application
2. Git Guard design
3. Context Builder strategy
4. Test Runner strategy
5. Failure and rollback handling
6. Scalability toward multi-file tasks
