---
name: project-status
description: "Status for ONE managed project. On a Trinity instance with Projects (standard 3.0, §28–§37) it runs on demand only (/project-status <project id or name>) — reads get_project, every task, list_project_executions, plan.md and charter.md chains: from the project's file space and the build-chain ledgers it can see; reports what moved since the last status, done and remaining, what waits on a person, and the projected finish from the open critical path (blocked_by plus plan order); publishes a Trinity report, links it to the project and sends one notification; writes nothing else on the project. Without Trinity Projects, runs the frozen offline mode (standard 2.x): the daily status of a GitHub-epic or folder project with Trinity asks for what waits on the operator."
argument-hint: "<project id or name | slug>"
automation: autonomous
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__report, mcp__trinity__send_notification, mcp__trinity__list_reports, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__list_project_tasks, mcp__trinity__get_project_log, mcp__trinity__add_project_task_note, mcp__trinity__update_project_task, mcp__trinity__link_to_project, mcp__trinity__list_project_executions, mcp__trinity__get_steward_digest, mcp__trinity__list_platform_files, mcp__trinity__read_platform_file, mcp__trinity__get_report
metadata:
  version: "2.0"
  created: 2026-10-02
  author: trinity-pm
  changelog:
    - "2.0: Standard 3.0 (operator rulings P1–P11, 2026-11-11; §36). On Trinity Projects status runs on demand only — per-project status schedules are retired there, the steward's wake keeps health current. A new first section reads the platform project (get_project, every task, list_project_executions, the steward digest, the log, plan.md and charter.md chains: from the file space, the chain ledgers it can see), computes what moved since the last status (kept in state_dir/outputs/<id>/status/), done and remaining per milestone, what waits on a person, and the projected finish from the open critical path (blocked_by plus plan order); publishes a report, links it with link_to_project kind report, one notification. Read-only on the project otherwise: no asks, no task writes. The old body is kept unchanged as the frozen offline mode"
    - "1.5: Reads the build chain (project standard rev 2 §24.3, ruling R-a 2026-11-04: the steward owns every project's record and the chain is its engineering executor). Step 1 resolves `chain.ledger` and `chain.stall_minutes`; Step 2 reads each chain folder the charter lists under `chains:` (or the epic's `## Engineering issues`) — the committed `ledger-entry.yaml` mirror and the run-log tail, else the latest build_chain report; Moved lists chain steps closed, PRs opened and validations decided; Waiting on you lists the chain's parked needs-operator questions with age and the **merges due** (validated, no longer draft, still open — merges are the operator's, §21.7, and an early merge gets post-merge validation by rule), raised as asks on the deployed agent like every other waiting-on-you item; the projection counts the chain's remaining steps × the observed median step duration; Risks lists stalls (§24.5) and container-only state"
    - "1.4.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.4: Platform mode (ent#788, ruling R38): on a Trinity instance with Projects enabled the daily report and the asks it raises are put on the platform project (link_to_project) so its members find them there; a platform-tracked project is read from the platform's task list and log instead of an epic. Without Trinity nothing changes"
    - "1.3: Fix — the ask request_id used / and #, which Trinity refuses (invalid_request_id), so no ask was ever filed; it is now <slug>:<owner>.<repo>:<N>. Asks respect the atomic caps (title ≤120, ≤5 options of ≤60 chars), dismissed is a fourth ending, and an answer of (something else) no longer flips the issue to active (Trinity dev ed5904906)"
    - "1.2: Promoted from the production orchestrator's local skill into the agent-dev plugin as the sixth project skill (ent#789) — reads the standard through the shared resolver (PROJECT_STANDARD.md or fleet/project-standard.md, §0 Configuration: registry, state_dir, member_repos, label roles), the ledger contract is documented here, a project without a ledger still gets a daily report (progress from the task checklist, no projected date — and says so) instead of failing, the report type is namespaced by the agent name"
    - "1.1: Waiting-on-you items become Trinity asks (operator 2026-10-02: 'that's why we have asks and approvals on trinity') — one idempotent ask_operator per needs-operator issue, approval asks carry the frozen proposal from the issue's Approval needed comment; ended asks are relayed back to the issue and the label flipped. A local user-scoped key cannot raise asks, so this only fires on the deployed agent"
    - "1.0: Initial version — operator ask 2026-10-02 for the builder-agent project (ent#762): 'let me know once a day how this is going and when you will be done'"
