---
name: create-playbook
description: Create a new skill or playbook. Guides through requirements gathering and generates the appropriate template based on complexity.
disable-model-invocation: false
user-invocable: true
argument-hint: "[skill-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "2.0"
  created: 2025-02-10
  author: Ability.ai
---

# Create Playbook

Create a new skill. Determines the right complexity tier and generates from the appropriate template.

> For concepts and patterns, see the [README](../../README.md).
> For template details, see [templates/](../../templates/).

---

## Workflow

### Step 1: Check for Existing Skills

```bash
ls -d .claude/skills/*/ 2>/dev/null | head -10
ls -d ~/.claude/skills/*/ 2>/dev/null | head -10
```

If similar skill exists, ask: update it, create variant, or proceed with new?

### Step 2: Gather Core Requirements

Ask or extract from context:

1. **Name**: lowercase-with-hyphens, descriptive
2. **Purpose**: One sentence - what does it accomplish?
3. **Tools needed**: Which tools will it use?

### Step 3: Determine Complexity Tier

Ask these questions to classify:

**Q1: Does this skill read or write any files, APIs, or external state?**
- NO → **Tier 1: Simple Skill** (skip to Step 4)
- YES → Continue to Q2

**Q2: Will this run unattended, on a schedule, or need reliability guarantees?**
- NO → **Tier 2: Stateful Skill** (skip to Step 4)
- YES → Continue to Q3

**Q3: What automation level?**
- Safe to run completely unattended → `autonomous`
- Needs human approval at checkpoints → `gated`
- Human monitors entire execution → `manual`

→ **Tier 3: Full Playbook**

### Step 4: Gather Tier-Specific Requirements

**For Tier 1 (Simple Skill):**
- Process steps (what does it do?)
- Outputs (what does it produce?)

**For Tier 2 (Stateful Skill):**
- State dependencies (what files/APIs does it read/write?)
- Process steps
- Outputs

**For Tier 3 (Full Playbook):**
- State dependencies
- Automation level (autonomous/gated/manual)
- Schedule (if autonomous or gated): cron expression
- Process steps
- Approval gates (if gated): where?
- Prerequisites

### Step 5: Determine Location

| Scope | Location | Use When |
|-------|----------|----------|
| Personal | `~/.claude/skills/[name]/` | Only you use it |
| Project | `.claude/skills/[name]/` | Team shares it |
| Plugin | `plugins/[plugin]/skills/[name]/` | Distribute widely |

Default to project scope unless specified.

### Step 6: Generate Skill

Use the appropriate template:

| Tier | Template |
|------|----------|
| 1 | `templates/simple-skill.md` |
| 2 | `templates/stateful-skill.md` |
| 3 (autonomous) | `templates/autonomous-template.md` |
| 3 (gated) | `templates/gated-template.md` |
| 3 (manual) | `templates/manual-template.md` |

Fill in the template with gathered requirements.

### Step 7: Confirm and Create

Present summary before creating:

```
## New Skill: [name]

**Tier**: [1/2/3] ([Simple/Stateful/Full Playbook])
**Automation**: [autonomous/gated/manual/n/a]
**Location**: [path]

**State Dependencies**: [list or "none"]
**Process**: [N] steps
**Approval Gates**: [count or "none"]

Create this skill?
```

After confirmation:
1. Create directory: `mkdir -p [path]`
2. Write SKILL.md
3. Verify creation

### Step 8: Verify

```bash
cat [path]/SKILL.md | head -20
```

Remind user they may need to restart Claude Code for the skill to be recognized.

---

## Quick Reference

**Tier 1 - Simple Skill:**
```yaml
---
name: skill-name
description: What it does
allowed-tools: [tools]
user-invocable: true
---
# Skill Name
## Purpose
## Process
## Outputs
```

**Tier 2 - Stateful Skill:**
```yaml
---
name: skill-name
description: What it does
allowed-tools: [tools]
user-invocable: true
---
# Skill Name
## Purpose
## State Dependencies
| Source | Location | Read | Write |
## Process
## Outputs
```

**Tier 3 - Full Playbook:**
```yaml
---
name: playbook-name
description: What it does
automation: gated
schedule: "0 9 * * 1"  # optional
allowed-tools: [tools]
user-invocable: true
---
# Playbook Name
## Purpose
## State Dependencies
## Prerequisites
## Process
### Step 1: Read Current State
### Step N: [Work]
### Final Step: Write Updated State
## Completion Checklist
## Error Recovery
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [adjust-playbook](../adjust-playbook/) | Modify existing skills |
| [playbook-architect](../playbook-architect/) | Audit and improve agent skills |
