---
name: fleet-reconcile
description: Fold already-verified fleet-reality deltas into every documented surface — fleet/orchestration.md prose (loaded each session), fleet/agent-profiles/ dossiers (dated addenda), CLAUDE.md, and the agent's memory system if it has one — then make one focused commit. Consumes deltas from the current session and, when present, an upstream audit skill's corrections_pending queue. Generates NO new evidence (no interviews, no audits). One batch approval gate before any edit is written.
when_to_use: After fixes are applied or an audit lands and the docs now trail reality — "reconcile the fleet docs", "fold today's changes into the narrative", "the orchestration doc is stale". Cheap (no agent compute); when the evidence itself is stale or missing, that's /profile-fleet (interviews) or your audit skill, not this.
automation: gated
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, Skill, mcp__trinity__list_agents, mcp__trinity__list_agent_schedules, mcp__trinity__get_agent_activity_summary, mcp__trinity__list_recent_executions, mcp__trinity__list_operator_queue
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-03
  author: orchestrator
  changelog:
    - "1.1: Reference the §3a role-reality subsection now that orchestration.md.template ships it — restores the ancestor's convention with a standard home"
    - "1.0: Initial bundle version — adopted from a production orchestrator's fleet-reconcile v1.1 and universalized: the audit-queue delta source is optional and convention-based (any skill's status.yaml carrying corrections_pending:), memory writes route to whatever memory system the agent has (or are skipped), section references align to the bundle's orchestration.md template, and the parallel-session drift guard is kept"
---

# Fleet Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `fleet-reconcile vX.Y — recent: <summary>`. Then proceed.

## Purpose

Keep the fleet's **documentation layer** true to verified reality. `fleet/orchestration.md` is imported into CLAUDE.md and loaded at every session start — a stale claim there propagates into every routing decision `/orchestrate` makes. This playbook takes deltas that are **already verified** (fixes applied this session, findings handed off by an audit skill) and folds them into every surface that documents the fleet, behind one batch approval.

**Boundary — what this playbook is NOT:**
- It does **not** generate evidence. No agent interviews (that is `/profile-fleet`), no audits (that is an upstream audit skill, if you have one). Live Trinity reads are allowed **only** to spot-confirm a delta already in hand before writing it.
- It does **not** touch GENERATED blocks in `orchestration.md` (§2 topology, §3 roster) — those are `/discover-agents`'s.
- It does **not** rewrite `fleet/agent-profiles/` dossier bodies — those are point-in-time interview evidence; they get dated addenda only. Full refresh = `/profile-fleet`.

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Delta queue (optional) | any `.claude/skills/*/status.yaml` carrying a `corrections_pending:` list — the handoff convention for audit skills; skip if none exists | ✓ | ✓ (move consumed items to `corrections_applied`) |
| Latest audit report (optional) | the audit skill's reports dir, newest file, if it keeps one | ✓ | |
| Narrative | `fleet/orchestration.md` (prose sections only) | ✓ | ✓ |
| Agent dossiers (if `/profile-fleet` has run) | `fleet/agent-profiles/*.md` | ✓ | ✓ (dated addenda under the header only) |
| Project instructions | `CLAUDE.md` | ✓ | ✓ (only when the skill set, a flow, or a table it carries changed) |
| Memory (if the agent has one) | whatever the agent's memory system defines (e.g. installed by `/add-memory`) | ✓ | ✓ (via its own conventions/skills — never invent a memory layout) |
| Trinity (spot-confirm only) | read-only MCP set in `allowed-tools` | ✓ | |
| Workspace git | repo root | ✓ | ✓ (one focused commit; no push unless asked) |

## Prerequisites

- At least one delta source: current-session verified changes, or a non-empty `corrections_pending` queue.
- Workspace is a clean-enough git repo to make one focused commit (unrelated dirty files are left unstaged, never swept in). If the agent isn't a git repo, apply the edits and skip Step 5 with a note.

## Process

### Step 1: Collect deltas

Gather from, in priority order:
1. **Current session context** — fixes applied, findings verified live, schedule/config changes made. These are the highest-trust deltas.
2. **`corrections_pending` queues** — `Glob` for `.claude/skills/*/status.yaml` and check each for a `corrections_pending:` list (audit skills use this as their machine-readable handoff). No such file is normal — proceed with session deltas only.
3. **Status changes in the newest audit report** (if the audit skill keeps a reports dir) whose doc surfaces were never updated.

For each delta record: *what changed, when, evidence (commit hash / execution id / live check), and which claim in which doc it invalidates*. A delta with no evidence tag does not proceed — either spot-confirm it now with a read-only Trinity call or drop it.

Also snapshot `git status --short` + `git log --oneline -3` now: parallel sessions may commit mid-run (a parallel commit can both absorb a pending edit and introduce a new fleet fact). Claims made in commits that land mid-run are **candidate deltas** — spot-confirm live before folding them in, and re-check the tree before staging in Step 5.

**If no deltas anywhere:** compare `orchestration.md`'s "Last reviewed" (§9) to the newest audit/profile run you can find. If the docs are older than the last evidence pass, something was likely missed — say so. Otherwise report "nothing to reconcile" and stop. If the evidence itself is old, suggest `/profile-fleet` or the audit skill (do not invoke them — they have their own gates and cost).

### Step 2: Map deltas to surfaces

ultrathink

Build the reconciliation plan — a table of `{surface, section, edit summary, evidence}` covering, per surface:

