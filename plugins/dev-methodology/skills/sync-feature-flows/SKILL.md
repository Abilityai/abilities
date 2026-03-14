---
name: sync-feature-flows
description: Analyze code changes and update affected feature flow documentation. Creates new flows for new features, updates existing flows for modified code.
allowed-tools: Agent, Read, Write, Edit, Grep, Glob, Bash
user-invocable: true
argument-hint: "[commit-range|file-list|'recent']"
automation: gated
---

# Sync Feature Flows

Analyze code changes and synchronize feature flow documentation.

## Purpose

Keep feature flow documentation in sync with code changes by:
- Detecting which features were affected by recent changes
- Updating existing flow documents with new file paths, line numbers, endpoints
- Creating new flow documents for newly introduced features
- Maintaining a minimal, navigable index in feature-flows.md

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Feature Flows Index | `docs/memory/feature-flows.md` | ✅ | ✅ | Flow index (keep minimal) |
| Feature Flow Docs | `docs/memory/feature-flows/*.md` | ✅ | ✅ | Individual flow documents |
| Git History | `.git` | ✅ | | Recent changes |
| Source Code | `src/` | ✅ | | All source files |

## Arguments

- `$ARGUMENTS`:
  - `recent` or empty: Analyze last 5 commits
  - `HEAD~N..HEAD`: Specific commit range
  - `file1.py file2.vue`: Specific files to analyze

## Process

### Step 1: Identify Changed Files

```bash
# If 'recent' or no argument
git log --oneline -5 --name-only | grep -E '\.(py|vue|js|ts|tsx|jsx)$' | sort -u

# If commit range provided
git diff --name-only $ARGUMENTS | grep -E '\.(py|vue|js|ts|tsx|jsx)$'
```

### Step 2: Map Files to Features

Find which existing flow documents reference the changed files:
```bash
grep -rl "changed-file-name" docs/memory/feature-flows/*.md
```

### Step 3: Check Existing Flows

Categorize:
- **Needs Update**: Flow exists but code changed significantly
- **Needs Creation**: No flow exists for this feature
- **Up to Date**: Flow exists and changes are minor

### Step 4: Present Analysis

[APPROVAL GATE]

Present findings and wait for approval before making changes.

### Step 5: Spawn Feature Flow Analyzer

For each flow that needs update or creation, use the feature-flow-analyzer agent.
Run agents sequentially to avoid conflicts in feature-flows.md.

### Step 6: Verify Index Size

```bash
wc -l docs/memory/feature-flows.md
```

If > 400 lines, the index may be bloated. Review and condense.

### Step 7: Report Completion

Report updated flows, created flows, and index status.

## Completion Checklist

- [ ] Changed files identified
- [ ] Files mapped to feature flows
- [ ] Existing flows checked
- [ ] Analysis presented (if manual)
- [ ] Feature-flow-analyzer spawned for each affected flow
- [ ] Index size verified (< 400 lines)
- [ ] Completion report generated
