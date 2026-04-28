---
name: autoplan
description: Auto-review pipeline — runs strategy, engineering, and security review in sequence and produces an implementation plan with auto-decisions. Used at the start of any In Progress issue.
allowed-tools: Bash, Read, Grep, Glob, Skill
user-invocable: true
argument-hint: "[issue-number]"
automation: manual
---

# Autoplan

Run the full pre-implementation review pipeline for an issue: strategy review, engineering review, and security review. Produces a structured plan with auto-decisions so the developer can approve or revise before implementation begins.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issue | GitHub repo | ✅ | | Issue title, body, acceptance criteria |
| Requirements | `docs/memory/requirements.md` | ✅ | | Feature context |
| Architecture | `docs/memory/architecture.md` | ✅ | | System design |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | | Existing patterns |

## Arguments

- `$ARGUMENTS`: GitHub issue number (e.g., `42` or `#42`). If omitted, reads from current branch name or asks.

## Process

### Step 1: Load Issue Context

```bash
ISSUE=${ARGUMENTS#\#}
gh issue view $ISSUE --json number,title,body,labels,assignees,milestone
```

Extract:
- Problem statement
- Acceptance criteria
- Priority and type labels
- Milestone or epic association

### Step 2: Strategy Review

Assess the issue at a product and architecture level:

1. **Scope clarity** — Is the acceptance criteria unambiguous? Flag if not.
2. **Dependencies** — Does this block or depend on other open issues?
3. **Risk level** — P0/P1 flags, auth/security surface, data migrations
4. **Approach options** — Enumerate 2-3 approaches; select the simplest that satisfies requirements
5. **Auto-decision**: Record chosen approach and rationale

### Step 3: Engineering Review

Translate the chosen approach into a concrete implementation plan:

1. **Files to modify** — identify specific files with line ranges
2. **Files to create** — new files and their purpose
3. **Data model changes** — schema/migration changes if any
4. **API surface changes** — new or modified endpoints
5. **Test plan** — what tests are needed (happy path, auth, edge cases)
6. **Effort estimate** — Small / Medium / Large
7. **Auto-decision**: Record implementation order and test strategy

### Step 4: Security Review

Identify security considerations before writing code:

1. **Auth boundaries** — Does this touch authentication or authorization?
2. **Input vectors** — New endpoints, file uploads, user-controlled data?
3. **Data exposure** — Can this leak PII, credentials, or internal state?
4. **Dependency risk** — New packages being introduced?
5. **Auto-decision**: Flag any items requiring explicit security attention during implementation

### Step 5: Produce Plan Document

Output the plan in this format:

```markdown
## Autoplan: Issue #[N] — [Title]

### Strategy Decision
**Chosen approach**: [description]
**Rationale**: [why]
**Risk level**: [Low / Medium / High]

### Implementation Plan
**Files to modify:**
- `path/to/file.py` — [what changes]

**Files to create:**
- `path/to/new.py` — [purpose]

**Order of changes:**
1. [step]
2. [step]

**Test plan:**
- [ ] [test case]
- [ ] [test case]

### Security Flags
- [flag or "None identified"]

### Auto-Decisions
| Decision | Choice | Confidence |
|----------|--------|------------|
| Approach | [name] | High/Medium/Low |
| Test strategy | [name] | High/Medium/Low |

### Human Review Required
- [ ] Approve approach
- [ ] Approve implementation plan
- [ ] Acknowledge security flags
```

## Completion Checklist

- [ ] Issue context loaded
- [ ] Strategy review completed with approach selected
- [ ] Engineering review completed with implementation plan
- [ ] Security review completed with flags identified
- [ ] Plan document output
- [ ] Human review checklist presented
