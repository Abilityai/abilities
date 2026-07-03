---
name: profile-fleet
description: Interview and introspect each fleet agent on Trinity — what it does, its skills, workflows/pipelines, responsibilities, and who it collaborates with — then reconcile self-reported answers against declared config and correct the fleet/orchestration.md narrative. Scope comes from the orchestration narrative (fleet/system-map.yaml + fleet/orchestration.md).
when_to_use: When the orchestration picture is stale or thin and you want an accurate, reality-checked account of what each fleet agent actually does — "interview the agents", "profile the fleet", "what do these agents really do", "make orchestration.md correct" — before an orchestration redesign or onboarding. Interviews spend agent compute; narrative edits go through an approval gate.
automation: gated
allowed-tools: Read, Grep, Write, Edit, Bash, Skill, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__chat_with_agent, mcp__trinity__get_execution_result, mcp__trinity__get_agent_info, mcp__trinity__get_agent_skills, mcp__trinity__list_agent_schedules, mcp__trinity__list_agent_pipelines, mcp__trinity__get_agent_pipeline_state, mcp__trinity__get_agent_tags, mcp__trinity__get_agent_activity_summary
effort: high
user-invocable: true
metadata:
  version: "1.3"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.3: Internalize field lessons from the production orchestrator's copy — §3 role corrections go into the adjacent §3a prose subsection, never the GENERATED roster table (learned on its first live run); upgrade specifically the proposed/hypothesized §4 edges; route edge-vs-reality drift to /align-agent-permissions when installed"
    - "1.2: Point to /fleet-reconcile as the cheap sibling — folding already-verified deltas into the narrative without new interviews; this playbook is the evidence generator"
    - "1.1: Pipeline introspection degrades gracefully — list_agent_pipelines/get_agent_pipeline_state are not on every Trinity build; when absent, fall back to the map's pipelines: field (repo projects/*/pipeline.yaml via /discover-agents), the shared ~/.trinity/pipeline-state/ read surface when visible, and interview Q3"
    - "1.0: Initial version — narrative-scoped fleet interview + introspection; declared-vs-self-reported reconciliation; proposes orchestration.md prose edits behind a diff gate; per-agent dossiers in fleet/agent-profiles/ as checkpoints + evidence"
---

# Profile Fleet

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `profile-fleet vX.Y — recent: <summary>`. Then proceed.

## Purpose

Build an **accurate, reality-checked picture** of the fleet by talking to the agents themselves — then fold it back into `fleet/orchestration.md`. For each fleet agent this **interviews** it (via `chat_with_agent`) about its mission, skills, workflows/pipelines, responsibilities, collaborations, and human gates, and **introspects** its declared config (skills, schedules, pipelines, tags, recent activity via Trinity MCP). It **reconciles** the three sources — what the agent says, what its config declares, and what `orchestration.md` currently claims — classifies each finding, and proposes corrected **prose** edits to the narrative behind an approval gate.

Scope is decided by the **orchestration narrative**, not a raw Trinity listing: only agents in `fleet/system-map.yaml` / `fleet/orchestration.md` (§3 Nodes) are profiled. The output is the *narrative* (`orchestration.md`); the *machine map* (`system-map.yaml`) stays owned by `/discover-agents`.

ultrathink — the value is in the reconciliation, not the transcription. Distinguish what an agent *actually does* from what it *claims* or *aspires to*. Cross-check every self-report against declared skills/schedules and flag contradictions rather than smoothing them over.

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Orchestration narrative (scope + target) | `fleet/orchestration.md` | ✓ | ✓ (prose sections only) |
| System map (nodes: `ref`, `source`, summary) | `fleet/system-map.yaml` | ✓ | |
| Live Trinity agents | `mcp__trinity__list_agents` | ✓ | |
| Declared config | `get_agent_info` / `get_agent_skills` / `list_agent_schedules` / `list_agent_pipelines` + `get_agent_pipeline_state` (when the build ships them) / `get_agent_tags` / `get_agent_activity_summary` | ✓ | |
| Self-report (interview) | `mcp__trinity__chat_with_agent` (+ `get_execution_result` to poll) | ✓ | |
| Per-agent dossiers (checkpoints + evidence) | `fleet/agent-profiles/<trinity_name>.md` | ✓ | ✓ |
| System map refresh (when stale) | `/discover-agents` | | ✓ (writes `system-map.yaml`) |

