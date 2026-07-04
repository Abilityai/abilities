---
name: project-steward
description: Autonomous sweep of all fleet-managed projects (GitHub epics labeled "project" in the registry repo named by fleet/project-standard.md). Reconciles outstanding agent dispatches, reviews each project against the standard, dispatches next work to explicitly-labeled owner agents via Trinity, escalates stalls, and writes a daily digest. Use manually to force a sweep, or ask "what's the state of my projects".
automation: autonomous
schedule: "0 7-19/2 * * 1-5"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__get_agent_health, mcp__trinity__chat_with_agent, mcp__trinity__get_chat_history, mcp__trinity__send_notification
effort: high
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-03
  author: orchestrator
  changelog:
    - "1.1: Ownership-matrix awareness — when orchestration.md §3b lists C/I agents for the task's domain, note C in the dispatch brief and address I in the digest; advisory etiquette only, never a gate or an extra dispatch"
    - "1.0: Initial bundle version — adopted from a production orchestrator's project-steward v1.6 (six field-hardened releases: gh bootstrap, GH_TOKEN from the origin remote, REST-labels scope pre-flight, no-op discipline for high-frequency cadence, time-based dispatch thresholds, GitHub-as-state-carrier) and universalized: registry repo + operator read from fleet/project-standard.md, needs-operator label, inline class = agent:<self>, owners resolved via system-map deployed_name and checked against orchestration.md §5 before dispatch"
---

