---
name: project-init
description: Create or adopt a long-term managed project per the project standard (PROJECT_STANDARD.md at the repo root, or fleet/project-standard.md on an orchestrator — its §0 block configures registry, label vocabulary and fleet hooks) — GitHub epic issue with idempotent label creation and a workspace carrying the project.md charter, at agent level (project_files/<slug>/) or, with --canon, as a shared project in the fleet's canon repo (projects/<slug>/ at the canon root — same charter, same epic, same steward; canon placement only decides who can read it). Use when starting a new multi-session project or bringing an existing project folder under management.
argument-hint: "[project name | adopt <existing-folder> | platform <slug>] [--canon] [--internal] [--no-platform] [--dry-run]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__create_project, mcp__trinity__import_project
user-invocable: true
metadata:
  version: "1.5.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.5.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.5: Platform mode (ent#788, ruling R38): on a Trinity instance with Projects enabled a new project is also created as a platform project (create_project — linked to the epic, or platform-tracked with --internal), and `platform <slug>` brings an existing folder project onto the platform in one import without rewriting it; the charter records platform_project. A refusal (no start-projects permission, no Projects) finishes in folder + GitHub mode and says what a person can do. Without Trinity nothing changes"
    - "1.4: One lineage (ent#789): the standard is resolved at the repo root OR at fleet/project-standard.md (an orchestrator's placement) and its new §0 Configuration block drives everything that used to be hard-coded — label vocabulary by role ($L_ACTIVE, $L_NEEDS_OPERATOR, $L_PRIORITY, …; a tracker-native hyphen vocabulary is now a config value), the owner-label prefix (owner: or agent:), extra epic labels (type-epic), state directory and fleet hooks. Label creation iterates the configured names. With fleet.orchestration set, its §3b ownership matrix supplies the default owner (informational). A missing standard materializes at fleet/project-standard.md when a fleet/ layer exists, else at the root. Absorbs the add-orchestrator template project-init 1.2 — that copy is retired"
    - "1.3: Internal tracking (ent#673, operator ruling 2026-09-22): `--internal` creates a project whose registry is its own workspace — project.md carries the epic's sections (Goal, Success criteria, Owners, Cadence, Current status, Tasks) and `tracking: internal` + `priority:` in the envelope, plus an empty tasks/ and an append-only log.md; no GitHub access, no labels, no epic. Forced when the standard's registry is `none`. Works at both placements (`--canon --internal` = a shared project with its tasks in the canon). External stays the default and writes `tracking: external` explicitly"
    - "1.2: Shared projects (operator rulings R21, 2026-09-10 — one PM standard, two visibility levels — and 2026-09-22 — shared projects at the canon root; ent#588): `--canon` creates the workspace in the fleet's canon repo at projects/<slug>/ — the top-level zone every agent writes directly, not inside any agent's folder — through the x-canon clone, pushed with /canon-publish, instead of project_files/<slug>/, and records `canon:projects/<slug>/` in the epic's Workspace field; this agent becomes the charter's owner: (the steward). A slug already taken in canon — by any steward — is a collision. `adopt --canon <slug>` adopts an existing canon project: one at the root keeps its steward unless it is this agent's (a project stewarded by another agent is refused — ask that agent); one still at the earlier agents/<self>/projects/<slug>/ placement is moved to projects/<slug>/ in the same publish (another agent's earlier-placement project is theirs to move). The charter is the same file at both levels and now carries the linted envelope the canon convention § Projects defines (owner = steward, status mirrors the epic label, epic as owner/repo#N, updated, review_by, tldr) plus an append-only decisions.md ledger with its own envelope; agent-level project.md gains the same envelope so moving a project changes readers and nothing else. `--dry-run` writes the workspace and prints the epic body without touching GitHub (so a scaffold can be linted before it exists). Default placement is unchanged (agent level)"
    - "1.1: Self-heal — when PROJECT_STANDARD.md is missing, materialize it from PROJECT_STANDARD.template.md shipped in this skill directory (resolving registry/operator/agent/max-age with sensible defaults). Makes the skill usable when assigned from the skills library without running the installer; the installer now copies from this directory instead of carrying its own copy"
    - "1.0: Initial version — owner/agent label distinction, unclassified quarantine, full Epic anatomy per PROJECT_STANDARD.md §4"
