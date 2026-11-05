---
name: project-init
description: Create or adopt a long-term managed project per the project standard (PROJECT_STANDARD.md at the repo root, or fleet/project-standard.md on an orchestrator — its §0 block configures registry, label vocabulary, fleet hooks and the kickoff mode) — the day-zero kickoff kit first (one page of intent, a charter with a delegation boundary, rulings.md, a probed setup manifest, the participation table for every owner agent, declared project metrics; blocking by default, standard §19–§20), then the GitHub epic issue with idempotent label creation and a workspace carrying the project.md charter, at agent level (project_files/<slug>/) or, with --canon, as a shared project in the fleet's canon repo (projects/<slug>/ at the canon root — same charter, same epic, same steward; canon placement only decides who can read it). On Trinity the platform project is created once by the deployed managing agent. Use when starting a new multi-session project or bringing an existing project folder under management.
argument-hint: "[project name | adopt <existing-folder> | platform <slug>] [--canon] [--internal] [--no-platform] [--dry-run] [--strict]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__create_project, mcp__trinity__import_project, mcp__trinity__chat_with_agent, mcp__trinity__get_credential_status, mcp__trinity__get_agent_permissions, mcp__trinity__get_agent_info, mcp__trinity__get_agent_skills, mcp__trinity__get_git_status
user-invocable: true
metadata:
  version: "1.6.0"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.6.0: Standard rev 2 (from a 2026-11 multi-agent project retrospective — §18 two machines, §19 kickoff kit, §20 participation contract, §27 adoption). New Step 4b runs the day-zero kit before anything is created: intent.md, the charter's Delegation boundary (ruling D1), rulings.md with a provisional flag, a machine-probed setup manifest (setup.md), the eleven-row participation table per owner agent, the record created once, the declared project_* metrics, and the critique flag (ruling D2). §0 `kickoff: blocking` (ruling R-b) stops the run on a missing item; `advisory` lists the gaps under ## Setup; an owner failing a machine-checkable participation row is written FAIL and receives no dispatch until it passes (`participation_check`). The epic body gains ## Delegation boundary, ## Setup, ## Participation and ## Engineering issues; ## Workspace may list the chain folders after the project folder; the charter envelope gains `chains:`. In platform mode a session whose key has no agent identity (`agent_key_required`) no longer creates the platform project itself: it dispatches `/project-init platform <slug>` to the deployed managing agent and records the receipt (ruling R-c). `adopt` runs the kit and reports gaps instead of refusing unless --strict"
    - "1.5.2: Trinity 1.0.0 truth sync (v1.0.0 ef8112ee8) — the projects.manage toggle lives in the agent Settings → Guardrails pane (Permissions to change itself) since the one-Settings-home redesign (ent#887–#891)"
    - "1.5.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.5: Platform mode (ent#788, ruling R38): on a Trinity instance with Projects enabled a new project is also created as a platform project (create_project — linked to the epic, or platform-tracked with --internal), and `platform <slug>` brings an existing folder project onto the platform in one import without rewriting it; the charter records platform_project. A refusal (no start-projects permission, no Projects) finishes in folder + GitHub mode and says what a person can do. Without Trinity nothing changes"
    - "1.4: One lineage (ent#789): the standard is resolved at the repo root OR at fleet/project-standard.md (an orchestrator's placement) and its new §0 Configuration block drives everything that used to be hard-coded — label vocabulary by role ($L_ACTIVE, $L_NEEDS_OPERATOR, $L_PRIORITY, …; a tracker-native hyphen vocabulary is now a config value), the owner-label prefix (owner: or agent:), extra epic labels (type-epic), state directory and fleet hooks. Label creation iterates the configured names. With fleet.orchestration set, its §3b ownership matrix supplies the default owner (informational). A missing standard materializes at fleet/project-standard.md when a fleet/ layer exists, else at the root. Absorbs the add-orchestrator template project-init 1.2 — that copy is retired"
    - "1.3: Internal tracking (ent#673, operator ruling 2026-09-22): `--internal` creates a project whose registry is its own workspace — project.md carries the epic's sections (Goal, Success criteria, Owners, Cadence, Current status, Tasks) and `tracking: internal` + `priority:` in the envelope, plus an empty tasks/ and an append-only log.md; no GitHub access, no labels, no epic. Forced when the standard's registry is `none`. Works at both placements (`--canon --internal` = a shared project with its tasks in the canon). External stays the default and writes `tracking: external` explicitly"
    - "1.2: Shared projects (operator rulings R21, 2026-09-10 — one PM standard, two visibility levels — and 2026-09-22 — shared projects at the canon root; ent#588): `--canon` creates the workspace in the fleet's canon repo at projects/<slug>/ — the top-level zone every agent writes directly, not inside any agent's folder — through the x-canon clone, pushed with /canon-publish, instead of project_files/<slug>/, and records `canon:projects/<slug>/` in the epic's Workspace field; this agent becomes the charter's owner: (the steward). A slug already taken in canon — by any steward — is a collision. `adopt --canon <slug>` adopts an existing canon project: one at the root keeps its steward unless it is this agent's (a project stewarded by another agent is refused — ask that agent); one still at the earlier agents/<self>/projects/<slug>/ placement is moved to projects/<slug>/ in the same publish (another agent's earlier-placement project is theirs to move). The charter is the same file at both levels and now carries the linted envelope the canon convention § Projects defines (owner = steward, status mirrors the epic label, epic as owner/repo#N, updated, review_by, tldr) plus an append-only decisions.md ledger with its own envelope; agent-level project.md gains the same envelope so moving a project changes readers and nothing else. `--dry-run` writes the workspace and prints the epic body without touching GitHub (so a scaffold can be linted before it exists). Default placement is unchanged (agent level)"
    - "1.1: Self-heal — when PROJECT_STANDARD.md is missing, materialize it from PROJECT_STANDARD.template.md shipped in this skill directory (resolving registry/operator/agent/max-age with sensible defaults). Makes the skill usable when assigned from the skills library without running the installer; the installer now copies from this directory instead of carrying its own copy"
    - "1.0: Initial version — owner/agent label distinction, unclassified quarantine, full Epic anatomy per PROJECT_STANDARD.md §4"
