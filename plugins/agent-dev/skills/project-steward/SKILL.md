---
name: project-steward
description: Autonomous sweep of all managed projects per the project standard (PROJECT_STANDARD.md at the repo root, or fleet/project-standard.md on an orchestrator — its §0 block configures registry, label vocabulary, state directory and fleet hooks) — external projects tracked in GitHub Issues and internal projects tracked in their own workspace files (standard §16), with the same policy for both. Verifies pending-verification claims against Definition of Done, dispatches next work to explicitly-labeled owner agents that passed the participation check (Trinity when available; triage-only when not), reads each project's build-chain ledgers and owns the record for the engineering issues they run (status, stalls, parked questions — never dispatching into a chain), escalates stalls per the staleness policy, sweeps open loops (ages every waiting-on item and the chain's own asks, drafts the operator's follow-ups), writes the two-half evening brief once a day, runs the quarantine classification pass, and writes a digest that closes the loop with the operator. Never asks a human anything mid-run.
automation: autonomous
schedule: "0 7-19/2 * * 1-5"   # default: every 2h, weekdays UTC — adjust, or delete this line for manual-only (the installer substitutes your choice)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__get_agent_health, mcp__trinity__chat_with_agent, mcp__trinity__get_execution_result, mcp__trinity__get_chat_history, mcp__trinity__send_notification, mcp__trinity__list_reports, mcp__trinity__get_report, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__list_project_tasks, mcp__trinity__get_project_log, mcp__trinity__update_project_task, mcp__trinity__add_project_task_note, mcp__trinity__add_project_log_entry, mcp__trinity__get_steward_digest, mcp__trinity__set_project_health
effort: high
user-invocable: true
metadata:
  version: "1.11"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.11: Project standard rev 2 (from a 2026-11 multi-agent project retrospective). The steward owns every project's record and reads the chain (§18, §24.3, ruling R-a): for each chain folder a charter lists under `chains:` (or the epic's `## Engineering issues` names) it reads the committed `ledger-entry.yaml` mirror and the run-log tail — or the latest `trinity_pm.build_chain` report when the folder is not visible — writes the engineering issues' step/PR/validation into the epic's Current status, posts one platform log entry per new outcome, treats a run parked at needs-operator as the project's own ask, flags a dispatch queued past `chain.stall_minutes` as a stall, reports container-only state (§22.7) and never dispatches into the chain. Participation gate (§20, `participation_check`): an owner missing from the epic's `## Participation` table or carrying a FAIL row receives no dispatch. Two-half evening brief (§23.2, ruling D3, `brief.evening_utc`): once a day the digest opens with every open decision + the default the night will run, and every access the night's work needs. The chain's parked questions and open by-hand setup rows age as loops (§23.5). §0 keys read: chain.ledger, chain.stall_minutes, brief.evening_utc, participation_check"
    - "1.10: Trinity 1.0.0 truth sync (v1.0.0 ef8112ee8) — a dispatch refused `skill_not_granted` (ent#662: a library-assigned playbook needs a per-skill admin grant; a permission edge covers only what the owner declares itself) is still `$L_BLOCKED`, and the steward comment + digest now name the exact grant for the operator"
    - "1.9.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.9: Platform mode (ent#788, ruling R38): on a Trinity instance with Projects enabled the sweep starts from get_steward_digest, sweeps platform-tracked projects through the platform's task list (verify, reopen, notes, dispatch brief by task id), and for every platform project records health (set_project_health) and one shared-log entry per outcome — a verified deliverable, a new blocker, a hand-off — so members see what the steward did. Priority, reopening, project status and membership stay a person's. Charters gain platform_project by a linking pass. Without Trinity, or without Projects, the sweep is unchanged"
    - "1.8: Platform-truth refresh (Trinity dev ed5904906, 1.0.0-aws.2) — a dispatch answered pending_approval ran nothing (posted as waiting on approval, no tracker entry, never re-sent); refused / inter_agent_depth_exceeded block the task; the tracker entry keeps the receipt's execution_id and a silent dispatch is read with get_execution_result before any re-ping"
    - "1.7: Fix — the 1.6 resolver's default label values were self-references ($L_ACTIVE etc.) instead of the colon vocabulary, so a standard without a §0 block resolved every label role to an empty string (quarantine and verification silently off, needs-operator writes failing). Defaults restored: status:active / status:blocked / status:needs-decision / status:paused / status:pending-verification / status:done / status:unclassified. Found 2026-10-07 reviewing the library copy before the first fleet run"
    - "1.6: One lineage (ent#789) — this skill absorbs the orchestrator-side project-steward (add-orchestrator template 1.3 / the production orchestrator's 1.5) so one steward runs everywhere. The standard is resolved at the repo root OR at fleet/project-standard.md and its §0 Configuration drives what the two lineages had hard-coded differently: label vocabulary by role ($L_NEEDS_OPERATOR, $L_BLOCKED, $L_PAUSED, the $L_LIVE set, the $L_PRIORITY prefix — a tracker-native hyphen vocabulary is now a config value), owner-label prefix, state directory ($STATE_DIR — fleet-placed on an orchestrator, project-steward by default), verification hold on/off (empty pending label = done claims verified in the same run), quarantine on/off. Fleet hooks when §0 names them: owners resolve to their deployed_name through the fleet map, a dispatch needs a sanctioned manager→owner edge in the narrative's §5, the §3b ownership matrix adds consulted agents to the brief and informed agents to the digest. Ported from the orchestrator copy: inline output for workspaces the run cannot see goes to $STATE_DIR/outputs/<slug>/; the waiting-on sweep lists with --limit 1000 (gh sorts by recent activity and silently truncates — the oldest loops were exactly what a low cap dropped, seen live 2026-10-06); Trinity MCP tools declared in allowed-tools"
    - "1.5: Internal tracking (ent#673): internal projects (charter `tracking: internal`, standard §16) are found by their charters — project_files/*/ and the canon projects this agent stewards (projects/<slug>/ with owner: <self>, or its earlier-placement folder) — and swept by the same steps with file operations instead of gh: task status in front matter (pending_since as the verification clock), comments as append-only `## Log` entries, the epic's comment thread as log.md, the epic's Current status/Tasks as project.md sections, a done task stays as a file with status: done. One staleness ladder, one digest, one run budget across both modes. The steward now writes into the canon only for internal projects it stewards (task files, log.md, charter status/Current status/Tasks) and publishes them with /canon-publish at the end of the run. A registry of `none` runs with no GitHub at all. Quarantine treats a folder with an internal charter as registered"
    - "1.4: Shared projects (operator ruling R21, 2026-09-10 — one PM standard, two visibility levels; ent#588): the project's workspace is resolved from the epic body's `## Workspace` field through the standard's §15 resolver — `canon:projects/<slug>/` (the canon root's shared zone, ruling 2026-09-22) reads through the x-canon clone (pull --ff-only, never force), any other value is a repo-relative path, a missing field means the epic body is the context — and never derived from the slug; the charter (project.md) and the append-only decisions.md ledger are read from wherever the epic points and treated identically at both levels (staleness ladder, escalation, dispatch unchanged; the charter's status: is expected to mirror the epic label, a disagreement is noted in the digest, never fixed here — the canon's /canon-reconcile owns the charter stamps). The quarantine pass stays on project_files/ and never scans the canon: a canon-placed project is registered by its epic, never discovered from a folder. The steward writes nothing into the canon"
    - "1.3: GH_TOKEN now resolves through git's credential helper (`git credential fill`) — Trinity v0.9.5 (ent#615) made agent remotes credential-less, so the old sed over `git remote get-url origin` returned an empty token and the run fell back to a possibly stale hosts.yml (the 403 class this block exists to prevent); the remote-URL parse stays as a fallback for pre-0.9.5 instances"
    - "1.2: Read-the-standard guard (missing PROJECT_STANDARD.md → exit with \"run /project-init first\", headless-safe); default `schedule:` in frontmatter replaces the installer-substituted placeholder; skill is now authored standalone (installer copies from here)"
    - "1.1: Loop closure (Invariant 7) — Step 3c open-loop pass ages every waiting-on:* task on the 3d/7d/14d ladder and drafts sendable nudges (never sends them), detects and records closes; digest opens with a closing statement and carries Your open loops + Loops closed; unanswered needs-decision asks get louder with age instead of aging out; operator-initiated results notify the operator directly; state.json gains open_loops (rebuildable from labels)"
    - "1.0: Initial version — completion lattice verification, owner/agent distinction, Invariant 4 escalation ladder (never mutates P1/P2), unclassified quarantine pass, Trinity-optional dispatch"
