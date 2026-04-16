---
name: pick-work
description: Pick the next task from the backlog — selects highest priority todo, moves to in-progress
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-04-14
  author: Ability.ai
---

# Pick Work

Select the next task from the GitHub Issues backlog and mark it as in-progress.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Task backlog |
| GitHub Labels | status:*, priority:* | Yes | Yes | Update status |

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Repository has required labels (run `/backlog` to check/create)

## Process

### Step 1: Check Current Work

First, check if there's already work in progress:

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 1
```

If an issue is already in-progress, report it and ask if user wants to:
1. Continue that work (show issue details)
2. Park it and pick something new
3. Cancel

### Step 2: Select Issue

**If specific issue number provided ($ARGUMENTS):**

```bash
gh issue view $ARGUMENTS --json number,title,body,labels,state
```

Verify it exists and is open.

**If no argument — find highest priority todo:**

```bash
# Try P0 first
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1

# If none, try P1
gh issue list --label "priority:p1" --label "status:todo" --state open --json number,title,body,labels --limit 1

# If none, try P2
gh issue list --label "priority:p2" --label "status:todo" --state open --json number,title,body,labels --limit 1

# If none, try any without priority label
gh issue list --label "status:todo" --state open --json number,title,body,labels --limit 1

# If still none, try any open issue without status label
gh issue list --state open --json number,title,body,labels --limit 10
```

Filter out issues that already have `status:in-progress`, `status:blocked`, or `status:done`.

### Step 3: Move to In-Progress

Remove `status:todo` (if present) and add `status:in-progress`:

```bash
gh issue edit $ISSUE_NUMBER --remove-label "status:todo" --add-label "status:in-progress"
```

Add a comment noting work started:

```bash
gh issue comment $ISSUE_NUMBER --body "Started working on this."
```

### Step 4: Present Issue

Display the full issue for the agent/user to work on:

```
## Picked: #$NUMBER — $TITLE

**Priority:** $PRIORITY
**Labels:** $OTHER_LABELS

### Requirements

$ISSUE_BODY

---

**Status:** Now in-progress

When done, run `/close-work "summary of what was done"`
```

## Outputs

- Issue moved to `status:in-progress`
- Comment added to issue
- Full issue details displayed for work

## Error Handling

| Error | Action |
|-------|--------|
| No open issues | Report "Backlog is empty" |
| Issue not found | Report issue number not found |
| Already in-progress | Ask user how to proceed |
| Label update fails | Report error, suggest checking permissions |
