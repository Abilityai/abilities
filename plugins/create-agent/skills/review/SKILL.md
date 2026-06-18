---
name: review-agent
description: Review an existing agent against best practices and report findings — a read-only audit of CLAUDE.md, skills, composition integrity, and Trinity readiness. Produces a prioritized findings report and hands off to /adjust-agent or /adjust-playbook to apply fixes. Makes no changes itself.
argument-hint: "[path to agent] [focus area]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Skill
metadata:
  version: "1.0"
  created: 2026-06-14
  author: Ability.ai
  changelog:
    - "1.0: Initial version — read-only agent audit that hands off to /adjust-agent"
---

# Review Agent

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `review-agent vX.Y — recent: <summary>`. Then proceed.

Audit an existing agent against best practices and produce a findings report. **Read-only by construction** — this skill has no `Write`/`Edit` tools and changes nothing. It is the *detect-and-report* half of the pair; `/adjust-agent` (agent-level) and `/agent-dev:adjust-playbook` (skill-level) are the *apply* half.

This skill is the single source of truth for the agent audit rubric. `/adjust-agent` invokes this skill to get its findings rather than duplicating the checks.

## When to Use

- "review this agent", "audit my agent", "check best practices"
- Periodic health check on an established agent
- Before deploying or hardening an agent
- To **apply** fixes after reviewing → run `/adjust-agent` or `/agent-dev:adjust-playbook`

---

## Step 1: Locate and Read the Agent

If `$0` (path) provided, use it. Otherwise assume the current working directory.

Verify it's an agent:
```bash
ls CLAUDE.md 2>/dev/null && ls -d .claude/skills 2>/dev/null
```

If `CLAUDE.md` doesn't exist, ask for the correct path.

Read all agent artifacts (a missing one is itself a finding):

1. `CLAUDE.md`
2. `template.yaml`
3. `.env.example`
4. `.gitignore`
5. `.mcp.json.template` or `.mcp.json`
6. All `SKILL.md` files: `find .claude/skills -name "SKILL.md" 2>/dev/null`
7. Top-level listing: `ls -la`

If `$ARGUMENTS` names a focus area (e.g. "composition", "schedules", "trinity"), audit only that area; otherwise run the full audit.

---

## Step 2: Audit

Evaluate each area and assign a status:

- **PASS** — meets best practice, no change needed
- **IMPROVE** — present but incomplete
- **MISSING** — not present at all

Detect and classify only — do **not** draft fixes (that's `/adjust-agent`'s job).

### 2a. Identity
- `## Identity` section with the agent name in bold
- One-sentence purpose statement
- 2-3 paragraph description: what it does, who it serves, approach
- Repository URL (if a git remote exists)

### 2b. Core Capabilities
- `## Core Capabilities` (or equivalent) section
- Each capability links to a skill (`/skill-name`)
- Descriptions explain *when* to use, not just *what*
- Cross-reference: every skill in `.claude/skills/` is listed, and every listed skill exists

### 2c. Artifact Dependency Graph
- `## Artifact Dependency Graph` section
- `artifacts:` block with `mode` (prescriptive/descriptive) and `direction` (source/target)
- `sources` declared for target artifacts
- `sync_skills:` mapping skills to source→target edges

### 2d. Recommended Schedules
- A `schedules:` block in `template.yaml` (the design source of truth)
- Each entry has `id`, `name`, `cron`, `message`
- Only automatable tasks listed (not interactive ones), with sensible cadences
- `enabled: false` by default; a `## Recommended Schedules` table in CLAUDE.md renders the block

### 2e. Guidelines
- `## Guidelines` section with 2-4 domain-specific, actionable rules (not generic advice)

### 2f. Skill Quality
For each `SKILL.md`:
- YAML frontmatter with `name`, `description`, `allowed-tools`, `user-invocable`
- `allowed-tools` is comma-separated (not a YAML array)
- Tools match what the skill actually needs (no over-permissioning)
- Clear, specific step-by-step instructions
- `metadata.version` present

### 2g. Composition Integrity

A cross-skill graph check — the part a per-file audit can't do. First build the call graph: which skills invoke which.

```bash
# Candidate invocations across all skills (review each by hand — see the two traps below)
grep -rnE "Invoke \`/|^Skill: " .claude/skills/*/SKILL.md 2>/dev/null
```

