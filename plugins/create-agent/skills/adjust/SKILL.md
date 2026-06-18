---
name: adjust-agent
description: Apply best-practice improvements to an existing agent — runs /review-agent to find issues, then proposes exact before/after changes to CLAUDE.md, skills, and Trinity files and applies the approved ones.
argument-hint: "[path to agent] [what to improve]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
metadata:
  version: "1.1"
  created: 2026-04-04
  updated: 2026-06-14
  author: Ability.ai
  changelog:
    - "1.1: Compose /review-agent for the audit instead of an inline rubric (Composition Rule — single-sourced); add Skill to allowed-tools; add composition-aware fix guidance"
    - "1.0: Initial version"
---

# Adjust Agent

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `adjust-agent vX.Y — recent: <summary>`. Then proceed.

Transition an existing agent to a better state. This is the *apply* half of the review/adjust pair: it invokes `/review-agent` (a read-only audit) to find issues, then proposes exact before/after diffs, gets approval, and applies them. Works like `/adjust-playbook`, but for the agent as a whole.

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

From `$ARGUMENTS` or conversation context, identify what the user wants. If the user asked for a general review, invoke `/review-agent` for the full audit (Step 3). If they asked for something specific, scope `/review-agent` to that focus area.

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

## Step 3: Audit (via /review-agent)

Invoke `/review-agent` to produce the findings — it is the single source of truth for the audit rubric (identity, capabilities, dependency graph, schedules, guidelines, skill quality, composition integrity, Trinity readiness, hygiene). Pass the agent path and, for a scoped request, the focus area:

```
Invoke `/review-agent [path] [focus area]`
```

Use its scorecard and findings table as the input to Step 4. Do **not** re-audit by hand — if a check seems missing, add it to `/review-agent` (so every caller benefits), not here.

---

## Step 4: Propose Changes

For each IMPROVE or MISSING finding from `/review-agent`, propose a specific change with exact before/after. Follow the adjust-playbook pattern.

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

**Fix guidance** for the non-obvious areas:
- *Dependency graph (MISSING)* — draft a complete `artifacts:` + `sync_skills:` block from the agent's actual files and skills.
- *Schedules (MISSING)* — propose cadences by task type: monitoring/health → 15m–1h; sync/update → 1–6h or daily; reports/summaries → daily/weekly; cleanup → weekly. Default `enabled: false`.
- *Composition findings* — for skill-internal fixes (missing `Skill` tool, broken invoke target, cycles, inlined logic), hand off to `/agent-dev:adjust-playbook` rather than rewriting the SKILL.md's logic here.

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

The audit rubric lives in [/review-agent](../review/) — the single source of truth. This skill consumes its findings and applies the approved fixes; it does not re-define the checks.

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/review-agent](../review/) | The read-only audit this skill applies — run first |
| [/create-agent:create](../create/) | Scaffold a new agent from scratch |
| [/agent-dev:adjust-playbook](../../agent-dev/skills/adjust-playbook/) | Modify a single skill/playbook |
