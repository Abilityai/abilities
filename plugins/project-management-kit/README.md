# Project Management Kit

Project and session management - organized folders for multi-session work with tracking.

## Installation

```bash
/plugin install project-management-kit@abilityai
```

## Skills

| Skill | Description |
|-------|-------------|
| `/project-management-kit:setup-projects` | Initialize the project/session structure |
| `/project-management-kit:create-project <name>` | Create a new tracked project |
| `/project-management-kit:create-session [topic]` | Create today's session folder |
| `/project-management-kit:archive-project <name>` | Archive a completed project |

## Setup

Run `/project-management-kit:setup-projects` to initialize. Creates:

```
projects/
├── PROJECT_INDEX.md      # Central project registry
└── .project-template/    # Template for new projects

sessions/
└── SESSION_INDEX.md      # Session tracking
```

## Project Structure

Each project folder contains:

```
projects/my-project/
├── README.md       # Project overview, goals, key files
├── STATUS.md       # Current status, next steps, blockers
├── DECISIONS.md    # Decision log with rationale
└── [project files]
```

### README.md
- Project description and purpose
- Goals (checkboxes)
- Key files reference
- Related projects/links

### STATUS.md
- Current status (active/paused/completed)
- What we're working on now
- Next steps (prioritized)
- Blockers
- Progress log

### DECISIONS.md
- Decision log with dates
- Rationale for each decision
- Outcomes

## Session Structure

Sessions are date-based temporary workspaces:

```
sessions/
├── 2025-01-15_api-research/
│   ├── README.md
│   ├── notes.md
│   └── scratch.py
└── 2025-01-16_client-prep/
    └── ...
```

## What Goes Where

| Content Type | Location | Why |
|--------------|----------|-----|
| Final deliverables | `projects/` | Persistent, tracked |
| Project documentation | `projects/` | Part of project |
| Code/content in development | `projects/` | Version controlled |
| Daily work artifacts | `sessions/` | Temporary |
| Research and exploration | `sessions/` | May not be kept |
| Drafts before ready | `sessions/` | Work in progress |
| Scratch files | `sessions/` | Disposable |

## Workflow

### Starting Work
1. Check `projects/PROJECT_INDEX.md` for active projects
2. Open project's `STATUS.md` to see next steps
3. Create session if needed: `/create-session research`

### During Work
- Update project `STATUS.md` as you progress
- Store temporary files in session folder
- Log decisions in `DECISIONS.md`

### Ending Work
- Update `STATUS.md` with progress and next steps
- Move final outputs from session to project
- Clean up temporary session files

## CLAUDE.md Integration

Setup adds comprehensive instructions ensuring:
- Project files stay in `projects/`, not `sessions/`
- STATUS.md is always updated when working
- Project index is checked before creating duplicates
- Sessions are cleaned periodically
