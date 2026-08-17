---
name: add-orchestrator
description: Make any agent a system-aware orchestrator — installs /discover-agents (discover the fleet from live Trinity and/or a repo list into a descriptive fleet/system-map.yaml), /compose-system (turn the map into a Trinity SystemManifest and deploy_system), and /orchestrate (route, fan out, and run ephemeral agents via Trinity MCP). Aligns with Trinity's existing SystemManifest; no parallel standard.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
argument-hint: "[--check]"
metadata:
  version: "1.22"
  created: 2026-07-01
  author: Ability.ai
  changelog:
    - "1.22: Install-time divergence detection (issue #8) — a read-only `--check` mode compares every installed runtime skill against its bundled template on three axes: `installed < bundled` (upgrade available), `installed > bundled` (BACK-PORT candidate — the field-hardened copy the marketplace should pull from, the signal issue #5 went weeks without), and equal version but differing content (local customization). Reported in the canon-doctor PASS/WARN/FAIL shape with a one-line fleet-readable verdict. Step 4's per-skill overwrite prompt now runs the same comparison, so the warning — a silent downgrade or an about-to-be-clobbered local edit — arrives at the moment of decision, not after. Deliberately scoped to add-orchestrator's own bundle and stateless; the plugin-framework-wide version is a separate follow-up. (Version skips 1.21, reserved for the open PR #7/#9.)"
    - "1.21: allowed-tools↔body drift fixes (issue #7) — /discover-agents v1.8 adds mcp__trinity__report to its grant (the Step 7 fleet_scan report was in the body but ungranted, silently never publishing under enforcement); /orchestrate v1.14 drops the three vestigial schedule tools (create/delete/list_agent_schedule) the v1.7 watchdog stopped using. Both are grant-vs-body hygiene, no behaviour change"
    - "1.20: orchestrate template 1.13 — dispatch is a one-line playbook call resolved from the target's live get_agent_skills catalog (fleet convention protocols/playbook-call.md); prose briefs are the recorded exception"
    - "1.19: Platform caveat rewritten for ent#89 (materialized at creation, disabled unless a literal YAML true, max 20, deduped by name, never re-applied on recreate) and the steward entry now scaffolds enabled: false so a template-derived agent cannot silently inherit an armed unattended sweep. Dropped the non-schema `id:` key in favour of `name:` as the identity key. Steward cadence no longer claims 'server-local time' — schedules and the container clock are both UTC (#1795), and legacy IANA aliases now 500 on create (#1823). Bundled /orchestrate → v1.12 (rooms + A2A routing)"
    - "1.18: Bundled /orchestrate v1.11 — event-choreography layer for standing 'whenever X happens, have Y react' asks (fourth routing pattern next to Single/Fan-out/Chain): custom domain events via emit_event alongside the #1578 backend terminals, subscriptions wired SELF-SERVICE (subscribe_to_event always subscribes the caller — the orchestrator dispatches the setup task to the subscriber, never subscribes on-behalf), edges recorded in orchestration.md §6, and four unenforced design rules (exact-triple match/no wildcards; no loop guard outside agent.task.* — custom event graphs must stay acyclic; wakes reach only running subscribers, at-most-once/no replay; interpolated payloads are a cross-agent injection surface). Allowed-tools catches up: event tools + the set_reminder/cancel_reminder the v1.7 watchdog already instructed"
    - "1.17: Step 9 summary separates the two GitHub tokens a deployed orchestrator depends on — the INSTANCE token (Settings → GitHub token) is what Trinity clones `github:` members with (the default create_agent/deploy_system path, required for private repos), while GH_TOKEN in the agent's .env only authenticates the agent's own gh/git calls; a private-repo fleet needs both. Bundled runtime skills: compose-system 1.3 + orchestrate 1.10 (repository-first members and rollouts)"
    - "1.16: Loop closure across the bundle — fleet/project-standard.md gains §12 (silence is a failure mode, both directions: the agent closes its loops with the operator; the operator is handed the loops only a human can close with people or agents outside the fleet), a waiting-on:<actor> label, the ### Waiting on / ### Loop closed comment formats, and a 3d/7d/14d nudge ladder in §8; bundled /project-steward v1.2 (Step 4b open-loop pass, digest opens with the closing statement and carries Your open loops, operator-initiated results notify the operator) and /orchestrate v1.9 (a run isn't done until delivery to the requester succeeds; every report ends with Your open loops / Waiting on you / Next without you). The agent drafts follow-ups, the human sends them — nothing here contacts a third party. Re-runs offer the §12 insert into an existing standard"
    - "1.15: Access-verification guidance — preflight flags an installed-but-unauthenticated gh (private github: sources, /sync-fleet-to-head pushes, and registry ops all depend on it); Q3's project layer verifies registry-repo write access + issues enabled via gh api before wiring the autonomous steward (a bad grant would otherwise surface as a silently failing schedule); Step 9's summary documents the deployed-credential story — GH_TOKEN via .env + inject_credentials, same convention as /add-canon Step 6b — for GitHub-touching skills on a Trinity instance"
    - "1.14: Bundled /discover-agents v1.7 — canon coverage line in the scan report (N/M mapped agents enrolled when the fleet has a canon), so an orchestrator that adopted /add-canon alone sees exactly which members are not yet aligned; /add-canon v1.1's fleet-enrollment step closes the gap from the orchestrator side"
    - "1.13: Canon-aware bundle — /discover-agents v1.6 scans each agent's x-canon: declaration (the shared canonical-data layer installed by the new sibling /add-canon) into a canon: field per map node with a cheap declared-folder drift check; /orchestrate v1.8 serves reads of published business facts from the canon repo (cited at canon@<sha>, staleness-flagged) instead of a chat turn and briefs the canon pointer into dispatches; orchestration.md gains a §3c data-layer subsection (offered as an upgrade insert on re-run, like §3b)"
    - "1.12: Bundled /orchestrate v1.7 — report-back subscriptions target the backend-emitted agent.task.completed/failed terminal events (trinity#1578) instead of a worker-emitted completion trailer, the deterministic fallback is a re-arming set_reminder one-shot (trinity#1296) instead of an orch-watch cron schedule, and teardown documents the #1580 spawn-provenance rule (agent keys can delete only agents they spawned); project-steward notes the agent.task.completed subscription as the push-style alternative to chat-history polling"
    - "1.11: Bundled /orchestrate v1.6 — dispatch is duration-aware and fire-and-park (never block-and-wait): quick tasks stay sync; long ones (or a queued_timeout receipt) go out chat_with_agent(parallel=true, async=true) with the execution_id parked in a run ledger (fleet/.orchestrate-runs.yaml) and the turn ended; dual wake-up — workers emit orchestration.task_completed via a standard prompt trailer the orchestrator pre-subscribes to ({{payload.task_id}}-templated message), plus a self-deleting orch-watch-<execution_id> watchdog schedule as deterministic fallback; new Step 6b report-back fetches the result, delivers via send_message (send_notification fallback), resumes parked chains, cleans up watcher + ledger, and only then tears down ephemerals"
    - "1.10: Bundled /discover-agents v1.5 — discovery source is asked up front when Trinity MCP is connected (live Trinity fleet as the Recommended default · sources.yaml repo scan · both/union); trinity/both runs roster from list_agents, so live agents missing from sources.yaml are no longer invisible (they land as live-only entries, match: live) and fleet/sources.yaml is required only for the repo-scan sources; Step 8's first scan now also fires when Trinity is connected even if sources.yaml is still the example"
    - "1.9: Platform-alignment fixes, verified against Trinity source — Step 7b calls create_agent_schedule with its real params (agent_name/name/cron_expression/message; schedule_name/cron/skill never existed) and documents that Trinity never reads template.yaml schedules: at agent creation (only /trinity:onboard//sync materialize it); Step 7's dashboard fleet panel now uses Trinity's real sections[]→widgets[] schema with rows /discover-agents materializes (the top-level fleet_map/panel_type block was silently never rendered); bundled templates: /discover-agents v1.4 sources topology edges from DECLARED intent (system.yaml permissions / §5) since agent_permissions are not exposed over MCP (get_agent_auth is subscription auth, not permissions) and materializes the dashboard Fleet rows; /orchestrate v1.5 makes ephemeral names rollout-unique via a persisted counter (delete_agent is a soft delete — names stay reserved until purge, ~180 days)"
    - "1.8: Ownership matrix (RACI-lite) — orchestration.md gains §3b, one fleet-wide informational table (domain → responsible/consulted/informed; A is structural: manager owns the record, operator owns escalations); loaded at session start via the existing @import, so the orchestrator routes by R and treats C/I as consult/notify etiquette — defaults, never gates; /orchestrate, /project-init, /project-steward, /profile-fleet read it advisorily; re-runs offer to insert §3b into an existing orchestration.md that predates it"
    - "1.7: Adopt the project-management layer (opt-in Q3) — /project-init + /project-steward (autonomous driver, from a production orchestrator's field-hardened v1.6) + a fleet/project-standard.md template; registry repo, operator, and cadence parameterized at install; steward schedule recorded in template.yaml schedules:; dispatches resolve owners via the map's deployed_name and respect orchestration.md §5; deliberately does NOT compose /orchestrate (transitive autonomy — its interactive disambiguation would hang an unattended run)"
    - "1.6: Internalize the production orchestrator's profile-fleet field lesson — §3 role corrections route to a §3a prose subsection (the §3 roster is GENERATED and must not be hand-edited); orchestration.md.template now ships the §3a stub; fleet-reconcile references it; /align-agent-permissions referenced when installed"
    - "1.5: Adopt /fleet-reconcile into the bundle (sixth skill) — gated doc-reconciliation that folds already-verified deltas (session fixes, audit corrections_pending queues) into orchestration.md prose, dossier addenda, CLAUDE.md, and memory, then makes one focused commit; universalized from a production orchestrator (optional convention-based audit queue, memory-system-agnostic, section refs aligned to the bundle's orchestration.md template)"
    - "1.4: Integrate with /add-pipeline (the intra-agent sibling) — /discover-agents scans each repo's projects/*/pipeline.yaml into a pipelines: field per map node, /orchestrate routes pipeline-shaped work to the owning agent instead of re-sequencing its stages as a chain, /profile-fleet degrades gracefully on Trinity builds without the pipeline MCP introspection tools; cross-pointers added both ways"
    - "1.3: Adopt two fleet-maintenance skills into the bundle — /sync-fleet-to-head (non-destructively bring in-scope agents to their GitHub HEAD; pull-only clean→stash_reapply ladder, conflict gates) and /profile-fleet (interview + introspect agents, reconcile self-report vs declared config, correct orchestration.md prose behind a gate; writes fleet/agent-profiles/). Both are narrative-scoped and compose /discover-agents"
    - "1.2: Add the orchestration-narrative layer — scaffolds fleet/orchestration.md (hybrid: human prose + tool-refreshed roster/topology blocks) as the standard home for the who-calls-whom-and-why intent, imports it into CLAUDE.md via @fleet/orchestration.md so it loads at session start; /discover-agents refreshes its roster+topology from live agent_permissions, /compose-system sources agent_permissions from its §5, /orchestrate routes by its edges/patterns"
    - "1.1: Self-description moves to x-capabilities: (no longer collides with Trinity's native flat capabilities: keyword list); scanner is zsh-safe and matches Trinity repo-first with an explicit deployed_name; two explicit modes up front — describe an existing fleet (map-only, read-only) vs provision a new system (map→manifest→deploy)"
    - "1.0: Initial version — installs /discover-agents, /compose-system, /orchestrate into a target agent; scans local + github:Org/repo repos for template.yaml/system.yaml into fleet/system-map.yaml; composes a Trinity SystemManifest; defines the optional self-description block"
