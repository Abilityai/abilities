---
name: project-steward
description: Autonomous sweep of all managed projects per the project standard (PROJECT_STANDARD.md at the repo root, or fleet/project-standard.md on an orchestrator — its §0 block configures registry, label vocabulary, state directory and fleet hooks) — external projects tracked in GitHub Issues and internal projects tracked in their own workspace files (standard §16), with the same policy for both. Verifies pending-verification claims against Definition of Done, dispatches next work to explicitly-labeled owner agents (Trinity when available; triage-only when not), escalates stalls per the staleness policy, sweeps open loops (ages every waiting-on item and drafts the operator's follow-ups), runs the quarantine classification pass, and writes a digest that closes the loop with the operator. Never asks a human anything mid-run.
automation: autonomous
schedule: "0 7-19/2 * * 1-5"   # default: every 2h, weekdays UTC — adjust, or delete this line for manual-only (the installer substitutes your choice)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__get_agent_health, mcp__trinity__chat_with_agent, mcp__trinity__get_execution_result, mcp__trinity__get_chat_history, mcp__trinity__send_notification
effort: high
user-invocable: true
metadata:
  version: "1.8"
  created: 2026-07-30
  author: add-project-management
  changelog:
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

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-steward v1.8 — recent: gate results and execution-id-aware re-pings`. Then proceed.

## Purpose

Keep every managed project moving without the operator having to push it. Each run:
1. Reconcile outstanding dispatches (read agent replies, post relay comments, verify done claims)
2. Review every open project epic: verify pending-verification tasks, dispatch next work, escalate stalls
3. Sweep open loops (Invariant 7): age every `waiting-on:*` task, draft the operator's nudges, keep unanswered asks alive
4. Run the quarantine pass: auto-stub unregistered workspace folders
5. Write the digest (material runs only), opening with what the operator now knows and what is waiting on them

**This skill never asks a human anything mid-run.** Anything ambiguous gets `$L_NEEDS_OPERATOR` and moves on. It is the sole writer of steward update comments on GitHub issues.

**It does close loops, in both directions (standard §14).** Nothing it touched ends in silence: work the operator initiated is reported back to the operator, an unanswered ask is re-surfaced with its age rather than dropped, and every loop parked on a third party is aged in the digest with a ready-to-send nudge. It drafts those nudges; **it never sends them** — contacting a client, vendor, or outside colleague is the human's act, always.

**Deliberate non-composition:** this skill dispatches only to owners explicitly named by `agent:*` labels — no routing judgment. The interactive disambiguation that `/orchestrate` provides would hang an unattended run.

**Trinity is optional.** When Trinity MCP is unavailable, the skill runs in triage-only mode: all registry operations continue; dispatch is skipped and noted in the digest. Nothing is lost.

**Two tracking modes, one steward.** A project's registry is its GitHub epic (external) or its own workspace files (internal, standard §16). Every step below is written for GitHub; for an internal project apply the same step through **Internal projects** (below) — same order, same thresholds, same run budget, same digest. A run may mix both.

## Runtime resolution (do this first, once per run)

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration**. A standard without a §0 block (written before template 1.3) resolves to the defaults below, which are exactly the pre-1.3 behaviour (colon vocabulary, `project-steward/` state, no fleet hooks):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
cfg() { awk -v k="$1" -v d="$2" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$0~p{v=$0;sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
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

**If no standard exists, exit (headless-safe, no prompt) and report: run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Then:
- `$REGISTRY` — `none` means every project is internal: skip the gh prerequisites below entirely. Pre-1.3 standards return it empty: read it from §1 (and `$AGENT_NAME`, `$OPERATOR` from §2, `$PV_MAX_AGE` from §12).
- `$AGENT_NAME` — tasks labeled `agent:$AGENT_NAME` are inline-class, never dispatched (a chat dispatch to yourself would loop).
- **Fleet hooks** (only when §0 sets them): `$FLEET_MAP` is the system map that turns an `agent:<name>` label into the live callable name (`deployed_name`, else the last segment of `ref:`; an owner absent from the map is unresolvable → `$L_NEEDS_OPERATOR`); `$FLEET_NARRATIVE` is the orchestration narrative whose §5 edges gate every dispatch and whose §3b ownership matrix supplies consulted / informed etiquette. Unset = call owners by their logical name, no edge check, no etiquette — the stand-alone behaviour.
- **Workspaces may be invisible to this run** (gitignored `project_files/` on a Trinity container): then the epic body is the authoritative context, workspace reads are skipped without complaint, and an inline task's output is written to `$STATE_DIR/outputs/<slug>/` (tracked, pushed with the state) with the task comment saying so — a local run can land it in the workspace later.
- **Workspace resolver (§15)** — per project, from the epic body, never from the slug:
  ```bash
  WS_SECTION=$(printf '%s' "$EPIC_BODY" | awk '/^## Workspace/{f=1;next} f&&/^## /{exit} f{print}')
  WS_FIELD=$(printf '%s' "$WS_SECTION" | grep -o '`[^`]*`' | head -1 | tr -d '`')          # first backticked path wins …
  [ -n "$WS_FIELD" ] || WS_FIELD=$(printf '%s' "$WS_SECTION" | awk 'NF{print;exit}' | xargs)  # … else the first non-empty line
  case "$WS_FIELD" in
    canon:*) CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $2}' template.yaml 2>/dev/null); CANON=${CANON:-canon}
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