**Two false-positive traps — exclude these before reporting** (see [Composing skills](../../../agent-dev/README.md#composing-skills-hierarchical-playbooks)):

- **Install ≠ compose.** An `add-*`/scaffold skill that `cp`s skill files into a target agent is *installing* deliverables, not composing — not a finding.
- **Example ≠ invocation.** An `` Invoke `/x` `` inside a code fence, in a skill whose job is to *generate* skill text, is documentation, not a call — not a finding.

Real findings:
- **Missing tool** — a skill that *executes* `` Invoke `/child` `` but lacks `Skill` in `allowed-tools` (the call can't run).
- **Broken target** — an invoke target that doesn't resolve to an existing skill (typo / missing child).
- **Cycle** — A invokes B invokes A (the harness won't re-enter a running skill).
- **Autonomy violation** — an `automation: autonomous` skill that invokes a `gated`/`manual` child (transitive autonomy — the heartbeat would hang).
- **Frozen pin** *(informational)* — a parent pins `/child-vN` while an unversioned `/child` exists, so it won't receive the child's fixes.
- **Inlined logic** *(candidate)* — a step that paraphrases or reimplements another skill's behavior instead of invoking it.

### 2h. Trinity Readiness
- `template.yaml` with `name`, `display_name`, `description`, `avatar_prompt`
- `.env.example` documenting required variables
- `.mcp.json.template` with Trinity server config
- `.gitignore` excluding `.env`, `.mcp.json`, `*.pem`, `*.key`, `.claude/projects/`, `.claude/todos/`

### 2i. Project Hygiene
- Git initialized
- No committed secrets
- Skill directory naming convention (lowercase-with-hyphens)

---

## Step 3: Report

Produce a findings report — **no edits, no AskUserQuestion to apply anything**. Order findings highest- to lowest-impact: structural gaps → completeness → quality → polish.

```
## Agent Review: [name]

**Path**: [path]
**Skills**: [count]
**Overall**: [healthy / needs work / incomplete]

### Findings

| # | Area | Status | Finding | Severity |
|---|------|--------|---------|----------|
| 1 | Composition | BROKEN | pipeline-tick invokes /foo, which doesn't exist | High |
| 2 | Identity | IMPROVE | Purpose statement missing | Medium |
| … | | | | |

### Scorecard

| Area | Status |
|------|--------|
| Identity | [PASS/IMPROVE/MISSING] |
| Capabilities | … |
| Dependency Graph | … |
| Schedules | … |
| Guidelines | … |
| Skill Quality | … |
| Composition Integrity | … |
| Trinity Ready | … |
| Hygiene | … |

### Apply fixes

This review changed nothing. To act on it:
- **Agent-level** (identity, graph, schedules, Trinity files): `/adjust-agent [path]`
- **Skill-level** (a specific SKILL.md — steps, permissions, composition): `/agent-dev:adjust-playbook [skill-name]`
```

---

## Audit Checklist Reference

| # | Area | Check | Priority |
|---|------|-------|----------|
| 1 | Identity | Named, purposeful, audience-aware | High |
| 2 | Capabilities | Listed, linked to skills, when-to-use | High |
| 3 | Dependency Graph | Artifacts declared, directions set, skills mapped | Medium |
| 4 | Schedules | Automatable skills scheduled with cadences | Medium |
| 5 | Guidelines | 2-4 domain-specific actionable rules | Medium |
| 6 | Skill Docs | CLAUDE.md ↔ .claude/skills/ in sync | High |
| 7 | Skill Quality | Frontmatter valid, permissions minimal, steps clear | High |
| 8 | Composition Integrity | Invocations resolve, no cycles, autonomy transitive, Skill tool present | High |
| 9 | Trinity Ready | template.yaml, .env.example, .gitignore, .mcp template | Low |
| 10 | Hygiene | Git init, no secrets, naming convention | Low |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/adjust-agent](../adjust/) | Apply the fixes this review surfaces (agent-level) |
| [/agent-dev:adjust-playbook](../../../agent-dev/skills/adjust-playbook/) | Apply fixes to a single skill |
| [/create-agent](../create/) | Scaffold a new agent from scratch |
