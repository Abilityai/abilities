# Playbook Builder

Create structured, reliable skills for Claude Code agents.

## What is a Playbook?

A **playbook** is a skill that follows a specific pattern for reliability and portability:

```
READ FRESH STATE → PROCESS → WRITE STATE → VERIFY
```

The term "playbook" is familiar from Ansible, runbooks, and SOPs. In Claude Code, a playbook is implemented as a SKILL.md file that follows this transactional pattern.

**Why use playbooks?**
- **Self-contained**: Don't rely on stale conversation context
- **Portable**: Work the same locally and on Trinity
- **Traceable**: All state changes are explicit
- **Recoverable**: Clear what to check if something fails

## Skill Complexity Tiers

Not every skill needs the full playbook ceremony. Choose based on complexity:

| Tier | Type | When to Use | Required Elements |
|------|------|-------------|-------------------|
| 1 | **Simple Skill** | Stateless, one-shot tasks | Purpose, Process |
| 2 | **Stateful Skill** | Reads/writes files or APIs | + State Dependencies table |
| 3 | **Full Playbook** | Scheduled, autonomous, needs reliability | + Read/Write steps, Checklist, Recovery |

**Decision tree:**
```
Is this stateless (no files, no APIs, no side effects)?
├─ YES → Simple Skill (Tier 1)
└─ NO → Does it read or write state?
         ├─ YES → Will it run unattended or scheduled?
         │        ├─ YES → Full Playbook (Tier 3)
         │        └─ NO → Stateful Skill (Tier 2)
         └─ NO → Simple Skill (Tier 1)
```

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install playbook-builder@abilityai
```

## Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **create-playbook** | `/create-playbook [name]` | Create a new skill (any tier) |
| **adjust-playbook** | `/adjust-playbook [name]` | Modify an existing skill |
| **playbook-architect** | `/playbook-architect` | Audit agent and propose improvements |

## Quick Start

### Create a New Skill

```bash
/create-playbook weekly-report
```

Guides you through creating a skill. Asks questions to determine the right tier (simple, stateful, or full playbook).

### Audit Your Agent

```bash
/playbook-architect
```

Reviews all your skills and proposes improvements **without losing any existing functionality**.

### Modify an Existing Skill

```bash
/adjust-playbook weekly-report "add email notification step"
```

Updates skill while preserving structure.

## Automation Levels (Tier 3 Only)

For full playbooks that run scheduled or unattended:

| Level | When It Runs | Human Role | Use For |
|-------|--------------|------------|---------|
| **Autonomous** | On schedule | None | Metrics, backups, monitoring |
| **Gated** | Schedule/trigger | Approve at checkpoints | Content, deployments |
| **Manual** | When invoked | Full control | Dangerous ops, migrations |

## The Transactional Pattern (Tier 2-3)

Stateful skills and full playbooks should:

1. **Declare state dependencies** - what it reads/writes
2. **Read fresh state** - at the start, every time
3. **Process** - execute steps, with optional approval gates
4. **Write state** - explicitly save all changes
5. **Verify** - completion checklist (Tier 3 only)

**Tier 2 (Stateful Skill):**
```yaml
---
name: my-skill
---
## State Dependencies
| Source | Location | Read | Write |
|--------|----------|------|-------|
| Config | config.yaml | ✓ | |
| Data | data.json | ✓ | ✓ |

## Process
[Steps that read and write state]
```

**Tier 3 (Full Playbook):**
```yaml
---
name: my-playbook
automation: gated
---
## State Dependencies
[Table of reads/writes]

## Process
### Step 1: Read Current State
### Step 2-N: Do Work (with [APPROVAL GATE] if gated)
### Final Step: Write Updated State

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

| Template | Tier | For |
|----------|------|-----|
| [simple-skill.md](templates/simple-skill.md) | 1 | Stateless, one-shot tasks |
| [stateful-skill.md](templates/stateful-skill.md) | 2 | Skills that read/write state |
| [autonomous-template.md](templates/autonomous-template.md) | 3 | Scheduled, unattended |
| [gated-template.md](templates/gated-template.md) | 3 | Approval checkpoints |
| [manual-template.md](templates/manual-template.md) | 3 | Human-controlled |

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
