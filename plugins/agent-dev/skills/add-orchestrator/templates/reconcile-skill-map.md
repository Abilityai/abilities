---
name: reconcile-skill-map
description: Diff each agent's declared intended Trinity-Library skills (fleet/skill-map.yaml) against its live get_agent_skills assignments, report drift, and apply approved additions via assign_skill_to_agent. Never removes an undeclared skill without a human decision — a live skill absent from the map may mean the map is behind, not that the assignment is wrong.
when_to_use: When you want to check or apply intended-vs-actual skill assignments across the fleet — "check the skill map", "does everyone hold the skills they should", "apply the skill map", after adding an agent to fleet/skill-map.yaml, periodic skill-assignment hygiene. This is the governance surface for ent#646 (only a designated orchestrator agent may change an agent's skills, its own included) — not a general-purpose skill installer.
automation: gated
argument-hint: "[--check] [agent ...]"
allowed-tools: Read, Write, Edit, Grep, AskUserQuestion, mcp__trinity__get_agent_skills, mcp__trinity__assign_skill_to_agent, mcp__trinity__sync_agent_skills, mcp__trinity__list_agents
effort: medium
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-09-20
  author: orchestrator
  changelog:
    - "1.1: Delivery ladder gains the `conflict` state (trinity#2914, Trinity dev 1a1deb2b, 2026-09-22) — a library skill whose name matches an agent-authored .claude/skills/<name>/ is now refused before a byte is staged; never retried via sync_agent_skills (force does not override), reported as an unassign-or-rename decision; pre-fix instances still overwrite, so diff repo-native names first there"
    - "1.0: Initial version — declared-intent skill map (fleet/skill-map.yaml) reconciled against live get_agent_skills; missing entries proposed for apply via assign_skill_to_agent (additive, single-skill — never set_agent_skills, which replaces the whole list and would silently wipe undeclared skills); undeclared live skills reported as drift and never auto-removed (no safe single-skill removal call exists yet, #493); live agents absent from the map entirely surface as a distinct `unmapped` state, never conflated with a reviewed `skills: []` entry; excludes role-companion agents (capabilities come from their canon role file instead) and an agent's own in-repo playbooks (a separate plane, governed by /sync-fleet-to-head). ent#646"
---

# Reconcile Skill Map

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `reconcile-skill-map vX.Y — recent: <summary>`. Then proceed.

## Purpose

