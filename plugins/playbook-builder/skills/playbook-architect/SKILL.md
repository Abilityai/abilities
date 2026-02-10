---
name: playbook-architect
description: Audit agent structure and propose playbook adoption. Reviews skills, commands, subagents, and instructions to recommend playbook framework adoption without losing any existing functionality.
disable-model-invocation: false
user-invocable: true
argument-hint: "[report|adopt skill-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Playbook Architect

Audit an agent's architecture and propose adoption of the playbook framework.

## Core Principle: No Functionality Loss

**This audit is conservative.** The goal is to:

1. **Preserve 100% of existing functionality** - nothing stops working
2. **Add playbook structure** - wrap existing logic, don't rewrite
3. **Suggest minimal additions** - only what's clearly missing
4. **Let user decide scope** - propose, don't force

**What we're NOT doing:**
- Deleting or removing anything
- Rewriting existing logic
- Adding complexity
- Breaking what works

---

## Commands

### `/playbook-architect` or `/playbook-architect report`

Generate a read-only audit report.

### `/playbook-architect adopt [component-name]`

Adopt a specific component to playbook format (interactive).

### `/playbook-architect adopt --all`

Adopt all components (with approval gates).

---

## Phase 1: Inventory Current Agent

### Step 1: Read Agent State

Scan all agent components:

```bash
# Agent root
echo "=== Agent Root ==="
ls -la

# Instructions
echo "=== Instructions ==="
[ -f "CLAUDE.md" ] && echo "CLAUDE.md: $(wc -l < CLAUDE.md) lines"
[ -f ".claude/settings.json" ] && echo ".claude/settings.json exists"

# Skills
echo "=== Skills ==="
ls -d .claude/skills/*/ 2>/dev/null | while read d; do
  name=$(basename "$d")
  lines=$(wc -l < "$d/SKILL.md" 2>/dev/null || echo "0")
  echo "$name: $lines lines"
done

# Commands (legacy)
echo "=== Commands ==="
ls .claude/commands/*.md 2>/dev/null | while read f; do
  name=$(basename "$f" .md)
  lines=$(wc -l < "$f")
  echo "$name: $lines lines"
done

# Subagents
echo "=== Subagents ==="
ls .claude/agents/*.md 2>/dev/null | while read f; do
  name=$(basename "$f" .md)
  lines=$(wc -l < "$f")
  echo "$name: $lines lines"
done

# Hooks
echo "=== Hooks ==="
[ -f ".claude/settings.json" ] && grep -q "hooks" .claude/settings.json && echo "Hooks configured"

# Resources
echo "=== Resources ==="
ls .claude/resources/ 2>/dev/null
```

### Step 2: Read Each Component

For each component found, read its contents to understand:
- What it does (purpose)
- What it reads (state inputs)
- What it writes (state outputs)
- How it's triggered (invocation)

---

## Phase 2: Analyze Against Playbook Framework

For each component, assess:

### Playbook Compliance Checklist

| Requirement | Check |
|-------------|-------|
| `automation:` field | Does frontmatter specify autonomous/gated/manual? |
| State Dependencies table | Is there a table of what's read/written? |
| Read State step | Does it read fresh state at start? |
| Write State step | Does it write state explicitly at end? |
| Completion Checklist | Is there a verification checklist? |

### Classification

Classify each component:

| Type | Description | Action |
|------|-------------|--------|
| **Ready** | Already follows playbook pattern | None needed |
| **Adoptable** | Has procedure, needs structure | Add playbook framing |
| **Worker** | Helper/utility, called by others | Keep simple, no playbook overhead |
| **Context** | Background knowledge, not actionable | Set `user-invocable: false` |
| **Legacy** | Old format (command) | Convert to skill with playbook structure |

---

## Phase 3: Generate Report

Present findings in this format:

```markdown
# Agent Architecture Audit

## Summary

| Category | Count | Ready | Needs Adoption |
|----------|-------|-------|----------------|
| Skills | N | X | Y |
| Commands | N | X | Y |
| Subagents | N | X | Y |
| Instructions | - | - | [analysis] |

## Current Capabilities

**Everything listed here continues to work unchanged.**

### Skills

| Skill | Purpose | Status | Recommendation |
|-------|---------|--------|----------------|
| [name] | [what it does] | [ready/adoptable/worker/context] | [action] |

### Commands (Legacy)

| Command | Purpose | Recommendation |
|---------|---------|----------------|
| [name] | [what it does] | [convert to skill / keep as-is] |

### Subagents

| Agent | Purpose | Recommendation |
|-------|---------|----------------|
| [name] | [what it does] | [keep / convert to playbook with context:fork] |

### Instructions (CLAUDE.md)

| Section | Lines | Type | Recommendation |
|---------|-------|------|----------------|
| [section] | N | [guidance/procedure/policy] | [keep / extract to skill] |

## Adoption Plan

### Phase 1: Quick Wins (no risk)

These additions improve structure without changing behavior:

1. **[skill-name]**: Add State Dependencies table, Completion Checklist
2. **[skill-name]**: Add `automation: manual` to frontmatter

### Phase 2: Conversions (low risk)

Convert legacy formats to skills:

1. **[command-name]** → skill with same functionality

### Phase 3: Enhancements (optional)

Suggested new playbooks based on patterns observed:

1. **[suggested-playbook]**: [rationale]

## What's NOT Changing

To be clear, these stay exactly as they are:
- [list of things explicitly preserved]
```

