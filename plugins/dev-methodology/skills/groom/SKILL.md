---
name: groom
description: Backlog grooming — audit board coverage, detect unranked items, review priority ordering, and propose rank updates. Requires human approval before applying any changes.
allowed-tools: Bash, Read
user-invocable: true
argument-hint: ""
automation: gated
---

# Groom

Audit the GitHub Issues backlog for health: coverage, ranking, priority ordering, and stale items. Propose changes; apply only after human approval.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | GitHub repo | ✅ | ✅ | Open issues + labels |
| GitHub Project | GitHub Projects | ✅ | ✅ | Board columns, Rank/Tier fields |

## Process

### Step 1: Fetch Current Backlog

```bash
# All open issues
gh issue list --state open --json number,title,labels,assignees,milestone --limit 200

# By priority
gh issue list --label "priority-p0" --state open --json number,title,labels
gh issue list --label "priority-p1" --state open --json number,title,labels
gh issue list --label "priority-p2" --state open --json number,title,labels
gh issue list --label "priority-p3" --state open --json number,title,labels

# In-progress and blocked
gh issue list --label "status-in-progress" --state open --json number,title,assignees
gh issue list --label "status-blocked" --state open --json number,title,labels
```

### Step 2: Board Coverage Audit

Check that every open issue is on the project board:

```bash
# Issues not in any board column (adjust project number as needed)
gh api graphql -f query='
  query {
    repository(owner: "OWNER", name: "REPO") {
      issues(first: 100, states: OPEN) {
        nodes { number title projectItems(first: 1) { totalCount } }
      }
    }
  }
'
```

Flag issues with `projectItems.totalCount == 0`.

**Action**: Add unlisted issues to the board.

### Step 3: Rank and Tier Coverage

Every `Todo` and `In Progress` issue should have:
- A **Rank** (numeric ordering within its tier)
- A **Tier** (P1a, P1b, P1c for P1 issues; or simple rank for P2/P3)

Flag issues missing Rank or Tier.

### Step 4: Priority Ordering Review

Check that the current ranking makes sense:

1. **P0 issues should all be In Progress** — if any P0 is in Todo, flag for immediate attention
2. **P1a issues should be ranked above P1b**, P1b above P1c
3. **Bugs should rank above features at the same tier** (they're regressions, not new work)
4. **Blocked issues should have a `status-blocked` label** and a note on what's blocking them

### Step 5: Stale Issue Detection

Flag issues that may need closure or re-evaluation:
- Open issues with no activity in 90+ days
- Issues marked `status-in-progress` with no assignee
- Issues with `status-in-dev` that are still open but the PR appears merged

```bash
# Find stale issues (no updates in 90 days)
gh issue list --state open --json number,title,updatedAt | \
  jq '[.[] | select(.updatedAt < (now - 7776000 | todate))]'
```

### Step 6: Produce Grooming Report

```markdown
## Backlog Grooming Report

**Date**: [date]
**Total open issues**: N

### Coverage Gaps
Issues not on project board: [N]
- #[number]: [title]

### Missing Rank/Tier
Issues without ranking: [N]
- #[number]: [title] (priority-p1, no tier)

### Priority Concerns
- P0 issues in Todo (should be in progress): [list or "None"]
- Bugs ranking below same-tier features: [list or "None"]
- Blocked issues without blocker note: [list or "None"]

### Stale Issues (90+ days)
- #[number]: [title] (last updated [date])

### Proposed Changes
1. Add #N, #M to project board
2. Assign Tier P1b to #N (consistent with similar scope issues)
3. Re-rank #42 above #38 (bug vs feature, same tier)
4. Close #17 — appears resolved per git history
```

**GATE**: Present report to user. Ask:
> "Apply these changes? [Y to apply all / list specific items to skip / N to cancel]"

### Step 7: Apply Approved Changes

Apply only the changes the user approved:

```bash
# Add labels
gh issue edit $N --add-label "status-ready"

# Add to project board
gh project item-add [project-number] --owner [owner] --url [issue-url]

# Close stale issues
gh issue close $N --reason "not planned"
```

Confirm each change with a brief output line.

## Completion Checklist

- [ ] All open issues fetched
- [ ] Board coverage audited
- [ ] Rank and tier coverage checked
- [ ] Priority ordering reviewed
- [ ] Stale issues detected
- [ ] Grooming report produced
- [ ] Human approval obtained
- [ ] Approved changes applied