---

# Project Steward

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-steward v1.9.1 — recent: arguments no longer break the config resolver`. Then proceed.

## Purpose

Keep every managed project moving without the operator having to push it. Each run:
1. Reconcile outstanding dispatches (read agent replies, post relay comments, verify done claims)
2. Review every open project epic: verify pending-verification tasks, dispatch next work to admitted owners (standard §20), escalate stalls
3. Read each project's build chains (standard §18, §24.3): the engineering issues a project runs through `/build-chain` are the steward's to *record* — step, PR, validation, stalls, parked questions — never its to dispatch
4. Sweep open loops (Invariant 7): age every `waiting-on:*` task and the chain's own asks (§23.5), draft the operator's nudges, keep unanswered asks alive
5. Run the quarantine pass: auto-stub unregistered workspace folders
6. Write the digest (material runs only), opening with what the operator now knows and what is waiting on them — and, once a day at `brief.evening_utc`, the two-half evening brief (§23.2): the decisions with the defaults the night will run, and the access the night's work needs

**This skill never asks a human anything mid-run.** Anything ambiguous gets `$L_NEEDS_OPERATOR` and moves on. It is the sole writer of steward update comments on GitHub issues.

**It does close loops, in both directions (standard §14).** Nothing it touched ends in silence: work the operator initiated is reported back to the operator, an unanswered ask is re-surfaced with its age rather than dropped, and every loop parked on a third party is aged in the digest with a ready-to-send nudge. It drafts those nudges; **it never sends them** — contacting a client, vendor, or outside colleague is the human's act, always.

**Deliberate non-composition:** this skill dispatches only to owners explicitly named by `agent:*` labels — no routing judgment. The interactive disambiguation that `/orchestrate` provides would hang an unattended run.

**Trinity is optional.** When Trinity MCP is unavailable, the skill runs in triage-only mode: all registry operations continue; dispatch is skipped and noted in the digest. Nothing is lost.

**On Trinity with Projects enabled the platform holds the project record** (standard §17): the same steps then run against it — see **Platform projects** below. Off Trinity nothing changes.

**Two tracking modes, one steward.** A project's registry is its GitHub epic (external) or its own workspace files (internal, standard §16). Every step below is written for GitHub; for an internal project apply the same step through **Internal projects** (below) — same order, same thresholds, same run budget, same digest. A run may mix both.

## Runtime resolution (do this first, once per run)

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
# rev 2 keys (standard 2.0, §18–§24) — absent in an older standard, so every default below is the pre-rev-2 behaviour except the brief and the chain read, which are additive
CHAIN_LEDGER=$(cfg chain.ledger run-log.md); CHAIN_STALL_MIN=$(cfg chain.stall_minutes 30)
BRIEF_UTC=$(cfg brief.evening_utc "18:00"); PARTICIPATION_CHECK=$(cfg participation_check on)
```

Labels are referred to by **role** from here on — `$L_NEEDS_OPERATOR` is the needs-operator label whatever the deployment names it, `$L_LIVE` is the comma-separated set that means "being worked" (split it with `tr ',' ' '`), `status:*` / `priority:*` mean the configured status / priority labels. An empty role turns its feature off (§0).

