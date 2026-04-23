---
name: create-playbook
description: Create a new skill or playbook. Guides through requirements gathering and generates the appropriate template based on complexity.
disable-model-invocation: false
user-invocable: true
argument-hint: "[skill-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "2.3"
  created: 2025-02-10
  updated: 2026-04-23
  author: Ability.ai
  changelog:
    - "2.3: Note project-specific vs official frontmatter; list newer official fields (model, context, paths, hooks) for Tier 3"
    - "2.2: Add No-Gates Rule — autonomous playbooks cannot have approval gates (breaks execution)"
    - "2.1: Add 45-minute rule to Design Constraints — autonomous playbooks must complete within this limit"
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
- Safe to run completely unattended, **no approval needed at any point** → `autonomous`
- Needs human approval at checkpoints → `gated`
- Human monitors entire execution → `manual`

⚠️ **Critical**: If user says "autonomous" but also mentions approval/review steps, clarify:
> "Autonomous playbooks cannot have approval gates — they run unattended and would hang waiting for approval that never comes. Should this be `gated` instead?"

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
- Approval gates (if gated): where? ⚠️ **Not allowed for autonomous — see No-Gates Rule**
- Prerequisites

### Step 4b: Self-Improvement Option

Ask the user:

> **Should this skill be self-improving?**
>
> Self-improving skills include a checklist at the end to consider tactical improvements after each run—things like clearer steps, better error handling, or more efficient flow. The skill's core purpose stays the same; only execution can improve.
>
> If in a git repo, improvements are committed for version control.

If user confirms YES, include the Self-Improvement Checklist (see below) at the end of the generated skill.

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
**Self-Improving**: [yes/no]

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
automation: gated        # project convention (see note below)
schedule: "0 9 * * 1"    # project convention, optional
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

## Frontmatter: Official vs Project Conventions

Skills here use a mix of official Claude Code frontmatter and project-specific fields.

**Official Claude Code fields** (https://code.claude.com/docs/en/skills.md):
- `name`, `description`, `allowed-tools`, `argument-hint`
- `user-invocable`, `disable-model-invocation`
- `model`, `effort` — override model/effort level for the skill
- `context: fork` + `agent:` — run the skill in a subagent
- `paths:` — glob patterns to scope auto-activation
- `hooks:` — skill-scoped lifecycle hooks
- `arguments:` — named `$name` substitution

**Project-specific (not official Claude Code)**:
- `metadata:` block with `version`, `changelog`, `author`
- `automation: autonomous | gated | manual`
- `schedule: "<cron>"`

The project fields are load-bearing for the `agent-dev` plugin's playbook model. They work locally but won't be recognized by tooling that only reads official Claude Code frontmatter. Anthropic's official path for scheduled/unattended execution is **Routines / Remote Tasks**, not a skill field.

When generating Tier 3 playbooks, keep the project fields (the rest of the plugin depends on them) and optionally add official fields like `model:`, `context: fork`, or `paths:` when they fit.

---

## Self-Improvement Checklist (Appendix)

When user opts into self-improving skills, append this section to the generated skill:

```markdown
## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Were there friction points, unclear steps, or inefficiencies?
- [ ] **Identify improvements**: Could error handling, step ordering, or instructions be clearer?
- [ ] **Scope check**: Only tactical/execution changes—NOT changes to core purpose or goals
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md with the specific improvement
  - [ ] Keep changes minimal and focused
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add <skill-path>/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(<skill-name>): <brief improvement description>"`
```

---

## Design Constraints

**The 45-Minute Rule**: Agent reliability degrades exponentially after ~45 minutes of continuous execution. Design playbooks accordingly:

- Autonomous playbooks must complete in under 45 minutes
- If a task is larger, break it into multiple scheduled runs (e.g., "process 50 items" not "process all items")
- Build checkpoints where state is saved — if interrupted, the next run can resume
- Long processes → multiple scheduled tasks with handoff via state files

When gathering requirements for Tier 3 playbooks, ask: "Can this complete in under 45 minutes? If not, how should we chunk it?"

**The No-Gates Rule for Autonomous Playbooks**: Autonomous playbooks run unattended on a schedule — there is no human to approve gates. An `[APPROVAL GATE]` in an autonomous playbook will cause execution to hang indefinitely, breaking the scheduled run.

- Autonomous playbooks MUST NOT contain any `[APPROVAL GATE]` markers
- If the workflow needs human approval at any point, it MUST be `gated` or `manual`, not `autonomous`
- When user requests autonomous + approval gates, explain the incompatibility and ask them to choose

---

## Autonomous Playbook Validation Checklist

Before generating any autonomous playbook, verify:

- [ ] **No approval gates** — grep the content for `[APPROVAL GATE]` — must return zero matches
- [ ] **No human decision points** — no "ask user", "wait for confirmation", "present options"
- [ ] **Complete error handling** — all failure paths handled without human intervention
- [ ] **Notifications on failure** — errors must alert via Slack, email, or logging
- [ ] **Under 45 minutes** — execution time within agent reliability window
- [ ] **Idempotent or safe to retry** — can re-run without causing duplicate effects

If any check fails, the playbook cannot be autonomous. Recommend `gated` instead.

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [adjust-playbook](../adjust-playbook/) | Modify existing skills |
| [playbook-architect](../playbook-architect/) | Audit and improve agent skills |
