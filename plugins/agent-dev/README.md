# agent-dev

Develop and extend existing Claude Code agents with skills, memory systems, backlog workflows, and planning tools.

## Installation

```
/plugin install agent-dev@abilityai
```

## Usage

### Adding Capabilities

```
/agent-dev:add-skill          # Create a new skill for the agent
/agent-dev:adjust-skill       # Modify an existing skill
/agent-dev:add-memory         # Add a memory system (file-index, brain, json-state, workspace)
/agent-dev:add-backlog        # Add GitHub Issues backlog workflow
```

### Backlog Workflow

Once backlog is installed, use these skills to manage work:

```
/agent-dev:backlog            # View GitHub Issues backlog
/agent-dev:pick-work          # Pick next issue to work on
/agent-dev:close-work         # Close current issue
/agent-dev:work-loop          # Run autonomous work loop
```

### Planning

```
/agent-dev:plan               # Plan multi-session work
```

## Skills

### Capability Building

| Skill | Description |
|-------|-------------|
| **add-skill** | Create a new skill/playbook for the agent (guided wizard) |
| **adjust-skill** | Modify an existing skill — update logic, add steps, change triggers |
| **add-memory** | Add one of four memory systems to the agent |
| **add-backlog** | Add GitHub Issues workflow for task management |

### Memory Systems

The `/add-memory` skill copies memory skills directly into the agent (no plugin dependency). Choose from:

| Type | Use Case | Skills Installed |
|------|----------|------------------|
| **file-index** | Agent needs awareness of workspace files | setup-index, refresh-index, search-files |
| **brain** | Connected notes, knowledge graph | setup-brain, create-note, search-brain, find-connections |
| **json-state** | Structured state, counters, config | setup-memory, load-memory, update-memory, memory-jq |
| **workspace** | Multi-session project tracking | setup-projects, create-project, create-session, archive-project |

### Backlog Workflow

| Skill | Description |
|-------|-------------|
| **backlog** | View GitHub Issues assigned to the agent |
| **pick-work** | Select next issue and update status |
| **close-work** | Mark current issue as complete |
| **work-loop** | Autonomous loop: pick → work → close → repeat |

### Planning

| Skill | Description |
|-------|-------------|
| **plan** | Plan large multi-session projects with scope analysis |

## How Memory Installation Works

When you run `/agent-dev:add-memory`:

1. Asks what kind of memory the agent needs
2. COPIES the memory skills into `[agent]/.claude/skills/`
3. Updates the agent's CLAUDE.md with documentation
4. Agent becomes self-contained — no plugin dependency

## Source

This plugin consolidates:
- playbook-builder (add-skill, adjust-skill)
- file-indexing, brain-memory, json-memory, workspace-kit (memory templates)
- github-backlog (backlog workflow)
- install-github-backlog (add-backlog)
- project-planner (plan)
