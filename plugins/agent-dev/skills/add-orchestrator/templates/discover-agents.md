---
name: discover-agents
description: Scan a list of agent repositories (local paths + github:Org/repo) for Trinity specs (template.yaml, system.yaml), cross-reference live Trinity agents, and assemble a descriptive fleet/system-map.yaml — the system-aware list.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__get_agent_tags, mcp__trinity__list_tags
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.0: Initial version — scans local + github repos for template.yaml/system.yaml, reads the optional capabilities: block, cross-references live Trinity agents, writes fleet/system-map.yaml"
---

# Discover Agents

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `discover-agents vX.Y — recent: <summary>`. Then proceed.

Build the **system-aware list**: read every repository in `fleet/sources.yaml`, find its Trinity specs, and assemble a descriptive `fleet/system-map.yaml`. Deployed agents and repo-only ("catalog") agents both land in the map. This is *description*, not deployment — `/compose-system` turns the map into a deployable Trinity manifest.

**Optional argument:** additional repo refs (space-separated, local paths or `github:Org/repo`) to scan **in addition to** `fleet/sources.yaml` for this run — handy for a one-off look without editing the sources file.

---

## Process

### Step 1: Load the source list

```bash
[ -f fleet/sources.yaml ] || { echo "No fleet/sources.yaml — run /add-orchestrator first."; exit 1; }
```

Read `fleet/sources.yaml`. Collect every non-comment, non-null entry under `repos:` into a list. Append any repo refs passed as arguments to this skill. Read `system_name:` (may be null). De-duplicate. If the list is empty, tell the user to add repos to `fleet/sources.yaml` and stop.

Determine **this** orchestrator's own name (for `generated_by`): read `name:` from local `template.yaml`, else the agent name in `CLAUDE.md`.

### Step 2: Locate and read each repo's Trinity specs

For each source, fetch `template.yaml` and (if present) `system.yaml`. Never do a full clone when a file fetch suffices.

**Local path** (starts with `/`, `.`, or `~`):

```bash
SRC="<path>"                    # expand ~ via $HOME
for spec in template.yaml system.yaml; do
  [ -f "$SRC/$spec" ] && echo "FOUND $SRC/$spec" || echo "MISSING $SRC/$spec"
done
```

**GitHub ref** (`github:Org/repo` or `github:Org/repo@branch`):

```bash
REF_SPEC="<Org/repo>"; BRANCH="<branch or empty>"
Q=""; [ -n "$BRANCH" ] && Q="?ref=$BRANCH"

if command -v gh >/dev/null 2>&1; then
  # Fetch raw file contents without cloning. Missing file → non-zero / 404.
  gh api "repos/$REF_SPEC/contents/template.yaml$Q" \
     -H "Accept: application/vnd.github.raw" 2>/dev/null > /tmp/tmpl.yaml \
     && echo "FOUND template.yaml" || echo "MISSING template.yaml"
  gh api "repos/$REF_SPEC/contents/system.yaml$Q" \
     -H "Accept: application/vnd.github.raw" 2>/dev/null > /tmp/sys.yaml \
     && echo "FOUND system.yaml" || echo "MISSING system.yaml"
else
  # Fallback: shallow clone into a temp dir, read, discard.
  TMP=$(mktemp -d)
  git clone --depth 1 ${BRANCH:+--branch "$BRANCH"} "https://github.com/$REF_SPEC" "$TMP" 2>/dev/null \
    && { cp "$TMP"/template.yaml /tmp/tmpl.yaml 2>/dev/null; cp "$TMP"/system.yaml /tmp/sys.yaml 2>/dev/null; } \
    || echo "UNREACHABLE $REF_SPEC (private or nonexistent — check gh auth)"
  rm -rf "$TMP"
fi
```

If a repo yields **neither** spec, still record it in the map with `spec_found: []` and a `notes:` explaining it (so the gap is visible, not silently dropped). A repo with only a `README` is a weak catalog entry, not an error.

### Step 3: Parse each `template.yaml`

Prefer `yq` for robustness; fall back to careful reading. Extract:

- `name`, `display_name`, `description`
- `resources` (`cpu`, `memory`)
- top-level `tags` (if any) and `schedules` (list of `{name/id, cron, skill/message, enabled}`)
- the optional **`capabilities:`** block: `role`, `summary`, `provides[]`, `lifecycle`, `tags`

Normalize into a map entry:

