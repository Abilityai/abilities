# Playbook Builder

Create and manage structured, transactional playbooks for Claude Code agents.

## What is a Playbook?

A **playbook** is a skill that follows a disciplined pattern:

```
READ FRESH STATE → PROCESS → WRITE STATE → VERIFY
```

Playbooks are:
- **Self-contained**: Don't rely on stale conversation context
- **Portable**: Work the same locally and on Trinity
- **Traceable**: All state changes are explicit
- **Recoverable**: Clear what to check if something fails

**Playbook = Skill** (same thing, different lens)

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install playbook-builder@abilityai
```

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **create-playbook** | `/create-playbook [name]` | Create a new playbook from scratch |
| **adjust-playbook** | `/adjust-playbook [name]` | Modify an existing playbook |
| **playbook-architect** | `/playbook-architect` | Audit agent and propose playbook adoption |

## Quick Start

### Audit Your Agent

```bash
/playbook-architect
```

Reviews all your skills, commands, subagents, and instructions. Proposes how to adopt the playbook framework **without losing any existing functionality**.

### Create a New Playbook

```bash
/create-playbook weekly-report
```

Guides you through creating a playbook with proper state management.

### Modify an Existing Playbook

```bash
/adjust-playbook weekly-report "add email notification step"
```

Updates playbook while preserving structure.

## Automation Levels

| Level | When It Runs | Human Role | Use For |
|-------|--------------|------------|---------|
| **Autonomous** | On schedule | None | Metrics, backups, monitoring |
| **Gated** | Schedule/trigger | Approve at checkpoints | Content, deployments |
| **Manual** | When invoked | Full control | Dangerous ops, migrations |

## The Transactional Pattern

Every playbook must:

1. **Declare state dependencies** - what it reads/writes
2. **Read fresh state** - at the start, every time
3. **Process** - execute steps, with optional approval gates
4. **Write state** - explicitly save all changes
5. **Verify** - completion checklist

```yaml
---
name: my-playbook
automation: gated
---

## State Dependencies
| Source | Location | Read | Write |
|--------|----------|------|-------|
| Config | config.yaml | ✓ | |
| Data | data.json | ✓ | ✓ |

## Process

### Step 1: Read Current State
[Always first]

### Step 2-N: Do Work
[Your steps, with [APPROVAL GATE] if gated]

### Final Step: Write Updated State
[Always last]

## Completion Checklist
- [ ] State read fresh
- [ ] Work done
- [ ] State written
```

## Conservative Adoption

The `playbook-architect` skill follows a **conservative approach**:

- **Preserves 100%** of existing functionality
- **Adds structure** on top, doesn't rewrite
- **Proposes changes** for user approval
- **Never deletes** anything

## Templates

| Template | For |
|----------|-----|
| [autonomous-template.md](templates/autonomous-template.md) | Scheduled, unattended |
| [gated-template.md](templates/gated-template.md) | Approval checkpoints |
| [manual-template.md](templates/manual-template.md) | Human-controlled |

## Scheduling on Trinity

Playbooks with `schedule:` run on Trinity:

```yaml
automation: autonomous
schedule: "0 6 * * *"
```

Use `/trinity-schedules` from the trinity-onboard plugin.

## Related

- [Trinity Onboard](../trinity-onboard/) - Deploy agents to Trinity
- [Skill Builder](../skill-builder/) - Lower-level skill creation

## License

MIT
