---
name: read-docs
description: Load all project documentation into context for this session.
allowed-tools: Read, Bash
user-invocable: true
automation: manual
---

# Read Project Documentation

Load all project documentation into context for this session.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Requirements | `docs/memory/requirements.md` | ✅ | | Feature requirements |
| Architecture | `docs/memory/architecture.md` | ✅ | | System design |
| Feature Flows | `docs/memory/feature-flows.md` | ✅ | | Flow index |
| GitHub Issues | GitHub repo | ✅ | | P0/P1 issues |
| Changelog | `docs/memory/changelog.md` | ✅ | | Recent changes |

## Process

### Step 1: Read Core Documentation

Read these files in full (no summaries until all are loaded):
- `docs/memory/requirements.md` - Feature requirements (SINGLE SOURCE OF TRUTH)
- `docs/memory/architecture.md` - Current system design
- `docs/memory/feature-flows.md` - Feature flow index

### Step 2: Query GitHub Roadmap

Query P0 and P1 issues from GitHub Issues:

```bash
# P0 issues (urgent, do immediately)
gh issue list --label "priority-p0" --state open --json number,title,labels

# P1 issues (critical path)
gh issue list --label "priority-p1" --state open --json number,title,labels
```

### Step 3: Read Recent Changelog

Read changelog using Bash (file may be large, only need recent entries):
```bash
head -150 docs/memory/changelog.md
```

Note: `CLAUDE.md` is loaded automatically at session start - no need to read it again.

### Step 4: Understand Project State

- What features are implemented?
- What's currently in progress?
- What are the current priorities from GitHub Issues?

### Step 5: Report Completion

```
Documentation loaded. Ready to work on {{PROJECT_NAME}}.

P0: [P0 issues or "None"]
P1: [P1 issues]
Recent: [most recent changelog entry]
```

## When to Use

- At the start of a new session
- When you need to understand the current project state
- Before starting work on a new task
- When switching between different areas of the codebase

## Principle

Load context first, then act. Never modify code without understanding the current state.

## Completion Checklist

- [ ] Requirements.md read
- [ ] Architecture.md read
- [ ] Feature-flows.md read
- [ ] P0/P1 issues queried from GitHub
- [ ] Recent changelog reviewed
- [ ] Summary reported