# Project Steward

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-steward vX.Y — recent: <summary>`. Then proceed.

## Purpose

Keep every fleet-managed project moving without the operator having to push it. Each run:
reconcile what agents reported back, review every open project epic for drift and
staleness, dispatch the next unit of work to its explicitly-named owner agent, and
surface only what genuinely needs the operator in a daily digest.

This playbook is the **sole writer of the project issue log** (see
`fleet/project-standard.md` §2). It never asks a human anything mid-run: anything
ambiguous gets `status:needs-operator` and moves on.

**Deliberate non-composition:** this playbook does **not** invoke `/orchestrate` to
dispatch. Autonomy is transitive — `/orchestrate` disambiguates weak matches
interactively, which would hang an unattended run. The steward needs no routing judgment:
it dispatches only to owners *explicitly named* by `agent:*` labels, resolved through the
map and checked against the §5 boundaries (standard §9).

## Runtime resolution (do this first, once per run)

- **`$REGISTRY`** = the registry repo named in `fleet/project-standard.md` §1 (the
  "Registry" row, e.g. `Org/repo`). Every `gh` command below targets it.
- **`$SELF`** = this agent's logical name: `name:` from `template.yaml`, else the CLAUDE.md
  agent name (same convention as `/discover-agents`' `generated_by`). Tasks labeled
  `agent:$SELF` are the inline class — never dispatched via Trinity (that would loop).

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Fleet project standard (conventions) | `fleet/project-standard.md` | Yes | No |
| Fleet system map (agent registry, deployed names) | `fleet/system-map.yaml` | Yes | No |
| Orchestration narrative (§5 dispatch boundaries) | `fleet/orchestration.md` | Yes | No |
| Project epics + task issues | `$REGISTRY` via `gh` | Yes | Yes (labels, comments, checklists) |
| Steward state (cursor + dispatch tracker) | `fleet/project-steward/state.json` | Yes | Yes |
| Daily digests | `fleet/project-steward/digests/YYYY-MM-DD.md` | No | Yes |
| Run log (newest first) | `fleet/project-steward/run_log.txt` | Yes | Yes |
| Fleet agents (health, chat) | Trinity MCP (`mcp__trinity__*`) | Yes | dispatch messages only |

## Runtime environments

This playbook runs in two places; behavior is identical except for git:

- **Local (the operator's machine)**: the local working copy of the managing agent's repo.
- **Trinity (the deployed twin, schedule `project-steward-sweep`)**: the container's git clone.

**GitHub is the sole state carrier.** Every run starts with a pull and ends by committing
and pushing ONLY `fleet/project-steward/` (state, digests, run log, inline outputs) — never
any other path. This keeps local and Trinity runs from diverging. The registry itself
(issues, labels) lives on GitHub anyway and needs no sync.

**Workspaces may be local-only.** If `project_files/` is gitignored (standard §1), Trinity
runs have NO project workspaces. On Trinity: treat the epic body as the authoritative
context, skip workspace reads without complaint, and write any inline-task output to
`fleet/project-steward/outputs/<slug>/` (tracked, pushed) — then say so in the task
comment so the operator or a local run can land it into the workspace later.

## Prerequisites

- **Bootstrap `gh` CLI** (do this before the auth check): if `gh` is not on PATH, download
  it to `~/.local/bin/gh` and `export PATH="$HOME/.local/bin:$PATH"`. This is idempotent.
  ```bash
  if ! command -v gh &>/dev/null; then
    export PATH="$HOME/.local/bin:$PATH"   # prior bootstrap may have installed here
  fi
  if ! command -v gh &>/dev/null; then
    mkdir -p ~/.local/bin
    curl -sL "https://github.com/cli/cli/releases/download/v2.63.2/gh_2.63.2_linux_amd64.tar.gz" | tar xz -C /tmp/
    cp /tmp/gh_2.63.2_linux_amd64/bin/gh ~/.local/bin/gh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  ```
- **Derive `GH_TOKEN` from the git remote (critical on Trinity)**: Trinity injects the
  agent's PAT into the origin remote URL — that is the ONE authoritative credential. A
  stale `~/.config/gh/hosts.yml` from an earlier bootstrap can shadow it with an old token
  (in production this caused three consecutive 403 runs). Exporting `GH_TOKEN` wins over
  hosts.yml in `gh`'s precedence, so always run:
  ```bash
  if [ -z "$GH_TOKEN" ]; then
    export GH_TOKEN=$(git remote get-url origin | sed -nE 's#https://[^:/@]+:([^@]+)@github.com/.*#\1#p')
  fi
  ```
  Never run `gh auth login` and never write hosts.yml — env-only keeps the credential in
  lockstep with git across PAT rotations.
- **PAT issues-scope pre-flight**: after bootstrapping `gh`, test that the issues API is
  accessible before writing any state. **Do not use `gh issue list --label ...`** — a
  label-filtered query returns `[]` (no error) even when the PAT lacks Issues scope. Use
  the REST labels endpoint instead, which 403s correctly on missing scope:
  ```bash
  gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1
  ```
  If this returns `Resource not accessible` or any HTTP 403/4xx: abort per Error Recovery
  immediately (before writing run_log, state, or digest — except for the FAILED log entry
  itself). Cause: PAT lacks `Issues: read` permission. Fix: update the PAT or configure
  `GH_TOKEN` with a token that has Issues scope.
- `gh auth status` succeeds with repo scope on `$REGISTRY` (on Trinity, the agent PAT
  should provide this via `GH_TOKEN`/git credentials). If auth fails entirely: abort per
  Error Recovery.
- Trinity MCP reachable. If not: run in **triage-only mode** (no dispatch, no
  reconciliation of chat replies; note it in the digest and retry next run).
- `fleet/project-standard.md` exists. If not: abort per Error Recovery.

## No-op discipline (high-frequency cadence)

This playbook runs every 2 hours during working hours — most runs will find nothing to do,
and a no-op run must be nearly free and leave no trace:

- After Step 1 (registry pull) and the Step 2 reconciliation scan, compute whether ANY
  actionable condition exists: an unreconciled dispatch with a reply waiting or past a
  time threshold, an active epic whose next task is dispatchable/inlinable, a staleness
  breach, a closure candidate, or registry changes since `last_run` (new/edited epics,
  label changes by the operator).
- **If none: stop.** Update `last_run` in the local `state.json` only — do NOT commit, do
  NOT write or update a digest, do NOT notify, do NOT post any comment. The next material
  run's commit will carry the state file.
- Overlap is tolerated, not managed: if a run fires while the previous is still executing,
  Trinity queues it; idempotency (comment-only-on-change, dispatch tracker) makes a
  back-to-back duplicate run a no-op.

## Hard limits (45-minute rule)

- Max **10 projects** reviewed per run. If more are open, review `priority:p1` first, then
  least-recently-updated; write the remainder to `state.json.carry_over` and start there next run.
- Max **3 dispatches** per run, max 1 open dispatch per project.
- Per-project review budget: read the epic, its open task issues, the last steward update,
  and the workspace `project.md`. Do not deep-read whole workspaces.

## Process

### Step 1: Read current state

0. Sync the workspace: `git pull --rebase --autostash origin main`. If the pull fails,
   continue anyway (the registry is on GitHub, only the standard/state may be slightly
   stale) and note it in the digest and run log.
1. Read `fleet/project-standard.md` — conventions are loaded fresh each run. Resolve
   `$REGISTRY` and `$SELF` (see Runtime resolution).
2. Read `fleet/project-steward/state.json` (create with empty defaults if missing:
   `{"last_run": null, "carry_over": [], "open_dispatches": []}`).
3. Pull the registry:
   ```bash
   gh issue list --repo "$REGISTRY" --label project --state open \
     --json number,title,labels,updatedAt,body --limit 50
   ```
4. Detect Trinity MCP. Absent → set `MODE=triage-only`.

### Step 2: Reconcile outstanding dispatches (skip in triage-only mode)

For each entry in `open_dispatches`:

1. `get_chat_history` with the dispatched agent; look for a reply after `sent_at`.
2. **Reply found**: post an "Agent report" relay comment on the task issue (format per
   standard §6), check the task off in the epic checklist if done (close the task issue),
   or leave open with the findings noted. Remove the tracker entry.
3. **No reply and 6+ hours since `sent_at`**: send one re-ping via `chat_with_agent`
   referencing the original dispatch; record `repinged_at`. (Time-based, not run-based —
   this playbook runs every 2 hours.)
4. **No reply and 24+ hours since `sent_at`** (re-ping already sent): set the epic
   `status:blocked`, post a steward comment naming the silent agent, remove the tracker
   entry, flag for digest.
5. **No reply, under threshold**: leave the tracker entry alone — not actionable.

### Step 3: Review each project (uniform pattern, max 10)

Build the review list: `carry_over` first, then `priority:p1`, then least-recently-updated.
Skip `status:paused` epics entirely. For each project:

1. Read the epic body + comments since the last steward update, open `project:<slug>` task
   issues, and the workspace `project.md` (local runs only — absent on Trinity, where the
   epic body is authoritative).
2. Compute: days since last activity, open/done task counts, current `status:*` label,
   whether an open dispatch exists.
3. Apply the standard's staleness policy (§8): 7 days idle → investigate and act;
   14 days → `status:needs-operator` + top of digest.

`ultrathink` here — deciding the true state of a project and its single best next action
is the judgment-heavy core of this playbook.

### Step 4: Autonomy triage, then act (deterministic, per project)

First classify the project's next actionable task into one of three autonomy classes:

- **auto-dispatch**: has an `agent:<fleet>` label, owner resolvable in
  `fleet/system-map.yaml`, the manager→owner edge is sanctioned by `orchestration.md` §5,
  agent healthy, no human gate implied by the task body → eligible for Trinity dispatch.
- **auto-inline**: `agent:$SELF`, fits the remaining run budget (~15 min), and touches only
  reading/analysis, workspace writes, or GitHub comments (no email sends, no CRM writes,
  no spend, nothing the fleet gates on humans) → the steward executes it in this run and
  posts the result as an agent-report comment.
- **needs-human**: everything else (missing owner, unsanctioned §5 edge, gated external
  effect, judgment call) → `status:needs-operator` + digest.

Then take exactly one action, in priority order:

1. **All success criteria met** → post a closure-proposal steward update, flag for digest.
   Do not close the epic (closure is the operator's call).
2. **`status:needs-operator` or `status:blocked` already set and unresolved** → no action;
   include in digest with age.
3. **auto-dispatch class, no open dispatch, dispatch budget left, agent healthy
   (`get_agent_health`)** → dispatch: resolve the owner's live callable name via the map
   (`deployed_name`, else last segment of `ref:` — per standard §9), send the standard
   brief (§9) via `chat_with_agent`, post a dispatch receipt on the task issue, add a
   tracker entry. If `orchestration.md` **§3b** (ownership matrix) lists **consulted**
   agents for the task's domain, add one Context line to the brief naming them (the owner
   should seek their input before calling it done); mention outcomes to the domain's
   **informed** agents in the digest. Advisory etiquette only — never a gate, never an
   extra dispatch.
4. **auto-inline class, run budget left** → execute the task now, post the result as an
   agent-report comment on the task issue, close it if the definition of done is met, and
   check it off in the epic. Max one inline task per run.
5. **Next task exists but owner is missing/ambiguous, edge unsanctioned, or agent
   unhealthy** → set `status:needs-operator` (missing owner / §5 edge) or `status:blocked`
   (unhealthy agent), post a steward update saying exactly what is needed. Never guess an
   owner; never dispatch across an edge §5 denies.
6. **Active project with zero defined tasks** → draft 1-3 candidate next tasks from the
   epic goal + workspace into a steward comment (as a proposal, not task issues), set
   `status:needs-operator`.
7. **Nothing to do** (work in flight, or waiting within staleness thresholds) → no comment,
   no label change. Silence is a valid outcome.

Then update labels and post at most **one** steward update comment per project, and only
if something changed since the last one (compare against the most recent
`### Steward update` comment — re-runs on the same day must be no-ops).