---

# Project Status

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-status v2.0 — recent: on Trinity Projects status is read from the platform, on demand only`. Then proceed.

## On Trinity Projects — the only mode there (standard 3.0, §28–§37)

On a Trinity instance with Projects, a project lives in the platform and nowhere else (§28), and `/project-status <project>` runs **on demand only** (§36). The steward's daily wake keeps health current, so no per-project status schedule is kept (§31): a deployment that starts wakes for a project retires that project's `/project-status` schedule in the same change. Any `/project-status` schedule applies to the offline mode only.

This section is read-only on the project. Its one write there is the link to its own report. It writes no task, no note, no health and no log entry, raises no ask, and writes nothing to GitHub. Asks belong to the steward (§34) and to the engineering executor.

### Step 0: Detect

Resolve §0 with the resolver in the offline mode's Step 1. Read only `agent`, `state_dir`, `chain.ledger`, `chain.stall_minutes` and `platform`. No standard file → use the defaults; do not stop. Then call `mcp__trinity__list_projects` once.

- `enabled: true` → run this section.
- `enabled: false`, no such tool, or `platform: off` in §0 → go to **Offline mode** below.
- Refused with `external_audience` or `turn_unknown` → this turn is not an internal one. Stop. Use nothing from the platform and repeat no project detail.

### Step 1: Resolve the project

Match the argument against the `list_projects` result: an exact id first, then the name (case-insensitive). No argument, no match, or more than one → list the projects by name and stop. Set `SPACE=project:<id>` and `OUT=$STATE_DIR/outputs/<id>/status`.

### Step 2: Read (read-only)

- `mcp__trinity__get_project` — goal, status, mode, health, members, agents, steward, any pending proposal.
- `mcp__trinity__list_project_tasks(project_id, status: all)` — every task with its status, assignee, owner, `for_person`, `parent`, `blocked_by`, `refs`, `waiting_on`, `rejections`.
- `mcp__trinity__list_project_executions(project_id)` — the runs behind the project, their duration and cost.
- `mcp__trinity__get_steward_digest` — the open asks on this project, and what waits on verification.
- `mcp__trinity__get_project_log` — the entries since the last status.
- From the file space (`list_platform_files`, `read_platform_file` on `SPACE`): `plan.md` (milestones, their targets, task order, any `Estimate (d)`), and `charter.md` for its `chains:` list.
- **Chain ledgers.** For each folder `chains:` names, read what this run can see, exactly as the offline Step 2 **Chain evidence** says: the folder's `ledger-entry.yaml` and the run-log tail, else the newest `<agent>.build_chain` report (`list_reports`, `get_report`). Read the PRs it names with `gh pr view` (read only). Nothing visible → write `chain ledger not readable from here` under Risks.
- **The last status.** The newest file in `$OUT/`. None → this is the first status; everything open counts as current, nothing as moved.

### Step 3: Compute

- **Moved since the last status:** tasks whose status changed (by the task list against the last file), new tasks, new log entries (`deliverable`, `decision`, `blocker`, `handoff`), chain steps that advanced, PRs opened or merged, runs finished and their cost.
- **Done / remaining:** done tasks over all tasks, parents counted once; the same per milestone when `plan.md` has milestones.
- **Waits on a person:** open tasks with `for_person: true`; tasks in `needs-decision`; tasks with a `waiting_on`; claims in `pending-verification` that only a person may verify (§34.4); a pending proposal on the project; open asks from the steward digest; the chain's parked questions and merges due (as the offline Step 4b defines them, listed only). Each with its age in days.
- **Projected finish.** Walk the open critical path: a task starts when all its `blocked_by` tasks are done, and tasks with no link follow the order of `plan.md`. A task's duration is its `Estimate (d)` from `plan.md` when there is one; else the median wall-clock of the project's finished task runs; else 2 working days, flagged. Chain issues take the chain projection of the offline Step 4. A task that waits on a person counts from today: the clock is on that person, so say so. The projected finish is the latest end date. Compare with the last status: the slip or gain in days, and the one task that caused it.
- **Risks** (at most 3): a stall over `chain.stall_minutes`, `ahead > 0` or a dirty tree in a chain, a task stale for a week, a health of `at-risk` or `off-track` and its line.

### Step 4: Write and deliver

Write `$OUT/<YYYY-MM-DD>.md` with the offline Step 5 layout (Projected done · Progress · Moved since the last status · Waiting on you · Next · Risks). Add a `Runs:` line (count and cost since the last status) and, with milestones, one line per milestone (`M<n>: <done>/<total>, <metric> target <target>`). A quiet project still gets a short file. Commit and push only the state dir.

Then, guarded (a local session or a refusal → skip silently; the file is the record):

1. `mcp__trinity__report` — `report_type: <agent_name_with_underscores>.project_status`, `title: "<Project> — <done>/<total>, done by <date>"`, `display_hint: markdown`, `payload: {markdown, project_id, projected_done, done, total}`.
2. `mcp__trinity__link_to_project(project_id, kind: report, target_id: <the report id from the receipt>)`. A refusal is ignored; the report stands.
3. One `mcp__trinity__send_notification` — title = the report title; message = the "Waiting on you" lines, or "Nothing needs you today."; `priority: high` only when something has waited on a person for 2 days or more.

When the project's status is done, title the report `"<Project> — done <date>"`.

## Offline mode (frozen — agents without Trinity Projects)

Runs only when `list_projects` is not enabled (standard §28). Written for standard 2.x; developed no further. Its §17 'linked project' passages are unreachable on Trinity.

## Purpose

One short daily answer to two questions about one managed project: **how is it going** and **when will it be done**. The steward (`/project-steward`) moves the work and escalates; this skill reports, and turns what waits on the operator into Trinity asks. It never dispatches. Its only registry writes are relaying an ended ask (one comment + the needs-operator → active label flip) — the managing agent is the project's sole issue writer, so this stays inside the standard (§2).

**Daily, even when quiet.** This is an operator-requested heartbeat for one project, so a no-change day still delivers a one-line report ("nothing moved; projected done <date>") — unlike the steward, which stays silent when nothing changed.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | ✓ | |
| Epic + tasks | `$REGISTRY`, label `project:<slug>`; plus every repo in `$MEMBER_REPOS` (comma-separated, §0) for member issues | ✓ | relay of an ended ask only |
| Build ledger | `<workspace>/plan.md` — see **Ledger contract** | ✓ | ✓ (`Status` / `Evidence` cells only, from verified evidence) |
| Chain ledgers | every folder the charter envelope lists under `chains:` (else the epic's `## Engineering issues` section): `<chain>/ledger-entry.yaml` (the committed mirror of the build-chain run — `status`, `dispatch_health[]`, `issues[].{ref,step,branch,tip,pr,validation,executions[]}`) and `<chain>/$CHAIN_LEDGER` (the run-log); when neither is visible to this run, the newest `<agent>.build_chain` report via `list_reports` / `get_report` — standard §18, §24.3 | ✓ | never — the chain writes its own ledger |
| Steward digest | `$STATE_DIR/digests/<today>.md` | ✓ | |
| Status history | `<workspace>/status/YYYY-MM-DD.md` + `status/asks.json` | ✓ | ✓ |