---

# Project Init

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-init v1.5.1 — recent: arguments no longer break the config resolver`. Then proceed.

## Purpose

Bring a long-term project under standardized management: create its registry and its workspace, both conforming to `PROJECT_STANDARD.md`. The registry is a GitHub epic issue (**external**, the default) or the workspace itself (**internal**, `--internal` — standard §16: `project.md` + `tasks/` + `log.md`, no GitHub). After init, `/project-steward` manages the project autonomously in either mode.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | Yes | No |
| Fleet map / narrative (optional, §0 `fleet.*`) | `fleet/system-map.yaml` (valid owner names), `fleet/orchestration.md` §3b (default owner) | Yes | No |
| GitHub issues + labels | the `$REGISTRY` repo via `gh` | Yes | Yes |
| Project workspace (agent level) | `project_files/<slug>/` | Yes | Yes |
| Project workspace (`--canon`) | `<x-canon.clone_path>/projects/<slug>/` — the canon's shared projects zone | Yes | Yes (the shared zone every agent writes directly; push = `/canon-publish`) |
| Canon declaration | `template.yaml → x-canon:` (`repo`, `clone_path`, `folder`) | Yes (`--canon` only) | No |

## Platform mode (Trinity Projects — standard §17)

On a Trinity instance with Projects enabled, the platform holds the project record (ruling R38) and this skill works against it. Without Trinity, or where Projects is not enabled, nothing in this section applies and the skill runs exactly as written below.

**Check once per run, after the standard is resolved.** `PLATFORM=$(cfg platform auto)`. Platform mode is **off** when that is `off`, or when this session has no `mcp__trinity__list_projects` tool. Otherwise call `mcp__trinity__list_projects`:

- `enabled: true` → **on**; its `projects` are the platform projects this agent works on.
- `enabled: false` → **off** (an install without Projects, an unlicensed one, or a local session on a person's key). Say nothing; carry on in folder + GitHub mode.
- `enabled: false` with a `message` about internal conversations, or any project tool refusing with `code: external_audience` or `turn_unknown` → someone outside the company is in this conversation, or the platform cannot identify the turn: platform mode is off for the run, and no project detail read from the platform is repeated here.

**Which projects are on the platform.** A project is on the platform when its charter envelope carries `platform_project: prj_…`, or — when the charter has no such line, or is not visible to this run — when a listed project's tracker link is the project's epic URL. It is one of two kinds:

- **Linked** — `tracking: external`. Tasks stay GitHub issues exactly as below; the platform carries the record people see in the Workspace, the shared log and the health.
- **Platform-tracked** — `tracking: platform`, or a platform project with no charter and no tracker link into `$REGISTRY`. Its tasks are the platform's task list (`T-NNN`, the same fields as a §16 task file); there is no `tasks/` folder and no `log.md`. Reference: `<slug>/T-NNN`, the slug being the charter's folder, else the project name in kebab-case.

A platform-tracked project whose platform cannot be reached this run is skipped and named in the output. It is never continued from a folder — after an import nothing syncs back.

**What this skill does in platform mode:**

- **New project (default, external).** Steps 1–7 run unchanged. Then call `mcp__trinity__create_project` with `name`, `goal` (the Goal paragraph, at most 2,000 characters) and `tracker_url` = the epic URL, and write `platform_project: <id>` into the charter envelope after `tracking:`. The project is **linked**.
- **New project with `--internal`.** The project is **platform-tracked** instead of internal: skip Steps 2, 5 and 6, call `mcp__trinity__create_project` with `name` and `goal`, and write the internal charter of Step 7 with `tracking: platform` and `platform_project: <id>`, without the `## Tasks` section, the `tasks/` folder or `log.md` — the platform holds those. `--no-platform` keeps a new project in folder + GitHub mode.
- **`platform <slug>`** — bring a project this agent already manages onto the platform, without rewriting it. Resolve its charter (`charter_for <slug>`, standard §16), make sure the folder is committed and pushed (the platform reads the deployed agent's files), then call `mcp__trinity__import_project` with `path` = the folder as the agent sees it (`project_files/<slug>` or `<canon clone>/projects/<slug>`). On success write `platform_project: <id>` into the charter. An internal project also gets `tracking: platform`, one closing line appended to `log.md` (`### Moved to the platform YYYY-MM-DD — <id>; this folder is no longer the registry`) and the same fact appended to `decisions.md`; its `tasks/` files stay as they are. An external project keeps `tracking: external` and becomes linked. `code: already_imported` (a person imported it in the Workspace, or an earlier run did) → find the project in `list_projects` (by tracker link, else by name; ask when more than one fits), then make the same charter changes as after a successful import.
- **`adopt`** runs as written, then continues as `platform <slug>`.

**When the platform says no.** `code: project_management_not_permitted`, or no `create_project` / `import_project` tool in this session: nothing was created on the platform. Finish in folder + GitHub mode and add to the summary: *"Not on the platform yet. An instance admin can allow this agent to start projects (agent Settings → Permissions to change itself), then run `/project-init platform <slug>`; or create or import it in Workspace → Projects — the next steward run links it."* Never retry, and never ask a person to add members or change who can see the project on the agent's behalf — those stay the owner's.

Publishing a charter change follows the placement: commit at agent level, `/canon-publish` in the canon. The summary (Step 8) gains one line: `Platform:  <id> — linked | platform-tracked | not on the platform (<reason>)`.

## Process

### Step 1: Read the standard

Read the standard — `PROJECT_STANDARD.md` at the repo root, or `fleet/project-standard.md` on an orchestrator. **If neither exists, materialize it first** — the standard's template ships next to this skill (`PROJECT_STANDARD.template.md` in this skill's directory: `.claude/skills/project-init/` when injected or installed, `${CLAUDE_PLUGIN_ROOT}/skills/project-init/` when run as a plugin command):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
[ -n "$STANDARD" ] && echo "standard: $STANDARD" || echo "standard: MISSING — materializing from template"
```

When missing, resolve the four config values (ask only where nothing sensible resolves): registry repo (`gh repo view --json nameWithOwner -q .nameWithOwner`, default = this repo; `none` when the deployment has no GitHub registry — every project is then internal, standard §16), operator (the human this deployment escalates to — ask), agent name (`grep '^name:' template.yaml | head -1 | awk '{print $(2)}'`, else the folder name), pending-verification max age (default `48` hours). Then:

```bash
TARGET=PROJECT_STANDARD.md; [ -d fleet ] && TARGET=fleet/project-standard.md
TEMPLATE="$(ls .claude/skills/project-init/PROJECT_STANDARD.template.md "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/project-init/PROJECT_STANDARD.template.md" 2>/dev/null | head -1)"
sed -e "s|{{REGISTRY}}|$REGISTRY|g" -e "s|{{OPERATOR}}|$OPERATOR|g" -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{PV_MAX_AGE}}|$PV_MAX_AGE|g" -e "s|{{DATE}}|$(date -u +%Y-%m-%d)|g" "$TEMPLATE" > "$TARGET"
if [ "$TARGET" = fleet/project-standard.md ]; then   # orchestrator placement: state beside the fleet layer, fleet hooks on
  sed -i.bak -e 's|^\(state_dir:\) [^#]*|\1 fleet/project-steward  |' \
             -e 's|^\(fleet.system_map:\) *[^#]*|\1 fleet/system-map.yaml  |' \
             -e 's|^\(fleet.orchestration:\) *[^#]*|\1 fleet/orchestration.md  |' "$TARGET" && rm -f "$TARGET.bak"
  mkdir -p fleet/project-steward/digests fleet/project-steward/outputs