**If none: stop.** Update `last_run` in `$STATE_DIR/state.json` only — do NOT commit, do NOT write a digest, do NOT notify, do NOT post any comment. Quiet runs leave no trace.

## Hard limits (45-minute rule)

- Max **10 projects** reviewed per run. If more are open, review `${L_PRIORITY}p1` first, then least-recently-updated. Write the remainder to `state.json carry_over` and start there next run.
- Max **3 dispatches** per run; max **1 open dispatch per project**.
- Max **1 inline task** executed per run.

## Process

### Step 1: Read current state

1. Sync: `git pull --rebase --autostash origin main` (continue on failure; note it in the digest).
2. Read the standard (resolving runtime variables as above).
3. Read `$STATE_DIR/state.json` (create with empty defaults if missing: `{"last_run": null, "carry_over": [], "open_dispatches": [], "open_loops": []}`). Each `open_loops` entry is `{issue, actor, asked_at, last_nudge, digests_carried}` — bookkeeping only; the `waiting-on:*` labels on GitHub are the truth, so a lost state file costs nudge timing, never a loop.
4. Pull the registry — both modes:
   ```bash
   [ "$REGISTRY" != none ] && gh issue list --repo "$REGISTRY" --label project --state open \
     --json number,title,labels,updatedAt,body --limit 50
   ```
   Internal projects are the charters the standard's §16 finder returns (`charters`) whose `mode_of` is internal and whose `status:` is not `done` — under the top-level canon `projects/` zone, only those whose `owner:` is this agent. For canon-placed ones, `git -C "$CANON" pull --ff-only` first (on failure, read the local copy and say so in the digest).
5. Check Trinity MCP availability.

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

- **auto-dispatch**: has `agent:<fleet-agent>` label (not `agent:$AGENT_NAME`); Trinity available; owner resolvable (through `$FLEET_MAP` when set — an owner absent from the map is **not** resolvable); with `$FLEET_NARRATIVE` set, the manager→owner edge is sanctioned by its §5; no human gate implied → eligible for Trinity dispatch. An unsanctioned edge or an unmapped owner is **needs-human**, with the steward update naming exactly which edge or map entry is missing — an autonomous run never silently violates the permission intent.
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

### Step 4: Act (deterministic priority order, per project)

Take exactly one action per project, in this order:

1. **All success criteria checked** → post a closure-proposal steward update, flag for digest. Do not close the epic (closure is the operator's call).
2. **`$L_NEEDS_OPERATOR` or `$L_BLOCKED` already set** → no action; include in digest with age.
3. **auto-dispatch, no open dispatch, dispatch budget left** (Trinity available):
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
      or `inter_agent_depth_exceeded` → `$L_BLOCKED` + steward comment + digest.
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

Post at most **one** steward update comment per project per run, and only if something changed since the last one.

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

Then the sections:

- **Needs operator** (top): each `$L_NEEDS_OPERATOR` item with the one decision or action required; items unanswered across 2+ digests come first with their age stated
- **Your open loops**: every `waiting-on:*` task, oldest first — actor, age, and the one sentence that would close it; loops past 3 days carry the drafted follow-up message verbatim, ready for the operator to send
- **Blocked**: blocker + age
- **Pending-verification**: items waiting, age vs max-age SLA
- **Dispatched this run**: agent, task, issue link
- **Verified this run**: task, pass/fail
- **Reconciled**: agent reports relayed since last run
- **Loops closed**: loops that resolved since the last digest, and how (answered / dropped / routed around)
- **Worked inline**: tasks executed inline, result links
- **Quarantine**: N folders stubbed
- **Healthy/quiet**: one line each
- **Carry-over + mode**: projects not reviewed; note if triage-only; one line per canon-placed project whose clone could not be read (`/canon-doctor`) or whose charter `status:` disagrees with the epic label

If (and only if) there are needs-operator items, blockers, past-max-age pending-verification, a loop crossing a nudge threshold, or errors: send a short summary via `mcp__trinity__send_notification` (when Trinity available) linking the digest path. Standing open loops that crossed no threshold this run stay in the digest without a notification — the list is always visible, the interruption is not.

**Results the operator personally asked for go to the operator** (standard §14a.4): when this run finished work the operator initiated by name, `send_notification` with the outcome, even on an otherwise quiet day. The issue log is the record; the notification is the loop closing.

### Step 7: Write updated state

1. Update `$STATE_DIR/state.json`: `last_run`, `carry_over`, `open_dispatches`, `open_loops`.
2. Prepend one summary line to `$STATE_DIR/run_log.txt`:
   `YYYY-MM-DD HH:MM UTC | reviewed N | dispatched N | verified N | inline N | needs-operator N | loops N (nudged N, closed N) | quarantine N | mode`
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
- **State file corrupt**: move to `state.json.bak-YYYY-MM-DD`, rebuild defaults, rebuild `open_dispatches` conservatively from recent dispatch receipt comments that lack a matching agent-report relay, and rebuild `open_loops` from the live `waiting-on:*` labels (ages from each issue's `### Waiting on` comment). Nudge timing resets; no loop is lost.
