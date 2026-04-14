# install-github-backlog

Add GitHub Issues task management to any Claude Code agent. This wizard creates skills **directly in your agent's directory** — fully self-contained, no plugin dependency.

## What It Does

Your agent's GitHub repository becomes its task queue:
- **Issues = work items** with priority and status labels
- **Skills live in the agent** — `/backlog`, `/pick-work`, `/close-work`, `/work-loop`
- **Autonomous mode** — schedule `/work-loop` on Trinity to process backlog automatically

## Usage

Run from inside any agent directory:

```
/install-github-backlog
```

The wizard will:
1. Verify you're in a GitHub repo with `gh` authenticated
2. Create the backlog skills in `.claude/skills/`
3. Set up status/priority labels in your repo
4. Update CLAUDE.md with the task management workflow

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/backlog` | View current workload by priority and status |
| `/pick-work` | Grab the next task, mark it in-progress |
| `/close-work "summary"` | Complete current task with summary |
| `/work-loop` | Autonomous processing until backlog empty |

## Labels Created

**Status:** `status:todo`, `status:in-progress`, `status:blocked`, `status:done`

**Priority:** `priority:p0` (do now), `priority:p1` (do soon), `priority:p2` (do eventually)

## Workflow

1. Create issues with requirements and priority labels
2. Run `/pick-work` to grab the highest priority task
3. Work on it (the issue is your spec)
4. Run `/close-work "what you did"` when done
5. Repeat

Or: deploy to Trinity and schedule `/work-loop` to run every few hours. The agent processes its backlog autonomously.

## Installation

```bash
/plugin install install-github-backlog@abilityai
```

Then run `/install-github-backlog` in your agent directory.

## Requirements

- Git repository with GitHub remote
- `gh` CLI installed and authenticated (`gh auth login`)

## License

MIT
