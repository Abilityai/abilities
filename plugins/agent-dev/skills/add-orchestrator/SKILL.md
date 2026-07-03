---
name: add-orchestrator
description: Make any agent a system-aware orchestrator — installs /discover-agents (scan a repo list for Trinity specs into a descriptive fleet/system-map.yaml), /compose-system (turn the map into a Trinity SystemManifest and deploy_system), and /orchestrate (route, fan out, and run ephemeral agents via Trinity MCP). Aligns with Trinity's existing SystemManifest; no parallel standard.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.6"
  created: 2026-07-01
  author: Ability.ai
  changelog:
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

**Two modes — pick by whether the fleet already exists. Don't force a linear pipeline.**

```
Mode A · Describe & route over an EXISTING fleet   (read-only — the common case)
  fleet/sources.yaml ──/discover-agents──▶ system-map.yaml (+ orchestration.md) ──/orchestrate──▶ work
  The map (facts) + orchestration.md (intent) ARE the read surface. No manifest, no deploy. Skip /compose-system.

Mode B · Provision a NEW system   (create agents that today are only catalog repos)
  author orchestration.md §5 ──/compose-system──▶ fleet/system.yaml (SystemManifest) ──deploy──▶ /orchestrate

Artifacts (four layers):
  fleet/sources.yaml       you curate — local paths + github:Org/repo
  fleet/system-map.yaml    FACTS (nodes) — descriptive, written by /discover-agents      (Mode A stops here)
  fleet/orchestration.md   NARRATIVE (edges + intent) — human prose + tool-refreshed blocks; imported into CLAUDE.md
  fleet/system.yaml        Trinity SystemManifest — prescriptive, written by /compose-system   (Mode B only)

Maintenance (keep the fleet + its narrative honest over time):
  /sync-fleet-to-head   non-destructively bring in-scope agents to their GitHub HEAD
  /profile-fleet        interview + introspect agents, reconcile reality, correct orchestration.md
  /fleet-reconcile      fold already-verified deltas into every doc surface — no new evidence, one gate
```

**Design invariant (do not violate):** orchestration is **agent-owned**. Trinity supplies the substrate (shared folders, agent-to-agent permissions, MCP messaging, cron) but runs **no central DAG engine**. So the roll-out → work → tear-down lifecycle lives *inside* `/orchestrate` — stitched from existing MCP calls — never as a new platform primitive. The multi-agent *definition* aligns 1:1 with Trinity's `SystemManifest` (the same YAML `deploy_system` consumes); this skill does **not** invent a competing format.

