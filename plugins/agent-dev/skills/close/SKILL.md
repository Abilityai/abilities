---
name: close
description: Close the current issue without a git commit — adds summary comment and marks done. Use /commit instead when skill files changed.
argument-hint: "\"summary of what was done\""
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Close

Complete the current in-progress issue with a summary comment. For issues where skill files were modified, use `/commit` instead — it closes the issue and creates a git commit in one step.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Close issue |
| GitHub Labels | status:* | Yes | Yes | Update status |

## Process

### Step 1: Check for Uncommitted Changes

```bash
git status --short
```

If SKILL.md files appear in the output, warn:

> "There are modified skill files (`git status`). Run `/commit` instead to create a git commit alongside closing this issue."

Let user confirm they want to close without committing.

### Step 2: Find In-Progress Issue

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 5
```

If multiple in-progress, ask which to close. If none, report "No issue currently in progress."

### Step 3: Get Summary

If `$ARGUMENTS` is provided, use it as the summary. Otherwise ask:

> "What was accomplished? Brief summary for the closing comment."

### Step 4: Add Completion Comment

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY

---
*Closed via /close*"
```

### Step 5: Update Labels and Close

```bash
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 6: Confirm

```
## Closed: #$NUMBER — $TITLE

$SUMMARY

Next: `/backlog` to see remaining work, or `/claim` for the next issue.
```

## Error Handling

| Error | Action |
|-------|--------|
| No in-progress work | Report and suggest `/claim` |
| Multiple in-progress | List them, ask which to close |
| Modified skill files | Recommend `/commit` before closing |