### Step 5: Write the digest (material runs only)

Skipped entirely on no-op runs. One file per day — `fleet/project-steward/digests/YYYY-MM-DD.md` —
created by the day's first material run and updated in place by later ones (append a
`## Run HH:MM` section rather than rewriting history). Contents:

- **Needs operator** (top): each `status:needs-operator` item with the one decision required.
- **Blocked**: blocker + age.
- **Worked autonomously**: inline tasks executed this run, with result links.
- **Dispatched today**: agent, task, issue link.
- **Reconciled**: agent reports relayed since last run.
- **Healthy/quiet**: one line each.
- **Carry-over + mode**: projects not reviewed this run; note if triage-only.

If (and only if) there are needs-operator items, blockers, or errors: send a short summary
via `mcp__trinity__send_notification` linking the digest path. Quiet days produce a digest
file but no notification.

### Step 6: Write updated state

1. Update `state.json`: `last_run`, `carry_over`, `open_dispatches` (with `sent_at`, `repinged_at`).
2. Prepend one summary line to `fleet/project-steward/run_log.txt`:
   `YYYY-MM-DD HH:MM | reviewed N | dispatched N | inline N | reconciled N | needs-operator N | mode`.
3. Push steward state (scoped — never add any other path):
   ```bash
   git add fleet/project-steward && git commit -m "steward: run $(date +%Y-%m-%d)" \
     && (git push origin main || (git pull --rebase --autostash origin main && git push origin main))
   ```
   If the push still fails, log it and stop — state is preserved locally in the working
   copy and the next run's pull/rebase will carry it. Inline-task outputs written under
   `fleet/project-steward/outputs/<slug>/` ride the same scoped commit. On local runs an
   inline task may write directly into the project's `project_files/<slug>/` workspace
   (if it is local-only per standard §1, it is never committed — the ignore rules keep it out).