Keep each agent's **Trinity Library skill assignments** matched to what `fleet/skill-map.yaml` declares it should hold — the declared-intent half of the ruling that only a designated orchestrator agent may change an agent's skills, its own included (ent#646, R31 2026-09-17). This is **not** a general skill installer: it only ever proposes what the map already declares, and it **never** removes a live skill the map doesn't mention without an explicit human decision — an undeclared skill may mean the map is stale, not that the assignment is wrong.

**Scope boundary (read before running):**
- Touches only Trinity **Library** assignments (`get_agent_skills` / `assign_skill_to_agent`). An agent's own in-repo playbooks (a git submodule, or its own `.claude/skills/`) are a separate plane, governed by `/sync-fleet-to-head`, not this skill.
- An agent holding a role under a role-companion framework (e.g. Tandem) declares capabilities in its own canon role file instead, resolved via its role assignment — never duplicated in `fleet/skill-map.yaml`. An entry with a `role:` field is skipped here entirely.
- An entry with `status: catalog-only` (not deployed yet) is skipped — nothing live to reconcile against.

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Declared intent | `fleet/skill-map.yaml` | ✓ | ✓ (`steward`/`last_reconciled` stamps only — never `agents:` content) |
| Live skill assignments | `mcp__trinity__get_agent_skills` | ✓ | |
| Apply an approved addition | `mcp__trinity__assign_skill_to_agent` | | ✓ |
| Delivery retry (only if `not_delivered`) | `mcp__trinity__sync_agent_skills` | | ✓ |
| Fleet roster (deployed check) | `fleet/system-map.yaml` / `mcp__trinity__list_agents` | ✓ | |

## Prerequisites

- Trinity MCP reachable.
- `fleet/skill-map.yaml` exists — seeded empty at install (`agents: {}`); this skill scaffolds it from the bundled template if still missing, then has nothing to reconcile until entries are added by hand.
- The permission this ruling describes (ent#596) may or may not be enforced yet on a given instance — mechanically, any agent key can call these MCP tools today regardless. This skill is the discipline layer, not the enforcement; behave identically either way.

## Run modes

| mode | trigger | approval gate |
|---|---|---|
| **interactive** *(default)* | `/reconcile-skill-map` | Step 3 (apply plan) |
| **check** | `/reconcile-skill-map --check` | none — read-only report, no `assign_skill_to_agent` calls |

Bare agent names restrict scope to that subset.

## Process

### Step 1: Load the map

Read `fleet/skill-map.yaml`. If missing, copy it from this skill's own `templates/skill-map.yaml.template` and stop — report the map is empty and needs entries before anything can reconcile. Never fabricate entries.

For each agent entry, skip and report under **out of scope** (don't call any API for it) any with `status: catalog-only` or a `role:` field.

Also read `fleet/system-map.yaml` (or `list_agents`) for the fleet's actual roster and diff it against the map's `agents:` keys: any live, non-role agent **absent from `agents:` entirely** is reported as **`unmapped`** — nobody has reviewed it yet. This is a distinct state from an agent present with `skills: []` (reviewed, rationale says why nothing's declared): `unmapped` means the map has no opinion at all, the other means it was deliberately reviewed and confirmed empty. Never conflate the two, and never auto-add an `unmapped` agent to the map with a guessed rationale — that decision is the human's.

### Step 2: Diff against live state

For each remaining **mapped** agent (i.e. not `unmapped`, not skipped in Step 1), call `get_agent_skills(agent_name)`. Compare its `skills[].name` set against the map's declared `skills[].name` set:

- **declared, not live** → `missing` — candidate to apply.
- **live, not declared** → `undeclared` — **drift**, report only, never auto-remove.
- **both** → `in sync`.

An agent the call errors on, or that no longer resolves live at all, is reported as `unreachable` — not silently skipped and not counted as either `missing` or `in sync`.

Sanity-check the tool result itself before trusting a fleet-wide pattern: if `get_agent_skills` returns an empty list for many/most agents in one sweep, treat that as worth spot-checking (e.g. against `list_agents`/a REST equivalent) before reporting "the registry is empty" as fact — an MCP-layer under-reporting bug is a known failure mode on this platform (seen on `list_agent_schedules`), not something to assume ruled out.

### Step 3: Present the plan — [APPROVAL GATE — interactive mode only]

**Check mode:** print the same table and stop — no gate, nothing applied.

```
agent          declared  live  missing              undeclared (drift)
trinity        2         2     —                    —
trinity-docs   0         0     —                    —
some-agent     3         1     skill-a, skill-b     legacy-skill-x

unmapped (live, never reviewed): another-agent, yet-another-agent
```

State plainly: only `missing` items are ever proposed for `assign_skill_to_agent`; `undeclared` items are reported so a human can either add rationale to the map (if the assignment is actually wanted) or remove it by hand elsewhere; `unmapped` agents are reported so a human can add them to the map with a real rationale — this skill does none of those three automatically. Get a yes before applying anything. If every mapped agent is `in sync` and nothing is `unmapped`, report and stop — no gate needed.

### Step 4: Apply approved additions

For each approved `missing` item, call `assign_skill_to_agent(agent_name, skill_name)` — **never `set_agent_skills`**, which replaces an agent's entire skill list and would silently delete any `undeclared` skill this run already promised not to touch. This is single-skill and additive today; when a bundle-assign primitive (packs #342 / sets #530) ships, swap this call — the map's schema already carries a plain skill-name list either way.

Read the response's `delivery` status per skill:
- `injected` — done.
- `pending_start` — the agent is stopped; the assignment is recorded and will apply on next start. Report, don't treat as failed.
- `in_progress` — still installing; note it may not show up in a `get_agent_skills` call made immediately after.
- `not_delivered` (with a `reason`) — call `sync_agent_skills(agent_name)` once as the documented manual retry, then report the final outcome either way. Do not loop retrying.
- `conflict` — the agent already has a **skill it wrote itself** at `.claude/skills/<name>/` (no platform marker), and Trinity refused to overwrite it before staging a byte (trinity#2914, dev since 2026-09-22). **Never retry via `sync_agent_skills`** — a forced sync does not override a conflict. The agent's own copy is what runs; the assignment row stays with `delivery_status: conflict` and shows in the Skills tab. Report it as a decision for the operator: unassign the library skill, or rename the agent's own — a name match is not proof of the same skill. On pre-fix instances (v0.9.5 images and earlier) the library copy silently **overwrites** the agent's, so on those diff `get_agent_skills` against the agent's repo-native skill names before any assignment.

Do not touch `undeclared` items regardless of approval scope — deciding whether to amend the map or remove the live assignment is explicitly out of this skill's hands (see Purpose). There is no safe single-skill removal call today (#493 tracks it); removing one means a human constructs the full correct list for `set_agent_skills` themselves, outside this skill.

### Step 5: Stamp and report

Update `fleet/skill-map.yaml`: set `last_reconciled` to today's date, and `steward` to this agent's own name if it is still `null`. Never touch the `agents:` block itself — that's declared intent, not a derived fact. Report a compact before → after: applied (agent → skill, with delivery status), still-drifted (unresolved `undeclared`), unmapped (live agents never added to the map), unreachable, out-of-scope (catalog-only / role-companion), in-sync count.

## Completion Checklist

- [ ] Role-companion and catalog-only agents skipped, not silently merged into the diff.
- [ ] Live agents absent from `agents:` entirely reported as `unmapped`, never conflated with a reviewed `skills: []` entry.
- [ ] Every remaining mapped agent's live state fetched via `get_agent_skills` (not assumed from a prior run).
- [ ] A suspiciously uniform empty-skills result across many agents was spot-checked, not reported as fact.
- [ ] Plan approved at the gate before any `assign_skill_to_agent` call (interactive mode) — or nothing applied at all (check mode).
- [ ] `set_agent_skills` never called by this skill, under any circumstance.
- [ ] No `undeclared` item ever auto-removed.
- [ ] `last_reconciled` stamped only after a completed run, not a partial/aborted one; `agents:` content untouched.

## Error Recovery

| Situation | Action |
|---|---|
| `fleet/skill-map.yaml` missing | Scaffold from `templates/skill-map.yaml.template`; report empty, stop. |
| `get_agent_skills` errors for an agent | Report `unreachable`; continue with the rest. |
| `assign_skill_to_agent` returns `not_delivered` | Retry once via `sync_agent_skills`; report whichever outcome follows. Do not loop. |
| `assign_skill_to_agent` returns `conflict` | The agent authored a same-name skill; Trinity refused the overwrite. Do not retry, do not force — report it as an unassign-or-rename decision for the operator. |
| An agent in the map no longer exists live | Report under `unreachable`; suggest updating its entry — never auto-delete from the map. |
| Trinity MCP unavailable | Read and print the map; note the diff can't run without live `get_agent_skills`. |
| Someone asks this skill to remove an undeclared skill | Decline — out of scope by design (Purpose); point at `set_agent_skills` as the manual, human-driven path, with the full correct list constructed by hand. |

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: a new drift shape, a `get_agent_skills`/`assign_skill_to_agent` quirk, or a scope-boundary edge case encountered?
- [ ] **Identify improvements**: could the diff, the plan table, or the role-companion/catalog-only exclusion be clearer or safer?
- [ ] **Scope check**: tactical/execution changes only — not the core purpose (declared intent, additive-only, never auto-removes, Library-plane only).
- [ ] **Apply improvement** (if identified): edit this SKILL.md; bump `metadata.version` and prepend a `changelog` entry (newest-first); keep changes minimal.
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/reconcile-skill-map/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(reconcile-skill-map): <brief improvement description>"`