fi
git add "$TARGET" && git commit -m "chore: materialize $TARGET from the project-init template" 2>/dev/null || true
```

`TARGET` is `fleet/project-standard.md` when a `fleet/` layer exists (this agent is an orchestrator — `/add-orchestrator` installed it), else `PROJECT_STANDARD.md`. The standard is the deployer's live configuration — edit that file to change behavior, never this skill.

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration**. A standard without a §0 block (written before template 1.3) resolves to the defaults below, which are exactly the pre-1.3 behaviour (colon vocabulary, `project-steward/` state, no fleet hooks):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
cfg() { awk -v k="${1}" -v d="${2}" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$(0)~p{v=$(0);sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
REGISTRY=$(cfg registry ""); AGENT_NAME=$(cfg agent ""); OPERATOR=$(cfg operator "")      # empty → take them from the §1/§2 prose (pre-1.3 standard)
STATE_DIR=$(cfg state_dir project-steward); PV_MAX_AGE=$(cfg pv_max_age_hours 48); QUARANTINE=$(cfg quarantine on); MEMBER_REPOS=$(cfg member_repos "")
L_OWNER=$(cfg labels.owner_prefix "owner:"); L_PRIORITY=$(cfg labels.priority_prefix "priority:")
L_LIVE=$(cfg labels.live "status:active"); L_ACTIVE=$(cfg labels.active "status:active")
L_BLOCKED=$(cfg labels.blocked "status:blocked"); L_NEEDS_OPERATOR=$(cfg labels.needs_operator "status:needs-decision")
L_PAUSED=$(cfg labels.paused "status:paused"); L_PENDING=$(cfg labels.pending_verification "status:pending-verification")
L_DONE=$(cfg labels.done "status:done"); L_UNCLASSIFIED=$(cfg labels.unclassified "status:unclassified")
L_EPIC_EXTRA=$(cfg labels.epic_extra ""); FLEET_MAP=$(cfg fleet.system_map ""); FLEET_NARRATIVE=$(cfg fleet.orchestration "")
```

