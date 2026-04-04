---
name: adjust-agent
description: Review an agent against best practices and apply improvements — proposes specific before/after changes to CLAUDE.md, skills, and Trinity files, then applies approved edits.
argument-hint: "[path to agent] [what to improve]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-04
  author: Ability.ai
---

# Adjust Agent

Review an existing agent against best practices and transition it to a better state. Works like `/adjust-playbook` but for the agent as a whole — proposes exact before/after diffs, gets approval, applies changes.

## When to Use

- User says "review this agent" or "improve my agent"
- User says "add a dependency graph" or "set up schedules"
- User says "make this agent Trinity-ready"
- After scaffolding an agent and wanting to harden it
- Periodic health check on an established agent

---

## Step 1: Locate and Read the Agent

If `$0` (path) provided, use it. Otherwise, assume current working directory.

Verify it's an agent:
```bash
ls CLAUDE.md 2>/dev/null && ls -d .claude/skills 2>/dev/null
```

If `CLAUDE.md` doesn't exist, ask for the correct path.

Read all agent artifacts (skip any that don't exist — their absence is itself a finding):

1. `CLAUDE.md`
2. `template.yaml`
3. `.env.example`
4. `.gitignore`
5. `.mcp.json.template` or `.mcp.json`
6. All `SKILL.md` files:
   ```bash
   find .claude/skills -name "SKILL.md" 2>/dev/null
   ```
7. Top-level file listing:
   ```bash
   ls -la
   ```

Parse and display the agent's current state:

```
## Current Agent: [name]

**Identity**: [one-line summary or "not defined"]
**Skills**: [count] — [list names]
**Dependency Graph**: [present / missing]
**Recommended Schedules**: [present / missing]
**Guidelines**: [count or "none"]
**Trinity Ready**: [yes / partially / no]
```

---

## Step 2: Determine What to Change

From `$ARGUMENTS` or conversation context, identify what the user wants. If the user asked for a general review, run the full audit (Step 3). If they asked for something specific, skip to the relevant area.

| Change Type | Examples |
|-------------|----------|
| **Full review** | "review this agent", "check best practices" |
| **Add dependency graph** | "add artifact dependencies", "set up the graph" |
| **Add schedules** | "recommend schedules", "which skills should be scheduled" |
| **Improve identity** | "flesh out the identity section", "improve CLAUDE.md" |
| **Add guidelines** | "add behavioral rules", "set up guidelines" |
| **Fix skill docs** | "sync skills with CLAUDE.md", "document the skills" |
| **Trinity readiness** | "make this Trinity-ready", "prepare for deployment" |
| **Skill quality** | "review skill permissions", "check the skills" |

If unclear, ask:

Use AskUserQuestion:
- **Question:** "What would you like to improve about this agent?"
- **Header:** "Adjust Agent"
- **Options:**
  1. Full review — Check everything against best practices
  2. Add artifact dependency graph
  3. Add recommended schedules
  4. Improve CLAUDE.md structure (identity, capabilities, guidelines)
  5. Trinity readiness (template.yaml, .env, .gitignore)
  6. Skill quality review
  7. Other (describe)

---

## Step 3: Audit

Evaluate each area below. For each, assign a status:

- **PASS** — meets best practice, no changes needed
- **IMPROVE** — present but incomplete
- **MISSING** — not present at all

Only audit areas relevant to the user's request (or all areas for a full review).

### 3a. Identity Section

Check for:
- `## Identity` section with agent name in bold
- One-sentence purpose statement
- 2-3 paragraph description covering: what it does, who it serves, approach
- Repository URL (if git remote exists)

### 3b. Core Capabilities

Check for:
- `## Core Capabilities` or equivalent section
- Each capability links to a skill (`/skill-name`)
- Descriptions explain *when* to use, not just *what*

Cross-reference: every skill in `.claude/skills/` should be listed, and every listed skill should exist.

### 3c. Artifact Dependency Graph

Check for:
- `## Artifact Dependency Graph` section
- `artifacts:` YAML block with `mode` (prescriptive/descriptive) and `direction` (source/target)
- `sources` declared for target artifacts
- `sync_skills:` mapping skills to source→target edges
- Direction rules summary

If missing, draft a complete graph from the agent's actual artifacts and skills.

### 3d. Recommended Schedules

Check for:
- `## Recommended Schedules` section
- Table with Skill, Schedule, Purpose columns
- Only automatable skills listed (not interactive ones)
- Sensible cadences for each skill type
- Reference to `/trinity-schedules`

If missing, analyze skills and propose schedules:
- Monitoring/health → every 15m–1h
- Sync/update → every 1–6h or daily
- Reports/summaries → daily or weekly
- Cleanup/maintenance → weekly

### 3e. Guidelines

Check for:
- `## Guidelines` section
- 2-4 domain-specific, actionable rules
- Rules specific to this agent's domain (not generic advice)

### 3f. Skill Quality

For each `SKILL.md`, check:
- YAML frontmatter with `name`, `description`, `allowed-tools`, `user-invocable`
- `allowed-tools` is comma-separated (not YAML array)
- Tools match what the skill actually needs (no over-permissioning)
- Clear, specific step-by-step instructions
- `metadata.version` present

### 3g. Trinity Readiness

Check for:
- `template.yaml` with `name`, `display_name`, `description`, `avatar_prompt`
- `.env.example` documenting required variables
- `.mcp.json.template` with Trinity server config
- `.gitignore` excluding `.env`, `.mcp.json`, `*.pem`, `*.key`, `.claude/projects/`, `.claude/todos/`

### 3h. Project Hygiene

Check for:
- Git initialized
- No committed secrets
- Skill directory naming convention (lowercase-with-hyphens)

---

## Step 4: Propose Changes

For each IMPROVE or MISSING finding, propose a specific change with exact before/after. Follow the adjust-playbook pattern.

```
## Proposed Changes to [Agent Name]

### Change 1: [Area] — [What changes]

**Status**: MISSING → adding / IMPROVE → updating

Before:
```
[current content, or "Section does not exist"]
```

After:
```
[exact new content to insert or replace]
```

**File**: [which file is being changed]
**Impact**: [what this enables or fixes]

---

### Change 2: [Area] — [What changes]

...

---

### Unchanged

Everything else remains the same:
- [list preserved sections/files]
```

**Ordering**: Present changes from highest to lowest impact:
1. Structural gaps (missing sections in CLAUDE.md)
2. Completeness (dependency graph, schedules)
3. Quality (skill permissions, guidelines)
4. Polish (hygiene, docs alignment)

---

## Step 5: Confirm

Use AskUserQuestion:
- **Question:** "Which changes should I apply?"
- **Header:** "Apply Changes"
- **Options:**
  1. **Apply all** — Make all proposed changes
  2. **Let me pick** — Select specific changes by number
  3. **Modify proposal** — Adjust a change before applying
  4. **Cancel** — No changes

If the user picks "Let me pick", list changes numbered and let them select.

If the user picks "Modify proposal", ask what to adjust about the specific change, re-propose, and confirm again.

---

## Step 6: Apply Changes

For each approved change:

1. Find the exact text to replace (or insertion point for new sections)
2. Apply with the Edit tool (or Write for new files)
3. Verify the edit succeeded by reading the changed region

Apply changes to one file at a time. If multiple changes target the same file, apply them top-to-bottom to avoid offset issues.

---

## Step 7: Verify and Report

Read each modified file and confirm changes applied correctly.

```
## Agent Updated: [Name]

Changes applied:
- [x] [Change 1 summary]
- [x] [Change 2 summary]
- [ ] [Skipped change — reason]

### Before / After

| Area | Before | After |
|------|--------|-------|
| Identity | [status] | [status] |
| Capabilities | [status] | [status] |
| Dependency Graph | [status] | [status] |
| Schedules | [status] | [status] |
| Guidelines | [status] | [status] |
| Skill Docs | [status] | [status] |
| Skill Quality | [status] | [status] |
| Trinity Ready | [status] | [status] |
| Hygiene | [status] | [status] |

### Remaining Items

[List anything still at IMPROVE or MISSING — can be addressed with another `/adjust-agent` run]
```

---

## Audit Checklist Reference

Quick reference for the full audit — all items that a well-structured agent should have:

| # | Area | Check | Priority |
|---|------|-------|----------|
| 1 | Identity | Named, purposeful, audience-aware | High |
| 2 | Capabilities | Listed, linked to skills, when-to-use | High |
| 3 | Dependency Graph | Artifacts declared, directions set, skills mapped | Medium |
| 4 | Schedules | Automatable skills scheduled with cadences | Medium |
| 5 | Guidelines | 2-4 domain-specific actionable rules | Medium |
| 6 | Skill Docs | CLAUDE.md ↔ .claude/skills/ in sync | High |
| 7 | Skill Quality | Frontmatter valid, permissions minimal, steps clear | High |
| 8 | Trinity Ready | template.yaml, .env.example, .gitignore, .mcp template | Low |
| 9 | Hygiene | Git init, no secrets, naming convention | Low |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/create-agent](../create-agent/) | Scaffold a new agent from scratch |
| [/adjust-playbook](../../playbook-builder/skills/adjust-playbook/) | Modify a single skill/playbook |
| [/playbook-architect](../../playbook-builder/skills/playbook-architect/) | Audit and bulk skill adoption |