**If no standard exists, exit (headless-safe, no prompt) and report: run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Then:
- `$REGISTRY` — `none` means every project is internal: skip the gh prerequisites below entirely. Pre-1.3 standards return it empty: read it from §1 (and `$AGENT_NAME`, `$OPERATOR` from §2, `$PV_MAX_AGE` from §12).
- `$AGENT_NAME` — tasks labeled `agent:$AGENT_NAME` are inline-class, never dispatched (a chat dispatch to yourself would loop).
- **Fleet hooks** (only when §0 sets them): `$FLEET_MAP` is the system map that turns an `agent:<name>` label into the live callable name (`deployed_name`, else the last segment of `ref:`; an owner absent from the map is unresolvable → `$L_NEEDS_OPERATOR`); `$FLEET_NARRATIVE` is the orchestration narrative whose §5 edges gate every dispatch and whose §3b ownership matrix supplies consulted / informed etiquette. Unset = call owners by their logical name, no edge check, no etiquette — the stand-alone behaviour.
- **Workspaces may be invisible to this run** (gitignored `project_files/` on a Trinity container): then the epic body is the authoritative context, workspace reads are skipped without complaint, and an inline task's output is written to `$STATE_DIR/outputs/<slug>/` (tracked, pushed with the state) with the task comment saying so — a local run can land it in the workspace later.
- **Rev 2 keys** (standard 2.0): `$CHAIN_LEDGER` is the run-log file name inside each chain folder the steward reads (**Chain reading**, below); `$CHAIN_STALL_MIN` is the queued age past which a chain dispatch is a stall; `$BRIEF_UTC` is the hour of the daily evening brief (empty = no brief); `$PARTICIPATION_CHECK` gates dispatch on the epic's `## Participation` table (`off` = dispatch as before). A pre-rev-2 standard has none of these keys: the defaults make the chain read and the brief additive and leave dispatch unchanged.
- **Workspace resolver (§15)** — per project, from the epic body, never from the slug:
  ```bash
  WS_SECTION=$(printf '%s' "$EPIC_BODY" | awk '/^## Workspace/{f=1;next} f&&/^## /{exit} f{print}')
  WS_FIELD=$(printf '%s' "$WS_SECTION" | grep -o '`[^`]*`' | head -1 | tr -d '`')          # first backticked path wins …
  [ -n "$WS_FIELD" ] || WS_FIELD=$(printf '%s' "$WS_SECTION" | awk 'NF{print;exit}' | xargs)  # … else the first non-empty line
  case "$WS_FIELD" in
    canon:*) CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $(2)}' template.yaml 2>/dev/null); CANON=${CANON:-canon}
             WS="$CANON/${WS_FIELD#canon:}"; git -C "$CANON" pull --ff-only >/dev/null 2>&1 || echo "canon clone stale/diverged — reading local copy" ;;
    "")      WS="" ;;                       # pre-§15 epic: no workspace, the epic body is the context
    *)       WS="$WS_FIELD" ;;              # repo-relative (project_files/<slug>/ by convention — the field wins)
  esac
  [ -n "$WS" ] && [ ! -d "$WS" ] && { echo "workspace $WS not visible here"; WS=""; }
  ```
  A `canon:` workspace with no `x-canon:` block or no clone means this instance is not enrolled — `WS=""`, note it once in the digest (`/canon-doctor` on this agent), and carry on from the epic body. For an external project the clone is read-only for this skill (charter stamps belong to `/canon-reconcile`, decisions to the owner in conversation). **The one exception is an internal project this agent stewards in the canon** (standard §16 — `projects/<slug>/` with `owner: $SELF`, or its own earlier-placement folder): there the workspace *is* the registry, so the steward writes its task files, `log.md` and the charter's `status:` / `## Current status` / `## Tasks` — in that project's folder only — and publishes them once at the end of the run (Step 7). Never another agent's folder; under the top-level `projects/` zone only charters whose `owner:` is this agent.

## Prerequisites

Only when at least one project is external (`$REGISTRY` is not `none`). An internal-only deployment needs no `gh`, no token and no pre-flight.

**Bootstrap gh CLI** (idempotent):
```bash
if ! command -v gh &>/dev/null; then
  export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v gh &>/dev/null; then
  mkdir -p ~/.local/bin
  curl -sL "https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz" | tar xz -C /tmp/
  cp /tmp/gh_2.63.2_linux_amd64/bin/gh ~/.local/bin/gh
  export PATH="$HOME/.local/bin:$PATH"
fi
```

**Derive GH_TOKEN from git's own credential** (critical on Trinity — env wins over cached hosts.yml). Since Trinity v0.9.5 (ent#615) agent remotes carry no token: git asks the platform's credential helper, which reads the live-rotated `.env` first — so ask git, don't parse the URL. The second block is the fallback for instances older than v0.9.5, where the PAT still rides the origin URL:
```bash
if [ -z "$GH_TOKEN" ]; then
  export GH_TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
fi
if [ -z "$GH_TOKEN" ]; then
  export GH_TOKEN=$(git remote get-url origin | sed -nE 's#https://[^:/@]+:([^@]+)@github.com/.*#\1#p')
fi
```

**PAT scope pre-flight** (use REST labels endpoint — issue list silently returns [] on missing scope):
```bash
PREFLIGHT=$(gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1)
```
If this returns a 403 or "Resource not accessible": abort immediately. Prepend a `FAILED` line to `$STATE_DIR/run_log.txt` (create the dir first). Attempt to notify the operator via Trinity `mcp__trinity__send_notification` if available. Stop.

**Detect Trinity MCP:** attempt `mcp__trinity__list_agents`. If it fails or is unavailable, set `TRINITY_MODE=triage-only` and continue.

**Detect platform mode (standard §17):** `PLATFORM=$(cfg platform auto)`. It is **off** when that is `off`, when `TRINITY_MODE=triage-only`, or when this session has no `mcp__trinity__list_projects` tool. Otherwise call it: `enabled: true` → on; `enabled: false` → off, silently (an install without Projects, an unlicensed one, a person's key). A project tool refusing with `code: external_audience` or `turn_unknown` (the platform cannot place this run as an internal one — an agent image older than the turn id, most often) turns it off for the run and is named once in the digest. With platform mode off, every project is swept exactly as before, and a platform-tracked project (charter `tracking: platform`) is **skipped and named in the digest** — never continued from its folder.

## No-op discipline (high-frequency cadence)

Most runs will find nothing to do. Before writing anything, compute whether ANY actionable condition exists:
- An unreconciled dispatch with a reply or past a time threshold
- An active epic with a dispatchable/inline/verifiable task
- A staleness breach
- New/edited epics or label changes since last run
- A `pending-verification` task past max-age
- A `waiting-on:*` loop crossing a nudge threshold (3 days, then weekly, then 14 days) — a quiet loop still ages
- A `$L_NEEDS_OPERATOR` ask that has now gone unanswered across two digests
- Unclassified workspace folders not yet stubbed
- Platform mode: the steward digest shows a task awaiting verification, a task blocked or waiting on a decision, a stale task, or a health update due
- A chain changed since the last sweep (**Chain reading**): a step closed, a PR opened or validated, a run newly parked at needs-operator, a new stall, or new container-only state — compared against `state.json.chain_seen`
- The evening brief is due: `$BRIEF_UTC` is set, the current UTC time is at or past it, and `state.json.last_brief_date` is not today

**If none: stop.** Update `last_run` in `$STATE_DIR/state.json` only — do NOT commit, do NOT write a digest, do NOT notify, do NOT post any comment. Quiet runs leave no trace.

## Hard limits (45-minute rule)

- Max **10 projects** reviewed per run. If more are open, review `${L_PRIORITY}p1` first, then least-recently-updated. Write the remainder to `state.json carry_over` and start there next run.
- Max **3 dispatches** per run; max **1 open dispatch per project**.
- Max **1 inline task** executed per run.

## Process

### Step 1: Read current state

1. Sync: `git pull --rebase --autostash origin main` (continue on failure; note it in the digest).
2. Read the standard (resolving runtime variables as above).
3. Read `$STATE_DIR/state.json` (create with empty defaults if missing: `{"last_run": null, "carry_over": [], "open_dispatches": [], "open_loops": [], "chain_seen": {}, "last_brief_date": null}`). Each `open_loops` entry is `{issue, actor, asked_at, last_nudge, digests_carried}` — bookkeeping only; the `waiting-on:*` labels on GitHub are the truth, so a lost state file costs nudge timing, never a loop. `chain_seen` is `{<chain folder>: {issues: {<ref>: {step, pr, validation}}, stalls: [...], parked: <question or null>, status}}` — the last chain state this steward recorded, so a sweep knows what is *new*; a lost file costs one repeated outcome entry, never a missed one.
4. Pull the registry — both modes:
   ```bash
   [ "$REGISTRY" != none ] && gh issue list --repo "$REGISTRY" --label project --state open \
     --json number,title,labels,updatedAt,body --limit 50
   ```
   Internal projects are the charters the standard's §16 finder returns (`charters`) whose `mode_of` is internal and whose `status:` is not `done` — under the top-level canon `projects/` zone, only those whose `owner:` is this agent. For canon-placed ones, `git -C "$CANON" pull --ff-only` first (on failure, read the local copy and say so in the digest).
5. Check Trinity MCP availability, then platform mode (Prerequisites). When on: `mcp__trinity__get_steward_digest`, and note which reviewed projects are linked or platform-tracked (**Platform projects**, below).
6. Read each project's build chains (**Chain reading**, below) — the chain folders the charter envelope lists under `chains:`, or the epic's `## Engineering issues` section names. A project with neither has no chain and nothing changes.

### Internal projects — the same steps, file operations instead of `gh`

For an internal project, `$WS` is the charter's folder and every step above and below applies with this translation (standard §16). Edit files with Read/Edit — never regenerate a task file from scratch, never rewrite a past Log entry.

| In a step below (GitHub) | For an internal project |
|---|---|
| Read the epic body + comments since the last steward update | Read `project.md`, and the entries in `log.md` after the last `### Steward update` |
| Read open `project:<slug>` task issues with labels and bodies | Read `tasks/T-*.md` whose `status:` is not `done` — front matter for the labels, body for the sections |
| The epic's `status:*` / `priority:*` label | The charter's `status:` / `priority:` |
| Set a task's `status:*` label | Set the task's `status:` and `updated:` in front matter; entering `pending-verification` sets `pending_since: <now UTC>`, leaving it removes the key |
| Age of `pending-verification` (label-change event) | `now − pending_since` |
| Post a comment on a task (dispatch receipt, relay, `[Verified]`, `[Verification failed]`, waiting-on, loop closed) | Append the same heading and text under the task's `## Log`, newest last |
| Close the task as done, check it off in the epic | `status: done` (the file stays), and `- [x] T-NNN …` in project.md's `## Tasks` |
| `waiting-on:*` label / its age | `waiting_on:` in front matter / the date on its `### Waiting on` Log entry |
| Post a steward update on the epic | Append it to `log.md` and replace the body of project.md's `## Current status` with its lines; set the charter's `status:` and `updated:` if they changed |
| Days since last activity | The newest of: the charter's `updated:`, any task's `updated:`, the last `log.md` entry date |
| Dispatch brief `Issue: <url>` | `Task: <slug>/T-NNN — <workspace>/tasks/T-NNN.md` |
| Task reference in the digest | `<slug>/T-NNN` |

A task file the charter lists but that no longer exists is an error for the digest (`<slug>/T-NNN missing`), never a closed task — absence is not deletion. A task file whose front matter will not parse is `needs-decision` in the digest with the file named; the steward does not repair it.

### Platform projects — the same steps against the platform record (standard §17)

Only in platform mode (detected in Prerequisites). Start with `mcp__trinity__get_steward_digest`: it lists the platform projects **this agent stewards**, each with its health and whether an update is due, tasks awaiting verification, tasks blocked or waiting on a decision, tasks untouched for a week, open asks, and whether it has gone quiet. Those join the review list beside the epics and the internal charters — one staleness ladder, one digest, one run budget. A platform project this agent is on but does not steward is not swept.

**Linked project** (tasks in GitHub): every step runs as written. In addition, per run:

- **Health** — `mcp__trinity__set_project_health` when the project's state changed this run or the digest says an update is due: `on-track` (nothing blocked, nothing waiting on a decision, nothing stale), `at-risk` (a task blocked, waiting on a decision, stale, or past `$PV_MAX_AGE`), `off-track` (a success criterion or a committed date can no longer be met without a decision); `note` = the one line the steward update opens with.
- **Shared log** — `mcp__trinity__add_project_log_entry`, **one entry per outcome this run produced, never one per run and never "nothing changed"**: a verified task → `deliverable` (what was delivered, the issue link); a task newly blocked or newly needing the operator → `blocker` (what is needed, from whom); a dispatch → `handoff` (task, owner). `task_id` is left out — the tasks are GitHub issues.

**Platform-tracked project**: every step applies with this translation. `$WS` is the charter's folder when there is one (files and drafts only), else empty.

| In a step (GitHub) | For a platform-tracked project |
|---|---|
| Read the epic body + comments since the last steward update | `mcp__trinity__get_project` — goal, status, steward, the latest 20 log entries and the open tasks; `mcp__trinity__get_project_log` for more |
| Read open `project:<slug>` task issues with labels and bodies | `mcp__trinity__list_project_tasks` (open is the default; `status: all` when counting done) |
| The epic's `status:*` label | The project's status — `paused` or `done` → skip it |
| Set a task's `status:*` label | `mcp__trinity__update_project_task` with `status` (the same six values) |
| Age of `pending-verification` | the task's `pending_since`, or the digest's awaiting-verification age |
| Post a comment on a task (dispatch receipt, relay, `[Verified]`, `[Verification failed]`, waiting-on, loop closed) | `mcp__trinity__add_project_task_note`, same heading and text |
| Close the task as done | `update_project_task` `status: done` with the `[Verified]` text as `note` — the steward agent may set done; a `done_needs_verification` refusal means this agent is not the steward: leave it and say so in the digest |
| Verification failed | `update_project_task` `status: active` with the `[Verification failed]` text as `note` |
| `waiting-on:*` label / its age | the task's `waiting_on` / the date on its `### Waiting on` note |
| Post a steward update on the epic | `set_project_health` (state + the update's first line) and one `add_project_log_entry` per outcome, as for a linked project, with `task_id` set |
| Days since last activity | the digest's last activity / quiet flag |
| Dispatch brief `Issue: <url>` | `Task: <project name> / T-NNN (Trinity project <id> — read it with get_project and list_project_tasks; claim done by moving the task to pending-verification with your evidence as the note)` |
| Task reference in the digest | `<slug>/T-NNN` |

**What stays a person's on the platform:** a task's priority, reopening a done task, the project's own status, its members and who can see it. When a step would change one of them (the closure proposal of Step 4.1, a priority escalation, a missing owner who is not on the project), the steward records the proposal as a `blocker` log entry and takes the needs-operator path (`status: needs-decision` on the task, or the digest's **Needs operator** section for the project) — it never works around a refusal. An owner agent that is not on the project cannot read the task: that is **needs-human** ("add <agent> to the project"), not a dispatch.

**Linking pass (cheap, every material run):** an external charter this agent can write that has no `platform_project:` line, while `list_projects` shows a project whose tracker link is its epic URL, gets the line written (agent level: committed with the state push; canon: `/canon-publish`). That is how a project a person created or imported in the Workspace becomes linked. An **internal** charter is never switched by this pass — a name is too weak a match: when `list_projects` shows a project with no tracker link whose name is the charter's project name, leave the charter alone, sweep the project from its folder this run, and put one line in **Needs operator**: *"<slug> looks imported to the platform as <id> — run `/project-init platform <slug>` to confirm, or tell me they are different projects."* Until that is answered the folder stays the registry.

### Chain reading — the engineering issues a project runs through `/build-chain` (standard §18, §24.3)

**The steward owns every project's record; a build chain is the project's engineering executor, never a project of its own** (ruling R-a). The chain has its own machine (`/build-chain`: plan → rulings → implement → review → fix → PR → validate, one ledger per run) and the steward **never dispatches into it**: an issue the epic lists under `## Engineering issues` is skipped by Step 3b/Step 4 even when it carries an `agent:*` label — the chain dispatches it. What the steward does is read the chain's state and keep the record people see current.

**Where the chain's state is.** Each chain folder (`project_files/chain-<id>/` by convention; the charter envelope's `chains:` list or the epic's `## Engineering issues` section names them, the steward never derives them from the slug) holds:
- `ledger-entry.yaml` — the committed mirror of the build-chain ledger: `status` (`pending | needs-operator | paused | done`), `project`, `issues[]` with `ref`, `step`, `branch`, `tip`, `pr`, `validation {decision, post_merge}`, `depends_on`, `executions[]` with `step`, `id`, `queued_at`, `started_at`, `closed`, `rider_bytes`, and `dispatch_health[]` (the stalls the chain itself recorded);
- `$CHAIN_LEDGER` (`run-log.md`) — the dated narrative; its newest entries carry a parked question (`needs-operator: <question>`), container-state lines (`ahead > 0`, `dirty tree`), rulings and lessons.

Read the mirror whole (it is small) and the run-log's last ~60 lines. **When the folder is not visible to this run** (gitignored `project_files/` on a container), read the chain's latest `trinity_pm.build_chain` report instead — `mcp__trinity__list_reports` filtered to that `report_type`, then `mcp__trinity__get_report`: its rows carry issue, step, branch, tip, PR, verdict, cost, rider KB and stalls — and say in the digest that the chain was read from its report (a parked question is then only in the report's title or notes; if absent, the digest says "parked, question not readable here").

**What the steward writes from it** (per project, per material run):
1. **The epic's `## Current status`** (in the steward update, §7): one line per engineering issue — `<ref>: <step>, PR <#n or —>, validation <APPROVE | REQUEST CHANGES | — >` — then one line for the run (`chain <id>: <status>, cost $<n>`), stalls (`<ref> <step> queued <m> min`), and any container-only state the ledger or run-log reports (`<ref>: ahead <n> / dirty tree — not pushed`, standard §22.7). For a platform project this is also the `set_project_health` note's second line.
2. **One platform log entry per *new* outcome** (platform mode, linked or platform-tracked project, `mcp__trinity__add_project_log_entry`): a PR opened → `deliverable` (ref, PR link); a validation decided → `deliverable` (APPROVE) or `blocker` (REQUEST CHANGES, round n); a run parked at `needs-operator` → `blocker` with the question verbatim; a new stall → `blocker` (`<ref> queued <m> min on <agent>`). *New* means absent from `state.json.chain_seen` for that chain; the chain itself posts its §7 receipts and closures on the issues and its own per-wake log entries when it runs with `--project`, so the steward never duplicates those — it logs the outcomes it is the first to record, and when the chain already logged the same outcome (same ref + same event in the project log since the last sweep) it skips it.
3. **A parked run is the project's ask.** A chain `status: needs-operator` (its question in the run-log) is treated exactly like a task carrying `$L_NEEDS_OPERATOR`: it enters the digest's **Needs operator** section with the question and its age (from the run-log entry's timestamp), is promoted after two digests, and is never retired. The steward does **not** label the engineering issue — the chain's ledger is its state — but it does label the **epic** `$L_NEEDS_OPERATOR` when no other needs-operator item already holds it, and removes that label when the run resumes.
4. **Stalls.** Any execution in the mirror with `queued_at` older than `$CHAIN_STALL_MIN` minutes and no `started_at` (or a `dispatch_health` entry not yet seen) is a stall line in the digest's **Stalls** section — `<chain> <ref> <step>: queued <m> min on <agent>` — and makes the run material. A stall is reported, never acted on: the steward re-sends nothing into a chain.
5. **Container-only state is a finding** (§22.7): `ahead > 0` or a dirty-tree line for any branch in the ledger or the run-log's newest entries goes into the status line above and the digest's **Blocked** section as `<ref>: work only in the engineer's container (ahead <n>)` — the chain's next wake pushes it; the steward records that it is not yet on GitHub.
6. **Material-run rule.** A chain step closed, a PR opened or validated, a run newly parked, a new stall, or new container-only state since `chain_seen` makes the run material (digest written, Current status posted); a chain that has not moved is silence, exactly like a quiet project. After writing, `chain_seen[<chain>]` is set to the state just recorded.

**Cadence.** While a project has a chain run with `status: pending` and an open execution, the steward's sweep is what reads it between the chain's own wakes — the scheduled cadence (every 2 h) is enough, because the chain writes its own ledger on every wake and the steward only has to notice. A chain whose folder and report are both unreadable is named once in **Carry-over + mode** and skipped.

### Step 2: Reconcile outstanding dispatches

For each entry in `open_dispatches` (skip in triage-only mode):

1. Use `mcp__trinity__get_chat_history` with the dispatched agent; look for a "Done claim" reply posted after `sent_at`.
2. **Reply found**: check DoD items against the claim (Step 3b verification protocol). If verified: close the task issue as done, check it off in the epic, post an agent-report relay comment. If failed: reopen with logged reason. Remove the tracker entry.
3. **No reply, 6+ hours since `sent_at`**: read `mcp__trinity__get_execution_result(agent, execution_id)` first when the entry has an `execution_id` — a run still in flight is not silence. Re-ping (once, via `mcp__trinity__chat_with_agent`, referencing the original dispatch) only when that run is terminal or the entry has no id; record `repinged_at`.
4. **No reply, 24+ hours since `sent_at`** (re-ping already sent): set the task issue to `$L_BLOCKED`, post a steward comment naming the silent agent, remove the tracker entry, flag in digest.
5. **Under threshold**: leave the tracker entry — not yet actionable.

### Step 3: Review each project (max 10)

Build the review list: `carry_over` first, then `${L_PRIORITY}p1`, then least-recently-updated. A **live** epic carries any label in `$L_LIVE`; `$L_BLOCKED` / `$L_NEEDS_OPERATOR` epics are reviewed for the digest only; skip `$L_PAUSED` epics entirely. For each project:

1. Read the epic body + comments since the last steward update. Resolve `$WS` (runtime resolution above); when it resolves, read the charter `$WS/project.md` and, if present, the ledger `$WS/decisions.md` — the same two files whether the project sits in `project_files/` or in the canon (standard §15; Tandem is `canon:projects/tandem/`, stewarded by corbin). If the charter's `status:` disagrees with the epic's `status:*` label, the epic wins and the disagreement goes in the digest — do not edit the charter (at canon level that is `/canon-reconcile`'s job; at agent level the owner's).
2. Read open `project:<slug>` task issues with their labels and bodies.
3. Compute: days since last activity, open/done/pending-verification task counts, current `status:*` label, whether an open dispatch exists.
4. Apply the staleness policy (§8 of the standard).

**`ultrathink` here** — determining the true state of a project and the single best next action is the judgment-heavy core of this skill.

### Step 3a: Pending-verification pass

**Skip this pass when `$L_PENDING` is empty** — the deployment has no verification hold (a product tracker that owns its status vocabulary, for instance): a done claim found in Step 2 is verified against the Definition of Done in that same step and the task closes directly (or reopens with the failure logged); nothing is parked. Otherwise, for each task issue with `$L_PENDING`:

1. Compute age: `(now - pending_since_timestamp)` in hours (read from the label-change timestamp in the issue events).
2. If age > `$PV_MAX_AGE`: set `$L_NEEDS_OPERATOR`, post steward comment: "Pending-verification for {age}h — exceeds the {PV_MAX_AGE}h SLA. Operator decision required to close or reopen.", add to digest top section. Continue.
3. If age ≤ `$PV_MAX_AGE`: look for a "Done claim" comment on the task issue (format: `### Done claim ...`).
4. **Done claim found**: verify each `## Definition of Done` checklist item against the claim. If all verifiable: post `[Verified]` comment, set `$L_DONE` (skip when empty — closing is the marker), close issue, check off in epic. If any unverifiable: post `[Verification failed]` comment with specifics, remove `pending-verification` label, restore `$L_ACTIVE`.
5. **No done claim and still active**: this task shouldn't be in pending-verification — log a steward comment noting the inconsistency, restore `$L_ACTIVE`.

### Step 3b: Autonomy triage (per project, per actionable task)

Classify the project's next actionable task:

- **engineering issue** (standard §18): the task is listed in the epic's `## Engineering issues` section (or its number appears as an issue `ref` in one of the project's chain mirrors) → **not the steward's to dispatch**, whatever `agent:*` label it carries; it is recorded through **Chain reading** and skipped here. Classify it first, before any of the classes below.
- **auto-dispatch**: has `agent:<fleet-agent>` label (not `agent:$AGENT_NAME`); Trinity available; owner resolvable (through `$FLEET_MAP` when set — an owner absent from the map is **not** resolvable); with `$FLEET_NARRATIVE` set, the manager→owner edge is sanctioned by its §5; **the owner is admitted** (the participation gate, below); no human gate implied → eligible for Trinity dispatch. An unsanctioned edge or an unmapped owner is **needs-human**, with the steward update naming exactly which edge or map entry is missing — an autonomous run never silently violates the permission intent.
- **Participation gate** (standard §20, `$PARTICIPATION_CHECK` = `on`): read the epic body's `## Participation` section — one row per `agent:*` owner, written by `/project-init` and re-checked when an owner is added, each row carrying the eleven requirements as `PASS | FAIL | n/a` cells (or a one-line verdict per agent, `admitted` / `not admitted: <rows>`). An owner **absent** from the table, or whose row carries any `FAIL`, is **not admitted**: the task is not dispatched, the digest lists it once under **Needs operator** as `owner not admitted: <agent> (<failed rows, or "no participation row">) — <n> task(s) waiting`, and the project gets **one** `$L_NEEDS_OPERATOR` steward update naming the agent and the rows, never one per task. A later sweep that finds the row passing dispatches normally. `off`, or an epic with no `## Participation` section under a pre-rev-2 standard, = dispatch as before, and the digest's **Carry-over + mode** says "participation check: off / no table".
- **auto-inline**: has `agent:$AGENT_NAME`; fits the remaining run budget (~15 min); touches only reading/analysis, workspace writes, or GitHub comments (no email, no external spend, no gated external effects) → execute it this run.
- **needs-human**: everything else (missing owner, judgment call, gated external effect, human approval required) → `$L_NEEDS_OPERATOR` + digest.

### Step 3c: Open-loop pass (Invariant 7 — standard §14)

Two sweeps, both cheap, both run every material run. Neither ever contacts anyone outside the registry.

**Outbound — loops the operator owes other people or agents.** Fetch every open task carrying a `waiting-on:*` label. `gh issue list` sorts by most-recently-updated and silently truncates at `--limit`, and a long-standing loop is by definition among the *least* recently updated issues — so a cap near the registry's open-issue count drops exactly the loops this pass exists for (seen live 2026-10-06: 5 of 6 standing loops missed at `--limit 100`). `--limit 1000` comfortably exceeds a busy tracker; raise it if the registry grows past that:
```bash
gh issue list --repo "$REGISTRY" --state open --json number,title,labels,url,updatedAt --limit 1000 \
  --jq '[.[] | select(any(.labels[].name; startswith("waiting-on:")))]'
```

For each, resolve the actor from the label and the loop's age from `state.json.open_loops` (falling back to the date on the issue's `### Waiting on` comment, else the label-application event). Then:

| Age since asked | Action |
|---|---|
| < 3 days | List it in the digest's **Your open loops** section with its age. No nudge, no notification. |
| ≥ 3 days, and ≥ 7 days since the last nudge | Draft a short, sendable follow-up message to the actor (2–4 sentences: what was asked, when, why it matters now, what response closes it) and put it in the digest verbatim under that loop. Record `last_nudge` in `state.json.open_loops`. |
| ≥ 14 days | Set `$L_NEEDS_OPERATOR`, post one steward update asking the operator to chase harder, drop it, or route around it. Keep listing it. **Never auto-drop a loop.** |

Detect closure while you're here: if the task's comments show the awaited answer arrived (an `### Agent report`, a `### Loop closed`, or the operator's own comment saying it landed), post `### Loop closed YYYY-MM-DD — answered` per §7, remove the `waiting-on:*` label, drop the state entry, and note the close in the digest. A close nobody recorded reads exactly like a loop nobody remembered.

**Never send the nudge.** The steward drafts; the operator sends. Emailing a client, vendor, or outside colleague on the operator's behalf is out of scope for this skill under every configuration.

**Inbound — loops this agent owes the operator.** For every open `$L_NEEDS_OPERATOR` item, count how many digests have carried it since the ask was posted. At two or more, promote it to the top of the digest's **Needs operator** section with the age stated plainly ("asked 9 days ago, 4 digests"). An ask is never retired for going stale — it gets louder, not quieter.

**The project's own asks age too** (standard §23.5). Two more kinds of loop enter the same ladder, with no label on any issue (their record is the chain ledger and the epic body):
- a **chain run parked at `needs-operator`** (Chain reading item 3) — actor = the operator, asked_at = the run-log entry's timestamp; it sits in **Needs operator** from day 0 and is promoted after two digests like any ask;
- an **open by-hand setup row** — a row of the epic's `## Setup` table (standard §19 item 4) marked `by hand` whose probe still reads unresolved, or that a chain run-log names as what the next step waits on (a token, a grant, a vault unlock, a merge) — actor = whoever the row names (the operator unless it names someone outside the fleet), listed in **Your open loops** with its age from the row's date (else the epic's last edit), the 3 / 7 / 14-day ladder applied as for a `waiting-on:*` task, the drafted nudge being the one sentence that unblocks it ("grant X on Y", "paste the token into Z").
Both are tracked in `state.json.open_loops` with `kind: chain-ask | setup-row` and a `key` (chain folder, or `setup:<row>`), so a lost state file rebuilds them from the ledgers and the epic body on the next sweep. In the retrospective behind rev 2 the longest waits were exactly these and never reached a digest, while two unrelated loops were aged in sixty of them.

### Step 4: Act (deterministic priority order, per project)

Take exactly one action per project, in this order (an **engineering issue** is never the action — Step 3b classified it out; its state is written by Chain reading, in the same steward update as whatever action this list picks):

1. **All success criteria checked** → post a closure-proposal steward update, flag for digest. Do not close the epic (closure is the operator's call).
2. **`$L_NEEDS_OPERATOR` or `$L_BLOCKED` already set** → no action; include in digest with age.
3. **auto-dispatch, no open dispatch, dispatch budget left, owner admitted** (Trinity available):
   ```
   a. mcp__trinity__get_agent_health(<agent>)
   b. If healthy: resolve the callable name — with $FLEET_MAP set, the owner's `deployed_name` in the map
      (else the last segment of its `ref:`); otherwise the logical name
   c. mcp__trinity__chat_with_agent(<agent>, <standard brief from the standard's §10>). With $FLEET_NARRATIVE
      set and its §3b ownership matrix listing *consulted* agents for the task's domain, add one Context line
      naming them (the owner seeks their input before calling it done); mention outcomes to the domain's
      *informed* agents in the digest. Etiquette only — never a gate, never an extra dispatch.
      The call answering `status: pending_approval` ran nothing (the owner's skill awaits a person's approval):
      post it on the task issue as waiting on approval, add no tracker entry, never re-send. `status: refused`
      or `inter_agent_depth_exceeded` → `$L_BLOCKED` + steward comment + digest. A refusal with
      `code: skill_not_granted` (ent#662 — the owner got that playbook from the skills library; an edge covers
      only the skills it declares itself) names the exact grant in the comment and the digest's operator
      section: *grant `<skill>` on `<agent>` to `<this agent>`* — the fix is that admin grant, never a re-send.
   d. Post dispatch receipt on the task issue
   e. Add tracker entry to open_dispatches: {project_slug, task_number, agent, sent_at, execution_id}
      (execution_id from the call's receipt, when it carries one)
   ```
   If unhealthy: `$L_BLOCKED` + steward comment + digest.
4. **auto-dispatch, Trinity unavailable (triage-only mode)**: note in digest that dispatch was skipped; task remains open.
5. **auto-inline, run budget left**: execute the task now; post result as agent-report comment on the task issue; close if DoD met; check off in epic. Max one inline task per run.
6. **needs-human**: set `$L_NEEDS_OPERATOR`, post one steward update saying exactly what decision is needed.
   **Wait ≠ decision.** If what's missing is a *response from someone outside the registry* rather than a call only the operator can make, this is an open loop, not a decision: create the label idempotently, apply it, post the `### Waiting on` comment (§7), and let Step 3c age it. Don't spend a `needs-decision` on a wait — that's how a decision queue turns into noise the operator stops reading.
   ```bash
   gh label create "waiting-on:$ACTOR" --repo "$REGISTRY" --color "d4c5f9" \
     --description "Open loop: awaiting $ACTOR" 2>/dev/null || true
   gh issue edit "$ISSUE" --repo "$REGISTRY" --add-label "waiting-on:$ACTOR"
   ```
7. **Next task exists but no actionable path**: if active project with zero tasks, draft 1–3 candidate next tasks as a proposal in a steward comment, set `$L_NEEDS_OPERATOR`.
8. **Nothing to do** (work in flight, within staleness thresholds) → no comment, no label change. Silence is valid.

Post at most **one** steward update comment per project per run, and only if something changed since the last one — a chain's movement (Chain reading item 6) counts as a change, and the chain lines ride in that same comment.

### Step 5: Quarantine pass (Invariant 6)

**Skip this step when `$QUARANTINE` is `off` or `$L_UNCLASSIFIED` is empty** — a repo whose `project_files/` legitimately holds non-project folders (build chains, scratch) opts out in §0 rather than having epics stubbed for them. Otherwise, list workspace folders and check each against the registry — **`project_files/` only, never the canon clone** (standard §9/§15: a canon-placed project is registered by its epic, never discovered from a folder; a `projects/<slug>/` in canon without a charter is the canon linter's `project-envelope` finding, not a quarantine case):
```bash
ls -d project_files/*/ 2>/dev/null | sed 's|project_files/||;s|/||'
```

A folder is registered when it has a `project:<slug>` epic **or** a `project.md` whose mode resolves to internal (standard §16) — skip those. For each remaining folder `<slug>`, create a quarantine epic (with `$REGISTRY` set):
```bash
gh issue create --repo "$REGISTRY" \
  --title "[Project] $SLUG (unclassified)" \
  --label "project,project:$SLUG,$L_UNCLASSIFIED" \
  --body "## Goal\nAuto-stubbed from unregistered workspace folder `project_files/$SLUG/`. Classify this project or close this epic.\n\n## Current status\n(maintained by /project-steward)"
```

With `$REGISTRY` = `none`, quarantine is a stub charter instead — `tracking: internal`, `status: paused`, `tldr: "(unclassified) project_files/$SLUG/ — classify or remove"`, `owner:` this agent — which keeps it out of every sweep until someone classifies it.

Batch these into one digest line: "N unclassified folder(s) auto-stubbed: <names>". Never create per-item notifications.

### Step 6: Write the digest (material runs only)

Skipped entirely on no-op runs. One file per day — `$STATE_DIR/digests/YYYY-MM-DD.md` — created on the first material run and updated by later ones (append a `## Run HH:MM UTC` section).

Open with the **closing statement** (standard §14a) — three lines, before any section: what is now true, what is waiting on the operator, and what the steward will do next unprompted. A digest that opens with a table of statuses makes the operator do the reading; one that opens with these three lines has already closed the loop.

**The evening brief (standard §23.2, ruling D3) — once a day, before the sections.** When `$BRIEF_UTC` is set and this is the first sweep at or after that hour UTC today (`state.json.last_brief_date` ≠ today), the run is material and the digest's run section opens, right after the closing statement, with `## Evening brief YYYY-MM-DD` in two halves:

1. **Decisions and tonight's defaults** — every open decision, one line each: the `$L_NEEDS_OPERATOR` items, every chain run parked with its question, every pending-verification task past `$PV_MAX_AGE`, every closure proposal — each with the steward's **recommendation** and the **default the fleet will run overnight if nothing is said** (for a parked chain question: the planner's recommended answer the run-log records, or "stays parked"; for a needs-operator task: "stays parked"; for a pending-verification: "stays open"). The operator overrules in the morning; nothing in this half is acted on by the steward itself beyond what Step 4 already did.
2. **Access needed tonight** — every token, grant, vault item, 1Password unlock, merge, account or by-hand setup row the night's queued work will need, so it is provided in one sitting: gathered from (a) each chain mirror's next steps (an issue at `pr` or `validate` waiting on a merge; a `needs-operator` whose question is an access; the run-log's newest "waiting on" line), (b) the epic's `## Setup` rows marked `by hand` that still read unresolved, (c) the open `waiting-on:*` loops and the setup-row loops of Step 3c, (d) the dispatch queue (`open_dispatches` and the tasks Step 4 would dispatch next, with the credentials their owners' `## Participation` rows list as unresolved). One line each: *what*, *for which step*, *who provides it*. Empty is written as "nothing — the night needs no access from you"; both overnight stalls in that retrospective were an access nobody had listed.

The brief is written once per day: set `state.json.last_brief_date` to today in Step 7 and never write a second one, even on later material runs that day (they append their run sections as usual). On Trinity the brief is also sent to the operator with `mcp__trinity__send_notification` (the digest path linked) — it is the one notification of the day that goes out even when nothing crossed a threshold, because its purpose is the night.

Then the sections:

- **Needs operator** (top): each `$L_NEEDS_OPERATOR` item with the one decision or action required, and each chain run parked at `needs-operator` with its question (Chain reading item 3); items unanswered across 2+ digests come first with their age stated; owners not admitted by the participation gate (Step 3b) with the failed rows
- **Your open loops**: every `waiting-on:*` task and every setup-row loop (Step 3c), oldest first — actor, age, and the one sentence that would close it; loops past 3 days carry the drafted follow-up message verbatim, ready for the operator to send
- **Chains**: one line per chain run — `<chain>: <status>, <n> issues (<steps>), PRs <list>, validations <list>, cost $<n>` — and the outcomes new since the last sweep; "read from report" when the folder was not visible
- **Stalls**: every chain execution queued past `$CHAIN_STALL_MIN` minutes without a start, and every `dispatch_health` entry not yet reported — chain, ref, step, agent, minutes
- **Blocked**: blocker + age; container-only state per ref (`ahead <n>` / dirty tree — not on GitHub yet, standard §22.7)
- **Pending-verification**: items waiting, age vs max-age SLA
- **Dispatched this run**: agent, task, issue link
- **Verified this run**: task, pass/fail
- **Reconciled**: agent reports relayed since last run
- **Loops closed**: loops that resolved since the last digest, and how (answered / dropped / routed around)
- **Worked inline**: tasks executed inline, result links
- **Quarantine**: N folders stubbed
- **Healthy/quiet**: one line each
- **Carry-over + mode**: projects not reviewed; note if triage-only; platform mode on or off, and any platform-tracked project skipped because the platform could not be reached; one line per canon-placed project whose clone could not be read (`/canon-doctor`) or whose charter `status:` disagrees with the epic label; participation check on / off / no table; chains whose folder and report were both unreadable

If (and only if) there are needs-operator items (a parked chain run included), blockers, a new stall, past-max-age pending-verification, a loop crossing a nudge threshold, the evening brief, or errors: send a short summary via `mcp__trinity__send_notification` (when Trinity available) linking the digest path. Standing open loops that crossed no threshold this run stay in the digest without a notification — the list is always visible, the interruption is not.

**Results the operator personally asked for go to the operator** (standard §14a.4): when this run finished work the operator initiated by name, `send_notification` with the outcome, even on an otherwise quiet day. The issue log is the record; the notification is the loop closing.

### Step 7: Write updated state

1. Update `$STATE_DIR/state.json`: `last_run`, `carry_over`, `open_dispatches`, `open_loops` (chain asks and setup rows included, with their `kind` and `key`), `chain_seen` (the chain state just recorded, per chain folder), `last_brief_date` (today, only when the brief was written this run).
2. Prepend one summary line to `$STATE_DIR/run_log.txt`:
   `YYYY-MM-DD HH:MM UTC | reviewed N | dispatched N (not admitted N) | verified N | inline N | needs-operator N | loops N (nudged N, closed N) | chains N (moved N, stalls N, parked N) | brief yes/no | quarantine N | mode`
3. Push steward state (scoped — never add any other path). The registry files of **agent-level internal projects this run changed** are part of the commit too — they are the registry, not scratch — added by exact path:
   ```bash
   git add "$STATE_DIR" $INTERNAL_WS_TOUCHED && \
   git commit -m "steward: run $(date -u +%Y-%m-%d)" && \
   (git push origin main || (git pull --rebase --autostash origin main && git push origin main))
   ```
   `$INTERNAL_WS_TOUCHED` = each `project_files/<slug>/` whose task files, `log.md` or charter this run wrote (empty when none).
4. **Canon-placed internal projects this run changed:** publish them once with `/canon-publish` (the shared `projects/` zone, lint-gated). If the publish is refused, leave the local changes, name the project in the digest, and let the next run retry — never force.
   If push fails, log it and stop — state is preserved locally; the next run's pull will carry it.

## Error recovery

- **`gh` auth/network failure**: abort before any writes; prepend a `FAILED` line to `$STATE_DIR/run_log.txt`; attempt `mcp__trinity__send_notification` if available.
- **Trinity MCP absent**: continue in triage-only mode; record in digest. Dispatch state is untouched — next healthy run resumes.
- **Single project fails mid-review**: post a steward update describing the defect, set `$L_NEEDS_OPERATOR`, continue with the next project.
- **Partial run (interrupted)**: safe to re-run — the changed-since-last-update check and dispatch tracker make all writes idempotent.
- **State file corrupt**: move to `state.json.bak-YYYY-MM-DD`, rebuild defaults, rebuild `open_dispatches` conservatively from recent dispatch receipt comments that lack a matching agent-report relay, and rebuild `open_loops` from the live `waiting-on:*` labels (ages from each issue's `### Waiting on` comment) plus the chain mirrors (parked runs) and the epics' `## Setup` rows. `chain_seen` rebuilds empty, so the next sweep re-records each chain's current state once (one repeated outcome entry at most); `last_brief_date` rebuilds null, so at most one extra brief is written that day. Nudge timing resets; no loop is lost.
- **A chain mirror will not parse** (`ledger-entry.yaml` malformed, or a run-log with no dated entries): read the chain from its latest `trinity_pm.build_chain` report when Trinity is available; otherwise name the chain in **Carry-over + mode** and skip it this run — never edit a chain folder, it is `/build-chain`'s.
