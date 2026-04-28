---
name: groom
description: Groom the backlog — tag untagged issues with skill:* labels, verify priorities, surface stale in-progress work
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Groom

Audit the open issue backlog for this agent. Tags issues with the skill they affect, surfaces missing priorities, and flags stale in-progress work. This is the agent-dev equivalent of backlog grooming — but the "areas" are skills, not features.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Backlog issues |
| GitHub Labels | skill:*, status:*, priority:* | Yes | Yes | Apply missing labels |
| Agent Skills | .claude/skills/ | Yes | No | Available skills to tag against |

## Process

### Step 1: Discover Available Skills

```bash
ls .claude/skills/
```

Build a list of skill names from the directory. These become the valid `skill:*` label values.

Also check if `skill:*` labels already exist in the repo:

```bash
gh label list --json name --jq '.[].name' | grep '^skill:'
```

Create any missing skill labels (one per skill directory):

```bash
gh label create "skill:$SKILL_NAME" --color "0075CA" --description "Issues affecting the $SKILL_NAME skill" 2>/dev/null || true
```

### Step 2: Fetch All Open Issues

```bash
gh issue list --state open --json number,title,body,labels --limit 100
```

### Step 3: Tag Untagged Issues

For each issue that has NO `skill:*` label:

1. Show the issue title and first 3 lines of body
2. List available skills
3. Ask (in one message, not per-issue): suggest which skill this issue most likely affects based on the title/body, then confirm or let user override

Tagging options per issue:
- A specific skill from `.claude/skills/` → apply `skill:<name>`
- **Project-level** → no skill tag (affects the agent as a whole, not a specific skill)
- **Skip** → leave untagged for now

Apply the label:

```bash
gh issue edit $NUMBER --add-label "skill:$SKILL_NAME"
```

### Step 4: Check Priority Coverage

For each open issue without a `priority:*` label:

List them grouped:
```
### Issues missing priority labels (3)
| # | Title | Status |
|---|-------|--------|
| 12 | Fix claim flow | todo |
```

Offer to set priorities in batch: "Assign priorities? (p0/p1/p2 for each, or skip)"

```bash
gh issue edit $NUMBER --add-label "priority:$PRIORITY"
```

### Step 5: Flag Stale In-Progress

```bash
gh issue list --label "status:in-progress" --state open --json number,title,updatedAt
```

For any in-progress issue not updated in the last 48 hours, flag it:

```
### Stale in-progress (1)
| # | Title | Last updated |
|---|-------|-------------|
| 7 | Update autoplan flow | 3 days ago |
```

Offer to move stale issues back to `status:todo` or add a check-in comment.

### Step 6: Summary

```
## Groom Complete

- Tagged: X issues with skill labels
- Prioritized: Y issues
- Stale flagged: Z in-progress issues

Run `/roadmap` to see the skill-grouped view, or `/claim` to start the next issue.
```

## Error Handling

| Error | Action |
|-------|--------|
| No `.claude/skills/` directory | Warn: "No skills found. Is this an agent repo?" |
| gh not authenticated | Tell user to run `! gh auth login` |
| No open issues | Report "Backlog is empty — nothing to groom" |
| Label creation fails | Note and continue |
