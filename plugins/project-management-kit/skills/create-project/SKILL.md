---
name: create-project
description: Create a new project folder with standard tracking structure
user-invocable: true
argument-hint: "<project-name>"
allowed-tools:
  - Read
  - Write
  - Bash(mkdir:*)
  - Bash(cp:*)
---

# Create Project

Create a new project folder with standard tracking structure.

## Arguments

`$ARGUMENTS` - The project name (will be converted to kebab-case)

## Step 1: Validate Project Name

Convert to kebab-case:
- "My New Project" → "my-new-project"
- Remove special characters
- Lowercase

## Step 2: Check for Duplicates

Read `projects/PROJECT_INDEX.md` and check if project exists.

If exists:
- Warn user
- Ask if they want to open existing project instead

## Step 3: Create Project Structure

```bash
mkdir -p "projects/$PROJECT_NAME"
```

## Step 4: Create README.md

Write `projects/$PROJECT_NAME/README.md`:

```markdown
# Project: [Project Name]

**Created**: [Today's date]
**Status**: active

## Overview

[Description to be filled in]

## Goals

- [ ] Define project goals

## Key Files

(none yet)

## Related

- Links to related projects or resources
```

## Step 5: Create STATUS.md

Write `projects/$PROJECT_NAME/STATUS.md`:

```markdown
# Status: [Project Name]

**Current Status**: active
**Last Updated**: [Today's date]

## Current Focus

Project just created - define initial scope and goals.

## Next Steps

1. [ ] Define project scope
2. [ ] Identify key deliverables
3. [ ] Create initial files

## Blockers

None

## Progress Log

- [Today's date]: Project created
```

## Step 6: Create DECISIONS.md

Write `projects/$PROJECT_NAME/DECISIONS.md`:

```markdown
# Decisions: [Project Name]

Log of significant decisions with context and rationale.

## Decision Log

| Date | Decision | Rationale | Outcome |
|------|----------|-----------|---------|
| [Today] | Created project | [reason] | Project initialized |
```

## Step 7: Update Project Index

Append to `projects/PROJECT_INDEX.md`:

```markdown
| [project-name] | active | [Today] | [Today] | [Brief description] |
```

## Step 8: Report

Tell user:
- Project created at `projects/[name]/`
- README.md, STATUS.md, DECISIONS.md initialized
- Update README.md with project details
- Update STATUS.md as you work