## Prerequisites

- Trinity MCP (`trinity` server) reachable; agents to profile are **running** (a stopped agent can only be introspected, not interviewed).
- `fleet/orchestration.md` and `fleet/system-map.yaml` exist (else refresh via `/discover-agents` in Step 1).
- **Recommended first:** run `/sync-fleet-to-head` so interviews describe each agent's *latest* code, not stale deployed behavior.
- A Trinity key with scope to introspect and chat with the in-scope agents. Some may be **teammate-owned** (another Trinity user); if a call is denied, degrade gracefully (Step 4 / Error Recovery).

## Composes

- `/discover-agents` — rebuilds `fleet/system-map.yaml` from repo specs + live Trinity. Invoked only when the map is missing or stale; this playbook otherwise **reads** it.
- `/sync-fleet-to-head` — recommended pre-step (not auto-invoked) so profiles reflect current HEAD.

## Process

### Step 1: Load scope from the narrative

1. Read `fleet/orchestration.md` — the current narrative (§3 Nodes, §4 Edges, §6 Patterns) is both the **target** to correct and the **prior belief** to reconcile against. Note any `<!-- BEGIN GENERATED:* -->` … `<!-- END GENERATED:* -->` blocks — those are **off-limits** for editing (owned by `/discover-agents` & `/compose-system`).
2. Read `fleet/system-map.yaml` `agents:` block. For each entry derive **`trinity_name`** = the `deployed_name` field if present, else the last segment of `ref:` (e.g. `trinity://default/researcher-prod` → `researcher-prod`); the map key is the logical name, the deployable name is in `deployed_name`/`ref:`. Also note `source:`, `role`, `summary`, `schedules`.
3. **Freshness:** if the map is missing or its agent set diverges materially from `list_agents`, invoke `/discover-agents`, then re-read. Do not hand-edit the map.

The set of `trinity_name` values in the narrative is the **in-scope list**. Agents live on Trinity but absent from the narrative are reported as out-of-scope (candidates for `/discover-agents`), not profiled.

### Step 2: Confirm scope & depth — [APPROVAL GATE 1]

`list_agents`, join to the in-scope list, and present:
- Agents to profile (and any out-of-scope / not-running ones that will be skipped).
- A note that interviewing spends fleet compute, including teammates' agents.
- **Depth choice** (materially changes cost/time):
  - **quick** — introspection only + one combined self-description message per agent.
  - **standard** — introspection + the full question battery (Step 4), single pass. *(default)*
  - **deep** — standard + targeted follow-ups on contradictions and half-built areas.
- Optional subset (from `$ARGUMENTS` or user) to profile only some agents.

Wait for the choice before spending compute.

### Step 3: Introspect declared facts (cheap, MCP-only, parallel)

For each in-scope, running agent gather the **declared** truth (no LLM turn, run concurrently):
- `get_agent_info` — type, owner, status, config.
- `get_agent_skills` — the skills/commands it actually has.
- `list_agent_schedules` (+ enabled/disabled) — its scheduled workflows.
- `list_agent_pipelines` / `get_agent_pipeline_state` — long-running pipelines it runs. **Not every Trinity build ships these two tools** — if they're absent from the MCP server, don't fail the introspection: fall back to the `pipelines:` field on the agent's `system-map.yaml` node (scanned from its repo's `projects/*/pipeline.yaml` by `/discover-agents`), read the shared `~/.trinity/pipeline-state/<pipeline_id>/` surface if it's visible from here, and lean on interview Q3 — marking those pipeline facts as declared-from-repo / interview-sourced rather than live-verified.
- `get_agent_tags` — declared capabilities/tags.
- `get_agent_activity_summary` — what it has actually been doing lately.