- **`fleet/orchestration.md`** (prose only — never the §2/§3 GENERATED blocks):
  - A **dated update block** — "Status update (YYYY-MM-DD, source)" — under §1, or extending whatever status convention the file has grown. Corrections move *into* the dated block; do not silently delete superseded claims — the narrative is a timeline.
  - §3a role-reality rows for affected agents (never the GENERATED §3 roster itself).
  - §4 edge rows only if wiring actually changed (new confirmed edge, edge died).
  - §5 boundaries only if grant intent changed — and note that §5 is enforced downstream by `/compose-system`, which must be re-run for the change to be real.
  - §6 choreography subsections whose reality/known-breakage lines are invalidated.
  - §7 escalation and §8 invariants when a delta touches them.
  - §9: bump "Last reviewed" with a one-line what-changed.
  - If the narrative has grown sections beyond the template, fold each change into the existing structure — never force the template's shape onto an evolved file.
- **`fleet/agent-profiles/<agent>.md`**: one dated blockquote addendum directly under the header — "**Update YYYY-MM-DD (source):** the <finding> below is OUTDATED/FIXED — <one-line reality + residuals>". Never edit the interview body.
- **`CLAUDE.md`**: only when the skill set, a flow, or a table it carries changed.
- **Memory** (only if the agent has a memory system): durable non-obvious lessons, written via that system's own conventions or skills. Do not store what the docs now already say — memory is for what future sessions need *before* reading docs.
- **`status.yaml`** (per queue consumed): move each consumed `corrections_pending` entry to `corrections_applied` as `{date, text}`.

Routing (out of scope here — list in the plan as recommendations, not edits): roster add/remove/rename → `/discover-agents` · self-reports no longer trusted → `/profile-fleet` · permission drift → re-run `/compose-system` from §5 (or `/align-agent-permissions` if installed) · agents behind their repos → `/sync-fleet-to-head` · need fresh findings → your audit skill.

### Step 3: [APPROVAL GATE] Present the plan

Show the full plan table (surface, edit, evidence) plus any routing recommendations. Ask via `AskUserQuestion`: **apply all / apply subset / cancel**. Nothing is written before this answer; "cancel" or no answer = stop with the plan saved to the conversation only.

### Step 4: Apply

Make the approved edits exactly as planned. Rules while editing:
- Every write dated; every claim traceable to its evidence tag.
- Use targeted `Edit` operations; keep unrelated lines untouched.
- Match each file's existing style and punctuation.

### Step 5: Commit

Re-check `git status` against the Step 1 snapshot (parallel-session guard), then stage **only** the files this run touched (orchestration.md, changed profiles, CLAUDE.md, memory files, status.yaml, and this SKILL.md if self-improved) and commit:

```
fleet: reconcile docs (YYYY-MM-DD) — <one-line delta summary>
```

Do not push unless the user asks. Unrelated dirty files stay unstaged.

### Final Step: Report

One compact summary: deltas consumed (and from where), surfaces edited, corrections moved to applied, commit hash, and any routing recommendations left for other skills.

## Completion Checklist

- [ ] Every delta has an evidence tag (session-verified, audit-queue, or spot-confirmed live)
- [ ] No GENERATED block touched; no dossier body rewritten (addenda only)
- [ ] Superseded claims moved into a dated update block, not silently deleted
- [ ] "Last reviewed" bumped in orchestration.md §9
- [ ] Consumed `corrections_pending` entries moved to `corrections_applied`
- [ ] Memory updated only via the agent's own memory conventions (or skipped if none)
- [ ] One focused commit, only this run's files, no push
- [ ] Zero writes before the approval gate

## Error Recovery

| Situation | Action |
|---|---|
| No `corrections_pending` queue anywhere | Normal — reconcile from session context only |
| `status.yaml` present but corrupt | Reconcile from session context; note the handoff queue was unreadable |
| An Edit anchor no longer matches (doc changed since read) | Re-read the file, re-anchor; if the section was restructured, fold the change into the new structure rather than forcing the old shape |
| Spot-confirm call fails | Drop that delta from the plan and say so; never write unconfirmed claims |
| Commit fails (hooks, conflicts) | Leave the edits in place, report the git error verbatim, do not retry destructively |
| Interrupted mid-apply | Edits are independent per surface; re-running Step 1 re-derives the remaining deltas (applied corrections are already in `corrections_applied` and drop out) |

## Related Skills

| Skill | Relationship |
|---|---|
| `/profile-fleet` | Generates new interview evidence and dossiers; use it when self-reports are stale — this playbook only folds deltas already in hand |
| `/discover-agents` | Owns the GENERATED roster/topology blocks and the system map |
| `/compose-system` | Enforces §5 intent as `agent_permissions` — a §5 edit here isn't real until it's re-run |
| `/sync-fleet-to-head` | Owns agent git-state reconciliation |
| `/align-agent-permissions` (if installed) | Owns permission-vs-reality drift analysis |
| Your audit skill (if installed) | Upstream — produces verified findings and the `corrections_pending` queue this playbook consumes |

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Were there friction points, unclear steps, or inefficiencies?
- [ ] **Identify improvements**: Could the surface list, edit conventions, or evidence rules be clearer?
- [ ] **Scope check**: Only tactical/execution changes — NOT the core purpose, the gate, or the no-new-evidence boundary
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md with the specific improvement
  - [ ] Bump `metadata.version` and prepend a `changelog` entry (newest-first)
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/fleet-reconcile/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(fleet-reconcile): <brief improvement description>"` (or fold into this run's reconcile commit)
