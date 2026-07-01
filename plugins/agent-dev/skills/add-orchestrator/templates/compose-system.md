---
name: compose-system
description: Turn fleet/system-map.yaml into a Trinity SystemManifest (fleet/system.yaml) — pick members, choose a permissions topology, validate with a dry-run deploy, and deploy_system on approval. Emits Trinity's native manifest format; no parallel schema.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__deploy_system, mcp__trinity__list_systems, mcp__trinity__get_system_manifest, mcp__trinity__restart_system, mcp__trinity__list_templates
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.0: Initial version — composes a Trinity SystemManifest from the system map, validates via dry_run, deploys on explicit approval, and always writes fleet/system.yaml for version control"
---

# Compose System

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `compose-system vX.Y — recent: <summary>`. Then proceed.

Take the descriptive `fleet/system-map.yaml` and produce a **prescriptive Trinity `SystemManifest`** at `fleet/system.yaml` — the exact YAML `deploy_system` consumes. Validate it with a dry-run, write it to the repo, and (only with explicit approval) deploy the whole multi-agent system in one shot.

**This emits Trinity's native format.** The `agents` map, `template` refs, `folders`, `schedules`, `tags`, and `permissions` preset all match Trinity's `SystemManifest`. We do not invent fields.

---

## Process

### Step 1: Load the map

```bash
[ -f fleet/system-map.yaml ] || { echo "No fleet/system-map.yaml — run /discover-agents first."; exit 1; }
```

Read it. If `agents:` is empty, tell the user to run `/discover-agents` and stop.

### Step 2: Choose members and topology

Use `AskUserQuestion`:

**Q1 — Which agents are members of this system?**
- `All discovered` (recommended) — every agent in the map
- `Deployed only` — skip catalog-only entries
- `Let me pick` — present the list, multi-select

**Q2 — Permissions topology** (Trinity presets):
- `orchestrator-workers` (recommended) — **this** agent is the orchestrator; every other member is a worker it may call. Restrictive and matches this skill's intent.
- `full-mesh` — every agent may call every other. Use for peer collaboration.
- `none` — no agent-to-agent calls; isolated members.
- `custom` — an explicit map, e.g. `{this-agent: [worker-a, worker-b]}`.

**Q3 — System-wide prompt?** (optional, free text) — one instruction injected into every member agent (Trinity's `prompt` field). Leave empty for none.

**Q4 — Shared folders?** (optional) — if members pass files, mark which `expose` (publisher) and which `consume`. Default: none (all `expose:false, consume:false`).

### Step 3: Resolve `template` refs

Each member needs a Trinity `template` ref. Resolve from the map's `source`/`ref`:

| Map entry | `template:` in manifest |
|---|---|
| `source: github:Org/repo` | `github:Org/repo` |
| `deployed: true` but local source | needs a registered Trinity template — check `mcp__trinity__list_templates`; if present use `local:<template-name>`, else flag |
| local source, not deployed, no template | **cannot deploy via manifest** — flag it: onboard it first (`/trinity:onboard` in that repo) or deploy via `deploy_local_agent`; still list it in `fleet/system.yaml` with a `# NEEDS-TEMPLATE` comment |

Don't drop un-deployable members silently — include them commented/flagged so the manifest is a complete picture, and list them in the Step 6 report.

### Step 4: Build the manifest

Assemble `fleet/system.yaml` in Trinity `SystemManifest` shape:

```yaml
name: <system_name from map, or "<agent>-fleet">
description: "<one line describing this system>"
prompt: "<from Q3, or omit>"

agents:
  prospector:
    template: github:Abilityai/prospector
    resources: {cpu: "2", memory: "4g"}     # from map; omit to use template defaults
    folders: {expose: false, consume: false}
    schedules:                               # carried over from the map (enabled as declared)
      - {name: weekly-account-refresh, cron: "0 8 * * 1", skill: refresh-accounts, enabled: false}
    tags: [sales, research]
  # … one entry per member …

permissions:
  preset: orchestrator-workers               # this agent orchestrates; others are workers
  # or, for custom:  map: {<this-agent>: [worker-a, worker-b]}

default_tags: [<system_name>]                # optional
# system_view:                               # optional pre-built dashboard view
#   name: <system_name>
```

Notes:
- Carry `resources`, `schedules`, `tags` straight from the map. Keep schedule `enabled` flags as declared (Trinity's declarative-schedules rule — the operator toggles them live).
- For `orchestrator-workers`, the orchestrator identity is **this** agent (its Trinity name). State that explicitly in the manifest comment.

### Step 5: Validate (dry-run) and write

Always write `fleet/system.yaml` to the repo first (so it's version-controlled even if we don't deploy).

If Trinity MCP is available, validate before deploying:

```
mcp__trinity__deploy_system with the manifest YAML and dry_run: true
```

Surface every warning it returns (unknown template, name collision, permission gaps). If MCP is unavailable, say so — the manifest is still written and valid to deploy later.

### Step 6: Deploy (explicit approval only)

Deploying creates/starts real agents and is outward-facing and not trivially reversible. **Show the dry-run result and the member list, then ask for explicit confirmation.** Only on a clear yes:

```
mcp__trinity__deploy_system with the manifest YAML (dry_run: false)
```

If a system with this `name` already exists (`mcp__trinity__list_systems`), tell the user and offer: `restart_system` to apply changes, deploy under a new name, or cancel. Do not blindly redeploy over a running system.

### Step 7: Report

```
Composed fleet/system.yaml — <N> members, permissions: <preset>
  deployable now:   <list>
  needs template:   <flagged members, if any>
Dry-run: <clean | warnings: …>
Deployed: <yes → system '<name>' | no — manifest written only>

Next: /orchestrate <task>  to put the system to work.
```

Publish a guarded Trinity report (`report_type: <agent>.system_composed`, `display_hint: markdown`) when the tool is available.

---

## Error handling

| Situation | Action |
|---|---|
| No/empty `fleet/system-map.yaml` | Send user to `/discover-agents`; stop |
| Member has no resolvable `template` | Include flagged with `# NEEDS-TEMPLATE`; explain onboarding path; don't block the others |
| `dry_run` returns warnings | Print them all; ask before real deploy |
| System name already exists | Offer restart / new-name / cancel — never silent overwrite |
| Trinity MCP absent | Write `fleet/system.yaml` anyway; skip validate/deploy; note how to deploy after `/trinity:connect` |
