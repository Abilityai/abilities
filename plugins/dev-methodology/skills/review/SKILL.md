---
name: review
description: Pre-landing code review for structural issues — SQL safety, race conditions, auth boundaries, credential exposure, scope drift, enum completeness, and test gaps. Produces a findings report with CRITICAL (block merge) and INFORMATIONAL categories.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
argument-hint: "[pr-number or branch]"
automation: manual
---

# Code Review

Pre-landing diff review for structural issues. Run before opening a PR or before merging. Catches problems that pass tests but indicate design or safety issues.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Git diff | current branch | ✅ | | Changes to review |
| Architecture | `docs/memory/architecture.md` | ✅ | | Auth boundaries, patterns |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | | Expected behavior |
| GitHub Issue | GitHub repo | ✅ | | Scope definition |

## Arguments

- `$ARGUMENTS`: PR number, branch name, or empty (reviews current branch vs default base).

## Process

### Step 1: Get the Diff

**If PR number provided:**
```bash
gh pr diff $ARGUMENTS
gh pr view $ARGUMENTS --json title,body,baseRefName,headRefName,files
```

**If branch or no argument:**
```bash
git diff main...HEAD
git log main..HEAD --oneline
```

### Step 2: SQL & Data Safety

Scan diff for:
- Raw string interpolation in SQL queries (f-string, % format, `.format()` with user input)
- Missing parameterized queries
- Mass assignment patterns (e.g., `**kwargs` passed directly to ORM create/update)
- Unvalidated bulk operations

**Severity**: CRITICAL if user-controlled input reaches a query without parameterization.

### Step 3: Race Conditions

Scan for:
- Check-then-act patterns on shared state (TOCTOU: read value → make decision → write based on old value)
- Missing locks on shared mutable objects
- Docker container startup races (service A assumes service B is ready)
- Async functions that read-modify-write without awaiting intermediate results

**Severity**: CRITICAL if exploitable under concurrent load.

### Step 4: Auth Boundaries

Check:
- New endpoints — do they have auth middleware applied?
- Resource ownership checks — can user A access user B's data?
- Admin-only operations — is the admin check present and correct?
- Middleware order — auth before business logic?

**Severity**: CRITICAL if an endpoint is reachable without proper authentication.

### Step 5: Credential Exposure

Scan diff for:
- Secrets, tokens, API keys in code or tests
- Credentials in error messages or logs
- Credentials in API responses (even partial)
- `.env` files committed

**Severity**: CRITICAL if real credentials are present.

### Step 6: Scope Drift

Compare diff against the linked issue's acceptance criteria:
- Are there changes unrelated to the stated issue?
- Were unrelated files modified (incidental refactoring)?
- Does the diff do more or less than the issue requires?

**Severity**: INFORMATIONAL — flag for discussion, don't block.

### Step 7: Enum Completeness

When new enum values are added:
- Is the new value handled in all `switch`/`match` statements that reference the enum?
- Are there `if isinstance(x, SomeEnum)` checks that need updating?
- Are there serializers, display formatters, or migration code that need updating?

**Severity**: CRITICAL if a code path silently ignores the new value.

### Step 8: Test Gaps

For each new endpoint, function, or behavior in the diff:
- Does a corresponding test exist?
- Does the test cover the happy path?
- Does the test cover the primary error/auth case?

**Severity**: INFORMATIONAL — flag gaps, don't block on coverage alone.

### Step 9: Fix-First Flow (Critical Findings)

If CRITICAL findings exist, offer to fix them:

```
CRITICAL findings detected. Would you like me to fix these before proceeding?
[Y] Fix all criticals → implement fixes → re-run review
[N] Show report only → you fix manually
```

### Step 10: Generate Findings Report

```markdown
## Code Review Report

**Branch**: [branch] → [base]
**Commits**: [N commits]
**Files changed**: [N files]

### CRITICAL Findings (block merge)
| # | Category | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | SQL Safety | src/api/users.py | 42 | Raw f-string in query |

### INFORMATIONAL Findings (review recommended)
| # | Category | File | Line | Note |
|---|----------|------|------|------|
| 1 | Scope Drift | src/utils/helpers.py | 15 | Unrelated refactor |

### Recommendation
**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

Rationale: [one sentence]
```

## Severity Reference

| Level | Action |
|-------|--------|
| **CRITICAL** | Block merge — must be resolved |
| **INFORMATIONAL** | Flag for awareness — human judgment call |

## Completion Checklist

- [ ] Diff obtained
- [ ] SQL & data safety checked
- [ ] Race conditions checked
- [ ] Auth boundaries checked
- [ ] Credential exposure checked
- [ ] Scope drift checked
- [ ] Enum completeness checked
- [ ] Test gaps checked
- [ ] Fix-first flow offered if criticals found
- [ ] Findings report generated with recommendation
