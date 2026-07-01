---
name: add-orchestrator
description: Make any agent a system-aware orchestrator — installs /discover-agents (scan a repo list for Trinity specs into a descriptive fleet/system-map.yaml), /compose-system (turn the map into a Trinity SystemManifest and deploy_system), and /orchestrate (route, fan out, and run ephemeral agents via Trinity MCP). Aligns with Trinity's existing SystemManifest; no parallel standard.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-01
  author: Ability.ai
  changelog:
    - "1.1: Self-description moves to x-capabilities: (no longer collides with Trinity's native flat capabilities: keyword list); scanner is zsh-safe and matches Trinity repo-first with an explicit deployed_name; two explicit modes up front — describe an existing fleet (map-only, read-only) vs provision a new system (map→manifest→deploy)"
    - "1.0: Initial version — installs /discover-agents, /compose-system, /orchestrate into a target agent; scans local + github:Org/repo repos for template.yaml/system.yaml into fleet/system-map.yaml; composes a Trinity SystemManifest; defines the optional self-description block"
---

# Add Orchestrator

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-orchestrator vX.Y — recent: <summary>`. Then proceed.

Turn any Trinity-compatible agent into a **system-aware orchestrator**: an agent that knows what other agents exist (deployed *or* just sitting in a GitHub repo), what each can do, and can route work to them, batch across them, or roll one out ephemerally, use it, and spin it back down.

**Two modes — pick by whether the fleet already exists. Don't force a linear pipeline.**

```
Mode A · Describe & route over an EXISTING fleet   (read-only — the common case)
  fleet/sources.yaml ──/discover-agents──▶ fleet/system-map.yaml ──/orchestrate──▶ work
  The map IS the read surface. No manifest, no deploy. Skip /compose-system.

Mode B · Provision a NEW system   (create agents that today are only catalog repos)
  fleet/system-map.yaml ──/compose-system──▶ fleet/system.yaml (Trinity SystemManifest) ──deploy──▶ /orchestrate

Artifacts:
  fleet/sources.yaml     you curate — local paths + github:Org/repo
  fleet/system-map.yaml  descriptive registry, written by /discover-agents   (Mode A stops here)
  fleet/system.yaml      Trinity SystemManifest, written by /compose-system   (Mode B only)
```

**Design invariant (do not violate):** orchestration is **agent-owned**. Trinity supplies the substrate (shared folders, agent-to-agent permissions, MCP messaging, cron) but runs **no central DAG engine**. So the roll-out → work → tear-down lifecycle lives *inside* `/orchestrate` — stitched from existing MCP calls — never as a new platform primitive. The multi-agent *definition* aligns 1:1 with Trinity's `SystemManifest` (the same YAML `deploy_system` consumes); this skill does **not** invent a competing format.

**What gets installed into the target agent:**

| Artifact | Location | Purpose |
|---|---|---|
| `.claude/skills/discover-agents/SKILL.md` | agent repo | scan repos → `fleet/system-map.yaml` |
| `.claude/skills/compose-system/SKILL.md` | agent repo | `system-map.yaml` → Trinity `SystemManifest` → deploy |
| `.claude/skills/orchestrate/SKILL.md` | agent repo | route / fan out / ephemeral, via Trinity MCP |
| `fleet/sources.yaml` | agent repo | the repo list you edit (local paths + `github:Org/repo`) |
| `fleet/system-map.yaml` | agent repo | descriptive registry (written by `/discover-agents`) |
| `fleet/system.yaml` | agent repo | Trinity manifest (written by `/compose-system`) |
| CLAUDE.md `## Orchestration` section | agent repo | wires the three skills + the flow |
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
- `All three` (discover-agents, compose-system, orchestrate) — recommended
- `Discovery only` (discover-agents) — just build the system map; wire deploy/routing later
- `Discovery + compose` (no orchestrate) — build and deploy systems, drive them manually via MCP

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
```

If the user pasted repos in Q2, append them under `repos:` in `fleet/sources.yaml` (one entry per line, preserving the header comments).

### Step 4: Copy the selected runtime skills

For each skill selected in Q1, copy its template. The templates are ready to use as-is — **no placeholder substitution** (they read `fleet/sources.yaml` / `fleet/system-map.yaml` at runtime and infer the agent name themselves):

```bash
for skill in discover-agents compose-system orchestrate; do
  # skip any the user didn't select in Q1
  is_selected "$skill" || continue
  mkdir -p ".claude/skills/$skill"
  cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
done
```

### Step 5: Wire CLAUDE.md

Append an `## Orchestration` section to the target agent's `CLAUDE.md` (only if one isn't already present — grep for `## Orchestration`). Read `templates/claude-section.md`, then write its contents. It documents the three skills, the `fleet/` artifacts, the discover → compose → orchestrate flow, and the agent-owned-orchestration invariant.

Also add a one-line pointer in the agent's Core Capabilities table for each installed skill (`/discover-agents`, `/compose-system`, `/orchestrate`) if such a table exists.

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
- /discover-agents   → scan fleet/sources.yaml into fleet/system-map.yaml
- /compose-system    → fleet/system-map.yaml → fleet/system.yaml (Trinity manifest) → deploy
- /orchestrate       → route / fan out / run ephemeral, via Trinity MCP

### Files
- fleet/sources.yaml      (edit this — your repo list)
- fleet/system-map.yaml   (<generated | empty until first scan>)
- CLAUDE.md               (Orchestration section added)
- dashboard.yaml          (fleet panel added | no dashboard.yaml)

### Trinity MCP: <available | not detected>
<if not: note that discover/compose still work locally; orchestrate + deploy need /trinity:onboard first>

### Next steps
1. Edit fleet/sources.yaml — add the repos (local paths and/or github:Org/repo) you want in the system.
2. /discover-agents            — build the system map.
3. /compose-system             — turn it into a Trinity manifest (dry-run deploy first).
4. /orchestrate <task>         — put the fleet to work.
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
| `CLAUDE.md` already has `## Orchestration` | Leave it; don't append a second section |

## Idempotency

Re-running is safe: existing `fleet/sources.yaml` and `fleet/system-map.yaml` are never clobbered (only seeded when absent), the CLAUDE.md section and dashboard panel are guarded by grep, and skill copies prompt before overwrite. To refresh the map, run `/discover-agents`; to re-wire a skill, delete its dir under `.claude/skills/` and re-run.
