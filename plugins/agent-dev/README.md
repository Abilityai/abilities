# agent-dev

Develop and extend existing Claude Code agents with skills, memory systems, a full GitHub Issues development workflow, and planning tools.

## Installation

```
/plugin install agent-dev@abilityai
```

## Usage

### Adding Capabilities

```
/agent-dev:create-playbook    # Create a new skill/playbook for the agent
/agent-dev:adjust-playbook    # Modify an existing skill/playbook
/agent-dev:add-memory         # Add a memory system (file-index, brain, json-state, workspace)
/agent-dev:add-backlog        # Install the full GitHub Issues development workflow
/agent-dev:add-git-sync       # Install auto-commit hooks for durable state
```

### Development Workflow

Once backlog is installed, the full cycle looks like:

```
/agent-dev:groom              # Tag issues with skill:* labels, set priorities
/agent-dev:roadmap            # View issues grouped by affected skill
/agent-dev:claim              # Claim the next issue, mark in-progress
/agent-dev:autoplan           # Analyze the issue against the current SKILL.md
# → /agent-dev:adjust-playbook or /agent-dev:create-playbook
/agent-dev:commit             # Stage skill files, write commit, close issue
```

Or run the full guided cycle in one command:

```
/agent-dev:sprint             # roadmap → claim → autoplan → implement → commit
```

For autonomous processing of project-level issues:

```
/agent-dev:work-loop          # Autonomous loop — skill issues are deferred to /sprint
```

### Planning

```
/agent-dev:plan               # Plan multi-session work
/agent-dev:backlog            # Priority-ordered view of open issues
```

## Skills

### Capability Building

| Skill | Description |
|-------|-------------|
| **create-playbook** | Scaffold a new skill/playbook (guided wizard) |
| **adjust-playbook** | Modify an existing skill — steps, logic, triggers, interface |
| **add-memory** | Copy a memory system into the agent |
| **add-backlog** | Install the full GitHub Issues development workflow |
| **add-git-sync** | Install auto-commit hooks for durable cross-session state |

### Development Workflow

Installed into the agent by `/add-backlog`. The units of work are skills; issues track what needs changing and why.

| Skill | Description |
|-------|-------------|
| **backlog** | Priority-ordered view of open issues |
| **roadmap** | Issues grouped by `skill:*` label — shows which skills have the most open work |
| **groom** | Tag untagged issues with `skill:*` labels, set missing priorities, flag stale in-progress |
| **claim** | Claim the next issue — surfaces the affected skill file to open |
| **autoplan** | Read the affected SKILL.md and produce a targeted change plan before touching files |
| **close** | Close an issue without a git commit (for project-level tasks) |
| **commit** | Stage changed skill files, write `[skill-name]: ... (closes #N)` commit, close issue |
| **sprint** | Human-supervised full cycle: roadmap → claim → autoplan → implement → commit |
| **work-loop** | Autonomous loop — processes project-level issues, defers `skill:*` issues to sprint |

**Label scheme:**
- `status:todo` / `status:in-progress` / `status:blocked` / `status:done`
- `priority:p0` (do now) / `priority:p1` (do soon) / `priority:p2` (do eventually)
- `skill:<name>` — which skill this issue affects (created dynamically by `/groom`)

### Planning

| Skill | Description |
|-------|-------------|
| **plan** | Plan large multi-session projects with scope analysis and approval gates |

### Memory Systems

The `/add-memory` skill copies memory skills directly into the agent (no plugin dependency). Choose from:

| Type | Use Case | Skills Installed |
|------|----------|------------------|
| **file-index** | Agent needs awareness of workspace files | setup-index, refresh-index, search-files |
| **brain** | Connected notes, knowledge graph | setup-brain, create-note, search-brain, find-connections |
| **json-state** | Structured state, counters, config | setup-memory, load-memory, update-memory, memory-jq |
| **workspace** | Multi-session project tracking | setup-projects, create-project, create-session, archive-project |

## How It Works

**Skill development is the unit of work.** When you create an issue like "improve claim flow to show skill file path", `/groom` tags it `skill:claim`. `/roadmap` surfaces it alongside all other `skill:claim` work. `/autoplan` reads `.claude/skills/claim/SKILL.md`, identifies what changes, and flags risks. `/commit` writes `[claim]: show skill file path on claim (closes #N)`.

`/work-loop` is the autonomous sprint — but it skips `skill:*` issues since modifying SKILL.md files requires the interactive wizard tools. Those stay in `/sprint`.

## Source

This plugin consolidates:
- playbook-builder (create-playbook, adjust-playbook)
- file-indexing, brain-memory, json-memory, workspace-kit (memory templates)
- github-backlog (backlog workflow)
- project-planner (plan)