| map field | source (in priority order) |
|---|---|
| `role` | `capabilities.role` → inferred from tags/description → `unknown` |
| `summary` | `capabilities.summary` → `description` (first line) |
| `capabilities` | `capabilities.provides[]` → `[]` |
| `tags` | union of `template.tags` and `capabilities.tags` (dedup) |
| `resources` | `template.resources` → omit |
| `lifecycle` | `capabilities.lifecycle` → `persistent` |
| `schedules` | `template.schedules[]` → `[]` |

Do **not** invent capabilities. If none are declared, leave `capabilities: []` and rely on `summary` + `tags`.

### Step 4: Note any `system.yaml` found in a scanned repo

If a scanned repo contains its own `system.yaml` (a Trinity `SystemManifest`), it describes a sub-system. Record its member agent names. Any member **not** itself present in `fleet/sources.yaml` goes into the map's top-level `unresolved:` list (name + which repo referenced it), so the user can decide whether to add it as a source. Do not recursively fetch it this run.

### Step 5: Cross-reference live Trinity (if MCP is available)

Detect Trinity MCP (`.mcp.json` present, or a `mcp__trinity__*` tool is callable). If available:

- Call `mcp__trinity__list_agents` once. Build a name→agent index.
- For each discovered agent, if its `name` matches a live agent:
  - `deployed: true`, `ref: trinity://<instance>/<name>` (use the connected instance's label; `trinity://default/<name>` if unknown)
  - Optionally enrich `tags` with live tags via `mcp__trinity__get_agent_tags`.
- Otherwise:
  - `deployed: false`, and `ref:` = `github://Org/repo` for a GitHub source, or `local:<path>` for a local one. These are the **catalog** agents `/orchestrate` can roll out ephemerally.

If MCP is **not** available: set every agent `deployed: false` and use the `github://` / `local:` ref. Add a top-level note that deployment status is unverified. Discovery still fully succeeds — it's a local operation.

### Step 6: Write `fleet/system-map.yaml`

Rewrite the file (preserve the leading comment header from the template). Set:

- `generated:` — current UTC timestamp: `date -u +%Y-%m-%dT%H:%M:%SZ`
- `generated_by:` — this orchestrator's name
- `system_name:` — from `sources.yaml`, else `<agent>-fleet`
- `agents:` — one keyed entry per discovered agent (key = agent `name`)
- `unresolved:` — from Step 4

Example of a written entry (shape only):

```yaml
agents:
  prospector:
    source: github:Abilityai/prospector
    ref: trinity://prod/prospector
    deployed: true
    role: research
    summary: "B2B SaaS sales research agent"
    capabilities:
      - skill: /research-company
        does: "deep-dive company research"
      - skill: /score-fit
        does: "score a company against the ICP"
    tags: [sales, research, capability:research-company]
    resources: {cpu: "2", memory: "4g"}
    lifecycle: persistent
    schedules:
      - {name: weekly-account-refresh, cron: "0 8 * * 1", skill: /refresh-accounts, enabled: false}
    spec_found: [template.yaml]
    notes: null
```

### Step 7: Report

Print a concise summary — do not dump the whole file:

```
Scanned N repos → M agents in fleet/system-map.yaml
  deployed:      X   (trinity://…)
  catalog-only:  Y   (github://… / local:… — rollable on demand)
  by role:       research 3 · comms 1 · ops 2 · …
  no spec found: <repos, if any>
  unresolved refs: <names from scanned system.yaml not in sources, if any>

Next: /compose-system to build a deployable Trinity manifest, or /orchestrate <task>.
```

Also publish a report to Trinity when available (guarded — skip silently if the tool isn't present):
- `mcp__trinity__report` with `report_type: <agent>.fleet_scan`, `display_hint: table`, payload = the per-agent rows just written.

---

## Error handling

| Situation | Action |
|---|---|
| No `fleet/sources.yaml` | Tell user to run `/add-orchestrator`; stop |
| `sources.yaml` empty (only comments) | Ask for repos or stop; don't write an empty map over a good one |
| GitHub repo private + `gh` unauthenticated | Record `notes: "unreachable — check gh auth"`; continue with other repos |
| `template.yaml` unparseable | Record the agent with `notes: "template.yaml parse error"`; keep what you can |
| Trinity MCP absent | All agents `deployed:false`; add unverified-status note; succeed locally |
| Same agent `name` from two sources | Keep the first, add `notes:` on the collision; don't silently merge |