---

# Project Init

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-init v1.6.0 — recent: the kickoff kit runs before anything is created`. Then proceed.

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

- **New project (default, external).** Steps 1–7 run unchanged. Then the platform project is created **once, by the deployed managing agent** (standard §19 item 6, ruling R-c). If this session runs *as* that agent (its key carries an agent identity — the `report` tool would publish, `create_project` does not refuse `agent_key_required`), call `mcp__trinity__create_project` with `name`, `goal` (the Goal paragraph, at most 2,000 characters) and `tracker_url` = the epic URL, and write `platform_project: <id>` into the charter envelope after `tracking:`. If the session's key has **no agent identity** (a local session on a person's key: `create_project` refuses `agent_key_required`, or the tool is absent while `list_projects` is not), do not create the project here: commit and push the workspace first (the deployed agent reads its own files), then dispatch the one-line call `/project-init platform <slug>` to the deployed managing agent — `$AGENT_NAME` from §0, resolved to its live `deployed_name` through `$FLEET_MAP` when set — with `mcp__trinity__chat_with_agent(agent_name, message, parallel: true, async: true)`, record the receipt's `execution_id` in the epic's `## Setup` row *platform project* (`dispatched <id> <time>`), and let the deployed run write `platform_project:` into the charter (its next pull carries it back). Never re-send on silence. The project is **linked**.
- **New project with `--internal`.** The project is **platform-tracked** instead of internal: skip Steps 2, 5 and 6, call `mcp__trinity__create_project` with `name` and `goal`, and write the internal charter of Step 7 with `tracking: platform` and `platform_project: <id>`, without the `## Tasks` section, the `tasks/` folder or `log.md` — the platform holds those. `--no-platform` keeps a new project in folder + GitHub mode.
- **`platform <slug>`** — bring a project this agent already manages onto the platform, without rewriting it. Resolve its charter (`charter_for <slug>`, standard §16), make sure the folder is committed and pushed (the platform reads the deployed agent's files), then call `mcp__trinity__import_project` with `path` = the folder as the agent sees it (`project_files/<slug>` or `<canon clone>/projects/<slug>`). On success write `platform_project: <id>` into the charter. An internal project also gets `tracking: platform`, one closing line appended to `log.md` (`### Moved to the platform YYYY-MM-DD — <id>; this folder is no longer the registry`) and the same fact appended to `decisions.md`; its `tasks/` files stay as they are. An external project keeps `tracking: external` and becomes linked. `code: already_imported` (a person imported it in the Workspace, or an earlier run did) → find the project in `list_projects` (by tracker link, else by name; ask when more than one fits), then make the same charter changes as after a successful import.
- **`adopt`** runs as written, then continues as `platform <slug>`.

**When the platform says no.** `code: agent_key_required` is not a no — it is the signal that this session is a person's, and the dispatch to the deployed agent above is the path (the `agent_name` form of the user-key tools, ent#1024, lets an admin's key do it directly once it ships). `code: project_management_not_permitted`, or no `create_project` / `import_project` tool in this session: nothing was created on the platform. Finish in folder + GitHub mode and add to the summary: *"Not on the platform yet. An instance admin can allow this agent to start projects (agent Settings → Guardrails → Permissions to change itself), then run `/project-init platform <slug>`; or create or import it in Workspace → Projects — the next steward run links it."* Never retry, and never ask a person to add members or change who can see the project on the agent's behalf — those stay the owner's.

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
KICKOFF=$(cfg kickoff blocking); PARTICIPATION_CHECK=$(cfg participation_check on); CHAIN_LEDGER=$(cfg chain.ledger run-log.md)   # rev 2 (§19, §20, §24.3): blocking | advisory; on | off; the chain run-log name
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
- **`--strict`** — `adopt` mode only: treat a missing kickoff-kit item (Step 4b) the way a new project does under `kickoff: blocking` — stop instead of reporting the gap.

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
- **Delegation boundary** (standard §19 item 2, ruling D1) — three lists, filled once: what the managing agent **decides alone and reports**, what **needs the operator**, what is a **person-only act by platform rule** (merges, credential pastes, seats, members, visibility). Offer the standard's defaults as the starting text and take edits; this is the one place the decide-and-report rule gets its scope.
- **Engineering issues** — the issues `/build-chain` will execute inside this project (standard §18), each as `owner/repo#N` with `depends_on` (another listed issue or `none`) and the chain folder it will run in (`project_files/chain-<id>/` by the build-chain convention). An empty list is fine; everything else is a task.
- **Setup** — every account, token (with the repos it must read or write), vault item (with the service account that reads or writes it), setting, subscription item, permission edge, skill assignment and model pin the project needs, plus the **by-hand list**: what only the operator can grant (1Password consoles, token pastes, merges, an owner account). Draft it from the owners and the engineering issues; Step 4b probes it.