---

# Add Orchestrator

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-orchestrator vX.Y — recent: <summary>`. Then proceed.

Turn any Trinity-compatible agent into a **system-aware orchestrator**: an agent that knows what other agents exist (deployed *or* just sitting in a GitHub repo), what each can do, and can route work to them, batch across them, or roll one out ephemerally, use it, and spin it back down.

> 🔍 **Already installed? `/add-orchestrator --check`** runs a read-only divergence report — per installed skill: upgrade available, back-port candidate (your copy is *ahead* of the bundle), or a local customization about to be clobbered — before you re-run and overwrite anything. See **Check mode** below.

**Two modes — pick by whether the fleet already exists. Don't force a linear pipeline.**

```
Mode A · Describe & route over an EXISTING fleet   (read-only — the common case)
  live Trinity and/or fleet/sources.yaml ──/discover-agents──▶ system-map.yaml (+ orchestration.md) ──/orchestrate──▶ work
  The map (facts) + orchestration.md (intent) ARE the read surface. No manifest, no deploy. Skip /compose-system.

Mode B · Provision a NEW system   (create agents that today are only catalog repos)
  author orchestration.md §5 ──/compose-system──▶ fleet/system.yaml (SystemManifest) ──deploy──▶ /orchestrate

Artifacts (four layers):
  fleet/sources.yaml       you curate — local paths + github:Org/repo (optional when discovering from live Trinity)
  fleet/system-map.yaml    FACTS (nodes) — descriptive, written by /discover-agents      (Mode A stops here)
  fleet/orchestration.md   NARRATIVE (edges + intent) — human prose + tool-refreshed blocks; imported into CLAUDE.md
  fleet/system.yaml        Trinity SystemManifest — prescriptive, written by /compose-system   (Mode B only)

