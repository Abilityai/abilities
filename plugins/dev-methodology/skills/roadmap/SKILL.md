---
name: roadmap
description: Query GitHub Issues for roadmap priorities and status
allowed-tools: Bash, Read, Write
user-invocable: true
automation: manual
---

# Roadmap

Query GitHub Issues to check current priorities, blockers, and work status.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| GitHub Issues | GitHub repo | Yes | No |
| GitHub Labels | priority-p0/p1/p2/p3, type-*, status-* | Yes | No |

## Process

### Step 1: Parse Command Arguments

- `/roadmap` or `/roadmap status` -> Show P0/P1 priorities
- `/roadmap all` -> Show all open issues by priority
- `/roadmap blockers` or `/roadmap blocked` -> Show blocked items
- `/roadmap in-progress` -> Show items being worked on
- `/roadmap create <title>` -> Create a new issue

### Step 2: Query GitHub Issues

**For status (default):**
```bash
gh issue list --label "priority-p0" --state open --json number,title,labels,assignees
gh issue list --label "priority-p1" --state open --json number,title,labels,assignees
```

**For all:**
```bash
gh issue list --state open --json number,title,labels,assignees --limit 50
```

**For blockers:**
```bash
gh issue list --label "status-blocked" --state open --json number,title,labels,assignees
```

**For in-progress:**
```bash
gh issue list --label "status-in-progress" --state open --json number,title,labels,assignees
```

### Step 3: Format Output

Present results in a clear table format.

### Step 4: Create Issue (if requested)

If user runs `/roadmap create <title>`:
1. Ask for priority and type
2. Create issue with labels
3. Return the issue URL

## Quick Commands

| Command | Description |
|---------|-------------|
| `/roadmap` | Show P0/P1 priorities |
| `/roadmap all` | All open issues |
| `/roadmap blocked` | Blocked items |
| `/roadmap in-progress` | Work in progress |
| `/roadmap create <title>` | Create new issue |

## Completion Checklist

- [ ] Command arguments parsed correctly
- [ ] GitHub Issues queried successfully
- [ ] Results formatted as table
- [ ] GitHub link provided for full view
