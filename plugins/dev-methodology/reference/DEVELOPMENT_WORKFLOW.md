# Development Workflow

> **For developers and AI assistants** working on this project.
> This guide defines the Software Development Lifecycle (SDLC) and explains how to use the project's tools, agents, and documentation effectively.

---

## Software Development Lifecycle (SDLC)

Four stages, tracked via `status-*` labels on GitHub Issues (the authoritative surface). The project board mirrors these for visual tracking.

```
Todo → In Progress → In Dev → Done
```

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SDLC STAGES                                 │
├──────────┬──────────────────────────────────────────────────────────┤
│          │                                                          │
│ TODO     │  Issue created, triaged with priority + type labels      │
│          │  Acceptance criteria defined before work begins           │
│          │                                                          │
├──────────┼──────────────────────────────────────────────────────────┤
│          │                                                          │
│ IN       │  /claim → /autoplan → approve → /implement               │
│ PROGRESS │  → /review → /cso --diff → /sync-feature-flows → PR     │
│          │  Label: status-in-progress                               │
│          │                                                          │
├──────────┼──────────────────────────────────────────────────────────┤
│          │                                                          │
│ IN DEV   │  PR merged — feature is shippable                        │
│          │  Awaiting next release cut                               │
│          │  Label: status-in-dev                                    │
│          │                                                          │
├──────────┼──────────────────────────────────────────────────────────┤
│          │                                                          │
│ DONE     │  Release PR merged + tagged                              │
│          │  Issues auto-closed via Closes #N in release body        │
│          │                                                          │
└──────────┴──────────────────────────────────────────────────────────┘
```

---

## Development Pipeline

The full pipeline for an issue (or run `/sprint` to orchestrate all steps):

```
/claim → /autoplan → [approve] → /implement → /review → /cso --diff → /sync-feature-flows → PR
```

| Step | Skill | What it does |
|------|-------|-------------|
| 1. Claim | `/claim` (GitHub) | Auto-assign + status-in-progress label |
| 2. Plan | `/autoplan` | Strategy + engineering + security review with auto-decisions |
| 3. Approve | *(manual)* | Review autoplan output, approve or revise |
| 4. Implement | `/implement` | Code the feature, write tests |
| 5. Code review | `/review` | Pre-landing diff review for structural issues |
| 6. Security audit | `/cso --diff` | Scan changes for vulnerabilities (P0/P1 recommended) |
| 7. Sync docs | `/sync-feature-flows` | Update feature flow documentation |
| 8. Ship | `/commit` + PR | Commit, push, create pull request |

---

## Context Loading

Always start a development session by loading context:

```
/read-docs
```

For targeted work, read the relevant feature flow directly:

```
@docs/memory/feature-flows/user-login.md
```

---

## Prioritization

| Priority | Label | Meaning |
|----------|-------|---------|
| **P0** | `priority-p0` | Blocking/urgent — drop everything |
| **P1** | `priority-p1` | Critical path — current focus |
| **P2** | `priority-p2` | Important — next up |
| **P3** | `priority-p3` | Nice-to-have |

Within P1, issues have a **Tier** for sub-prioritization: **P1a** (highest) → **P1b** → **P1c**.

**Rule**: Work P0 first, then P1 by Tier, then by Rank (lowest number first). Bugs above features at the same tier.

---

## Review Checklist

### Code Review (`/review`) checks

| Category | Check |
|----------|-------|
| **SQL & Data Safety** | Raw queries, missing parameterization, mass assignment |
| **Race Conditions** | Shared state, TOCTOU, Docker container races |
| **Auth Boundaries** | Missing auth, resource ownership, admin access |
| **Credential Exposure** | Secrets in logs, error messages, responses |
| **Scope Drift** | Diff matches the issue requirements |
| **Enum Completeness** | New values handled everywhere they're referenced |
| **Test Gaps** | New endpoints/paths without tests |

### Process Validation (`/validate-pr`) checks

| Category | Check |
|----------|-------|
| **Commit Messages** | Descriptive, conventional prefix (feat/fix/refactor/docs) |
| **Requirements** | Updated if new feature or scope change |
| **Architecture** | Updated if API/schema/integration changes |
| **Feature Flows** | Created/updated for behavior changes |
| **Security** | No secrets, keys, emails, IPs in diff |
| **Traceability** | Links to requirements and issue |

---

## Weekly Maintenance

Run these checks regularly to keep the codebase healthy:

| Skill | Purpose |
|-------|---------|
| `/validate-architecture` | Check codebase against architectural invariants |
| `/validate-schema` | Detect schema/migrations/docs drift |
| `/validate-config` | Detect env var drift across docker-compose/.env.example/code |
| `/generate-user-docs` | Regenerate user documentation from code |
| `/groom` | Audit backlog, rank issues, review priorities (requires human approval) |

---

## Slash Commands Reference

| Command | Purpose | SDLC Stage |
|---------|---------|------------|
| `/read-docs` | Load project context | In Progress |
| `/autoplan [issue]` | Strategy + eng + security plan | In Progress |
| `/implement <issue>` | End-to-end feature implementation | In Progress |
| `/review` | Pre-landing code review | In Progress |
| `/cso [--diff\|--comprehensive]` | Security audit | In Progress |
| `/update-docs` | Update documentation | In Progress |
| `/sync-feature-flows` | Sync feature flow docs with code changes | In Progress |
| `/security-check` | Validate no secrets in staged files | In Progress |
| `/add-testing` | Add tests for a feature | In Progress |
| `/test-runner [filter] [--verbose]` | Run test suite with report | In Progress / Review |
| `/validate-pr <number>` | Validate PR against methodology | Review |
| `/validate-architecture` | Check codebase against architectural invariants | Weekly |
| `/validate-schema` | Check schema vs migrations vs architecture.md | Weekly |
| `/validate-config` | Check env vars across docker-compose, .env.example, code | Weekly |
| `/groom` | Backlog grooming | Todo |
| `/roadmap [epics\|themes\|orphans\|all]` | Query priorities and board coverage | All |
| `/sprint [issue]` | Full dev cycle (orchestrates all above) | All |
| `/release [version-tag]` | Cut a release — checklist, notes, PR, tag | Release |

---

## Memory Files

The `docs/memory/` directory contains persistent project state:

```
docs/memory/
├── requirements.md      ← SINGLE SOURCE OF TRUTH for features
├── architecture.md      ← Current system design
├── feature-flows.md     ← Index of all feature flow documents
└── feature-flows/       ← Individual feature documentation
```

---

## Development Skills

Skills in `.claude/skills/` define HOW to approach specific tasks:

| Skill | Principle | When |
|-------|-----------|------|
| `verification` | No "done" claims without evidence | Before saying "done" |
| `systematic-debugging` | Find root cause BEFORE fixing | When fixing bugs |
| `tdd` | Failing test first, then minimal code | When writing new code |
| `code-review` | Verify feedback technically first | When responding to PR comments |

---

## Quick Start Checklist

**For every development session (or just run `/sprint`):**

- [ ] `/claim` the issue
- [ ] Load context (`/read-docs` or read relevant feature flows)
- [ ] `/autoplan` — plan review
- [ ] Review and approve the plan
- [ ] `/implement` — build the feature
- [ ] `/review` — pre-landing code review
- [ ] `/cso --diff` — security audit (recommended for P0/P1)
- [ ] `/test-runner` — run test suite
- [ ] `/sync-feature-flows` — update documentation
- [ ] Open PR with `Fixes #N`, run `/validate-pr`

**For PR reviews:**

- [ ] Quick triage: issue link, priority label, PR size
- [ ] `/review` — code quality
- [ ] `/validate-pr <number>` — docs and process
- [ ] `/cso --diff` — security (P0/P1 or security-sensitive PRs)

**Weekly maintenance:**

- [ ] `/validate-architecture`
- [ ] `/validate-schema`
- [ ] `/validate-config`
- [ ] `/generate-user-docs`
- [ ] `/groom` (requires human judgment for prioritization decisions)