The workspace is the epic body's `## Workspace` field resolved through the standard's §15 resolver — never derived from the slug.

## Ledger contract

`plan.md` is a markdown table with at least these columns (others are free): `Step` · `Issue` (`owner/repo#N`, or blank for work with no issue) · `Estimate (d)` (working days) · `Depends on` (comma-separated step ids, or blank) · `Status` (`todo · in-progress · waiting-on-operator · done`) · `Evidence` (merged PR, commit, file — what proves `done`). The ledger is the project's plan; this skill only ever edits the `Status` and `Evidence` cells, from evidence, never from a summary. `/build-chain`-style chain ledgers already have this shape.

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

- **Any platform project (linked or platform-tracked):** after the report is published (Step 5), put it on the project with `mcp__trinity__link_to_project` (`kind: report`, `target_id` = the report's id from the `report` receipt), and tag every ask this run raised in Step 4b with `kind: ask` and the ask's id from its receipt — so members find the status and the open asks on the project page. A refusal here is ignored; the report and the asks stand without it.
- **Platform-tracked project:** there is no epic. Find the project by the charter's `platform_project:` or by slug in `list_projects`. Evidence (Step 2) is `mcp__trinity__list_project_tasks` with `status: all` plus `mcp__trinity__get_project_log`; a ledger step whose `Issue` cell reads `T-NNN` is done when that task is `done`. Waiting-on-you (Step 4b) is every task in `needs-decision`; the request id is `<slug>:T-NNN`, and an ended ask is relayed with `mcp__trinity__add_project_task_note` (the `### Operator answer` text) and, when an option was chosen, `mcp__trinity__update_project_task` back to `active`. The ledger and the status files live in the charter's folder when there is one, else in `$STATE_DIR/outputs/<slug>/`.

## Process

### Step 1 — Resolve the standard and read

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration** (a standard without §0 resolves to the defaults: `project-steward/` state, no member repos):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
[ -n "$STANDARD" ] || { echo "no project standard — run /project-init first"; exit 1; }
cfg() { awk -v k="${1}" -v d="${2}" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$(0)~p{v=$(0);sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
REGISTRY=$(cfg registry ""); AGENT_NAME=$(cfg agent ""); STATE_DIR=$(cfg state_dir project-steward); MEMBER_REPOS=$(cfg member_repos "")
L_ACTIVE=$(cfg labels.active "status:active"); L_NEEDS_OPERATOR=$(cfg labels.needs_operator "status:needs-decision")
CHAIN_LEDGER=$(cfg chain.ledger run-log.md); CHAIN_STALL_MIN=$(cfg chain.stall_minutes 30)   # rev 2 (§18, §24): the build-chain run-log name and the stall threshold
```

Pre-1.3 standards return `$REGISTRY` / `$AGENT_NAME` empty — read them from §1 / §2. Then `git pull --rebase --autostash` (continue on failure, say so). Find the epic (`gh issue list --repo "$REGISTRY" --label project --label "project:<slug>" --state all`), resolve the workspace from its `## Workspace` field (§15), read `project.md` and `plan.md`. **No ledger** is not an error: note `no ledger at <workspace>/plan.md — progress from the task checklist, no projected date` and continue without Steps 3–4's projection.

**Chain folders (rev 2).** Read the charter envelope's `chains:` list (paths relative to the managing agent's repo); when the charter has none or is not visible, take the chain folders named in the epic's `## Engineering issues` section (the epic also lists them after the project folder in `## Workspace`). A project with neither has no chain — skip every chain line below without comment. The chain is the project's engineering executor (standard §18): this skill reads its ledger and never writes it.

### Step 2 — Collect evidence (read-only)

For every step in the ledger, and every open issue labeled `project:<slug>` in `$REGISTRY` and in each `$MEMBER_REPOS` repo: state, status labels, last comment date + first line, linked PRs (`gh pr list --repo <repo> --search "<ref>"`) with draft/merged state. Read today's steward digest if present. Read the newest file in `status/` as "yesterday".

**Chain evidence**, per chain folder:
- `<chain>/ledger-entry.yaml` — the run's `status`, `dispatch_health[]`, and per issue `ref`, `step`, `branch`, `tip`, `pr`, `validation` (`decision`, `post_merge`), `blocked_on_ruling`, and `executions[]` (`step`, `id`, `queued_at`, `started_at`, `closed`, `cost`). Parse with python3 + PyYAML; a missing mirror is not an error.
- `<chain>/$CHAIN_LEDGER` — the last 60 lines: parked `needs-operator` questions (their first appearance is the ask's age), stall lines, `ahead > 0` / dirty-tree findings.
- For every `pr` the ledger names: `gh pr view <url> --json isDraft,state,mergedAt,reviewDecision` — this is what decides *merges due* below.
- When the chain folder is not visible to this run (a gitignored `project_files/` on a container): `list_reports` for the newest `<agent_name_with_underscores>.build_chain` report, `get_report` for its rows (issue · step · branch · tip · PR · verdict · cost · rider KB · stalls); say `chain read from the build_chain report of <date>, not from the ledger` in the Risks section. No report either → `chain ledger not readable from here` and carry on.

Compare the chain's per-issue `step` with yesterday's status file: a step that advanced is a move.

### Step 3 — Reconcile the ledger (evidence only)

A step is **done** only when its issue is closed or its Definition of Done is evidenced (merged PR, pushed commit, recorded file). Update `Status` / `Evidence` cells accordingly. Never mark done from a summary or a label alone.

### Step 4 — Project the finish date

Critical-path walk over the ledger: each remaining step starts when all its `Depends on` steps finish; its duration is `Estimate (d)` in working days (weekdays). Steps in `waiting-on-operator` count **from today** with their estimate — the clock is on the operator, so say so. The projected finish = the latest end date. Compare with yesterday's projection: state the slip or gain in days and the one step that caused it. If an estimate is blank, use 2 days and flag it.

**Chain issues** are projected from the chain ledger, not from `plan.md` estimates: for each issue not `done`, the remaining steps are the ones after its current `step` in the chain's order (`prep → plan → ruled → implement → review → fix → pr → validate → done`); the duration of one step is the **median wall-clock of closed executions in `executions[]` across the whole run** (queued-to-closed), with a floor of 30 minutes; an issue with `depends_on` another starts when that one reaches `pr`. Issues with no dependency run in parallel (standard §21.2), so the chain's finish is the longest single path, not the sum. A parked issue (`needs-operator`, `blocked_on_ruling`) counts from today — the clock is on the operator. A `plan.md` row whose `Issue` is a chain issue takes the chain's projection and its `Evidence` cell gets the PR url when the PR is open. No closed executions yet → use the plan-ledger estimate as before and flag `chain duration unknown`.

### Step 4b — Turn waiting-on-you into Trinity asks (deployed agent only)

For every open issue in the project carrying `$L_NEEDS_OPERATOR`:
- **request_id** = `<slug>:<owner>.<repo>:<N>` (letters, digits, `.` `_` `:` `-` only — a `/` or `#` is refused `invalid_request_id`) (+ `:<sha-or-date>` when the issue's newest `### Approval needed` comment names a revision) — stable, so a daily re-raise **replays** and never duplicates.
- **Approval** when the newest `### Approval needed` comment exists: `type: approval`, `options` from that comment (≤5, each ≤60 chars — shorten and move the detail to `question`) and `proposal` (JSON) copied verbatim, `question` = its prose; title ≤120 chars. **Question** otherwise: `question` = the issue's Objective + Definition of done, with the defaults stated in the body.
- `to: primary`, `priority: high` when waiting ≥ 2 days, else `medium`.
- Read every earlier request_id back with `get_my_ask`. **Ended** (answered / cancelled / dismissed / expired) and not yet relayed → post `### Operator answer YYYY-MM-DD` on the issue with the disposition and the answer verbatim, flip `$L_NEEDS_OPERATOR` → `$L_ACTIVE` only when a listed option was chosen (or a question answered); a response of `(something else)` approves none of the options — relay `response_text` and leave the label; cancelled / dismissed / expired leave it too (say so in the report; a dismissed ask is not re-raised straight away). Record relayed ids in `<workspace>/status/asks.json` so a relay happens once.
- A refusal naming the key (`requires a key that carries an agent identity`), or no Trinity tools at all, means a local session: skip this step silently; the issues still carry the request.

**Chain items that wait on the operator** (rev 2) go through the same step, same caps, same ask contract:
- **Parked questions** — every chain issue whose ledger `step`/`status` is `needs-operator` (or carries `blocked_on_ruling`): `type: question`, request_id `<slug>:chain:<run-id>:<N>`, `question` = the parked question quoted from the run-log with the planner's recommendation, age = days since the run-log line that parked it. The chain itself never re-asks; this skill is where the question reaches the operator daily until answered.
- **Merges due** — every PR the chain's `validation.decision` is `APPROVE` on (so no longer a draft) that is still open: one ask per PR, `type: approval`, request_id `<slug>:merge:<owner>.<repo>:<pr-number>`, title `Merge <repo>#<N> — <issue title>` (≤120), `options` `["merge now","hold — say why","close without merging"]`, `question` = the PR's base, tip sha, validation date and the chain's *Before merge* notes. **Merges are the operator's; the chain never gates on them** (standard §21.7, ruling D9) — a PR the operator merges before the chain marks it ready is not an error: the chain records `validation.post_merge: true` and validates the merge commit by rule, and this skill reports it under Moved, not Risks. An ended merge ask is relayed to the chain issue as `### Operator answer` like any other; `hold` keeps the PR in Waiting on you with its reason until it is merged or closed.
- Locally (no agent key) both kinds are listed in the report only, same as the issue-based items.

The "Waiting on you" section of the report names each ask by title and says it is in the Trinity operator queue.

### Step 5 — Write and deliver

Write `<workspace>/status/<today>.md`:

```
# <Project> — status <YYYY-MM-DD>
**Projected done:** <date> (<+N/-N days vs yesterday, cause> | unchanged | no ledger — no projection)
**Progress:** <done>/<total> steps · critical path: <step> → <step> → …
## Moved since yesterday
- <one line per real change, with issue/PR link> | nothing moved
- chain: <issue> <old step> → <new step> · PR <url> opened · validate <APPROVE|REQUEST CHANGES> (<post-merge> when the operator merged first)
## Waiting on you
- <issue> — <what exactly to do, one line> (waiting <N> days)
- chain question: <issue> — <the parked question, one line> (waiting <N> days)
- merge due: <repo>#<N> — <title>, validated <date>, base <branch> (waiting <N> days)
## Next 24h
- <what the steward / owners / this agent will do next>
## Risks
- <only real ones, max 3> | none
- stall: <issue> <step> queued <N> min (threshold <CHAIN_STALL_MIN>) · container-only state: <issue> <branch> ahead <N> / dirty
```

Chain lines appear only when the project has a chain; the stall line only when `dispatch_health` has an entry, or an execution shows `queued_at` with no `started_at` older than `$CHAIN_STALL_MIN` minutes. "nothing moved" covers the chain too.

Commit only `<workspace>/` (`status(<slug>): <date> — projected <date>`), push. A canon-placed workspace publishes through `/canon-publish` instead.

Then publish `mcp__trinity__report` — `report_type: <agent_name_with_underscores>.project_status`, `title: "<Project> — <done>/<total>, done by <date>"`, `display_hint: markdown`, `payload: {markdown: <the file>, slug, projected_done, done, total}`, `to: operator`. Then one `mcp__trinity__send_notification` — `notification_type: status`, `category: progress`, `priority: high` only if something waits on the operator for ≥2 days, else `normal`; title = the report title; message = the "Waiting on you" lines, or "Nothing needs you today."

**Guard:** if the Trinity tools are unavailable or refuse (local session, user key), skip silently — the committed file is the record. Trinity is the upgrade, never the gate.

## Completion

Once the epic closes, deliver a final report (`title: "<Project> — done <date>"`) and print `project done — disable the project-status schedule` so the operator or an interactive session turns it off.