---

## Phase 4: Adopt (Interactive)

When user runs `/playbook-architect adopt [name]`:

### Step 1: Load Current Component

Read the component's current content completely.

### Step 2: Show Current State

```
## Current: [name]

[Display full current content]

---

Playbook compliance:
- automation: ❌ missing
- State Dependencies: ❌ missing
- Read State: ⚠️ implicit (reads files but not structured)
- Write State: ⚠️ implicit
- Checklist: ❌ missing
```

### Step 3: Propose Additions

**Key: We ADD to existing content, not replace.**

```
## Proposed Additions

I will ADD these sections to [name]:

1. Frontmatter addition:
   ```yaml
   automation: [inferred-level]
   ```

2. New section after Purpose:
   ```markdown
   ## State Dependencies

   | Source | Location | Read | Write | Description |
   |--------|----------|------|-------|-------------|
   | [inferred from content] |
   ```

3. Restructure existing steps to include:
   - Step 1: Read Current State (wrap existing reads)
   - Step N: Write Updated State (wrap existing writes)

4. Add at end:
   ```markdown
   ## Completion Checklist
   - [ ] [inferred from content]
   ```

## What Stays The Same

ALL existing logic, instructions, and behavior remain unchanged.
I'm adding structure around it, not rewriting it.
```

### Step 4: Confirm

Ask user to approve the specific changes before applying.

### Step 5: Apply Changes

Use Edit tool to add sections. Preserve all existing content.

### Step 6: Verify

Show the updated component and confirm nothing was lost.

---

## Inference Rules

### Inferring Automation Level

| If component... | Then automation = |
|-----------------|-------------------|
| Has scheduling/cron references | `autonomous` |
| Has "confirm", "review", "approve" language | `gated` |
| Has dangerous operations (delete, deploy, publish) | `gated` or `manual` |
| Is simple utility | `manual` |
| Default | `manual` |

### Inferring State Dependencies

Look for patterns:
- `cat`, `Read`, file paths → state input
- `Write`, `Edit`, `>`, `>>` → state output
- API calls with GET → state input
- API calls with POST/PUT → state output
- Git operations → state output

### Inferring Checklist Items

From the component's stated outputs and purpose:
- "Creates X" → "[ ] X created"
- "Updates Y" → "[ ] Y updated"
- "Sends Z" → "[ ] Z sent"

---

## Safety Rails

### Never Do

1. **Delete any content** - only add
2. **Rewrite logic** - only restructure
3. **Change behavior** - only add observability
4. **Force adoption** - only propose

### Always Do

1. **Show before/after** - full transparency
2. **Get approval** - for each change
3. **Preserve originals** - can always revert via git
4. **Verify after** - confirm nothing broke

### If Unsure

When component doesn't clearly fit playbook pattern:

```
## [name] - Needs Review

This component doesn't clearly map to the playbook pattern:
- [reason]

Options:
1. Keep as-is (no changes)
2. Minimal adoption (just add frontmatter)
3. Skip for now

Recommend: [1/2/3] because [reason]
```

---

## Example Report

```markdown
# Agent Architecture Audit: content-agent

## Summary

| Category | Count | Ready | Needs Adoption |
|----------|-------|-------|----------------|
| Skills | 4 | 1 | 3 |
| Commands | 2 | 0 | 2 (convert) |
| Subagents | 1 | 1 | 0 |
| Instructions | 1 | - | review |

## Current Capabilities

### Skills

| Skill | Purpose | Status | Recommendation |
|-------|---------|--------|----------------|
| weekly-content | Create weekly content | Adoptable | Add State Deps, Checklist |
| publish | Publish to blog | Adoptable | Add automation: gated |
| utils | Helper functions | Worker | Keep simple |
| research | Research topics | Ready | None needed |

### Commands (Legacy)

| Command | Purpose | Recommendation |
|---------|---------|----------------|
| /commit | Git commit | Convert to skill |
| /status | Show status | Keep as-is (too simple) |

### Subagents

| Agent | Purpose | Recommendation |
|-------|---------|----------------|
| explorer | Codebase research | Keep (worker) |

### Instructions (CLAUDE.md)

| Section | Lines | Type | Recommendation |
|---------|-------|------|----------------|
| Overview | 15 | Context | Keep in CLAUDE.md |
| Content Rules | 25 | Policy | Keep or extract to policy skill |
| Daily Process | 40 | Procedure | Already a skill, keep reference |

## Adoption Plan

### Phase 1: Quick Wins
1. `weekly-content`: +State Dependencies, +Checklist
2. `publish`: +automation: gated

### Phase 2: Conversions
1. `/commit` command → skill (use git-workflow plugin instead?)

### Phase 3: Optional
No new playbooks suggested - current coverage looks complete.

## What's NOT Changing
- All 4 skills continue working as before
- /status command stays as-is
- explorer subagent unchanged
- CLAUDE.md content preserved
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/create-playbook](../create-playbook/) | Create new playbooks from scratch |
| [/trinity-compatibility](../../trinity-onboard/skills/trinity-compatibility/) | Similar audit for Trinity adoption |