Labels are referred to by **role** from here on — `$L_NEEDS_OPERATOR` is the needs-operator label whatever the deployment names it, `$L_LIVE` is the comma-separated set that means "being worked" (split it with `tr ',' ' '`), `status:*` / `priority:*` mean the configured status / priority labels. An empty role turns its feature off (§0).

Pre-1.3 standards: when `$REGISTRY` / `$AGENT_NAME` / `$OPERATOR` come back empty, read them from §1 and §2 as before. These override any remembered values.

### Step 2: Verify gh access (external only)

Skip this step for an internal project (`--internal`, or `$REGISTRY` is `none`) — it touches no GitHub.

```bash
gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1
```

If this returns an error (403, 404, or "Resource not accessible"), stop and report exactly what failed. The PAT must have `repo` + `issues` scope on `$REGISTRY`.

### Step 3: Gather inputs

Determine mode from the argument: `adopt` (argument starts with "adopt" or names an existing `project_files/` folder) or `new` (default). Two flags, both off by default:

- **`--canon`** — a **shared (company) project** (standard §15, ruling R21): the workspace lives in the fleet's canon repo at `projects/<slug>/` — the top-level shared zone, not inside any agent's folder (ruling 2026-09-22) — so every agent and human on the canon can read the definition, and this agent is its steward (the charter's `owner:`). Managed exactly like an agent-level project — same charter, same epic, same steward, same intake, same ledger; only the readers differ. Requires this agent to be enrolled in the canon:
  ```bash
  grep -q '^x-canon:' template.yaml || { echo "not enrolled in a canon — run /add-canon first, or drop --canon"; exit 1; }
  CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $(2)}' template.yaml); CANON=${CANON:-canon}
  SELF=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/folder:/{print $(2)}' template.yaml | sed 's#^agents/##; s#/$##'); SELF=${SELF:-$AGENT_NAME}
  [ -d "$CANON/.git" ] || { echo "canon clone missing at $CANON/ — run /canon-doctor (it self-heals from x-canon.repo)"; exit 1; }
  git -C "$CANON" pull --ff-only || { echo "canon clone diverged — resolve with /canon-publish before creating a shared project"; exit 1; }
  ```
  `$SELF` is this agent's canon name — it becomes the new charter's `owner:` (the steward). The skill writes only `projects/<slug>/` in the canon: the shared zone every agent writes directly (CONVENTIONS.md § Projects). It never writes another agent's folder, and never takes over a project another agent stewards.
- **`--internal`** — the project tracks its tasks **in its own workspace** (standard §16): no epic, no labels, no GitHub access. Forced when `$REGISTRY` is `none`. Combines with `--canon` (a shared project whose tasks live in the canon folder, readable by everyone on the canon) and with `adopt`.
- **`--dry-run`** — write the workspace (charter + ledger) and print the epic body, but create nothing on GitHub (no labels, no issue). The charter's `epic:` then reads `<registry>#0` until the real init replaces it. Use it to lint a canon scaffold before it exists, or to preview.

For `adopt` mode: read the existing folder (look for `project.md`, `README.md`, any status files) and draft goal/criteria from what's there. `adopt --canon <slug>` names an existing canon project (e.g. `adopt --canon tandem`), resolved in this order:

1. `$CANON/projects/<slug>/` (the root zone). Its charter already names an `owner:` other than `$SELF` → **refuse**: it is stewarded by that agent — adopt it from there, or have the operator reassign the steward in the charter. No charter, or `owner: $SELF` → adopt it here.
2. `$CANON/agents/$SELF/projects/<slug>/` — this agent's project at the **earlier placement**. Adopt it and **move** it to the root in the same publish: `git -C "$CANON" mv "agents/$SELF/projects/<slug>" "projects/<slug>"` (fails if `projects/<slug>/` already exists — stop and report the clash). The epic's Workspace field then records `canon:projects/<slug>/`.
3. `$CANON/agents/<other>/projects/<slug>/` — another agent's project at the earlier placement → **refuse**: moving it is that agent's write (its own folder), not this one's.

Use AskUserQuestion for inputs that cannot be determined from context:
- **Name** (derive slug as kebab-case; confirm no collision with existing epics)
- **Goal** (one paragraph)
- **Success criteria** (2–5 checkable items)
- **Owner(s)** — who is accountable (human names and/or agent names). With `$FLEET_NARRATIVE` set and its §3b ownership matrix holding a domain row that matches the project's work, offer that domain's **responsible** agent as the default — an informational default the operator can override, never a gate. With `$FLEET_MAP` set, an agent owner must exist in the map (or be this agent).
- **Priority** — default `p2`
- **Cadence** — default "as needed"

### Step 4: Check for collisions

```bash
[ "$REGISTRY" != none ] && gh issue list --repo "$REGISTRY" --label project --state all --search "$NAME" --json number,title,labels
ls -d project_files/$SLUG 2>/dev/null                                  # agent level
[ -n "$CANON" ] && ls -d "$CANON/projects/$SLUG" "$CANON"/agents/*/projects/"$SLUG" 2>/dev/null   # --canon: any steward's, either placement
```

If an epic already exists for this project, or the folder already holds a `project.md`, stop and show it — offer to update instead.

### Step 5: Ensure labels exist (idempotent, external only)

Internal projects skip Steps 5 and 6 entirely — their status, priority and owners live in the charter (Step 7).

Create any missing labels **by the names §0 configures** — the standard's own labels plus every status / priority role it names. All `2>/dev/null || true` so re-runs are safe, and a label the tracker already owns (a product tracker's `status-blocked`, `priority-p1`) is simply a no-op:

```bash
mk() { [ -n "${1}" ] && gh label create "${1}" --repo "$REGISTRY" --color "${2}" --description "${3}" 2>/dev/null || true; }
mk project 0e8a16 "Project epic issue"
mk task    c2e0c6 "Task belonging to a project"
for L in $(printf '%s' "$L_LIVE" | tr ',' ' '); do mk "$L" 1d76db "Being worked"; done
mk "$L_ACTIVE"       1d76db "Being worked"
mk "$L_BLOCKED"      d93f0b "External dependency blocking progress"
mk "$L_NEEDS_OPERATOR" fbca04 "A decision or action only the operator can take"
mk "$L_PAUSED"       cccccc "Deliberately on hold"
mk "$L_PENDING"      e4e669 "Agent claimed done; awaiting DoD verification"
mk "$L_DONE"         6e5494 "Verified complete (absorbing; only a human reopens)"
mk "$L_UNCLASSIFIED" f9d0c4 "Auto-stubbed workspace folder not yet classified"
mk "${L_PRIORITY}p1" b60205 "High priority"; mk "${L_PRIORITY}p2" ff9f1c "Normal priority"; mk "${L_PRIORITY}p3" c5def5 "Low priority"
for L in $(printf '%s' "$L_EPIC_EXTRA" | tr ',' ' '); do mk "$L" 3e4b9e "Epic"; done
# Project-specific labels
mk "project:$SLUG" 5319e7 "Membership: project $NAME"
for OWNER in $OWNERS; do mk "${L_OWNER}$OWNER" 0052cc "Accountable: $OWNER"; done
```

