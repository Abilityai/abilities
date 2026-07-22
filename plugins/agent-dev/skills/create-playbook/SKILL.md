---
name: create-playbook
description: Create a new skill or playbook. Guides through requirements gathering and generates the appropriate template based on complexity.
disable-model-invocation: false
user-invocable: true
argument-hint: "[skill-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "2.10"
  created: 2025-02-10
  updated: 2026-07-09
  author: Ability.ai
  changelog:
    - "2.10: Correct the stall-watchdog facts in the Long-Running-Task Rule — since trinity#1369 the no-output watchdog is 1800s (not 300s) and watches mcp__* tools only (Bash is unwatched, piping doesn't 're-arm' anything); add set_reminder as the Trinity-side way to verify a decoupled job's artifact without waiting for the next cron"
    - "2.9: Add the Reporting Rule to Design Constraints + a validation-checklist line — a skill that yields a surfaceable result (summary, batch, metrics) ends with a guarded mcp__trinity__report step (namespaced report_type, a display_hint, JSON payload) so scheduled/headless runs leave a visible record on the Trinity Reports tab; guarded to skip silently off-Trinity (reporting is an upgrade, never a gate)"
    - "2.8: Add the Long-Running-Task Rule to Design Constraints + a validation-checklist line — a headless/scheduled run is one agent turn and CANNOT host a >~10-min job (the harness auto-backgrounds it past the ~10-min sync Bash ceiling, active waiting is blocked, and ending the turn reaps every background task/monitor). Such work must be decoupled to an OS-level cron/systemd/sidecar + done-marker; the run only triggers and verifies the artifact moved. In-turn oversight is an interactive-only affordance, not a headless one"
    - "2.7: Generated skills now include the what's-new banner + a seed changelog; documented the required changelog + banner convention for every tier"
    - "2.6: Add the Composition Rule — playbooks invoke child skills by name (compose, don't copy); reuse-check step, Composes section, transitive autonomous check"
    - "2.5: Add when_to_use/arguments/shell/effort/substitution-vars to frontmatter; fix hot-reload advice; add supporting-files step; add Routines note"
    - "2.4: Add Single-Task Rule — scheduled skills must be scoped to one task type per invocation"
    - "2.3: Note project-specific vs official frontmatter; list newer official fields (model, context, paths, hooks) for Tier 3"
    - "2.2: Add No-Gates Rule — autonomous playbooks cannot have approval gates (breaks execution)"
    - "2.1: Add 45-minute rule to Design Constraints — autonomous playbooks must complete within this limit"
---

# Create Playbook

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-playbook vX.Y — recent: <summary>`. Then proceed.

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

### Step 4b: Supporting Files

Ask: Does this skill need supporting files (templates, example outputs, helper scripts)?

- If YES: plan a `scripts/`, `examples/`, or `reference.md` alongside SKILL.md, referenced from the main file so Claude knows when to load them. Keep SKILL.md under 500 lines — move large reference material to separate files.
- If NO: proceed.

### Step 4c: Self-Improvement Option

Ask the user:

> **Should this skill be self-improving?**
>
> Self-improving skills include a checklist at the end to consider tactical improvements after each run—things like clearer steps, better error handling, or more efficient flow. The skill's core purpose stays the same; only execution can improve.
>
> If in a git repo, improvements are committed for version control.

If user confirms YES, include the Self-Improvement Checklist (see below) at the end of the generated skill.

### Step 4d: Deep Reasoning

If this skill involves complex multi-step logic or architectural decisions, add `ultrathink` anywhere in the skill body to request deeper reasoning when it runs.

### Step 4e: Reuse Check (Composition)

Does any planned step duplicate work an existing skill already does? If so, **invoke that skill instead of reimplementing it** — ``Invoke `/child-skill` `` (namespace cross-plugin calls: ``/plugin:child-skill ``). Then:

- Add `Skill` to `allowed-tools`.
- List each child under a `## Composes` section so the dependency is greppable.
- Call the **unversioned** name to ride the latest version (so child fixes propagate automatically); pin `/child-vN` only to freeze against a child's breaking changes.

See **The Composition Rule** in Design Constraints. Never call another skill's `scripts/`/`reference.md`/templates directly — go through the skill entry point.

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

Edits to existing skill files hot-reload without restart. A restart is only needed if the top-level skills directory (`~/.claude/skills/` or `.claude/skills/`) didn't exist before this session.

---

## Quick Reference

