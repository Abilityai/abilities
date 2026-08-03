---
name: create-playbook
description: Create a new skill or playbook. Guides through requirements gathering and generates the appropriate template based on complexity.
disable-model-invocation: false
user-invocable: true
argument-hint: "[skill-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "2.13"
  created: 2025-02-10
  updated: 2026-08-03
  author: Ability.ai
  changelog:
    - "2.13: Trinity-first docs refresh (verified vs Claude Code 2.1.220) — ship the five tier templates as bundled supporting files (Step 6 pointed at a nonexistent templates/ dir; now ${CLAUDE_SKILL_DIR}/templates/); reframe the frontmatter reference as engine fields vs Trinity platform fields (add disallowed-tools, background:, ${CLAUDE_PROJECT_DIR}, allowed-tools grant semantics + accepted formats, name≡directory note; requires:/automation:/schedule: documented as platform contract, not caveat); replace the Routines advisory with the Trinity scheduling path (schedule: → template.yaml → create_agent_schedule; message invokes by slash name; timeout ≤ agent cap); add the Scheduled-Invocation Rule (scheduled playbooks keep disable-model-invocation: false, schedule messages use the slash name) and the Foreground-Fork Rule (headless-bound context: fork must set background: false — forks run in background by default since 2.1.218 and are reaped at turn-end) with matching validation-checklist lines; official supporting-file names in Step 4b; description/name coaching in Step 2"
    - "2.12: Add the Library-Grade Rule to Design Constraints + Step 5b library-target question — a skill destined for a shared skills library declares a requires: frontmatter contract (env keys, packages, binaries), references credentials only as named env vars (never .env reads, no interactive auth, materialize-from-env when a tool demands a credential file), fails with named missing-key errors, and passes a deterministic env-coherence + secret-scan check before contribution"
    - "2.11: New Step 9 registers the created skill in the agent's CLAUDE.md — Core Capabilities row + request-phrased Request Dispatch row when the table exists, and resolves the playbook-gap operator-queue item (playbook-gap-<slug>) the skill was created to close"
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
> Tier templates are bundled with this skill in [templates/](templates/) — reference them at runtime via `${CLAUDE_SKILL_DIR}/templates/`.

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

1. **Name**: lowercase-with-hyphens, descriptive. For project/personal skills the **directory name is the command** (`name:` is display-only); for plugin skills `name:` sets the command segment — keep name and directory identical so they never drift.
2. **Purpose** → the `description:` field: third person, *what it does + when to use it*, key use case first — the skill listing truncates `description` + `when_to_use` at 1,536 characters.
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

- If YES: plan supporting files alongside SKILL.md using the official names — `reference.md` (detailed docs), `examples.md` (usage examples), `scripts/` (executables), `templates/` (files to fill in) — each referenced from SKILL.md so Claude knows when to load them (they load only when referenced, never automatically). Point at bundled scripts via `${CLAUDE_SKILL_DIR}`. Keep SKILL.md under 500 lines — move large reference material to separate files.
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

### Step 5b: Library Target?

Ask: **Is this skill destined for a shared skills library** — a catalog repo distributed to many agents — rather than just this agent?

- If YES: apply **The Library-Grade Rule** (Design Constraints) during generation — the `requires:` frontmatter block, env-var-only credentials, named missing-key errors, no host-specific assumptions — and run its deterministic check before finishing.
- If NO (default): proceed as agent-local.

### Step 6: Generate Skill

Read the appropriate template (bundled with this skill) and fill in the gathered requirements:

| Tier | Template |
|------|----------|
| 1 | `${CLAUDE_SKILL_DIR}/templates/simple-skill.md` |
| 2 | `${CLAUDE_SKILL_DIR}/templates/stateful-skill.md` |
| 3 (autonomous) | `${CLAUDE_SKILL_DIR}/templates/autonomous-template.md` |
| 3 (gated) | `${CLAUDE_SKILL_DIR}/templates/gated-template.md` |
| 3 (manual) | `${CLAUDE_SKILL_DIR}/templates/manual-template.md` |