### Step 6: Create the epic issue

Build the body per the standard's epic anatomy (§4). Use the inputs from Step 3. The `Current status` section says "(maintained by /project-steward — do not hand-edit)" as its initial value. The `Tasks` section starts empty.

```bash
cat > /tmp/epic-body.md << 'EOF'
## Goal
$GOAL

## Success criteria
$SUCCESS_CRITERIA_ITEMS

## Workspace
$WORKSPACE_FIELD

## Owners
$OWNERS_LIST

## Cadence
$CADENCE

## Current status
(maintained by /project-steward — do not hand-edit; latest steward update wins)

## Tasks
<!-- tasks will be listed here as #NN items by /project-task -->
EOF

gh issue create --repo "$REGISTRY" \
  --title "[Project] $NAME" \
  --label "project,project:$SLUG,$L_ACTIVE,${L_PRIORITY}$PRIORITY${L_EPIC_EXTRA:+,$L_EPIC_EXTRA}" \
  --body-file /tmp/epic-body.md
```

`$WORKSPACE_FIELD` is the **recorded** workspace path — the field every project skill resolves from (standard §15; nothing derives it from the slug): `` `project_files/$SLUG/` `` at agent level, `` `canon:projects/$SLUG/` `` with `--canon` (adopt: the actual folder after any move). With `--dry-run`, print `/tmp/epic-body.md` instead of creating the issue and skip Step 5 too.

For each owner, add the `${L_OWNER}<name>` label (`owner:` by default; `agent:` on a fleet whose owners are the executing agents — one label, never a GitHub assignee):
```bash
for OWNER in $OWNERS; do
  gh issue edit $ISSUE_NUMBER --repo "$REGISTRY" --add-label "${L_OWNER}$OWNER"
done
```

### Step 7: Scaffold the workspace

The workspace root is `$WS` = `project_files/$SLUG` (agent level) or `$CANON/projects/$SLUG` (`--canon`). **The charter is the same file at both levels** — `project.md` with the envelope the canon convention § Projects defines (standard §15), so moving a project later changes readers and nothing else:

```bash
mkdir -p "$WS"
TODAY=$(date -u +%Y-%m-%d); REVIEW=$(date -u -d "+30 days" +%Y-%m-%d 2>/dev/null || date -u -v+30d +%Y-%m-%d)
cat > "$WS/project.md" <<CHARTER
---
owner: $SELF_OR_AGENT_NAME
status: active
tracking: external
epic: $REGISTRY#$ISSUE_NUMBER
updated: $TODAY
review_by: $REVIEW
tldr: "$TLDR"
---

# $NAME — project charter

**Registry epic:** $EPIC_URL — the authoritative record for tasks and status; \`status:\` above mirrors its \`status:*\` label.

## Goal
$GOAL

## Success criteria
$SUCCESS_CRITERIA_ITEMS

## Owners
$OWNERS_LIST

## Cadence
$CADENCE
CHARTER
[ -f "$WS/decisions.md" ] || cat > "$WS/decisions.md" <<LEDGER
---
owner: $SELF_OR_AGENT_NAME
status: canonical
updated: $TODAY
tldr: "$NAME — decision ledger (append-only)"
---

# $NAME — decision ledger

Append-only: what was decided, by whom, when, and the consequence. Never rewrite an entry.
LEDGER
```