This is the yardstick the interview is checked against.

### Step 4: Interview each agent (parallel, checkpointed)

Interview via `chat_with_agent` (`parallel=true`; use `async=true` + poll `get_execution_result` for **deep**). **Tailor** the questions with the skills/schedules from Step 3 (specific beats generic). Ask (skip 2–8 for **quick**):

1. **Mission:** In 2–3 sentences — what are you, and what is your single core responsibility?
2. **Skills:** For each of your main skills/commands, one line: what it does and when it fires. *(You have: `<skills from Step 3>` — confirm/correct.)*
3. **Workflows & pipelines:** What end-to-end workflows or scheduled/pipeline jobs do you run, and what triggers each? *(Declared schedules: `<from Step 3>`.)*
4. **Systems (I/O):** What systems/data do you read from and write to?
5. **Collaboration:** Which other agents do you hand off to or depend on, and for exactly what? Who hands off to you?
6. **Human gates:** Which of your actions require a human to approve before they take effect?
7. **Boundaries:** What are you explicitly *not* supposed to do?
8. **Reality check:** What's genuinely working today vs half-built or aspirational?

**Checkpoint:** write each agent's dossier to `fleet/agent-profiles/<trinity_name>.md` (declared facts + self-report + a short reconciliation stub) as it completes. On re-run, skip agents already profiled today unless refreshing — this makes long runs resumable and gives Gate 2 an auditable evidence trail.

### Step 5: Reconcile & synthesize (ultrathink)

Per agent, compare **self-report ↔ declared config ↔ current orchestration.md** and tag each fact:
- **Confirmed** — all sources agree.
- **Corrected** — doc is wrong/outdated; interview + config agree on the truth.
- **New** — real (backed by a skill/schedule/activity) but missing from the doc.
- **Contradiction** — self-report conflicts with declared config → record both, flag for human, don't pick silently.
- **Aspirational** — claimed but not backed by any skill/schedule/activity → mark as intent, not reality.
- **Gone** — in the doc but the agent denies / no longer does it.

Then draft **prose** edits to `orchestration.md`:
- **§3 Nodes (roles)** — correct each agent's role/"does" to reality. **Caveat (learned in the field):** the §3 roster table is a `<!-- GENERATED:roster -->` block owned by `/discover-agents` — do NOT edit it. Put role corrections in the adjacent prose subsection **§3a Role reality (interview-corrected)** (create it if the narrative predates it) and note they'll be folded into the generated summaries on the next `/discover-agents` run.
- **§4 Edges** — upgrade proposed/hypothesized edges the interviews confirm (annotate evidence: *confirmed-by-caller* vs *declared-config* vs *still-hypothesized*); add discovered edges; drop denied ones.
- **§6 Collaboration patterns** — refine choreographies from the real workflows/pipelines.
- **§1 overview** and **§5 permissions intent** — only if the interviews change the high-level picture. Note that §5 changes are enforced downstream by `/compose-system` (re-run it to push permission intent into the manifest); reconciling §4 edges against real call history is `/align-agent-permissions` (if installed) — this playbook edits narrative, it does not deploy permissions.
- Update the **Status** note and **Last reviewed** date (`date -u +%Y-%m-%d`).

Never write inside a `<!-- BEGIN GENERATED -->` block; if a whole section is generated, leave it and note the gap.

### Step 6: Review the narrative diff — [APPROVAL GATE 2]

Present the proposed `orchestration.md` changes section-by-section, each change tagged with its class (Confirmed/Corrected/New/…) and evidence source. Surface contradictions and aspirational items explicitly. Wait for approval; apply all/some/none per the user's call.

### Final Step: Apply and report

