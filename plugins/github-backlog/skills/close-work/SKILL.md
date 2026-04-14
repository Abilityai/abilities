---
name: close-work
description: Mark current work done — adds summary comment, updates labels, closes issue
argument-hint: "\"summary of what was done\""
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-14
  author: Ability.ai
---

# Close Work

Complete the current in-progress task. Adds a summary comment, updates status, and closes the issue.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Close issue |
| GitHub Labels | status:* | Yes | Yes | Update status |

## Process

### Step 1: Find In-Progress Issue

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 5
```

If multiple in-progress issues, ask which one to close.
If none found, report "No in-progress work to close."

### Step 2: Parse Summary

The argument should be a summary of work completed. If not provided, ask:

> "What was accomplished? Provide a brief summary for the closing comment."

### Step 3: Add Completion Comment

```bash
gh issue comment $ISSUE_NUMBER --body "## Completed

$SUMMARY

---
*Closed by agent via /close-work*"
```

### Step 4: Update Labels and Close

Remove in-progress, optionally add done label, then close:

```bash
gh issue edit $ISSUE_NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $ISSUE_NUMBER --reason completed
```

### Step 5: Confirm

```
## Closed: #$NUMBER — $TITLE

**Summary:** $SUMMARY

Issue closed and marked done.

Next: Run `/backlog` to see remaining work, or `/pick-work` to start the next task.
```

## Outputs

- Summary comment added to issue
- Issue labeled `status:done`
- Issue closed with "completed" reason
- Confirmation message

## Error Handling

| Error | Action |
|-------|--------|
| No in-progress work | Report and suggest `/pick-work` |
| Multiple in-progress | List them, ask which to close |
| Close fails | Report error, check permissions |
| No summary provided | Ask for summary before closing |
