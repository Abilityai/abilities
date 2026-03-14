# Development Workflow

> **For developers and AI assistants** working on this project.
> This guide explains how to use the project's tools, agents, and documentation effectively.

---

## The Development Cycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT CYCLE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   1. CONTEXT LOADING                                                │
│      ↓                                                              │
│   /read-docs -> Load requirements, architecture, roadmap             │
│      ↓                                                              │
│   Read relevant feature-flows/* for the area you'll work on         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   2. DEVELOPMENT                                                    │
│      ↓                                                              │
│   /implement <source> -> End-to-end automated implementation         │
│      ↓    OR                                                        │
│   Manual implementation following existing patterns                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   3. TESTING                                                        │
│      ↓                                                              │
│   test-runner agent -> Run test suite (required)                     │
│      ↓                                                              │
│   Manual verification -> UI/API tests (recommended)                  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   4. DOCUMENTATION                                                  │
│      ↓                                                              │
│   /sync-feature-flows -> Update affected feature flows               │
│      ↓                                                              │
│   /update-docs -> Update changelog, architecture, requirements       │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   5. COMMIT & REVIEW                                                │
│      ↓                                                              │
│   /security-check -> Pre-commit security validation                  │
│      ↓                                                              │
│   /commit -> Stage, commit, push, link issues                        │
│      ↓                                                              │
│   /validate-pr -> Validate PR meets all methodology requirements     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Context Loading

**Always start a development session by loading context.**

### Option A: Full Context Load (New Session)

```
/read-docs
```

This loads:
- `docs/memory/requirements.md` - Feature requirements (source of truth)
- `docs/memory/architecture.md` - System design
- GitHub Issues - Current priorities (P0/P1)
- `docs/memory/changelog.md` - Recent changes

### Option B: Targeted Context (Specific Feature Work)

If you know what you're working on, load the relevant feature flow directly:

```
@docs/memory/feature-flows/user-login.md
@docs/memory/feature-flows/data-export.md
```

---

## Phase 2: Development

### Option A: Automated Implementation

Use `/implement` for end-to-end feature development:

```
/implement #42
/implement docs/requirements/new-feature.md
/implement "Add a user profile page with avatar upload"
```

### Option B: Manual Development

1. **Check requirements**: Does `requirements.md` cover this feature?
2. **Check roadmap**: Is this the current priority? (`/roadmap`)
3. **Read feature flow**: Understand existing data flow before modifying

---

## Phase 3: Testing

Use the `test-runner` agent:

| Tier | Duration | When |
|------|----------|------|
| Smoke | ~1 min | Quick validation |
| Core | ~5 min | Default, pre-commit |
| Full | ~15+ min | Release validation |

---

## Phase 4: Documentation

| Document | When to Update |
|----------|----------------|
| `changelog.md` | Always |
| `architecture.md` | API/schema/integration changes |
| `requirements.md` | New features, scope changes |
| `feature-flows/*.md` | Behavior changes |

---

## Phase 5: Commit & Review

1. `/security-check` - Pre-commit security validation
2. `/commit closes #17` - Stage, commit, push, link issues
3. `/validate-pr 42` - Validate PR meets methodology

---

## Best Practices

### DO
- Load context before starting work
- Read feature flows before modifying features
- Run tests after every significant change
- Use `/commit` for consistent commit messages
- Run `/validate-pr` before approving any PR

### DON'T
- Skip context loading
- Modify features without reading their flow
- Commit without running tests
- Leave feature flows outdated after changes
- Merge PRs without running validation