**Sibling layer — `/add-pipeline`:** this skill is the *inter*-agent layer (route / fan out / lifecycle across a fleet); `/add-pipeline` is the *intra*-agent one (a population of items crawling through a staged DAG inside a single agent, advanced by that agent's own heartbeat). They compose, same invariant on both sides: `/discover-agents` surfaces each fleet agent's pipelines (`pipelines:` per map node, scanned from `projects/*/pipeline.yaml`), and `/orchestrate` routes pipeline-shaped work *to* the owning agent rather than re-sequencing its stages as a cross-agent chain. Conversely, when one pipeline's instances are really isolated tenants, the answer is one agent per tenant via this orchestrator — add-pipeline's "multi-instance, not multi-tenant" boundary points here.

**What gets installed into the target agent:**

| Artifact | Location | Purpose |
|---|---|---|
| `.claude/skills/discover-agents/SKILL.md` | agent repo | scan repos → `fleet/system-map.yaml` |
| `.claude/skills/compose-system/SKILL.md` | agent repo | `system-map.yaml` → Trinity `SystemManifest` → deploy |
| `.claude/skills/orchestrate/SKILL.md` | agent repo | route / fan out / ephemeral, via Trinity MCP |
| `.claude/skills/sync-fleet-to-head/SKILL.md` | agent repo | non-destructively bring in-scope agents to their GitHub HEAD (fleet git hygiene) |
| `.claude/skills/profile-fleet/SKILL.md` | agent repo | interview + introspect agents; reconcile reality and correct the `orchestration.md` narrative |
| `.claude/skills/fleet-reconcile/SKILL.md` | agent repo | fold already-verified deltas into the doc surfaces (narrative, dossiers, CLAUDE.md, memory) behind one gate — no new evidence |
| `fleet/sources.yaml` | agent repo | the repo list you edit (local paths + `github:Org/repo`) |
| `fleet/system-map.yaml` | agent repo | descriptive FACTS/nodes registry (written by `/discover-agents`) |
| `fleet/orchestration.md` | agent repo | design NARRATIVE — edges, permission intent, patterns; imported into CLAUDE.md, loads at session start (human prose + tool-refreshed blocks) |
| `fleet/system.yaml` | agent repo | Trinity manifest (written by `/compose-system`) |
| CLAUDE.md `## Orchestration` section + `@fleet/orchestration.md` import | agent repo | wires the skills + loads the narrative at session start |
| dashboard.yaml `fleet` panel | agent repo (if present) | shows discovered agents at a glance |

---

## Process

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
```

If `CLAUDE.md` is missing, ask the user to point to the right directory or run `/create-agent` first.

Trinity MCP is **not** required to install — `/discover-agents` and `/compose-system` produce their files locally, and `/orchestrate` degrades to explaining what it *would* do when MCP is absent. Note whether `.mcp.json` (or `~/.trinity/config`) is present so the summary can tell the user which live features are available now.

### Step 2: Confirm scope

Use `AskUserQuestion`:

**Q1 — Which skills to install?**
- `All six` (discover-agents, compose-system, orchestrate, sync-fleet-to-head, profile-fleet, fleet-reconcile) — recommended
- `Core three` (discover-agents, compose-system, orchestrate) — the discover → compose → route trio, without the fleet-maintenance skills
- `Discovery only` (discover-agents) — just build the system map; wire the rest later

If any target skill directory already exists under `.claude/skills/`, ask per-skill: overwrite / skip / cancel. Never silently overwrite.

**Q2 — Seed `fleet/sources.yaml` with the current repo list?** (free text, optional)
- Offer to paste an initial list of repositories now (local paths and/or `github:Org/repo`), or start with the commented example and edit later.

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

If the user pasted repos in Q2, append them under `repos:` in `fleet/sources.yaml` (one entry per line, preserving the header comments).

### Step 4: Copy the selected runtime skills

For each skill selected in Q1, copy its template. The templates are ready to use as-is — **no placeholder substitution** (they read `fleet/sources.yaml` / `fleet/system-map.yaml` at runtime and infer the agent name themselves):

```bash
for skill in discover-agents compose-system orchestrate sync-fleet-to-head profile-fleet fleet-reconcile; do
  # skip any the user didn't select in Q1
  is_selected "$skill" || continue
  mkdir -p ".claude/skills/$skill"
  cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
done
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

```bash
if [ -f dashboard.yaml ]; then
  if ! grep -q "fleet_map" dashboard.yaml; then
    cat >> dashboard.yaml <<'EOF'

# Added by /add-orchestrator — managed block, do not edit by hand
fleet_map:
  panel_type: table
  source: fleet/system-map.yaml
  columns: [agent, ref, role, deployed, lifecycle, schedules]
  sort_by: [role, agent]
EOF
  fi
else
  echo "ℹ️  No dashboard.yaml — skipping fleet panel. The orchestrator still works; it just won't render on Trinity until a dashboard.yaml exists."
fi
```

### Step 8: First scan (advisory)

If `fleet/sources.yaml` has at least one real (non-comment) entry and `/discover-agents` was installed, invoke it once to produce an initial `fleet/system-map.yaml` — call the skill by name, don't reimplement it:

```
Invoke `/discover-agents`
```

If `sources.yaml` is still just the example, skip this and tell the user to add repos then run `/discover-agents`.

### Step 9: Summary

Print:

```
## Orchestrator installed into <agent name>

### Skills added
- /discover-agents    → scan fleet/sources.yaml into fleet/system-map.yaml
- /compose-system     → fleet/system-map.yaml → fleet/system.yaml (Trinity manifest) → deploy
- /orchestrate        → route / fan out / run ephemeral, via Trinity MCP
- /sync-fleet-to-head → non-destructively bring in-scope agents to their GitHub HEAD
- /profile-fleet      → interview + introspect agents, correct the orchestration.md narrative
- /fleet-reconcile    → fold already-verified deltas into the doc surfaces — no new evidence

### Files
- fleet/sources.yaml       (edit this — your repo list)
- fleet/system-map.yaml    (FACTS/nodes — <generated | empty until first scan>)
- fleet/orchestration.md   (NARRATIVE/intent — author §4–§7; imported into CLAUDE.md)
- CLAUDE.md                (Orchestration section + @fleet/orchestration.md import added)
- dashboard.yaml           (fleet panel added | no dashboard.yaml)

### Trinity MCP: <available | not detected>
<if not: note that discover/compose still work locally; orchestrate + deploy need /trinity:onboard first>

### Next steps
1. Edit fleet/sources.yaml — add the repos (local paths and/or github:Org/repo) in the system.
2. /discover-agents            — build the map + refresh orchestration.md's roster/topology.
3. Author fleet/orchestration.md — the who-calls-whom edges (§4) and permission intent (§5).
   Fleet already on Trinity? You're done — skip to step 5.
4. /compose-system             — (provisioning NEW agents only) derive agent_permissions from §5, dry-run, deploy.
5. /orchestrate <task>         — put the fleet to work (routes by the map + orchestration.md).
6. Keep it honest over time     — /sync-fleet-to-head (agents on latest code), /profile-fleet (narrative matches reality), /fleet-reconcile (fold verified deltas into the docs cheaply).
```

---

## Error handling

| Situation | Action |
|---|---|
| Not in an agent dir (no CLAUDE.md) | Ask for path or refuse |
| A target skill dir already exists | Ask per-skill: overwrite / skip / cancel |
| `template.yaml` absent | Skip Step 6 (capabilities block); note the agent isn't self-describing yet |
| `gh` missing and a source is `github:...` | The installed `/discover-agents` falls back to `git clone --depth 1`; warn here |
| Trinity MCP unavailable | Install anyway; discover + compose work locally; orchestrate/deploy print manual guidance |
| `CLAUDE.md` already has `## Orchestration` | Leave the section; still grep-add the `@fleet/orchestration.md` import if it's missing |
| `orchestration.md` `GENERATED:*` markers deleted by a user | `/discover-agents` re-inserts the section from template before refreshing (never guesses) |

## Idempotency

Re-running is safe: existing `fleet/sources.yaml`, `fleet/system-map.yaml`, and `fleet/orchestration.md` are never clobbered (only seeded when absent); the CLAUDE.md section, the `@fleet/orchestration.md` import, and the dashboard panel are each grep-guarded; and skill copies prompt before overwrite. `/discover-agents` rewrites only the fenced `GENERATED:*` blocks in `orchestration.md` — your prose is never touched. To refresh, run `/discover-agents`; to re-wire a skill, delete its dir under `.claude/skills/` and re-run.
