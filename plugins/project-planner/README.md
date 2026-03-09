# Project Planner

Plan and execute large multi-session projects with scope analysis, session splitting, and state tracking.

## Installation

```bash
/plugin install project-planner@abilityai
```

## Skills

| Skill | Description |
|-------|-------------|
| `/project-planner:project-plan [name]` | Plan or continue a multi-session project |

## What It Does

When you have a large task that can't be completed in a single session, this skill:

1. **Analyzes scope** — reads your requirements and identifies every change needed
2. **Splits into sessions** — groups changes into 3-8 item sessions with dependency ordering
3. **Executes with approval gates** — runs one session at a time, getting your sign-off after each
4. **Tracks state** — maintains `project_plan.yaml` so you can resume across sessions

## Usage

### Start a new project
```
/project-planner:project-plan my-refactor --plan requirements.md
```

### Resume work (auto-detects next session)
```
/project-planner:project-plan my-refactor
```

### Check progress
```
/project-planner:project-plan my-refactor --status
```

### Other commands
```
/project-planner:project-plan my-refactor --session 3    # Jump to session 3
/project-planner:project-plan my-refactor --skip 2       # Skip session 2
/project-planner:project-plan my-refactor --abandon      # Mark abandoned
/project-planner:project-plan my-refactor --add "new change description"
```

## How It Works

### Phase A: Planning
- Gathers requirements from files or conversation
- Reads current state of affected files
- Categorizes changes by size (S/M/L)
- Groups into dependency-ordered sessions
- Presents plan for approval before saving

### Phase B: Execution (per session)
- Identifies next unblocked session
- Executes each change: read → apply → verify → mark done
- Presents session review with accept/revise/rollback options
- Updates state file after each session

### Phase C: Completion
- Shows final summary with stats
- Option to clean up state file

## State File

Progress is tracked in `project_plan.yaml`:

```yaml
project:
  title: "My Refactor"
  status: active
  total_changes: 15

sessions:
  - id: 1
    title: "Update core interfaces"
    status: completed
    completed_at: "2025-01-15"
  - id: 2
    title: "Migrate consumers"
    status: pending
    depends_on: [1]
```

## When to Use This vs. Workspace Kit

| Need | Use |
|------|-----|
| Organize files into project folders | **workspace-kit** |
| Track project status with markdown | **workspace-kit** |
| Break a big task into planned sessions | **project-planner** |
| Execute changes with state tracking | **project-planner** |

They work well together: use workspace-kit for folder structure, project-planner for execution planning within a project.