Replace every `[bracketed]` placeholder; drop optional sections (e.g. `## Composes`) that don't apply.

### Step 7: Confirm and Create

Present summary before creating:

```
## New Skill: [name]

**Tier**: [1/2/3] ([Simple/Stateful/Full Playbook])
**Automation**: [autonomous/gated/manual/n/a]
**Location**: [path]
**Self-Improving**: [yes/no]
**Library-Grade**: [yes/no]

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

Edits to existing skill files hot-reload without restart. A restart is only needed if the top-level skills directory (`~/.claude/skills/` or `.claude/skills/`) didn't exist before this session. Plugin-hosted skills refresh with `/reload-plugins`.

### Step 9: Register in the Agent's CLAUDE.md

If the agent's CLAUDE.md lists capabilities, register the new skill so it's discoverable and dispatchable:

1. Add a row to `## Core Capabilities` (skill + purpose).
2. If a `## Request Dispatch` table exists, add a row phrased as the *incoming request* that should route to this skill — what gets asked, not the skill name restated.
3. If this skill was created to close a flagged **playbook gap**, resolve the flag: on Trinity, find the `playbook-gap-*` operator-queue item (`mcp__trinity__list_operator_queue`) and resolve it via `mcp__trinity__respond_to_operator_queue`, noting the new skill's name.

Skip silently when CLAUDE.md has no such sections, or for internal helper skills not meant for direct dispatch.

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
automation: gated        # Trinity platform field (see note below)
schedule: "0 9 * * 1"    # Trinity platform field, optional
disable-model-invocation: false   # keep false for scheduled playbooks (Scheduled-Invocation Rule)
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

## Frontmatter: Engine Fields vs Trinity Platform Fields

Skills here run on the Claude Code engine and deploy to the Trinity platform, and their frontmatter mixes both layers — **both are load-bearing**. The engine ignores unknown frontmatter by design, so platform fields are safe extensions, not hacks.