**Tier 1 - Simple Skill:**
```yaml
---
name: skill-name
description: What it does
allowed-tools: [tools]
user-invocable: true
metadata:
  version: "1.0"
  author: Ability.ai
  changelog:
    - "1.0: Initial version — <one-line summary>"
---
# Skill Name

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `skill-name vX.Y — recent: <summary>`. Then proceed.

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
allowed-tools: [tools]   # include `Skill` if it invokes other skills
effort: high             # optional: low/medium/high/xhigh/max
user-invocable: true
---
# Playbook Name
## Purpose
## State Dependencies
## Prerequisites
## Composes               # optional: child skills this playbook invokes
## Process
### Step 1: Read Current State
### Step N: [Work]
### Final Step: Write Updated State
## Completion Checklist
## Error Recovery
```

**Every tier (required):** include the `metadata:` block (with a newest-first `changelog`) and the what's-new banner shown in the Tier 1 example, placed right after the H1. The banner surfaces the *top* (newest) changelog entry on launch, so keep the changelog newest-first. See the repo `CLAUDE.md` → "Skill Changelog & What's-New Banner".

---

## Frontmatter: Official vs Project Conventions

Skills here use a mix of official Claude Code frontmatter and project-specific fields.

**Official Claude Code fields** (https://code.claude.com/docs/en/skills.md):
- `name`, `description`, `allowed-tools`, `argument-hint`
- `user-invocable`, `disable-model-invocation`
- `when_to_use` — additional trigger context; combined with `description`, capped at 1,536 chars in skill listing
- `arguments` — named positional args: `arguments: [issue, branch]` → `$issue`, `$branch` in content
- `model`, `effort` — override model/effort level (`low`/`medium`/`high`/`xhigh`/`max`)
- `shell` — `bash` (default) or `powershell` for `!` command blocks
- `context: fork` + `agent:` — run the skill in a subagent
- `paths:` — glob patterns to scope auto-activation
- `hooks:` — skill-scoped lifecycle hooks

**String substitutions available in skill content:**
- `$ARGUMENTS` — full argument string; `$ARGUMENTS[N]` / `$N` — positional (0-based)
- `$name` — named arg from `arguments:` frontmatter
- `${CLAUDE_SESSION_ID}` — current session ID
- `${CLAUDE_EFFORT}` — active effort level
- `${CLAUDE_SKILL_DIR}` — absolute path to the skill's directory (use for bundled scripts)

**Project-specific (not official Claude Code)**:
- `metadata:` block with `version`, `changelog` (newest-first), `author` — **required on every skill**: bump `version` and prepend a `changelog` entry on each edit, and pair it with the what's-new banner after the H1 (see the repo `CLAUDE.md` → "Skill Changelog & What's-New Banner")
- `automation: autonomous | gated | manual`
- `schedule: "<cron>"`

The project fields are load-bearing for the `agent-dev` plugin's playbook model. They work locally but won't be recognized by tooling that only reads official Claude Code frontmatter. Anthropic's official path for cloud-hosted scheduled execution is **Routines** — create one with `/schedule` in the CLI or at claude.ai/code/routines. Routines run on Anthropic infrastructure without a local machine.

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

**The Single-Task Rule for Scheduled Skills**: Autonomous playbooks execute in a single context window. Iterating over multiple *different* tasks (e.g., "process all backlog items") fills that window with context from each prior item, adding noise to every subsequent step.

- Each scheduled invocation must be scoped to **one task or one task type**
- Process one item per invocation; let the scheduler re-invoke for the next
- Exception: batch tasks where every item has *identical* context needs (same files, same pattern) are fine — e.g., running the same quality gate on N wizard files all read the same kind of data
- When a user asks for a scheduled loop, design it as single-item-per-invocation and explain that the cron handles repetition

**The Long-Running-Task Rule (>~10 min)**: A **headless/scheduled run is a single agent turn**, and it **cannot host a job longer than the synchronous Bash window (~10 min max tool timeout)** — a hard platform ceiling, not something a bigger budget fixes. Design around it:

- **Don't try to babysit it in-turn.** Past ~10 min the harness **auto-backgrounds** the job (not your choice), active waiting is **blocked** (`sleep`/poll loops rejected — "use monitor with an until-loop"), and the moment the turn ends, **every background task and monitor spawned in it is reaped** (the completion event fires as `killed`, not `completed`; the promised re-invoke never comes). Streaming heartbeat output changes nothing — the no-output stall watchdog (`AGENT_TOOL_STALL_LIMIT_S`, default 1800s) watches `mcp__*` tools only since trinity#1369, Bash isn't watched, and neither the ~10-min ceiling nor the turn-end reaping cares about output. The async monitor / re-invoke model works **interactively** (the session persists) but **NOT** in a headless run.
- **≤ ~10 min:** run it as one **foreground, un-piped, streaming** Bash call, in-turn. Don't pipe through `tail`/`grep` (buffers output and hides live progress from the transcript).
- **> ~10 min** (a FAISS/index rebuild, full bootstrap, bulk embedding, a big migration): it **must run outside the agent turn** — an **OS-level job** (container cron / systemd unit / small non-LLM sidecar) that builds the artifact and writes a **done-marker**. The scheduled skill only **triggers it and does the fast parts**: check the marker / artifact freshness and, if fresh, run the quick follow-ups. On Trinity, the triggering run can also `set_reminder` (one-shot deferred self-trigger, trinity#1296) to come back and verify the artifact landed instead of waiting for the next cron tick.
- **Always verify the artifact moved** (mtime advanced *and* a stats count > 0) before declaring success — never trust the exit code or `business_status`. A run that ends without the artifact changing is a **failure**, not a `skipped`.

**The Composition Rule**: When a playbook needs work another skill already does, it **invokes that skill by name** (``Invoke `/child-skill` ``, `Skill` in `allowed-tools`) — it never inlines the child's steps, calls its internal scripts/files directly, or paraphrases what it does. The parent holds only the orchestration; the child stays the single source of truth, so its fixes propagate automatically. Call the unversioned name to ride latest; pin `/child-vN` only to freeze. Composition is a DAG (no cycles, keep it shallow). See [Composing skills](../../README.md#composing-skills-hierarchical-playbooks) for the full rule.

**The Reporting Rule**: A skill that produces a **surfaceable result** — a summary, a batch of items, a metrics snapshot — should **end with a guarded Trinity report** so an operator can see what the run produced without reading chat (this is the *only* window into a scheduled/headless run). Add a final step that calls the `mcp__trinity__report` MCP tool with a namespaced `report_type` (`<agent>.<result>` in `lower_snake`, e.g. `oracle.weekly_summary`), a short `title`, a JSON `payload`, and a `display_hint` — `table` (`{columns, rows}`), `kpi` (`{tiles:[{label,value,unit?}]}`), `markdown` (`{markdown}`), `timeline` (`{events:[{ts,label,detail}]}`), or omit for raw JSON. The report lands on the agent's **Reports** tab and the fleet **Operations → Reports** view — an append-only history alongside the live `dashboard.yaml` snapshot.

- **Guard it.** The tool exists only on Trinity (it publishes under the agent's own key). If `mcp__trinity__report` isn't available — e.g. running locally — skip the step **silently**. Reporting is an upgrade, never a gate: the skill must produce its result with or without Trinity.
- **Not for conversational replies** — only result-producing and scheduled runs.

---

## Autonomous Playbook Validation Checklist

Before generating any autonomous playbook, verify:

- [ ] **No approval gates** — grep the content for `[APPROVAL GATE]` — must return zero matches
- [ ] **No human decision points** — no "ask user", "wait for confirmation", "present options"
- [ ] **Complete error handling** — all failure paths handled without human intervention
- [ ] **Notifications on failure** — errors must alert via Slack, email, or logging
- [ ] **Under 45 minutes** — execution time within agent reliability window
- [ ] **No in-turn job over ~10 min** — a headless run can't host a job past the ~10-min sync Bash ceiling (auto-backgrounded, then reaped at turn-end); anything longer (index rebuild, bulk embedding, big migration) is decoupled to an OS-level cron/systemd/sidecar + done-marker, and the run only triggers + verifies the artifact moved (never off an exit code / `business_status`)
- [ ] **Idempotent or safe to retry** — can re-run without causing duplicate effects
- [ ] **Single-task scope** — processes one task type per invocation; iteration over varied items happens across invocations, not within one
- [ ] **Composed children are autonomous-safe** — autonomy is transitive: recurse into every `/invoked` skill; none of them may contain `[APPROVAL GATE]` or human decision points, and the whole tree must fit the 45-minute / single-task budget
- [ ] **Result-producing runs report** — a skill that yields a surfaceable result ends with a guarded `mcp__trinity__report` step (the Reporting Rule), skipped silently when the tool is absent — so a scheduled/headless run leaves a visible record on the Reports tab

If any check fails, the playbook cannot be autonomous. Recommend `gated` instead.

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [adjust-playbook](../adjust-playbook/) | Modify existing skills |
| [/create-agent:review-agent](../../../create-agent/skills/review/) | Read-only audit of an agent's skills (composition integrity, quality) |
