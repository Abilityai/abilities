---
name: backlog
description: Show current GitHub Issues backlog — what's in progress, what's next, priorities
argument-hint: "[all|in-progress|blocked]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-04-14
  author: Ability.ai
---

# Backlog

View the agent's task backlog from GitHub Issues.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | No | Task backlog |
| GitHub Labels | status:*, priority:* | Yes | No | Status and priority |

## Process

### Step 1: Parse Arguments

- `/backlog` or `/backlog status` → Show overview (in-progress + next up)
- `/backlog all` → Show all open issues by priority
- `/backlog in-progress` → Show only in-progress items
- `/backlog blocked` → Show blocked items
- `/backlog p0` or `/backlog p1` → Show specific priority

### Step 2: Verify GitHub CLI

```bash
gh auth status 2>&1 | head -3
```

If not authenticated, tell user to run `! gh auth login`.

### Step 3: Check Labels Exist

```bash
gh label list --json name --jq '.[].name' | grep -E '^(status:|priority:)' | sort
```

If missing required labels, offer to create them:

```bash
gh label create "status:todo" --color "0E8A16" --description "Ready to work"
gh label create "status:in-progress" --color "FBCA04" --description "Currently working"
gh label create "status:blocked" --color "D93F0B" --description "Waiting on something"
gh label create "status:done" --color "6E5494" --description "Finished"
gh label create "priority:p0" --color "B60205" --description "Do now"
gh label create "priority:p1" --color "D93F0B" --description "Do soon"
gh label create "priority:p2" --color "FBCA04" --description "Do eventually"
```

### Step 4: Query Issues

**For overview (default):**

```bash
# In-progress
gh issue list --label "status:in-progress" --state open --json number,title,labels,assignees,updatedAt

# Next up (P0 todos)
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,labels,assignees

# P1 todos  
gh issue list --label "priority:p1" --label "status:todo" --state open --json number,title,labels,assignees --limit 5
```

**For all:**
```bash
gh issue list --state open --json number,title,labels,assignees,updatedAt --limit 50
```

**For in-progress:**
```bash
gh issue list --label "status:in-progress" --state open --json number,title,labels,body,assignees,updatedAt
```

**For blocked:**
```bash
gh issue list --label "status:blocked" --state open --json number,title,labels,body,assignees
```

### Step 5: Format Output

Present results in a clear format:

```
## Backlog Overview

### In Progress (1)
| # | Title | Priority | Updated |
|---|-------|----------|---------|
| 42 | Implement feature X | p1 | 2h ago |

### Next Up — P0 (2)
| # | Title |
|---|-------|
| 45 | Critical bug fix |
| 46 | Urgent deploy |

### Queued — P1 (3)
| # | Title |
|---|-------|
| 48 | Add new endpoint |
| 49 | Refactor auth |
| 50 | Update docs |

**Total open: 12 issues**

View full backlog: [Issues →](https://github.com/owner/repo/issues)
```

## Outputs

- Formatted backlog summary
- Link to GitHub Issues page
- Label setup guidance if labels missing

## Error Handling

| Error | Action |
|-------|--------|
| gh not authenticated | Tell user to run `! gh auth login` |
| Not in a git repo | Report "Not in a GitHub repository" |
| No labels configured | Offer to create them (show commands) |
| API rate limited | Report error, suggest waiting |
