---
name: review-agent
description: Review an existing agent against best practices and report findings — a read-only audit of CLAUDE.md, skills, composition integrity, and Trinity readiness. Produces a prioritized findings report and hands off to /adjust-agent or /adjust-playbook to apply fixes. Makes no changes itself.
argument-hint: "[path to agent] [focus area]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Skill
metadata:
  version: "1.4"
  created: 2026-06-14
  updated: 2026-07-29
  author: Ability.ai
  changelog:
    - "1.4: Audit checklist matches the current platform contract — schedule entries key on `name` (there is no `id` field), template.yaml must declare credentials: + credential_setup: (gate T-015, ent#128), .mcp.json.template must keep ${VAR} inside env blocks with an allowlisted command and no hand-written trinity entry, and .gitignore must exclude .claude/settings.json (trinity#2036) and .trinity/*"
    - "1.3: Trinity-readiness check (2h) now audits repository deployability — remote present, tree clean, branch pushed, plus the instance GitHub token note for private repos — because Trinity deploys an agent by cloning its repo; a repo-less agent is reported as deploy-by-upload-only (no reproducible source) with the one-command fix"
    - "1.2: Audit Request Dispatch (new check 2k) — CLAUDE.md carries the SOP routing table: request-phrased rows, every user-invocable skill covered or deliberately internal, routes resolve, playbook-gap fallback with operator-queue escalation and /agent-dev:create-playbook pointer; scorecard + checklist rows added"
    - "1.1: Audit Documentation Coherence — README/ARCHITECTURE/TARGET-ARCHITECTURE present, current/target split intact, docs match skills and subagents"
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
2. `README.md`, `ARCHITECTURE.md`, `TARGET-ARCHITECTURE.md` (a missing one is a Documentation Coherence finding)
3. `template.yaml`
4. `.env.example`
5. `.gitignore`
6. `.mcp.json.template` or `.mcp.json`
7. All `SKILL.md` files: `find .claude/skills -name "SKILL.md" 2>/dev/null`
8. Any subagents: `ls .claude/agents/*.md 2>/dev/null`
9. Top-level listing: `ls -la`

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
- Each entry has `name`, `cron`, `message` (optionally `timezone`, `purpose`, `enabled`) — `name` is the identity key Trinity dedups on; there is **no** `id` field, and a stray `id:` is silently ignored
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
- `template.yaml` with `name`, `display_name`, `description`, `avatar_prompt`, and a `credentials:` block naming every `${VAR}` used in `.mcp.json.template` (gate T-015), each enriched by a `credential_setup:` entry (ent#128)
- `.env.example` documenting required variables
- `.mcp.json.template` declaring the agent's **own** MCP servers, with `${VAR}` placeholders **inside `env` blocks only** (a placeholder in `command`/`url`/`args` makes Trinity withhold the whole server at startup) and an allowlisted literal `command` — never a hand-written `trinity` entry, which the platform overwrites
- `.gitignore` excluding `.env`, `.env.*`, `.mcp.json`, `credentials.json`, `*.pem`, `*.key`, `.claude/projects/`, `.claude/todos/`, `.claude/plugins/`, `.claude/settings.json` (trinity#2036), and `.trinity/*` with the authored hooks negated
- **Deployable from its repository** — Trinity deploys an agent by cloning its GitHub repo, so this is the difference between a reproducible deployment and an upload:
  - a `git remote` exists (`git remote get-url origin`)
  - the working tree is clean and the branch is pushed — anything uncommitted or unpushed simply won't exist on the deployed agent
  - if the repo is private, note that the instance needs a GitHub token (**Settings → GitHub token**, *Contents: Read*) to clone it
  - no remote → finding: *deploys by upload only; no reproducible source*. Not a blocker (the local-file path works), but the fix is one command: `gh repo create <name> --private --source=. --push`

### 2i. Project Hygiene
- Git initialized
- No committed secrets
- Skill directory naming convention (lowercase-with-hyphens)

### 2j. Documentation Coherence
The agent should keep an honest current→target picture and a human-facing overview.
- `README.md` present — human-facing capabilities overview, and its skill/capability list matches the actual skills
- `ARCHITECTURE.md` present — describes *current* state; components it names (skills, subagents, data, schedules) actually exist on disk, and nothing real is undocumented
- `TARGET-ARCHITECTURE.md` present — describes *target* state; the current/target split is intact (no item described as shipped/live in `ARCHITECTURE.md` is still listed as "planned" in the target doc)
- The dependency graph registers these docs with correct `mode`/`direction` (README + ARCHITECTURE descriptive targets; TARGET-ARCHITECTURE prescriptive source)
- A `/reconcile-docs` skill exists to maintain this coherence (and ideally is scheduled)

This is the *detect* counterpart to a generated agent's own `/reconcile-docs` — the agent self-checks; this audit verifies the machinery is present and the docs aren't already drifting.

### 2k. Request Dispatch

The agent's SOP for incoming requests — from the user, other agents, or the operator queue.

- `## Request Dispatch` section in CLAUDE.md with a request-routing table
- Rows are phrased as *requests* (what gets asked), not restated skill names, and every route resolves to an existing skill
- Every user-invocable skill in `.claude/skills/` has a dispatch row, or is deliberately internal (e.g. a vendored helper composed by another skill)
- A **playbook-gap fallback** is present: unmatched task requests are handled if safe and flagged — to the user interactively, or as a `playbook-gap-<slug>` operator-queue item when headless on Trinity — with a pointer to `/agent-dev:create-playbook`
- Cross-reference: the dispatch table and Core Capabilities agree (no skill listed in one but missing from the other)

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
| Documentation Coherence | … |
| Request Dispatch | … |
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
| 9 | Documentation Coherence | README/ARCHITECTURE/TARGET-ARCHITECTURE present, current/target split intact, docs match skills & subagents, /reconcile-docs exists | Medium |
| 10 | Request Dispatch | SOP routing table in CLAUDE.md — request-phrased rows, routes resolve, all user-invocable skills covered, playbook-gap fallback | Medium |
| 11 | Trinity Ready | template.yaml, .env.example, .gitignore, .mcp template | Low |
| 12 | Hygiene | Git init, no secrets, naming convention | Low |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/adjust-agent](../adjust/) | Apply the fixes this review surfaces (agent-level) |
| [/agent-dev:adjust-playbook](../../../agent-dev/skills/adjust-playbook/) | Apply fixes to a single skill |
| [/create-agent](../create/) | Scaffold a new agent from scratch |