**Engine fields** (Claude Code — https://code.claude.com/docs/en/skills.md):
- `name`, `description`, `argument-hint`
- `allowed-tools` — a permission *grant*: listed tools run without prompts while the skill's turn is active, and the grant clears on the next user message. It does **not** restrict Claude to those tools. Accepts space/comma-separated strings or YAML lists; supports Bash rule syntax (`Bash(git add *)`) and `${CLAUDE_SKILL_DIR}` substitution
- `disallowed-tools` — the actual restriction: tools removed while the skill is active
- `user-invocable`, `disable-model-invocation` — ⚠️ scheduled playbooks must keep `disable-model-invocation: false` (see the Scheduled-Invocation Rule)
- `when_to_use` — additional trigger context; combined with `description`, capped at 1,536 chars in skill listing
- `arguments` — named positional args: `arguments: [issue, branch]` → `$issue`, `$branch` in content
- `model`, `effort` — override model/effort while the skill is active (`model: inherit` keeps the session model; effort `low`/`medium`/`high`/`xhigh`/`max`)
- `shell` — `bash` (default) or `powershell` for `!` command blocks
- `context: fork` + `agent:` + `background:` — run the skill in a subagent; forks run in the **background by default** — set `background: false` for anything bound for scheduled/headless use (see the Foreground-Fork Rule)
- `paths:` — glob patterns to scope auto-activation
- `hooks:` — skill-scoped lifecycle hooks

**String substitutions available in skill content:**
- `$ARGUMENTS` — full argument string; `$ARGUMENTS[N]` / `$N` — positional (0-based)
- `$name` — named arg from `arguments:` frontmatter
- `${CLAUDE_SESSION_ID}` — current session ID
- `${CLAUDE_EFFORT}` — active effort level
- `${CLAUDE_SKILL_DIR}` — absolute path to the skill's directory (use for bundled scripts and templates)
- `${CLAUDE_PROJECT_DIR}` — project root (the same path hooks receive)

**Trinity platform fields** (this plugin's playbook model — read by the platform and fleet tooling, not by the engine):
- `metadata:` block with `version`, `changelog` (newest-first), `author` — **required on every skill**: bump `version` and prepend a `changelog` entry on each edit, and pair it with the what's-new banner after the H1 (see the repo `CLAUDE.md` → "Skill Changelog & What's-New Banner")
- `automation: autonomous | gated | manual`
- `schedule: "<cron>"` — the durable schedule declaration; see below
- `requires:` — the library-grade dependency contract (env keys, packages, binaries) — see the Library-Grade Rule

**How a `schedule:` becomes a live schedule (Trinity):** the per-skill `schedule:` feeds the agent's `template.yaml` `schedules:` block — the durable/discovery copy, which Trinity never reads at agent creation. `/trinity:onboard` / `/trinity:sync` materialize it into live schedules via `create_agent_schedule`. The schedule's `message` is the prompt the agent receives — **it must invoke the skill by its slash name** — and its `timeout_seconds` must fit the agent's execution cap (default 3600s). The skill must also work when invoked manually, without Trinity — Trinity is the upgrade, never the gate.

When generating Tier 3 playbooks, keep the platform fields (the rest of the plugin depends on them) and add engine fields like `model:`, `context: fork`, or `paths:` when they fit.

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
- On Trinity this is a hard ceiling, not just a heuristic: a schedule's `timeout_seconds` must fit the agent's execution cap (default 3600s / 60 min) — 45 minutes is the headroom that survives it

When gathering requirements for Tier 3 playbooks, ask: "Can this complete in under 45 minutes? If not, how should we chunk it?"

**The No-Gates Rule for Autonomous Playbooks**: Autonomous playbooks run unattended on a schedule — there is no human to approve gates. An `[APPROVAL GATE]` in an autonomous playbook will cause execution to hang indefinitely, breaking the scheduled run.

- Autonomous playbooks MUST NOT contain any `[APPROVAL GATE]` markers
- If the workflow needs human approval at any point, it MUST be `gated` or `manual`, not `autonomous`
- When user requests autonomous + approval gates, explain the incompatibility and ask them to choose

**The Scheduled-Invocation Rule**: A scheduled playbook must stay invocable by the scheduler:

- Keep `disable-model-invocation: false` (the default). A natural-language schedule message reaches the skill through *model* invocation, which `disable-model-invocation: true` blocks — it also blocks preloading into subagents.
- Write the schedule `message` to invoke the skill by its **slash name** (`/skill-name args`), never as a paraphrase — on Trinity a message naming a missing skill fails loudly as `SKILL_NOT_FOUND`; a paraphrase that half-matches just drifts silently.

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

**The Foreground-Fork Rule (headless forks)**: `context: fork` skills run in the **background by default**. A headless/scheduled run is one agent turn, and turn-end reaps every background task (see the Long-Running-Task Rule) — so a scheduled playbook that invokes a background-forked skill can silently lose it. Any skill that uses `context: fork` and is bound for scheduled/headless use — or is composed by a playbook that is — must set `background: false` (wait for the fork's result in-turn), or not fork at all.

**The Composition Rule**: When a playbook needs work another skill already does, it **invokes that skill by name** (``Invoke `/child-skill` ``, `Skill` in `allowed-tools`) — it never inlines the child's steps, calls its internal scripts/files directly, or paraphrases what it does. The parent holds only the orchestration; the child stays the single source of truth, so its fixes propagate automatically. Call the unversioned name to ride latest; pin `/child-vN` only to freeze. Composition is a DAG (no cycles, keep it shallow). See [Composing skills](../../README.md#composing-skills-hierarchical-playbooks) for the full rule.

**The Reporting Rule**: A skill that produces a **surfaceable result** — a summary, a batch of items, a metrics snapshot — should **end with a guarded Trinity report** so an operator can see what the run produced without reading chat (this is the *only* window into a scheduled/headless run). Add a final step that calls the `mcp__trinity__report` MCP tool with a namespaced `report_type` (`<agent>.<result>` in `lower_snake`, e.g. `oracle.weekly_summary`), a short `title`, a JSON `payload`, and a `display_hint` — `table` (`{columns, rows}`), `kpi` (`{tiles:[{label,value,unit?}]}`), `markdown` (`{markdown}`), `timeline` (`{events:[{ts,label,detail}]}`), or omit for raw JSON. The report lands on the agent's **Reports** tab and the fleet **Operations → Reports** view — an append-only history alongside the live `dashboard.yaml` snapshot.

- **Guard it.** The tool exists only on Trinity (it publishes under the agent's own key). If `mcp__trinity__report` isn't available — e.g. running locally — skip the step **silently**. Reporting is an upgrade, never a gate: the skill must produce its result with or without Trinity.
- **Not for conversational replies** — only result-producing and scheduled runs.

**The Library-Grade Rule (shared skills library)**: A skill destined for a **shared skills library** — a catalog repo synced to many agents — is the same artifact held to a stricter portability contract. The consuming agent is unknown at authoring time: possibly headless, differently credentialed, on a different host. Library-grade skills MUST:

- **Declare their contract in frontmatter** — a `requires:` block listing every env key the skill reads plus its runtime deps, so a platform or reviewer can check fulfillment before the skill ever runs:
  ```yaml
  requires:
    env: [SLACK_BOT_TOKEN]      # every credential/config key the skill reads
    packages: [playwright]      # runtime packages (pip/npm), if any
    binaries: [ffmpeg]          # required executables, if any
  ```
  Keep `automation:` and `user-invocable` accurate — they are part of the same contract.
- **Reference credentials only as named env vars** — never read `.env` or other credential files directly. The environment is the interface; how keys get there is the consuming platform's business, and coupling to the delivery mechanism breaks the skill the moment it changes.
- **Fail with a named, actionable error when a key is missing** — e.g. "`SLACK_BOT_TOKEN` not set — add it to this agent's credentials" — never a silent skip or a generic failure.
- **Never assume interactive credential acquisition** (`gcloud auth login`, browser OAuth) — the consuming agent may be headless.
- **Materialize-from-env** when a tool demands a credential *file*: write the env var's content to a temp file at runtime and point the tool at it. The env var stays the contract; the file is the skill's own runtime artifact.
- **Carry no host-specific assumptions** — no absolute paths, no workspace files not shipped inside the skill directory; reference bundled scripts via `${CLAUDE_SKILL_DIR}`.

Deterministic pre-contribution check (env coherence + secrets):

```bash
# Env keys the skill actually references (excluding harness substitutions):
grep -rhoE '[$]\{?[A-Z][A-Z0-9_]{2,}\}?' [path]/SKILL.md [path]/scripts/ 2>/dev/null \
  | tr -d '${}' | sort -u | grep -v -e '^ARGUMENTS' -e '^CLAUDE_'
```

Every name in that list must appear in `requires.env` — and every declared key must actually be referenced (no decorative declarations). Then scan the skill directory for literal secrets (tokens, keys, passwords): there must be none. **A failed check is a blocker for contribution, never an advisory.**

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
- [ ] **Invocable when scheduled** — `disable-model-invocation` is false/absent, and the schedule message invokes the skill by slash name (the Scheduled-Invocation Rule)
- [ ] **No background forks** — the skill and every composed child using `context: fork` sets `background: false` (the Foreground-Fork Rule) — a background fork is reaped at turn-end in a headless run
- [ ] **Result-producing runs report** — a skill that yields a surfaceable result ends with a guarded `mcp__trinity__report` step (the Reporting Rule), skipped silently when the tool is absent — so a scheduled/headless run leaves a visible record on the Reports tab

If any check fails, the playbook cannot be autonomous. Recommend `gated` instead.

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [adjust-playbook](../adjust-playbook/) | Modify existing skills |
| [/create-agent:review-agent](../../../create-agent/skills/review/) | Read-only audit of an agent's skills (composition integrity, quality) |