## Completion Checklist

- [ ] Every reviewed epic has exactly one `status:*` label
- [ ] Every dispatch has: receipt comment + tracker entry + healthy-agent check + sanctioned §5 edge
- [ ] No steward comment posted where nothing changed (idempotency held)
- [ ] Digest written; notification sent only if warranted
- [ ] `state.json` and `run_log.txt` updated
- [ ] Run completed under 45 minutes (else halve the project cap via Self-Improvement)

## Error Recovery

- **`gh` auth/network failure**: abort before any writes; prepend a `FAILED` line to
  `run_log.txt`; attempt `send_notification` telling the operator the steward cannot reach
  GitHub.
- **Trinity MCP absent or erroring**: continue in triage-only mode (labels, comments,
  digest still happen); record it in the digest and `run_log.txt`. Dispatch state is
  untouched, so nothing is lost — next healthy run reconciles.
- **Single project fails mid-review** (malformed epic, deleted folder): post a steward
  update describing the defect, set `status:needs-operator`, continue with the next project.
- **Partial run** (interrupted): safe to re-run — Step 4's changed-since-last-update check
  and the dispatch tracker make all writes idempotent.
- **State file corrupt**: move it to `state.json.bak-YYYY-MM-DD`, rebuild defaults, and
  rebuild `open_dispatches` conservatively from the most recent "Dispatched" receipts that
  lack a matching "Agent report" comment.

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Were there friction points, unclear steps, or inefficiencies?
- [ ] **Identify improvements**: Could error handling, step ordering, or instructions be clearer?
- [ ] **Scope check**: Only tactical/execution changes — NOT changes to core purpose or goals
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md with the specific improvement
  - [ ] Keep changes minimal and focused
  - [ ] Bump `metadata.version` and prepend a changelog entry
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/project-steward/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(project-steward): <brief improvement description>"`
