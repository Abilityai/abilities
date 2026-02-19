---
name: archive-project
description: Archive a completed or inactive project
user-invocable: true
argument-hint: "<project-name>"
allowed-tools:
  - Read
  - Write
  - Bash(mkdir:*)
  - Bash(mv:*)
---

# Archive Project

Archive a completed or inactive project.

## Arguments

`$ARGUMENTS` - The project name to archive

## Step 1: Verify Project Exists

Check `projects/$PROJECT_NAME/` exists.

If not found:
- List available projects
- Ask user to confirm the correct name

## Step 2: Read Current Status

Read `projects/$PROJECT_NAME/STATUS.md` to understand current state.

## Step 3: Confirm Archive

Show user:
- Project name
- Current status
- Last updated date
- Brief summary

Ask for confirmation before archiving.

## Step 4: Update Status

Update `projects/$PROJECT_NAME/STATUS.md`:

```markdown
**Current Status**: archived
**Last Updated**: [Today's date]
**Archived**: [Today's date]

## Archive Reason

[User-provided or "Project completed" default]

## Final State

[Summary of what was accomplished]
```

## Step 5: Move to Archive

```bash
mkdir -p projects/_archive
mv "projects/$PROJECT_NAME" "projects/_archive/$PROJECT_NAME"
```

## Step 6: Update Project Index

Update `projects/PROJECT_INDEX.md`:
- Change status to "archived"
- Add archive date

Or move entry to an "Archived Projects" section.

## Step 7: Report

Tell user:
- Project archived to `projects/_archive/[name]/`
- STATUS.md updated with archive details
- Project Index updated
- Can be restored by moving back to `projects/`