### Step 4: Check for collisions

```bash
[ "$REGISTRY" != none ] && gh issue list --repo "$REGISTRY" --label project --state all --search "$NAME" --json number,title,labels
ls -d project_files/$SLUG 2>/dev/null                                  # agent level
[ -n "$CANON" ] && ls -d "$CANON/projects/$SLUG" "$CANON"/agents/*/projects/"$SLUG" 2>/dev/null   # --canon: any steward's, either placement
```

If an epic already exists for this project, or the folder already holds a `project.md`, stop and show it — offer to update instead.

### Step 4b: Kickoff kit (standard §19–§20 — nothing is dispatched until it exists)

The workspace root `$WS` is `project_files/$SLUG` (agent level) or `$CANON/projects/$SLUG` (`--canon`); create it now (`mkdir -p "$WS"`) — Step 7 writes the charter into the same folder. Eight items, in this order; each has a written artifact and, where one exists, a machine check. Every Trinity tool call below is *when available* (the tool is in this session and does not refuse): otherwise the row is `by hand` with the file that holds the declaration. Nothing here is skipped silently; the verdict per item is written into `## Setup` of the epic (Step 6).

| # | item | artifact | machine check | verdict |
|---|---|---|---|---|
| 1 | One page of intent | `$WS/intent.md` — an ASCII target of the system after the project, the list of objects it creates, the list it retires (a new truth artifact only with the named retirement of the one it replaces) | file exists, > 10 non-empty lines, has the three headings `## Target`, `## Creates`, `## Retires` | present / missing |
| 2 | Delegation boundary (D1) | the charter's `## Delegation boundary` section (Step 7) with three sub-lists: *decides alone and reports* · *needs the operator* · *person-only by platform rule* | each sub-list has ≥ 1 line | present / missing |
| 3 | Rulings file | `$WS/rulings.md` — one line per ruling, `R<n> <YYYY-MM-DD> <confirmed\|provisional>: <text>`; may be empty, must exist. A `provisional` ruling may produce a design note and nothing else: `/build-chain` parks an issue that depends on one | file exists; every non-empty line matches `^R[0-9]+ [0-9]{4}-[0-9]{2}-[0-9]{2} (confirmed\|provisional): ` | present / missing / malformed line N |
| 4 | Setup manifest | `$WS/setup.md` — one table: `kind · name · scope (repos, vault, agent) · who grants · probe · result`, with the by-hand rows last | per row, by kind: **credential** → `[ -n "${!NAME}" ]` locally / `mcp__trinity__get_credential_status` on Trinity · **token scope** → `gh api repos/<owner>/<repo> -q .permissions` per repo the row names (push/pull/admin flags) · **edge** → `mcp__trinity__get_agent_permissions` lists it · **model pin** → `mcp__trinity__get_agent_info` resolved model equals the pin · **setting / subscription item / skill assignment / vault item** → `by hand` unless a read tool exists in this session | per row: ok / FAIL / by hand |
| 5 | Participation table (§20) | `$WS/participation.md` — eleven rows per `agent:*` owner (the standard's §20 table, columns *requirement · declared in · check · verdict*) | rows 1 (`mcp__trinity__get_agent_skills`, or the agent's slash-command list for repo-skill agents — the engineer reads 0 there — matched against the task list), 2 (`mcp__trinity__get_git_status`: ahead = 0 and clean, else *container-only state*), 5 (`gh api repos/<repo> -q .permissions` **with that agent's token, only when it is in hand**; else `by hand`), 7 (`mcp__trinity__get_credential_status` for every name the agent's `template.yaml credentials:` declares), 8 (`mcp__trinity__get_agent_permissions` plus the probe call the edge is for). Rows 3, 4, 6, 9, 10, 11 are `by hand` and name the file that holds the declaration (`template.yaml x-capabilities`, `protocols/playbook-call.md`, the agent's `runtime.model`, its skill text, `readiness-report.sh`, its `docs/rulings.md`) | per row: ok / FAIL / by hand |
| 6 | The record, created once | the epic (Step 6) and, in platform mode, the platform project **created by the deployed managing agent** (Platform mode section above) | — | created / dispatched `<execution_id>` / offline |
| 7 | Declared project metrics (§24.4) | the managing agent's `template.yaml metrics:` carries the `project_*` set | `for m in project_operator_asks project_ask_wait_p50_minutes project_block_hours project_dispatches project_rider_bytes_p50 project_redispatch_rate project_dispatch_queue_age_p95_minutes project_defects project_person_visible_leaks project_cost_usd; do grep -q "name: $m\$" template.yaml \|\| echo "missing: $m"; done` | declared / missing: <list> |
| 8 | Critique before a reversible build (D2) | one line in `rulings.md`'s header: `critique: not required` or `critique: <date> <where it is filed>` | needed only when a ruling in `rulings.md` **changes where state lives, who holds a credential, or builds something new** — then ask one question: run the independent critique now (one call bounded to the ruling text) or record who runs it before the first plan is dispatched; otherwise write `critique: not required` | recorded |

**Blocking (ruling R-b).** `KICKOFF=blocking` (the default): a `missing` or `malformed` verdict on items 1–7, or a `FAIL` on a setup row that names a credential, token or edge the first dispatch needs, **stops the run before Step 5** — print the missing items as a list, each with the file it lives in and the one line that would satisfy it, and end. `KICKOFF=advisory`: continue, and every gap is written under `## Setup` of the epic as an open row. `adopt` mode reports the gaps the same way and continues unless `--strict`. A `by hand` verdict never blocks: it is a row the operator grants in one sitting, and the evening brief (standard §23.2) carries it.

**Participation gate.** An owner agent with a `FAIL` on any machine-checkable row (1, 2, 5, 7, 8) is written into the table as `FAIL` with the row that failed; the summary says **that agent receives no dispatch until it passes** — `/project-steward` enforces it on every sweep by re-reading `## Participation`. `PARTICIPATION_CHECK=off` disables the gate, never the table: the rows are still probed and written.

Commit the kit with the workspace (Step 7 commits `$WS`); with `--canon` it rides the same publish.

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

## Delegation boundary
**Decides alone and reports:** $BOUNDARY_ALONE
**Needs the operator:** $BOUNDARY_OPERATOR
**Person-only by platform rule:** $BOUNDARY_PERSON

## Setup
$SETUP_TABLE
<!-- the probed manifest of Step 4b: kind · name · scope · who grants · probe · result; open rows are what the operator grants in one sitting -->

## Participation
$PARTICIPATION_TABLE
<!-- standard §20: eleven rows per agent:* owner; FAIL on a machine-checkable row = no dispatch to that agent until it passes -->

## Engineering issues
$ENGINEERING_ISSUES
<!-- issues /build-chain executes: owner/repo#N — depends_on: <ref|none> — chain: project_files/chain-<id>/ ; empty list allowed -->

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

`$WORKSPACE_FIELD` is the **recorded** workspace path — the field every project skill resolves from (standard §15; nothing derives it from the slug): `` `project_files/$SLUG/` `` at agent level, `` `canon:projects/$SLUG/` `` with `--canon` (adopt: the actual folder after any move). It may list **several backticked paths, one per line: the project folder first, then each chain folder** from `## Engineering issues` (`` `project_files/chain-<id>/` ``) — the first path is the workspace, the rest are the chain folders whose `$CHAIN_LEDGER` the steward reads (standard §24.3). With `--dry-run`, print `/tmp/epic-body.md` instead of creating the issue and skip Step 5 too.

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
chains: [$CHAIN_FOLDERS]
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

## Delegation boundary
Agreed once at kickoff (standard §19 item 2, ruling D1). Inside the first list the managing agent decides, writes "decided under rule N" to \`decisions.md\`, and reports — it never asks.

**Decides alone and reports:**
$BOUNDARY_ALONE

**Needs the operator:**
$BOUNDARY_OPERATOR

**Person-only by platform rule:**
$BOUNDARY_PERSON
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

`$SELF_OR_AGENT_NAME` is `$SELF` with `--canon` (the steward — the canon linter's `ownership` rule requires it to name an `agents/<name>/` folder in the canon) and `$AGENT_NAME` at agent level. `$TLDR` is one line (quoted; no unescaped `"`), drafted from the goal. `status:` is the epic vocabulary (`active | blocked | needs-decision | paused | pending-verification | done`) — never `canonical`/`draft`. `chains:` is the comma-separated list of chain folders from `## Engineering issues` (`[]` when there are none); the internal charter carries the same key and the same `## Delegation boundary` section. With `--dry-run`, `$ISSUE_NUMBER` is `0`.

**Adopt mode:** keep the existing folder; create or update `project.md` so it carries the envelope above plus the charter sections (an adopted canon folder like Tandem may already have one — then only fill missing keys, never rewrite the body). Step 4b has already run against the folder: a missing kit item is a reported gap (an open row under `## Setup`), not a refusal, unless `--strict`; `intent.md`, `rulings.md`, `setup.md` and `participation.md` are created empty-but-valid where absent so the next run can fill them. Record the **actual** folder path in the epic body's Workspace field (may differ from the slug).

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
Chains:    <project_files/chain-<id>/ … | none>
Labels:    project, project:$SLUG, $L_ACTIVE, ${L_PRIORITY}$PRIORITY, ${L_OWNER}<...>${L_EPIC_EXTRA:+, $L_EPIC_EXTRA}   (internal: none — status/priority/owners are in project.md)
Kickoff:   <8/8 present | N gaps (advisory): <item — file> …>   (standard §19; mode: $KICKOFF)
Participation: <every owner passes | <agent>: FAIL row <n> — no dispatch until it passes>   (standard §20; gate: $PARTICIPATION_CHECK)
By hand:   <the setup rows only the operator can grant — one sitting>

Next steps:
  /project-task — create the first task
  /project-steward — run a sweep (or let the schedule do it)
  /canon-publish — (--canon only) push the charter + ledger; others read it with /canon-consume projects $SLUG
```

With `--dry-run`: `Epic: (dry run — not created)` and the printed epic body.
