---
name: create-session
description: Create a date-based session folder for today's work
user-invocable: true
argument-hint: "[topic-description]"
allowed-tools: Read, Write, Bash
---

# Create Session

Create a date-based session folder for today's work artifacts.

## Arguments

`$ARGUMENTS` - Optional topic description for the session

## Step 1: Generate Session Name

Format: `YYYY-MM-DD_topic-description`

If no topic provided, use: `YYYY-MM-DD_work-session`

Examples:
- `2025-01-15_api-research`
- `2025-01-15_client-meeting-prep`
- `2025-01-15_work-session`

## Step 2: Check for Existing Session

Look for existing session folder for today:

```bash
ls -d sessions/$(date +%Y-%m-%d)_* 2>/dev/null
```

If exists:
- Show existing session(s)
- Ask if user wants to use existing or create new

## Step 3: Create Session Folder

```bash
mkdir -p "sessions/YYYY-MM-DD_topic/"
```

## Step 4: Create Session README

Write `sessions/YYYY-MM-DD_topic/README.md`:

```markdown
# Session: [Date] - [Topic]

## Focus

[What this session is about]

## Work Items

- [ ] Item 1
- [ ] Item 2

## Files

| File | Purpose |
|------|---------|
| (none yet) | - |

## Outcomes

(To be filled at session end)

## Move to Projects

Files to move to permanent project locations:
- [ ] file.ext → projects/project-name/
```

## Step 5: Update Session Index

Append to `sessions/SESSION_INDEX.md`:

```markdown
| [Date] | [Topic] | - | - |
```

## Step 6: Report

Tell user:
- Session folder created at `sessions/[folder]/`
- Use for temporary work, research, drafts
- Move final outputs to `projects/` when done
- Delete temp files when no longer needed
