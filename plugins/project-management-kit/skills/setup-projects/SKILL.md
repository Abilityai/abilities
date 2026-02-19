---
name: setup-projects
description: Initialize project and session management structure with CLAUDE.md integration
user-invocable: true
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# Setup Projects

Initialize project and session management for organized multi-session work.

## Step 1: Ask Configuration

Use AskUserQuestion:

**Question 1**: "Where should projects be stored?"
- Options:
  - "projects/ folder (Recommended)" - Standard location
  - "Custom location" - Specify a different path

**Question 2**: "Where should session files be stored?"
- Options:
  - "sessions/ folder (Recommended)" - Date-based session storage
  - "Inside each project" - Project-specific sessions

## Step 2: Create Directory Structure

```bash
mkdir -p projects
mkdir -p sessions
```

## Step 3: Create Project Index

Write `projects/PROJECT_INDEX.md`:

```markdown
# Project Index

Central registry of all projects.

| Project | Status | Created | Last Active | Description |
|---------|--------|---------|-------------|-------------|
| (none yet) | - | - | - | - |

## Status Legend
- **active** - Currently being worked on
- **paused** - On hold, will resume
- **completed** - Finished, archived
- **archived** - No longer relevant
```

## Step 4: Create Session Index

Write `sessions/SESSION_INDEX.md`:

```markdown
# Session Index

Date-based session tracking.

| Date | Focus | Projects Touched | Key Outcomes |
|------|-------|------------------|--------------|
| (none yet) | - | - | - |

## Session Folder Format
`YYYY-MM-DD_brief-description/`

## Contents
Each session folder contains work artifacts from that date:
- Drafts and work-in-progress
- Research notes
- Temporary files
- Session summary (optional)
```

## Step 5: Create Project Template

Write `projects/.project-template/`:

```
.project-template/
├── README.md          # Project overview
├── STATUS.md          # Current status and next steps
├── DECISIONS.md       # Decision log
└── .gitkeep
```

**README.md template:**
```markdown
# Project: ${PROJECT_NAME}

## Overview
[Brief description of the project]

## Goals
- [ ] Goal 1
- [ ] Goal 2

## Key Files
- `file1.ext` - Description
- `file2.ext` - Description

## Related
- [[Link to related project]]
```

**STATUS.md template:**
```markdown
# Status: ${PROJECT_NAME}

**Current Status**: active | paused | completed
**Last Updated**: YYYY-MM-DD

## Current Focus
[What we're working on now]

## Next Steps
1. [ ] Step 1
2. [ ] Step 2

## Blockers
- None

## Recent Progress
- YYYY-MM-DD: [What was done]
```

## Step 6: Update CLAUDE.md

Add comprehensive project management instructions:

```markdown
## Project & Session Management

Organized structure for multi-session work.

### Directory Structure
- `projects/[project-name]/` - Project folders with tracking
- `sessions/YYYY-MM-DD_description/` - Date-based session work

### Project Folder Structure
Each project MUST contain:
- `README.md` - Project overview and goals
- `STATUS.md` - Current status, next steps, blockers

Optional:
- `DECISIONS.md` - Decision log with rationale
- `docs/` - Documentation
- `src/` - Source code/content

### Session Folders
For temporary work, drafts, and daily artifacts:
- Create: `sessions/YYYY-MM-DD_brief-topic/`
- Store: Work-in-progress, research, temporary files
- Clean: Move final outputs to projects, delete temp files

### What Goes Where

**Projects folder** (persistent, tracked):
- Deliverables and final outputs
- Project documentation
- Code and content being developed
- Status tracking and decisions

**Sessions folder** (temporary, date-based):
- Daily work artifacts
- Research and exploration
- Drafts before they're ready
- Scratch files and experiments

### Commands
- `/project-management-kit:create-project <name>` - New project
- `/project-management-kit:create-session [topic]` - Today's session folder
- `/project-management-kit:archive-project <name>` - Archive completed project

### Rules
1. NEVER store project files in sessions/ - they belong in projects/
2. ALWAYS update STATUS.md when working on a project
3. Check PROJECT_INDEX.md before creating new projects (avoid duplicates)
4. Clean sessions/ periodically - move outputs, delete temps
```

## Step 7: Confirm Setup

Report:
- Project management initialized
- `projects/` ready for project folders
- `sessions/` ready for date-based work
- CLAUDE.md updated with management instructions
- Use `/project-management-kit:create-project <name>` to start