Maintenance (keep the fleet + its narrative honest over time):
  /sync-fleet-to-head   non-destructively bring in-scope agents to their GitHub HEAD
  /profile-fleet        interview + introspect agents, reconcile reality, correct orchestration.md
  /fleet-reconcile      fold already-verified deltas into every doc surface — no new evidence, one gate

Drive (opt-in project-management layer — Q3 at install):
  /project-init         create/adopt a managed project (epic + workspace) per fleet/project-standard.md
  /project-steward      autonomous sweep: reconcile dispatches, dispatch next work to labeled owners,
                        escalate stalls, age the operator's open loops, write a daily digest —
                        never asks mid-run
```

**Loop closure (standard §12) runs through the whole bundle.** Silence is a failure mode, not an outcome, in both directions. Inbound: `/orchestrate` isn't done until the requester has actually been told the outcome — including when the run failed — and the steward's digest opens with what's now true, what's waiting on the operator, and what happens next unprompted. Outbound: work parked on somebody the fleet can't dispatch to — a client, a vendor, a colleague, an agent in another fleet — is labeled `waiting-on:<actor>`, aged in every digest under **Your open loops**, and handed to the operator with a drafted follow-up. **The agent drafts; the human sends** — nothing in this bundle contacts a third party on the operator's behalf.

**Design invariant (do not violate):** orchestration is **agent-owned**. Trinity supplies the substrate (shared folders, agent-to-agent permissions, MCP messaging, cron) but runs **no central DAG engine**. So the roll-out → work → tear-down lifecycle lives *inside* `/orchestrate` — stitched from existing MCP calls — never as a new platform primitive. The multi-agent *definition* aligns 1:1 with Trinity's `SystemManifest` (the same YAML `deploy_system` consumes); this skill does **not** invent a competing format.

**Sibling layer — `/add-pipeline`:** this skill is the *inter*-agent layer (route / fan out / lifecycle across a fleet); `/add-pipeline` is the *intra*-agent one (a population of items crawling through a staged DAG inside a single agent, advanced by that agent's own heartbeat). They compose, same invariant on both sides: `/discover-agents` surfaces each fleet agent's pipelines (`pipelines:` per map node, scanned from `projects/*/pipeline.yaml`), and `/orchestrate` routes pipeline-shaped work *to* the owning agent rather than re-sequencing its stages as a cross-agent chain. Conversely, when one pipeline's instances are really isolated tenants, the answer is one agent per tenant via this orchestrator — add-pipeline's "multi-instance, not multi-tenant" boundary points here.

**Data layer — `/add-canon`:** the third sibling is the fleet's *published-truth* layer — a shared, separately-versioned canon repo where each agent owns `agents/<name>/` (canonical business facts) and `protocols/` holds inter-agent contracts; writes are own-folder-only, cross-folder via PR. The integration mirrors `pipelines:`: `/discover-agents` scans each agent's `x-canon:` declaration into a `canon:` field per map node, `/orchestrate` serves reads of published facts from the canon folder (cited at `canon@<sha>`) instead of a chat turn — writes still route to the owning agent — and `orchestration.md` §3c records who owns which canonical domain. Install the layer itself with `/add-canon`; this skill only *consumes* the declarations.

**What gets installed into the target agent:**

| Artifact | Location | Purpose |
|---|---|---|
| `.claude/skills/discover-agents/SKILL.md` | agent repo | discover live Trinity and/or repos → `fleet/system-map.yaml` |
| `.claude/skills/compose-system/SKILL.md` | agent repo | `system-map.yaml` → Trinity `SystemManifest` → deploy |
| `.claude/skills/orchestrate/SKILL.md` | agent repo | route / fan out / ephemeral, via Trinity MCP |
| `.claude/skills/sync-fleet-to-head/SKILL.md` | agent repo | non-destructively bring in-scope agents to their GitHub HEAD (fleet git hygiene) |
| `.claude/skills/profile-fleet/SKILL.md` | agent repo | interview + introspect agents; reconcile reality and correct the `orchestration.md` narrative |
| `.claude/skills/fleet-reconcile/SKILL.md` | agent repo | fold already-verified deltas into the doc surfaces (narrative, dossiers, CLAUDE.md, memory) behind one gate — no new evidence |
| `.claude/skills/project-init/SKILL.md` | agent repo (opt-in, Q3) | create/adopt a managed project per the standard |
| `.claude/skills/project-steward/SKILL.md` | agent repo (opt-in, Q3) | autonomous project driver — sweep, dispatch, escalate, digest |
| `fleet/project-standard.md` | agent repo (opt-in, Q3) | project-management conventions both skills read at runtime — registry repo, labels, comment formats, dispatch protocol |
| steward schedule | `template.yaml` `schedules:` + Trinity MCP (opt-in, Q3) | `project-steward-sweep`, default cron `0 7-19/2 * * 1-5` |
| `fleet/sources.yaml` | agent repo | the repo list you edit (local paths + `github:Org/repo`) |
| `fleet/system-map.yaml` | agent repo | descriptive FACTS/nodes registry (written by `/discover-agents`) |
| `fleet/orchestration.md` | agent repo | design NARRATIVE — edges, permission intent, patterns; imported into CLAUDE.md, loads at session start (human prose + tool-refreshed blocks) |
| `fleet/system.yaml` | agent repo | Trinity manifest (written by `/compose-system`) |
| CLAUDE.md `## Orchestration` section + `@fleet/orchestration.md` import | agent repo | wires the skills + loads the narrative at session start |
| dashboard.yaml `Fleet` section | agent repo (if present) | table widget (Trinity's `sections[]`→`widgets[]` schema) — rows materialized by `/discover-agents` after each scan |

---

## Process

### Check mode (`--check`) — install-time divergence detection

Invoked as `/add-orchestrator --check`: a **read-only** report of how this agent's *installed* runtime skills compare to the *bundled* templates they were copied from. Nothing is written, no files are touched. The same per-skill comparison is called inline by **Step 4**'s overwrite prompt, so the warning reaches the operator *at the moment of the overwrite decision*, not after it (issue #8). When `--check` is the invocation, run this section and stop — skip the install steps.

**Scope is deliberate and stateless.** This compares only the skills add-orchestrator itself installs (`discover-agents`, `compose-system`, `orchestrate`, `sync-fleet-to-head`, `profile-fleet`, `fleet-reconcile`, and the Q3 pair `project-init` / `project-steward`) against *this bundle's* `templates/`. It is **not** a general skill-registry inventory and keeps **no state on disk** — the bundle is the reference, the installed copy is the subject. The plugin-framework-wide version (every plugin that copies skills into agent repos) is a separate, larger call filed as a follow-up.

**Per skill, resolve two version stamps and compare content:**
- `installed` = `metadata.version` in the agent's `.claude/skills/<skill>/SKILL.md`
- `bundled`   = `metadata.version` in this skill's `templates/<skill>.md`

Compare **numerically, per dotted component** — `1.9 < 1.13`, so a plain string compare is wrong. Then classify into the three states issue #8 asked for (the third is the one everyone forgets):

| State | Verdict | Meaning |
|---|---|---|
| not installed | — (skip) | the agent never adopted this skill — a plain install, nothing to reconcile |
| `installed == bundled`, content identical | **PASS** | in sync |
| `installed == bundled`, content differs | **WARN** | **local customization** — the copy was hand-edited (e.g. a field-directive routing block). Surface the diff *before* an overwrite silently destroys it |
| `installed < bundled` | **WARN** | **upgrade available** — the bundle moved ahead; overwriting pulls the copy forward |
| `installed > bundled` | **FAIL** | **back-port candidate** — the *installed* copy is ahead of the bundle: a field-hardened local copy the marketplace should pull *from*, and overwriting it is a silent **downgrade**. The signal nobody was watching for weeks (issue #5) |

`FAIL` here does not mean "broken" — it is the loudest state on purpose, because a back-port candidate and an about-to-be-clobbered customization are exactly the two failures issue #8 was filed for.

**Mechanics** (read-only — resolves stamps, then diffs installed vs bundled):

```bash
SKILL_DIR="<this add-orchestrator skill's own directory>"
ver()  { grep -m1 -E '^[[:space:]]*version:' "$1" 2>/dev/null | tr -dc '0-9.'; }
# numeric dotted compare → prints <, =, or >
vcmp() { awk -v a="$1" -v b="$2" 'BEGIN{
  n=split(a,x,"."); m=split(b,y,"."); L=(n>m?n:m);
  for(i=1;i<=L;i++){u=x[i]+0; v=y[i]+0; if(u<v){print "<";exit} if(u>v){print ">";exit}}
  print "=" }'; }

for skill in discover-agents compose-system orchestrate sync-fleet-to-head profile-fleet fleet-reconcile project-init project-steward; do
  inst=".claude/skills/$skill/SKILL.md"; bund="$SKILL_DIR/templates/$skill.md"
  [ -f "$inst" ] || { echo "$skill: — not installed"; continue; }
  iv=$(ver "$inst"); bv=$(ver "$bund"); cmp=$(vcmp "$iv" "$bv")
  if [ "$cmp" = "=" ]; then
    if diff -q "$bund" "$inst" >/dev/null 2>&1; then echo "$skill: PASS in sync (v$iv)"
    else echo "$skill: WARN local customization — installed v$iv == bundled, content differs"; fi
  elif [ "$cmp" = "<" ]; then echo "$skill: WARN upgrade available — installed v$iv < bundled v$bv"
  else echo "$skill: FAIL back-port candidate — installed v$iv > bundled v$bv (overwrite = downgrade)"; fi
done
```

An installed copy is a byte-for-byte `cp` of `templates/<skill>.md` (Step 4 does no placeholder substitution), so on a clean install `diff -q` is exact and any difference at an equal version is a genuine local edit. To *show* the customization, run `diff "$bund" "$inst"` (or `git diff --no-index -- "$bund" "$inst"`) and print a compact hunk.

**Why equal-version is the only clean customization signal.** The bundle carries only the *current* template, not the historical one a behind copy was made from. So at `installed < bundled` the diff mixes the upgrade delta with any local edits and cannot cleanly separate them; only at `installed == bundled` is every differing line a local customization. Show the full diff for the equal-version case; for the behind case, lead with the version gap and offer the (mixed) diff on request.

**Report** — canon-doctor PASS/WARN/FAIL shape, ordered most-severe first (FAIL → WARN → PASS → not installed), closing with one verdict line an orchestrator can read fleet-wide:

```
add-orchestrator divergence check — <agent name>
  profile-fleet       FAIL  back-port candidate — v1.6 > bundled v1.4 (overwrite = downgrade)
  orchestrate         WARN  local customization — v1.13 == bundled, 12 lines differ (diff below)
  sync-fleet-to-head  WARN  upgrade available — v1.0 < bundled v1.4
  discover-agents     PASS  in sync (v1.7)
  compose-system      PASS  in sync (v1.3)
  fleet-reconcile     —     not installed

  verdict: DIVERGED — 1 back-port candidate, 1 behind, 1 customized. Back-port profile-fleet into the bundle before overwriting; review the orchestrate diff before any re-copy.
```

`verdict: IN SYNC` needs every installed skill at PASS; WARN and FAIL both count against it. Keep the verdict to one line — orchestrators dispatch this fleet-wide and read only that line per agent.

### Step 1: Preflight

Run from inside the target agent directory (the agent you want to *make* an orchestrator), or ask for the path.

```bash
# Must be an agent root (CLAUDE.md present)
[ -f CLAUDE.md ] || ask_user_for_agent_path

# Must have a .claude/skills/ directory (create if missing)
mkdir -p .claude/skills

# Recommended tooling used by the installed skills:
command -v yq >/dev/null 2>&1 || warn "yq not installed — discover/compose parse YAML more robustly with it. Install: brew install yq"
command -v gh >/dev/null 2>&1 || warn "gh not installed — github:Org/repo sources will fall back to shallow git clone. Install: brew install gh (and gh auth login)"
command -v gh >/dev/null 2>&1 && ! gh auth status >/dev/null 2>&1 && \
  warn "gh installed but not logged in — private github: sources, /sync-fleet-to-head pushes, and the project layer's registry ops will fail. Run: gh auth login"
```

If `CLAUDE.md` is missing, ask the user to point to the right directory or run `/create-agent` first.

Trinity MCP is **not** required to install — `/discover-agents` and `/compose-system` produce their files locally, and `/orchestrate` degrades to explaining what it *would* do when MCP is absent. Note whether `.mcp.json` (or `~/.trinity/config`) is present so the summary can tell the user which live features are available now.

### Step 2: Confirm scope

Use `AskUserQuestion`:

**Q1 — Which skills to install?**
- `All six` (discover-agents, compose-system, orchestrate, sync-fleet-to-head, profile-fleet, fleet-reconcile) — recommended
- `Core three` (discover-agents, compose-system, orchestrate) — the discover → compose → route trio, without the fleet-maintenance skills
- `Discovery only` (discover-agents) — just build the system map; wire the rest later

If any target skill directory already exists under `.claude/skills/`, ask per-skill: overwrite / skip / cancel. Never silently overwrite — and never *blindly*: run the **Check mode** comparison for that skill first and fold its verdict into the prompt (Step 4 spells out how), so the operator sees an upgrade, a back-port candidate, or a local customization before choosing.

**Q2 — Seed `fleet/sources.yaml` with the current repo list?** (free text, optional)
- Offer to paste an initial list of repositories now (local paths and/or `github:Org/repo`), or start with the commented example and edit later.

**Q3 — Add the project-management layer?** (opt-in — this installs an *autonomous, scheduled* driver, so it is never bundled silently)
- `No` — skip; re-run this skill later to add it.
- `Yes` — install `/project-init` + `/project-steward` and seed `fleet/project-standard.md` (which carries the §12 loop-closure discipline: the steward reports back to the operator rather than only filing on issues, and ages the operator's `waiting-on:<actor>` loops with drafted-but-unsent follow-ups). Then gather three parameters:
  - **Registry repo** — which GitHub repo hosts the project epics (default: this agent's own origin repo).
  - **Operator** — the human name `status:needs-operator` escalates to.
  - **Steward cadence** — cron for the sweep (default `0 7-19/2 * * 1-5`, i.e. every 2h, weekdays). **Times are UTC unless you say otherwise** — `create_agent_schedule` and a declared `schedules:` entry both default `timezone` to `UTC`, and the agent container's own clock is UTC. If "working hours" should mean the operator's clock, ask for a timezone and pass it (`timezone: "Europe/London"`); never a legacy IANA alias (`Europe/Kiev`, `Asia/Calcutta`) — those no longer resolve and the schedule 500s on create.

  Then **verify registry access before wiring the steward** — it runs unattended, so a bad grant surfaces as a silently failing schedule, not an error in front of anyone: `gh api "repos/$REGISTRY_REPO" --jq '{push: .permissions.push, issues: .has_issues}'` — expect `push: true, issues: true`. On failure, warn and have the user fix access (or pick another repo) before the first sweep; don't hard-stop the install — the layer is repairable. Note that a **deployed** steward additionally needs a `GH_TOKEN` in the instance's `.env` (see the Trinity note in Step 9's summary).

### Step 3: Scaffold the fleet directory

```bash
mkdir -p fleet
SKILL_DIR="<this add-orchestrator skill's own directory>"

# Seed the sources list only if absent (never clobber a user-edited list)
[ -f fleet/sources.yaml ] || cp "$SKILL_DIR/templates/sources.example" fleet/sources.yaml

# Seed an empty, well-formed system-map so /orchestrate and dashboards don't choke pre-scan
[ -f fleet/system-map.yaml ] || cp "$SKILL_DIR/templates/system-map.yaml.template" fleet/system-map.yaml

# Seed the narrative layer (hybrid: human prose + tool-refreshed blocks) — never clobber an authored file.
# SYSTEM_NAME = sources.yaml `system_name`, else "<agent>-fleet". Only {{SYSTEM_NAME}}/{{DATE}} are substituted.
if [ ! -f fleet/orchestration.md ]; then
  sed -e "s/{{SYSTEM_NAME}}/$SYSTEM_NAME/g" -e "s/{{DATE}}/$(date -u +%Y-%m-%d)/g" \
      "$SKILL_DIR/templates/orchestration.md.template" > fleet/orchestration.md
fi
```

**Upgrade path — §3b ownership matrix:** if `fleet/orchestration.md` already exists but has no `### 3b` section (an install predating v1.8), offer to add it — never insert silently into an authored narrative. On yes, copy the `### 3b. Ownership matrix` section from the template, inserted after §3a (before `## 4`), with its table left empty for the human to fill. On no, skip; re-running offers again.

**Upgrade path — §3c data layer:** same rule for `### 3c` (an install predating v1.13): offer to insert the `### 3c. Data layer` section from the template after §3b (before `## 4`), table left empty. Only relevant once the fleet adopts `/add-canon`, so mention that when offering.

**Upgrade path — §12 loop closure:** `fleet/project-standard.md` is live fleet configuration and is never clobbered, so an install predating v1.16 has no `## 12. Loop closure` — and `/project-steward`'s open-loop pass reads it. If the file exists and `grep -q '## 12. Loop closure' fleet/project-standard.md` fails, offer to append that section from the template (plus the `waiting-on:<actor>` row in §3, the two comment formats in §6, and the open-loop ladder paragraph in §8), substituting the existing `{{AGENT_NAME}}`/`{{OPERATOR}}` values. On no, skip and say the steward's loop pass stays inert until the section exists.

If the user pasted repos in Q2, append them under `repos:` in `fleet/sources.yaml` (one entry per line, preserving the header comments).

If the project layer was selected in Q3, also seed the standard and the steward's state dirs (never clobber an existing standard — it is live fleet configuration):

```bash
if [ ! -f fleet/project-standard.md ]; then
  sed -e "s|{{REGISTRY_REPO}}|$REGISTRY_REPO|g" -e "s|{{OPERATOR}}|$OPERATOR|g" \
      -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" -e "s|{{DATE}}|$(date -u +%Y-%m-%d)|g" \
      "$SKILL_DIR/templates/project-standard.md.template" > fleet/project-standard.md
fi
mkdir -p fleet/project-steward/digests fleet/project-steward/outputs
```

(`$AGENT_NAME` = this agent's logical name — `name:` from `template.yaml`, else the CLAUDE.md agent name. Label creation in the registry repo is NOT done here — `/project-init` creates the taxonomy idempotently on first use.)

### Step 4: Copy the selected runtime skills

For each skill selected in Q1, copy its template. The templates are ready to use as-is — **no placeholder substitution** (they read `fleet/sources.yaml` / `fleet/system-map.yaml` at runtime and infer the agent name themselves).

**Before overwriting any existing `.claude/skills/<skill>/SKILL.md`, run the Check-mode comparison for that one skill (above) and present its verdict inside the overwrite prompt** — this is the moment issue #8 exists for. Make the prompt say what the operator is about to do:
- **PASS** (in sync) — nothing to warn about; the overwrite is a no-op. Offer skip as the default.
- **upgrade available** (`installed < bundled`) — "orchestrate v1.11 → v1.13 (upgrade). Overwrite / skip / cancel." Overwrite is the safe default.
- **local customization** (`installed == bundled`, content differs) — show the diff first: "orchestrate v1.13 == bundled but **12 lines were hand-edited** (diff below) — overwriting DISCARDS them. Overwrite / skip / cancel." Default to skip; if they overwrite, tell them to re-apply the edit.
- **back-port candidate** (`installed > bundled`) — "profile-fleet installed v1.6 is **ahead** of bundled v1.4 — overwriting is a DOWNGRADE and loses field-hardening. Recommend skip and back-port the installed copy into the marketplace instead. Overwrite / skip / cancel." Default to skip.

A fresh install (no existing copy) skips all of this and just copies.

```bash
for skill in discover-agents compose-system orchestrate sync-fleet-to-head profile-fleet fleet-reconcile; do
  # skip any the user didn't select in Q1
  is_selected "$skill" || continue
  mkdir -p ".claude/skills/$skill"
  cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
done

# Project layer (Q3) — same copy pattern, same overwrite prompt rules
if project_layer_selected; then
  for skill in project-init project-steward; do
    mkdir -p ".claude/skills/$skill"
    cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
  done
fi
```

### Step 5: Wire CLAUDE.md

Append an `## Orchestration` section to the target agent's `CLAUDE.md` (only if one isn't already present — grep for `## Orchestration`). Read `templates/claude-section.md`, then write its contents. It documents the three skills, the `fleet/` artifacts, the discover → compose → orchestrate flow, and the agent-owned-orchestration invariant.

Also add a one-line pointer in the agent's Core Capabilities table for each installed skill (`/discover-agents`, `/compose-system`, `/orchestrate`) if such a table exists.

**Import the narrative so it loads at session start.** `templates/claude-section.md` already ends with an `@fleet/orchestration.md` import — Claude Code pulls `@`-referenced files into context at load time. The grep-guard below covers the case where the `## Orchestration` section already existed (re-run) and predates this feature, so the import is added exactly once:

```bash
if ! grep -q '@fleet/orchestration.md' CLAUDE.md; then
  printf '\n**Loaded at session start (design narrative):**\n@fleet/orchestration.md\n' >> CLAUDE.md
fi
```

> **Token caveat (tell the user):** an `@`-import is always-on context. Keep `orchestration.md` lean — aim for < ~200 lines, tight summary up top, detail below. If a system's narrative grows large, swap the hard import for a strong pointer instead: a `CLAUDE.md` line like *"At session start, before any cross-agent routing, read `fleet/orchestration.md`."* Ship the `@`-import as the default.

### Step 6: Advertise this agent's own capabilities (the convention)

The scanner reads an optional **`x-capabilities:`** block from each agent's `template.yaml` — a rich, hyphenated *extension* key that coexists with Trinity's native flat `capabilities:` keyword list (the `x-` prefix keeps them from colliding). Since this agent is about to advertise *others*, make it self-describing too. If `template.yaml` exists and has no `x-capabilities:` key, offer to append the block from `templates/capabilities-block.template.yaml`, filled from the agent's CLAUDE.md identity:

```yaml
x-capabilities:
  role: orchestration
  summary: "<one line from the agent's identity>"
  provides:
    - skill: /orchestrate
      does: "route work across the fleet, fan out, run ephemeral agents"
    - skill: /discover-agents
      does: "build the system map from a repo list"
  lifecycle: persistent
  tags: [orchestrator, fleet, capability:orchestrate]
```

Leave any existing native `capabilities:` list untouched — append `x-capabilities:` beside it. This block is **additive and optional**: `/discover-agents` works on agents that lack it, falling back to `description`, `tags`, and the native `capabilities:` list. Do not fabricate capabilities the agent doesn't have.

### Step 7: Extend dashboard.yaml (if present)

Trinity's dashboard schema is `sections[]` → `widgets[]` with **materialized values** — the UI renders exactly what's in the file and never reads other files (a top-level `fleet_map:` key with `panel_type:`/`source:`, which versions ≤1.8 emitted, is silently ignored). So install a real section whose table `/discover-agents` re-materializes after every scan.

Grep-guard on `managed by /add-orchestrator`; if absent, append this section under the file's `sections:` list (creating a minimal `title:` + `sections:` scaffold if the file is empty) — use `yq` or a direct edit:

```yaml
  # managed by /add-orchestrator — rows refreshed by /discover-agents
  - title: "Fleet"
    layout: list
    widgets:
      - type: table
        title: "Fleet map"
        columns:
          - { key: agent, label: "Agent" }
          - { key: role, label: "Role" }
          - { key: deployed, label: "Deployed" }
          - { key: ref, label: "Ref" }
          - { key: pipelines, label: "Pipelines" }
        rows: []   # materialized by /discover-agents after each scan — starts empty
        max_rows: 30
```

**Migration:** if a top-level `fleet_map:` key from a ≤1.8 install is present, remove it (it never rendered) when adding the real section.

If there is no `dashboard.yaml`: `echo "ℹ️  No dashboard.yaml — skipping fleet panel. The orchestrator still works; it just won't render on Trinity until a dashboard.yaml exists."`

### Step 7b: Steward schedule (project layer only)

Skip unless Q3 selected the project layer. The steward is autonomous — it needs its schedule wired, and the schedule must be durable and discoverable, not live-only:

1. **Record it in `template.yaml`'s `schedules:` block** (grep-guard on `project-steward-sweep` so re-runs never duplicate). This is the source of truth `/trinity:sync` reconciles and `/discover-agents` reads. (Platform caveat, ent#89: Trinity **does** materialize this block at agent creation — entries land **disabled unless they declare a literal YAML `enabled: true`**, max 20, deduped by `name`, never re-applied on recreate. Because this entry is an *autonomous* steward, declare `enabled: false` here and let the `create_agent_schedule` call below arm the live one, so an agent created later from this template does not silently inherit an armed unattended sweep.)
   ```yaml
   - name: project-steward-sweep     # identity key — Trinity dedups on `name`; there is no `id` field
     cron: "<from Q3, default 0 7-19/2 * * 1-5>"
     message: "Run /project-steward"
     purpose: Sweep fleet-managed projects — reconcile dispatches, dispatch next work, escalate, digest
     timezone: UTC                   # canonical IANA only — legacy aliases (Europe/Kiev) 500 on create
     enabled: false                  # armed live in step 2; keeps a template-derived agent from inheriting an unattended sweep
   ```
2. **If Trinity MCP is available**, install the live schedule via `create_agent_schedule` with its real params: `agent_name`, `name: "project-steward-sweep"`, `cron_expression: "<from Q3>"`, `message: "Run /project-steward"`, optional `description`. (There is no `schedule_name`/`cron`/`skill` param — the `message` is the prompt the agent receives, so it must name the skill.) If not, print that the steward works locally when invoked manually and the schedule will be reconciled by `/trinity:onboard` / `/trinity:sync` later.
3. If `template.yaml` is absent, warn: the schedule exists live-only (invisible to `/trinity:sync` and fleet discovery) — same caveat as `/add-pipeline`.

### Step 8: First scan (advisory)

If `/discover-agents` was installed and either `fleet/sources.yaml` has at least one real (non-comment) entry **or Trinity MCP is connected** (the skill can roster the live fleet directly), invoke it once to produce an initial `fleet/system-map.yaml` — call the skill by name, don't reimplement it:

```
Invoke `/discover-agents`
```

If `sources.yaml` is still just the example **and** Trinity MCP is absent, skip this and tell the user to add repos (or connect Trinity) and then run `/discover-agents`.

### Step 9: Summary

Print:

```
## Orchestrator installed into <agent name>

### Skills added
- /discover-agents    → discover live Trinity and/or fleet/sources.yaml into fleet/system-map.yaml
- /compose-system     → fleet/system-map.yaml → fleet/system.yaml (Trinity manifest) → deploy
- /orchestrate        → route / fan out / run ephemeral, via Trinity MCP
- /sync-fleet-to-head → non-destructively bring in-scope agents to their GitHub HEAD
- /profile-fleet      → interview + introspect agents, correct the orchestration.md narrative
- /fleet-reconcile    → fold already-verified deltas into the doc surfaces — no new evidence
- /project-init       → create/adopt a managed project (epic + workspace)   [if Q3 = yes]
- /project-steward    → autonomous project driver — sweep, dispatch, close loops, digest [if Q3 = yes]

### Files
- fleet/sources.yaml       (edit this — your repo list)
- fleet/system-map.yaml    (FACTS/nodes — <generated | empty until first scan>)
- fleet/orchestration.md   (NARRATIVE/intent — author §4–§7; imported into CLAUDE.md)
- fleet/project-standard.md (project-management conventions | not installed — Q3 skipped)
- CLAUDE.md                (Orchestration section + @fleet/orchestration.md import added)
- dashboard.yaml           (Fleet section added — rows refresh on each /discover-agents | no dashboard.yaml)

### Trinity MCP: <available | not detected>
<if not: note that discover/compose still work locally; orchestrate + deploy need /trinity:onboard first>
<if deploying this orchestrator to Trinity: GitHub-touching skills — /sync-fleet-to-head, /project-steward,
 reading private github: sources — need a GH_TOKEN in the deployed .env (fine-grained PAT covering those repos;
 injected by /trinity:onboard Step 5e via inject_credentials — same convention as /add-canon Step 6b)>

### Two different GitHub tokens — don't conflate them
- **The instance token** (Trinity UI → Settings → GitHub token): what *Trinity* clones with. It's what makes
  the default deploy path work — `create_agent(template: github:Org/repo)` and every `github:` member in a
  `deploy_system` manifest. Required for private repos; public ones clone without it.
- **GH_TOKEN in this agent's .env**: what *this agent's own* `gh`/git commands run as inside its container.
  It never affects how Trinity clones fleet members.
A fleet of private repos needs both: the instance token to deploy the members, the agent token for the
orchestrator's own repo work.

### Next steps
1. Edit fleet/sources.yaml — add the repos (local paths and/or github:Org/repo) in the system.
   (Fleet already live on Trinity? /discover-agents can roster it directly — sources.yaml then just adds catalog repos.)
2. /discover-agents            — build the map + refresh orchestration.md's roster/topology.
3. Author fleet/orchestration.md — the who-calls-whom edges (§4) and permission intent (§5).
   Fleet already on Trinity? You're done — skip to step 5.
4. /compose-system             — (provisioning NEW agents only) derive agent_permissions from §5, dry-run, deploy.
5. /orchestrate <task>         — put the fleet to work (routes by the map + orchestration.md).
6. Keep it honest over time     — /sync-fleet-to-head (agents on latest code), /profile-fleet (narrative matches reality), /fleet-reconcile (fold verified deltas into the docs cheaply).
7. (Project layer) /project-init <name> — bring the first project under management; the steward sweeps it on schedule,
   closes its loops back to you, and hands you the ones only you can close with people outside the fleet.
```

---

## Error handling

| Situation | Action |
|---|---|
| Not in an agent dir (no CLAUDE.md) | Ask for path or refuse |
| A target skill dir already exists | Run the **Check mode** comparison for that skill, then ask per-skill: overwrite / skip / cancel — with the verdict (upgrade / back-port candidate / local customization + diff) in the prompt |
| `--check` invoked | Run **Check mode** only (read-only divergence report); skip all install steps |
| `template.yaml` absent | Skip Step 6 (capabilities block); note the agent isn't self-describing yet |
| `gh` missing and a source is `github:...` | The installed `/discover-agents` falls back to `git clone --depth 1`; warn here |
| `gh` installed but not authenticated | Warn at preflight; `github:` sources degrade to anonymous clone (public repos only) and Q3's registry probe catches the project layer |
| Registry probe fails (Q3 — no push or issues disabled) | Warn, don't hard-stop — the user fixes access before the steward's first sweep |
| Trinity MCP unavailable | Install anyway; discover + compose work locally; orchestrate/deploy print manual guidance |
| `CLAUDE.md` already has `## Orchestration` | Leave the section; still grep-add the `@fleet/orchestration.md` import if it's missing |
| `orchestration.md` `GENERATED:*` markers deleted by a user | `/discover-agents` re-inserts the section from template before refreshing (never guesses) |

## Idempotency

Re-running is safe: existing `fleet/sources.yaml`, `fleet/system-map.yaml`, and `fleet/orchestration.md` are never clobbered (only seeded when absent); the CLAUDE.md section, the `@fleet/orchestration.md` import, and the dashboard panel are each grep-guarded; the §3b ownership-matrix and §3c data-layer inserts are grep-guarded on `### 3b`/`### 3c`, and the standard's §12 loop-closure insert on `## 12. Loop closure`, each applied only on an explicit yes; and skill copies prompt before overwrite, the prompt now carrying the **Check mode** verdict (upgrade / back-port candidate / local customization) so a re-run never silently downgrades a field-hardened copy or discards a local edit. `/add-orchestrator --check` is fully read-only — it writes nothing and is safe to run anytime. `/discover-agents` rewrites only the fenced `GENERATED:*` blocks in `orchestration.md` — your prose is never touched. To refresh, run `/discover-agents`; to re-wire a skill, delete its dir under `.claude/skills/` and re-run.
