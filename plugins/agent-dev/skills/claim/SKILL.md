---
name: claim
description: Claim the next issue from the backlog — picks highest priority todo, moves it to in-progress
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Claim

Select the next issue from the GitHub Issues backlog and mark it as in-progress.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Task backlog |
| GitHub Labels | status:*, priority:*, skill:* | Yes | Yes | Update status |

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- Repository has required labels (run `/backlog` to check/create)

## Process

### Step 1: Check Current Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 1
```

If an issue is already in-progress, report it and ask:
1. Continue that work (show full issue)
2. Park it and claim something new
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

# If none, try any status:todo
gh issue list --label "status:todo" --state open --json number,title,body,labels --limit 1
```

### Step 3: Move to In-Progress

```bash
gh issue edit $ISSUE_NUMBER --remove-label "status:todo" --add-label "status:in-progress"
gh issue comment $ISSUE_NUMBER --body "Claimed — starting work."
```

### Step 4: Present Issue

Display the full issue. If a `skill:*` label is present, surface it prominently:

```
## Claimed: #$NUMBER — $TITLE

**Priority:** $PRIORITY
**Skill scope:** $SKILL_LABEL  → open `.claude/skills/$SKILL_NAME/SKILL.md`

### Requirements

$ISSUE_BODY

---

Next steps:
- Run `/autoplan` to analyze the change before implementing
- Or run `/adjust-playbook $SKILL_NAME` / `/create-playbook` directly
- When done, run `/commit` to close this issue
```

If no `skill:*` label present, note: "No skill tag — run `/groom` to tag this issue, or proceed with `/autoplan`."

## Outputs

- Issue moved to `status:in-progress`
- Comment added to issue
- Full issue details with skill scope displayed

## Error Handling

| Error | Action |
|-------|--------|
| No open issues | Report "Backlog is empty" |
| Issue not found | Report issue number not found |
| Already in-progress | Ask user how to proceed |
| Label update fails | Report error, check permissions |