Apply approved edits to `fleet/orchestration.md` (prose only). Report:
- Sections changed; counts by class (corrected N, new N, contradictions N, aspirational N, gone N).
- Agents profiled vs skipped (not running / out-of-scope / permission).
- Where dossiers were written (`fleet/agent-profiles/`).
- Downstream pointers: `/compose-system` to enforce §5; `/align-agent-permissions` (if installed) to reconcile edges against real call history; `/discover-agents` if map summaries need refreshing.

## Completion Checklist

- [ ] Scope taken from `fleet/system-map.yaml` / `orchestration.md`, not a raw `list_agents` sweep.
- [ ] Depth confirmed at Gate 1 before spending agent compute.
- [ ] Declared facts (skills/schedules/pipelines/tags/activity) gathered for every profiled agent.
- [ ] Interview answers cross-checked against declared facts; contradictions flagged, not smoothed.
- [ ] Aspirational claims separated from working reality.
- [ ] Per-agent dossiers written to `fleet/agent-profiles/` (checkpoint + evidence).
- [ ] Only prose sections edited; no `<!-- GENERATED -->` block touched.
- [ ] Diff reviewed at Gate 2 before writing `orchestration.md`.
- [ ] "Last reviewed" date updated; downstream steps noted.

## Error Recovery

| Situation | Action |
|---|---|
| `fleet/system-map.yaml` missing/stale | Invoke `/discover-agents`, then re-read. |
| Agent stopped / unhealthy | Introspect only; mark dossier "introspection-only, not interviewed"; skip its self-report. |
| `chat_with_agent` returns `queued_timeout` | The task is still running — poll `get_execution_result(execution_id)`; do NOT resend (duplicate-guard will kill it). |
| Permission denied on a teammate-owned agent | Try introspection (often still allowed); if chat denied, note "not interviewable with current key" and continue. |
| `list_agent_pipelines` / `get_agent_pipeline_state` not on this Trinity build | Skip the probe without erroring; use the map's `pipelines:` field + `~/.trinity/pipeline-state/` when visible; tag pipeline facts as not live-verified. |
| Thin/evasive answers | Fall back to declared facts; mark those facts low-confidence; in **deep** mode, one targeted follow-up, then move on. |
| Self-report contradicts declared skills/schedules | Record both in the dossier, tag **Contradiction**, defer to human at Gate 2. |
| Whole target section is a GENERATED block | Do not edit; report that the correction belongs in `/discover-agents` / `/compose-system` instead. |
| Run is large / risks the 45-min window | Interview in parallel; rely on per-agent checkpoints; profile a subset per invocation and resume. |

## Operational Notes

- **Three sources, one truth.** Self-report says *intent*, config says *capability*, activity says *reality*. Weight reality highest; an agent that claims a workflow with no matching schedule/skill/activity is aspirational.
- **Profiles describe deployed code.** Results reflect whatever is currently running — run `/sync-fleet-to-head` first for an at-HEAD picture.
- **Narrative, not enforcement.** This playbook only edits `orchestration.md`. Turning §5 intent into enforced `agent_permissions` is `/compose-system`; reconciling §4 edges against real call history is `/align-agent-permissions`, if installed.
- **The cheap sibling.** When the deltas are *already verified* (a fix applied this session, an audit's findings) the docs don't need a re-interview — `/fleet-reconcile` folds them into the narrative, dossier addenda, CLAUDE.md, and memory behind one gate, at zero agent compute. Reach for this playbook only when the evidence itself is stale.
- **The self-reference:** if this orchestrator is itself in the fleet (often deployed under a different name), profiling it is self-introspection — describe it from what you know rather than interviewing yourself in a loop.

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Which interview questions produced signal vs noise? Any MCP introspection that added/removed value?
- [ ] **Identify improvements**: Could the question battery, reconciliation classes, or diff presentation be sharper?
- [ ] **Scope check**: Only tactical/execution changes — NOT the core purpose (narrative-scoped, reality-checked, gated narrative edits).
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md; bump `metadata.version` and prepend a `changelog` entry (newest-first).
  - [ ] Keep changes minimal and focused.
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/profile-fleet/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(profile-fleet): <brief improvement description>"`
