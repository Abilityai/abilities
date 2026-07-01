---
name: discover-agents
description: Scan a list of agent repositories (local paths + github:Org/repo) for Trinity specs (template.yaml, system.yaml), cross-reference live Trinity agents repo-first, and assemble a descriptive fleet/system-map.yaml — the system-aware list. Read-only; works on any agent or fleet.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__get_agent_info, mcp__trinity__get_agent_tags, mcp__trinity__list_tags
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-01
  author: orchestrator
  changelog:
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
  # fallback: shallow clone if gh unavailable or produced nothing
  if [ ! -s "$WORK/template.yaml" ] && [ "$FETCH_STATUS" != "auth" ]; then
    git clone --depth 1 ${branch:+--branch "$branch"} "https://github.com/$repo" "$WORK/clone" 2>/dev/null \
      && { cp "$WORK/clone/template.yaml" "$WORK/template.yaml" 2>/dev/null
           cp "$WORK/clone/system.yaml"   "$WORK/system.yaml"   2>/dev/null; }
  fi
}

for repo in "${REPOS[@]}"; do
  WORK="$(mktemp -d)"; FETCH_STATUS="ok"
  case "$repo" in
    github:*) spec="${repo#github:}"; fetch_github "${spec%@*}" "$( [ "$spec" != "${spec#*@}" ] && echo "${spec#*@}" )" ;;
    *) SRC="${repo/#\~/$HOME}"
       cp "$SRC/template.yaml" "$WORK/template.yaml" 2>/dev/null
       cp "$SRC/system.yaml"   "$WORK/system.yaml"   2>/dev/null ;;
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

Never invent `provides`. If neither native keywords nor `x-capabilities` exist, rely on `summary` + `tags`.

### Step 4: Note any `system.yaml` found in a scanned repo

If a scanned repo carries its own `system.yaml` (a sub-system manifest), record its member agent names. Any member **not** itself in `fleet/sources.yaml` goes into the map's top-level `unresolved:` list. Don't recursively fetch this run.

### Step 5: Cross-reference live Trinity — **repo-first**, not name-first

Name-only matching is wrong and dangerous: an agent's deployed name often differs from its `template.yaml` name (e.g. `ruby` → `ruby-internal`), so a name match would mark it undeployed and `/orchestrate` would try to stand up a **duplicate**. Match on the source **repo** instead.

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

### Step 7: Report + recommend the right next step

Summarize; don't dump the file:

```
Scanned N repos → M agents in fleet/system-map.yaml
  deployed:      X   (matched repo-first; callable via deployed_name)
  catalog-only:  Y   (github://… / local:… — rollable on demand)
  by role:       research 3 · comms 1 · ops 2 · …
  unreachable:   <repos needing gh auth, if any>
  name-only:     <low-confidence matches to verify, if any>

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