**Internal (`--internal`)** — the charter IS the registry (standard §16), so it carries what the epic would have: `tracking: internal`, `priority:` in the envelope, no `epic:` line, and the epic's `Current status` and `Tasks` sections in the body. Replace the charter above with this one, and add the task folder and the project log:

```bash
cat > "$WS/project.md" <<CHARTER
---
owner: $SELF_OR_AGENT_NAME
status: active
tracking: internal
priority: $PRIORITY
updated: $TODAY
review_by: $REVIEW
tldr: "$TLDR"
---

# $NAME — project charter

**Registry:** this folder (standard §16, internal tracking) — tasks in \`tasks/\`, the project's log in \`log.md\`.

## Goal
$GOAL

## Success criteria
$SUCCESS_CRITERIA_ITEMS

## Owners
$OWNERS_LIST

## Cadence
$CADENCE

## Current status
(maintained by /project-steward — do not hand-edit; latest steward update wins)

## Tasks
<!-- tasks are listed here as T-NNN items by /project-task and /project-intake -->
CHARTER
mkdir -p "$WS/tasks" && touch "$WS/tasks/.gitkeep"
[ -f "$WS/log.md" ] || printf '# %s — project log\n\nAppend-only: steward updates and state news, newest last (standard §16).\n' "$NAME" > "$WS/log.md"
```

An external charter written by this skill also states its mode, `tracking: external`, right after `status:` — explicit beats inferred (§16's rule 2 exists for charters written before the key did).

At agent level, commit the new workspace (`git add "$WS" && git commit -m "project: init $SLUG (internal)"`) — for an internal project those files are the registry, so they are never left uncommitted. `--canon` publishes through the gate below as usual.

`$SELF_OR_AGENT_NAME` is `$SELF` with `--canon` (the steward — the canon linter's `ownership` rule requires it to name an `agents/<name>/` folder in the canon) and `$AGENT_NAME` at agent level. `$TLDR` is one line (quoted; no unescaped `"`), drafted from the goal. `status:` is the epic vocabulary (`active | blocked | needs-decision | paused | pending-verification | done`) — never `canonical`/`draft`. With `--dry-run`, `$ISSUE_NUMBER` is `0`.

**Adopt mode:** keep the existing folder; create or update `project.md` so it carries the envelope above plus the charter sections (an adopted canon folder like Tandem may already have one — then only fill missing keys, never rewrite the body). Record the **actual** folder path in the epic body's Workspace field (may differ from the slug).

**`--canon` only — lint, then publish:**

```bash
[ -f "$CANON/tools/canon-lint/canon_lint.py" ] && \
  python3 "$CANON/tools/canon-lint/canon_lint.py" --repo "$CANON" --scope "projects/$SLUG"
```

A `project-envelope` / `ownership` FAIL here is fixed before anything is pushed (the charter is the linter's contract). Then push through the canon's own gate — `/canon-publish` (the `projects/` zone is a direct commit for any agent; it re-runs the lint and refuses a red project). Never `git push` the canon clone by hand from this skill, and never with `--dry-run`.

### Step 8: Summary

Print:
```
## Project initialized: $NAME

Registry:  $EPIC_URL | this folder (internal — tasks/, log.md)
Workspace: <project_files/$SLUG/ | canon:projects/$SLUG/ (shared — readable and writable by every agent and human on the canon; steward: $SELF)>
Labels:    project, project:$SLUG, $L_ACTIVE, ${L_PRIORITY}$PRIORITY, ${L_OWNER}<...>${L_EPIC_EXTRA:+, $L_EPIC_EXTRA}   (internal: none — status/priority/owners are in project.md)

Next steps:
  /project-task — create the first task
  /project-steward — run a sweep (or let the schedule do it)
  /canon-publish — (--canon only) push the charter + ledger; others read it with /canon-consume projects $SLUG
```

With `--dry-run`: `Epic: (dry run — not created)` and the printed epic body.
