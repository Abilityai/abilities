---
name: implement
description: End-to-end feature implementation from requirements to tests to documentation. Takes requirements file, GitHub issue, or description as input.
allowed-tools: Agent, Read, Write, Edit, Grep, Glob, Bash, Skill
user-invocable: true
argument-hint: "<requirements-file|issue-number|'description'>"
automation: autonomous
---

# Implement Feature

End-to-end feature implementation from requirements to tested, documented code.

## Purpose

Autonomously implement features by:
1. Parsing requirements from file, GitHub issue, or inline description
2. Understanding existing patterns via feature flows
3. Implementing with minimal necessary changes
4. Creating and running tests
5. Updating documentation

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Requirements | `docs/requirements/*.md` | ✅ | | Feature specs |
| GitHub Issues | GitHub repo | ✅ | | Issue details |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | | Existing patterns |
| Architecture | `docs/memory/architecture.md` | ✅ | | System design |
| Source Code | `src/` | ✅ | ✅ | Implementation |
| Tests | `tests/` | ✅ | ✅ | Test files |

## Arguments

- `$ARGUMENTS`:
  - File path: `docs/requirements/MY_FEATURE.md`
  - Issue number: `#42` or `42`
  - Inline description: `"Add endpoint for X that does Y"`

## Process

### Step 1: Parse Requirements

**If file path provided:**
Read and parse the requirements document.

**If issue number provided:**
```bash
gh issue view ${ARGUMENTS#\#} --json title,body,labels
```

**If inline description:**
Use the provided description directly as requirements.

**Extract:**
- Feature name/ID
- Core requirements (what must be built)
- Acceptance criteria (how to verify it works)
- Related features/flows (what to study first)

### Step 2: Study Existing Patterns

Read relevant feature flows to understand existing patterns.
Based on requirements, identify 2-4 related flows and read them.

Also read:
- `docs/memory/architecture.md` - for system context
- `CLAUDE.md` - for development rules

### Step 3: Plan Implementation

1. **Files to modify** - list specific files with line ranges
2. **Files to create** - new files needed
3. **Order of changes** - dependencies between changes
4. **Test strategy** - what tests to write

### Step 4: Implement Feature

**Backend first (if applicable):**
1. Database schema/migrations (if needed)
2. Service layer logic
3. Router/controller endpoints
4. Models/schemas

**Frontend second (if applicable):**
1. Store/state management
2. Components
3. Views/routing

### Step 5: Create Tests

Coverage targets:
- Happy path (success case)
- Authentication/authorization
- Input validation
- Error cases
- Edge cases from requirements

### Step 6: Run Tests

Invoke the test-runner agent to execute tests.

### Step 7: Fix Test Failures

If tests fail:
1. Analyze failure
2. Identify root cause
3. Fix the issue
4. Re-run tests

**Max iterations:** 3 fix attempts.

### Step 8: Sync Feature Flows

Invoke sync-feature-flows to update documentation:
```
/sync-feature-flows recent
```

### Step 9: Update Documentation

Invoke update-docs to finalize:
```
/update-docs
```

### Step 10: Report Completion

Output final status with changes made, tests results, and documentation updated.

## Completion Checklist

- [ ] Requirements parsed from input
- [ ] Related feature flows studied
- [ ] Implementation plan created
- [ ] Feature implemented
- [ ] Tests created
- [ ] Tests run via test-runner agent
- [ ] All tests passing (or max fix attempts reached)
- [ ] Feature flows synced
- [ ] Documentation updated
- [ ] GitHub issue updated (if issue number was provided)
- [ ] Completion report generated

## Error Recovery

| Error | Recovery |
|-------|----------|
| Requirements file not found | Ask for correct path or use inline description |
| GitHub issue not found | Verify issue number, check repo access |
| Test runner unavailable | Run tests directly |
| Tests fail after 3 fix attempts | Report current state, list remaining failures |
| Feature flow sync fails | Create flow manually using feature-flow-analysis |

## Best Practices Enforced

- **Minimal necessary changes** - only modify what's required
- **No unsolicited refactoring** - don't "improve" unrelated code
- **Follow existing patterns** - match code style
- **No over-engineering** - simplest solution that works
