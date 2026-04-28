---
name: sprint
description: Full dev cycle orchestrator — runs the complete pipeline for an issue from claim through PR. Orchestrates autoplan, implement, review, cso, sync-feature-flows, and commit in sequence with human approval gates.
allowed-tools: Bash, Read, Skill
user-invocable: true
argument-hint: "[issue-number]"
automation: gated
---

# Sprint

Orchestrate the complete development pipeline for a single issue. Each step runs in sequence; human approval gates are inserted at key decision points.

## Pipeline

```
/claim → /autoplan → [human approves plan] → /implement → /review → /cso --diff → /sync-feature-flows → /commit + PR
```

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issue | GitHub repo | ✅ | ✅ | Issue assignment + status labels |
| All skill states | see individual skills | ✅ | ✅ | Each step delegates to its skill |

## Arguments

- `$ARGUMENTS`: GitHub issue number (e.g., `42` or `#42`). If omitted, checks current branch for issue number or asks.

## Process

### Step 1: Claim the Issue

```bash
ISSUE=${ARGUMENTS#\#}
gh issue comment $ISSUE --body "/claim"
# Alternatively, assign directly:
gh issue edit $ISSUE --add-assignee @me --add-label "status-in-progress"
```

Confirm assignment. If already assigned to someone else, ask before proceeding.

### Step 2: Create Feature Branch

```bash
SLUG=$(gh issue view $ISSUE --json title --jq '.title' | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | cut -c1-40)
git checkout -b feature/${ISSUE}-${SLUG}
```

### Step 3: Autoplan

Run the planning pipeline:
```
/autoplan $ISSUE
```

**GATE**: Present the plan. Ask:
> "Does this plan look right? [Y to proceed / describe changes needed]"

Do not proceed until the user approves the plan.

### Step 4: Implement

Run implementation with the approved plan as context:
```
/implement $ISSUE
```

### Step 5: Code Review

Run pre-landing code review on the branch diff:
```
/review
```

If CRITICAL findings exist, fix them before continuing.

### Step 6: Security Audit

Run scoped security audit on branch changes:
```
/cso --diff
```

If CRITICAL findings exist, fix them before continuing.

### Step 7: Sync Feature Flows

Update documentation for behavior changes:
```
/sync-feature-flows recent
```

### Step 8: Commit and Open PR

Run commit + PR creation:
```
/commit closes #$ISSUE
```

Then open a PR:
```bash
gh pr create \
  --title "$(gh issue view $ISSUE --json title --jq '.title')" \
  --body "Fixes #$ISSUE" \
  --base main
```

### Step 9: Summary

Report pipeline completion:

```markdown
## Sprint Complete: Issue #[N]

| Step | Status |
|------|--------|
| Claim | ✅ |
| Branch created | ✅ feature/[N]-[slug] |
| Autoplan | ✅ approved |
| Implement | ✅ |
| Code review | ✅ [N criticals / clean] |
| Security audit | ✅ [N criticals / clean] |
| Feature flows | ✅ synced |
| PR opened | ✅ #[pr-number] |
```

## Approval Gates

| Gate | When | Action if rejected |
|------|------|--------------------|
| Plan approval | After autoplan | Revise plan, re-present |
| Critical review findings | After /review | Fix before proceeding |
| Critical security findings | After /cso | Fix before proceeding |

## Completion Checklist

- [ ] Issue claimed and branch created
- [ ] Autoplan completed and approved
- [ ] Feature implemented
- [ ] Code review clean (no unresolved criticals)
- [ ] Security audit clean (no unresolved criticals)
- [ ] Feature flows synced
- [ ] PR opened with issue reference
