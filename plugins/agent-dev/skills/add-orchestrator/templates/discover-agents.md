---
name: discover-agents
description: Scan a list of agent repositories (local paths + github:Org/repo) for Trinity specs (template.yaml, system.yaml, projects/*/pipeline.yaml), cross-reference live Trinity agents repo-first, and assemble a descriptive fleet/system-map.yaml — the system-aware list. Read-only; works on any agent or fleet.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__get_agent_info, mcp__trinity__get_agent_tags, mcp__trinity__list_tags
user-invocable: true
metadata:
  version: "1.4"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.4: Topology edges now sourced from DECLARED intent (fleet/system.yaml permissions, else orchestration.md §5) and labeled as such — live agent_permissions are not exposed over MCP (get_agent_auth is subscription auth status, not permissions; they live behind REST /api/agents/{name}/permissions and are set by deploy_system at deploy time), so 'live edges' were never obtainable; new Step 6c materializes the dashboard.yaml Fleet table rows (Trinity's real sections[]→widgets[] schema — the UI renders values, it reads no files)"
    - "1.3: Also scan each repo's projects/*/pipeline.yaml (long-running pipelines installed by /add-pipeline) into a pipelines: field per map node — {id, stages} — so pipeline-owning agents are visible to /orchestrate routing and /profile-fleet introspection"
    - "1.2: After writing the map, refresh fleet/orchestration.md's fenced GENERATED:roster (node table) and GENERATED:topology (Mermaid graph whose edges are the live agent_permissions via get_agent_auth) — in place, touching only content between the markers, never prose; re-inserts the section from template if markers were deleted; nodes-only with an unverified note when Trinity is absent"
    - "1.1: Read the rich self-description from x-capabilities: (native flat capabilities: list no longer collides); per-field yq extraction with a type guard so one bad field never aborts a file; bash-forced, array-based, glob-free scan (zsh-safe); gh auth + org-access preflight; repo-first Trinity matching with an explicit deployed_name + live status/owner/autonomy; guarded report swallows auth-scope failures; two-mode next steps"
    - "1.0: Initial version — scans local + github repos for template.yaml/system.yaml, cross-references live Trinity agents, writes fleet/system-map.yaml"
---

# Discover Agents

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `discover-agents vX.Y — recent: <summary>`. Then proceed.

Build the **system-aware list**: read every repository in `fleet/sources.yaml`, find its Trinity specs, cross-reference what's live on Trinity, and assemble a descriptive `fleet/system-map.yaml`. Deployed agents and repo-only ("catalog") agents both land in the map.

This is **read-only** and mode-agnostic — it just describes reality. What you do next depends on your goal:
- **Existing fleet → reference & route:** the map alone is enough. Go straight to `/orchestrate`. **Do not** run `/compose-system`.
- **Provision a new system:** `/compose-system` turns the map into a deployable Trinity manifest.

**Optional argument:** extra repo refs (space-separated, local paths or `github:Org/repo`) to scan **in addition to** `fleet/sources.yaml` for this run.

> **Shell note:** the snippets below use bash features (arrays, `mapfile`). The default shell here may be zsh, so **run them under bash** — either the blocks are executed via bash, or wrap a block as `bash -c '…'`. They avoid unquoted word-splitting and filename globs on purpose.

---

## Process

### Step 1: Load sources + preflight

```bash
[ -f fleet/sources.yaml ] || { echo "No fleet/sources.yaml — run /add-orchestrator first."; exit 1; }
```

Read the repo list into a bash **array** (never `for x in $VAR`):

```bash
if command -v yq >/dev/null 2>&1; then
  mapfile -t REPOS < <(yq -r '.repos[]?' fleet/sources.yaml 2>/dev/null | grep -Ev '^(null|)$')
else
  mapfile -t REPOS < <(grep -E '^\s*-\s+' fleet/sources.yaml | sed -E 's/^\s*-\s*//' | grep -Ev '^(null|)$')
fi
# append any repo refs passed as arguments to this skill
# REPOS+=( "$@" )
[ "${#REPOS[@]}" -gt 0 ] || { echo "No repos in fleet/sources.yaml — add some and re-run."; exit 1; }
```

**GitHub auth preflight** — do this *before* the scan so a token gap is one clear message, not 16 "unreachable" rows:

```bash
if printf '%s\n' "${REPOS[@]}" | grep -q '^github:'; then
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "gh authenticated as: $(gh api user -q .login 2>/dev/null || echo '?')"
    echo "NOTE: private repos resolve only for orgs your token can read. If some come back"
    echo "      'unreachable', run: gh auth login  (and request access to that org)."
  else
    echo "⚠️  gh not authenticated (or not installed). PRIVATE github: repos WILL be unreachable."
    echo "    Fix now: gh auth login   — or expect public repos only."
  fi
fi
```

Determine **this** orchestrator's own name (for `generated_by`): `name:` from local `template.yaml`, else the CLAUDE.md agent name.

### Step 2: Fetch each repo's specs (portable, glob-free)

Work in a per-repo temp dir and clean it with `rm -rf` on the directory — **no `rm *.yaml`** (globs behave differently under zsh/nullglob and error on no-match):

```bash
copy_pipelines() {  # $1=repo root on disk → copies projects/*/pipeline.yaml into $WORK
  local p
  for p in "$1"/projects/*/pipeline.yaml; do
    [ -f "$p" ] && cp "$p" "$WORK/pipeline-$(basename "$(dirname "$p")").yaml"
  done
}

fetch_github() {  # $1=Org/repo  $2=branch(optional)  → sets FETCH_STATUS, writes to $WORK
  local repo="$1" branch="$2" q="" http
  [ -n "$branch" ] && q="?ref=$branch"
  for spec in template.yaml system.yaml; do
    if command -v gh >/dev/null 2>&1; then
      http=$(gh api "repos/$repo/contents/$spec$q" -H "Accept: application/vnd.github.raw" \
               >"$WORK/$spec" 2>"$WORK/.err"; echo $?)
      if [ "$http" -ne 0 ]; then
        rm -f "$WORK/$spec"
        # classify: auth/scope vs genuinely missing
        if grep -qiE '401|403|HTTP 401|HTTP 403|Bad credentials|Must have admin' "$WORK/.err"; then
          FETCH_STATUS="auth"     # token can't read this repo
        fi
      fi
    fi
  done
  # pipelines (optional): projects/*/pipeline.yaml — one listing call, then fetch each
  if command -v gh >/dev/null 2>&1 && [ "$FETCH_STATUS" != "auth" ]; then
    mapfile -t PROJ_DIRS < <(gh api "repos/$repo/contents/projects$q" \
      -q '.[] | select(.type=="dir") | .name' 2>/dev/null)
    for proj in "${PROJ_DIRS[@]}"; do
      gh api "repos/$repo/contents/projects/$proj/pipeline.yaml$q" -H "Accept: application/vnd.github.raw" \
        >"$WORK/pipeline-$proj.yaml" 2>/dev/null || rm -f "$WORK/pipeline-$proj.yaml"
    done
  fi
  # fallback: shallow clone if gh unavailable or produced nothing
  if [ ! -s "$WORK/template.yaml" ] && [ "$FETCH_STATUS" != "auth" ]; then
    git clone --depth 1 ${branch:+--branch "$branch"} "https://github.com/$repo" "$WORK/clone" 2>/dev/null \
      && { cp "$WORK/clone/template.yaml" "$WORK/template.yaml" 2>/dev/null
           cp "$WORK/clone/system.yaml"   "$WORK/system.yaml"   2>/dev/null
           copy_pipelines "$WORK/clone"; }
  fi
}

for repo in "${REPOS[@]}"; do
  WORK="$(mktemp -d)"; FETCH_STATUS="ok"
  case "$repo" in
    github:*) spec="${repo#github:}"; fetch_github "${spec%@*}" "$( [ "$spec" != "${spec#*@}" ] && echo "${spec#*@}" )" ;;
    *) SRC="${repo/#\~/$HOME}"
       cp "$SRC/template.yaml" "$WORK/template.yaml" 2>/dev/null
       cp "$SRC/system.yaml"   "$WORK/system.yaml"   2>/dev/null
       copy_pipelines "$SRC" ;;
  esac
  # → parse $WORK/template.yaml and $WORK/system.yaml (Step 3), remembering FETCH_STATUS
  rm -rf "$WORK"
done
```

Record outcome per repo: specs found, or `notes: "unreachable — token lacks access (gh auth)"` when `FETCH_STATUS=auth`, or `notes: "no template.yaml found"` when simply absent. **Never drop a repo silently** — a repo with no spec is still a (weak) catalog row.

### Step 3: Parse each `template.yaml` — per field, with a type guard

Extract each field in its **own** `yq` call with a default, so one malformed field can't abort the rest of the file:

```bash
f="$WORK/template.yaml"; [ -s "$f" ] || SKIP_PARSE=1
NAME=$(yq -r '.name // ""'            "$f" 2>/dev/null)
DISP=$(yq -r '.display_name // ""'    "$f" 2>/dev/null)
DESC=$(yq -r '.description // ""'     "$f" 2>/dev/null | head -1)
CPU=$( yq -r '.resources.cpu // ""'   "$f" 2>/dev/null)
MEM=$( yq -r '.resources.memory // ""' "$f" 2>/dev/null)

# NATIVE capabilities: — GUARD ON TYPE. Trinity uses a flat list; older/other
# agents might have nothing. Only read it as keywords when it is a sequence.
CAP_TYPE=$(yq -r '.capabilities | type' "$f" 2>/dev/null)   # !!seq | !!map | !!null | (error)
case "$CAP_TYPE" in
  '!!seq') CAP_KEYWORDS=$(yq -r '.capabilities[]' "$f" 2>/dev/null) ;;   # native flat list
  *)       CAP_KEYWORDS="" ;;                                            # absent / map / unknown → ignore
esac

# RICH self-description lives under x-capabilities (hyphenated key needs bracket form)
XROLE=$(yq -r '.["x-capabilities"].role // ""'      "$f" 2>/dev/null)
XSUM=$( yq -r '.["x-capabilities"].summary // ""'   "$f" 2>/dev/null)
XLIFE=$(yq -r '.["x-capabilities"].lifecycle // "persistent"' "$f" 2>/dev/null)
# provides[] and tags[] similarly, each in its own call

# PIPELINES (optional) — one $WORK/pipeline-<slug>.yaml per projects/<slug>/pipeline.yaml
# found in Step 2. These are /add-pipeline long-running DAGs the agent runs internally.
for pf in "$WORK"/pipeline-*.yaml; do
  [ -f "$pf" ] || continue
  P_ID=$(    yq -r '.pipeline_id // ""'    "$pf" 2>/dev/null)
  P_STAGES=$(yq -r '.stages | length // 0' "$pf" 2>/dev/null)
  # → append {id: $P_ID, stages: $P_STAGES} to this entry's pipelines[] (skip if P_ID empty)
done
```

Normalize into a map entry (priority order):

| map field | source |
|---|---|
| `role` | `x-capabilities.role` → inferred from tags/keywords/description → `unknown` |
| `summary` | `x-capabilities.summary` → `description` |
| `capability_keywords` | native flat `capabilities:` list (only if it was `!!seq`) → `[]` |
| `provides` | `x-capabilities.provides[]` → `[]` |
| `tags` | template `tags:` ∪ `x-capabilities.tags` (dedup) |
| `lifecycle` | `x-capabilities.lifecycle` → `persistent` |
| `resources`, `schedules` | from `template.yaml` → omit / `[]` |
| `pipelines` | repo `projects/*/pipeline.yaml` → `{id, stages}` per file → `[]` |

Never invent `provides`. If neither native keywords nor `x-capabilities` exist, rely on `summary` + `tags`.

A non-empty `pipelines:` marks the agent as the owner of that long-running work — `/orchestrate` routes pipeline-shaped tasks (a population of items through stages over many runs) *to* it rather than re-sequencing the stages across agents, and `/profile-fleet` uses the field as its fallback when a Trinity build lacks the pipeline MCP introspection tools. A `pipeline-<id>-heartbeat` entry in `schedules:` is corroborating evidence the pipeline is actually wired.

### Step 4: Note any `system.yaml` found in a scanned repo

If a scanned repo carries its own `system.yaml` (a sub-system manifest), record its member agent names. Any member **not** itself in `fleet/sources.yaml` goes into the map's top-level `unresolved:` list. Don't recursively fetch this run.

### Step 5: Cross-reference live Trinity — **repo-first**, not name-first

Name-only matching is wrong and dangerous: an agent's deployed name often differs from its `template.yaml` name (e.g. `researcher` → `researcher-prod`), so a name match would mark it undeployed and `/orchestrate` would try to stand up a **duplicate**. Match on the source **repo** instead.

If Trinity MCP is available:

1. `mcp__trinity__list_agents` → for each live agent, get its source repo and live signal. Use `mcp__trinity__get_agent_info` / `mcp__trinity__get_agent` if the repo/owner/status aren't in the list payload.
2. Build a **normalized-repo → live-agent** index. Normalize both sides: lowercase, strip `github:` / `https://github.com/` / trailing `.git` / any `@branch`.
3. For each discovered agent, look up its `github_repo`:
   - **match** → `deployed: true`, `match: repo`, and capture the live fields:
     - `deployed_name:` ← the live agent's actual name (**the string `/orchestrate` calls**)
     - `ref: trinity://<instance>/<deployed_name>`
     - `status:` (running/stopped), `owner:`, `autonomy:` (autonomy_enabled) — carry whatever the API exposes; these sharpen routing.
   - **no match** → `deployed: false`, `match: none`, `ref: github://Org/repo` (or `local:<path>`). These are the catalog agents `/orchestrate` can roll out ephemerally.
4. **Fallback only if live repo info is unavailable:** try a name match, but set `match: name` and `notes: "name-only match — verify deployed_name"` so the low confidence is visible. Never silently treat a name match as authoritative.

If Trinity MCP is **absent**: every agent `deployed: false`, `match: none`, `deployed_name: null`; add a top-level note that deployment status is unverified. Discovery still fully succeeds.

### Step 6: Write `fleet/system-map.yaml`

Rewrite the file (keep the comment header). Set `generated` (`date -u +%Y-%m-%dT%H:%M:%SZ`), `generated_by`, `system_name` (from `sources.yaml`, else `<agent>-fleet`), the `agents:` map (key = template `name`), and `unresolved:`.

### Step 6b: Refresh the machine blocks in `fleet/orchestration.md`

`orchestration.md` is the narrative layer. It's hybrid-owned: prose is the human's, but two fenced blocks are tool-written. Refresh **only** those blocks; never touch prose.

First ensure the file exists — if a user deleted it, recreate it from the installer template (substituting `{{SYSTEM_NAME}}`/`{{DATE}}`) before refreshing:

```bash
[ -f fleet/orchestration.md ] || echo "orchestration.md missing — recreate from templates/orchestration.md.template first."
```

Rewrite strictly between the HTML-comment markers (replace text between `<!-- BEGIN GENERATED:X … -->` and `<!-- END GENERATED:X -->`). If a marker pair is missing (user deleted it), re-insert the whole section from the template rather than guessing.

- **`GENERATED:roster`** → a compact node table from the map, one row per agent:
  `| agent | role | does (summary) | ref |` — use `deployed_name` in `ref` when deployed.
- **`GENERATED:topology`** → a Mermaid `graph LR`:
  - **nodes** = the discovered agents (label with role).
  - **edges** = the **declared** permission topology: read `fleet/system.yaml`'s `permissions` (preset or explicit map) if `/compose-system` has produced one; else translate `orchestration.md` §5's allow statements. Render `caller --> callee` per declared edge and stamp the block with `%% edges = declared intent (system.yaml / §5) — not live-verified`.
  - **Live `agent_permissions` are not readable over MCP** — no tool exposes them (`get_agent_auth` is subscription auth status, not permissions). They live behind REST `GET /api/agents/{name}/permissions` and are set by `deploy_system` at deploy time. Never present these edges as live-verified; drift since the last deploy is invisible from here.
  - No manifest and an empty §5 → render **nodes only** with `%% edges unknown — no system.yaml and §5 not yet authored`.

Example of a refreshed topology block (shape only — note the outer fence is 4 backticks so the inner mermaid fence nests cleanly):

````
<!-- BEGIN GENERATED:topology (written by /discover-agents from system-map + declared permissions) -->
```mermaid
graph LR
  %% edges = declared intent (system.yaml / §5) — not live-verified
  orchestrator[orchestrator · orchestration]
  researcher[researcher · research]
  orchestrator --> researcher
```
<!-- END GENERATED:topology -->
````

Leave §4 (edges + why), §5 (permissions intent), §6 (patterns), and every other prose section untouched — those are the human's to author.

### Step 6c: Materialize the dashboard Fleet table (if present)

If `dashboard.yaml` contains the section marked `managed by /add-orchestrator`, rewrite that table widget's `rows:` from the fresh map — one row per agent:

```yaml
rows:
  - { agent: <map key>, role: <role>, deployed: <yes|no>, ref: <ref>, pipelines: <ids comma-joined or —> }
```

Trinity renders `dashboard.yaml` values as-is — it never reads other files — so this write is what keeps the UI current. Touch only the managed section's `rows:`; skip silently if the file or the section is absent.

### Step 7: Report + recommend the right next step

Summarize; don't dump the file:

```
Scanned N repos → M agents in fleet/system-map.yaml
  deployed:      X   (matched repo-first; callable via deployed_name)
  catalog-only:  Y   (github://… / local:… — rollable on demand)
  by role:       research 3 · comms 1 · ops 2 · …
  pipelines:     <agents owning long-running pipelines, with ids — omit line if none>
  unreachable:   <repos needing gh auth, if any>
  name-only:     <low-confidence matches to verify, if any>
  orchestration.md: refreshed (roster N, declared-intent edges M)
  dashboard:        Fleet rows refreshed | no dashboard.yaml / no managed section

Next:
  • Fleet already on Trinity → /orchestrate <task>   (the map is enough; skip /compose-system)
  • Standing up NEW agents from catalog repos → /compose-system
```

Publish a Trinity report **only if it succeeds** — guard against both tool-absence *and* auth-scope errors (the report tool needs an agent-scoped key; an admin/user MCP key will fail):

```
try: mcp__trinity__report(report_type: "<agent>.fleet_scan", display_hint: "table", payload: <rows>)
     — if it raises tool-not-found OR an auth/permission/scope error, swallow it and continue.
```

---

## Error handling

| Situation | Action |
|---|---|
| No `fleet/sources.yaml` | Tell user to run `/add-orchestrator`; stop |
| `sources.yaml` empty | Ask for repos or stop; don't overwrite a good map with an empty one |
| `gh` unauthenticated + `github:` sources present | Preflight warns once (Step 1); unreachable repos get `notes:`, others still scan |
| Private repo, token lacks org access | `FETCH_STATUS=auth` → `notes: "unreachable — token lacks access"`; continue |
| `template.yaml` unparseable / one bad field | Per-field extraction keeps the good fields; `notes: "partial parse"` |
| Native `capabilities:` is a list (not a map) | Expected — read as `capability_keywords`; never index it with `.role` |
| Deployed name ≠ template name | Repo-first match resolves it into `deployed_name`; that's what `/orchestrate` uses |
| Trinity MCP absent | All `deployed:false`; unverified-status note; succeed locally |
| Report tool present but key out of scope | Swallow the auth error; the map write already succeeded |
