---
name: project-status
description: Daily operator status for ONE managed project per the project standard — what moved since yesterday, what is done, what waits on the operator (raised as Trinity asks when the platform is there), and the projected finish date computed from the remaining critical path in the project's build ledger (plan.md). Read-only against the registry; delivers a Trinity report plus one notification, or just the committed status file when Trinity is absent. Use when the operator wants a per-project daily "how is it going and when will it be done".
argument-hint: "<slug>"
automation: autonomous
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__report, mcp__trinity__send_notification, mcp__trinity__list_reports, mcp__trinity__ask_operator, mcp__trinity__get_my_ask
metadata:
  version: "1.2"
  created: 2026-10-02
  author: trinity-pm
  changelog:
    - "1.2: Promoted from the production orchestrator's local skill into the agent-dev plugin as the sixth project skill (ent#789) — reads the standard through the shared resolver (PROJECT_STANDARD.md or fleet/project-standard.md, §0 Configuration: registry, state_dir, member_repos, label roles), the ledger contract is documented here, a project without a ledger still gets a daily report (progress from the task checklist, no projected date — and says so) instead of failing, the report type is namespaced by the agent name"
    - "1.1: Waiting-on-you items become Trinity asks (operator 2026-10-02: 'that's why we have asks and approvals on trinity') — one idempotent ask_operator per needs-operator issue, approval asks carry the frozen proposal from the issue's Approval needed comment; ended asks are relayed back to the issue and the label flipped. A local user-scoped key cannot raise asks, so this only fires on the deployed agent"
    - "1.0: Initial version — operator ask 2026-10-02 for the builder-agent project (ent#762): 'let me know once a day how this is going and when you will be done'"
---

# Project Status

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-status v1.2 — recent: sixth project skill, ledger contract documented`. Then proceed.

## Purpose

One short daily answer to two questions about one managed project: **how is it going** and **when will it be done**. The steward (`/project-steward`) moves the work and escalates; this skill reports, and turns what waits on the operator into Trinity asks. It never dispatches. Its only registry writes are relaying an ended ask (one comment + the needs-operator → active label flip) — the managing agent is the project's sole issue writer, so this stays inside the standard (§2).

**Daily, even when quiet.** This is an operator-requested heartbeat for one project, so a no-change day still delivers a one-line report ("nothing moved; projected done <date>") — unlike the steward, which stays silent when nothing changed.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | ✓ | |
| Epic + tasks | `$REGISTRY`, label `project:<slug>`; plus every repo in `$MEMBER_REPOS` (comma-separated, §0) for member issues | ✓ | relay of an ended ask only |
| Build ledger | `<workspace>/plan.md` — see **Ledger contract** | ✓ | ✓ (`Status` / `Evidence` cells only, from verified evidence) |
| Steward digest | `$STATE_DIR/digests/<today>.md` | ✓ | |
| Status history | `<workspace>/status/YYYY-MM-DD.md` + `status/asks.json` | ✓ | ✓ |

The workspace is the epic body's `## Workspace` field resolved through the standard's §15 resolver — never derived from the slug.

## Ledger contract

`plan.md` is a markdown table with at least these columns (others are free): `Step` · `Issue` (`owner/repo#N`, or blank for work with no issue) · `Estimate (d)` (working days) · `Depends on` (comma-separated step ids, or blank) · `Status` (`todo · in-progress · waiting-on-operator · done`) · `Evidence` (merged PR, commit, file — what proves `done`). The ledger is the project's plan; this skill only ever edits the `Status` and `Evidence` cells, from evidence, never from a summary. `/build-chain`-style chain ledgers already have this shape.

## Process

### Step 1 — Resolve the standard and read

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration** (a standard without §0 resolves to the defaults: `project-steward/` state, no member repos):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
[ -n "$STANDARD" ] || { echo "no project standard — run /project-init first"; exit 1; }
cfg() { awk -v k="$1" -v d="$2" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$0~p{v=$0;sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
REGISTRY=$(cfg registry ""); AGENT_NAME=$(cfg agent ""); STATE_DIR=$(cfg state_dir project-steward); MEMBER_REPOS=$(cfg member_repos "")
L_ACTIVE=$(cfg labels.active "status:active"); L_NEEDS_OPERATOR=$(cfg labels.needs_operator "status:needs-decision")
```

Pre-1.3 standards return `$REGISTRY` / `$AGENT_NAME` empty — read them from §1 / §2. Then `git pull --rebase --autostash` (continue on failure, say so). Find the epic (`gh issue list --repo "$REGISTRY" --label project --label "project:<slug>" --state all`), resolve the workspace from its `## Workspace` field (§15), read `project.md` and `plan.md`. **No ledger** is not an error: note `no ledger at <workspace>/plan.md — progress from the task checklist, no projected date` and continue without Steps 3–4's projection.

### Step 2 — Collect evidence (read-only)

For every step in the ledger, and every open issue labeled `project:<slug>` in `$REGISTRY` and in each `$MEMBER_REPOS` repo: state, status labels, last comment date + first line, linked PRs (`gh pr list --repo <repo> --search "<ref>"`) with draft/merged state. Read today's steward digest if present. Read the newest file in `status/` as "yesterday".

### Step 3 — Reconcile the ledger (evidence only)

A step is **done** only when its issue is closed or its Definition of Done is evidenced (merged PR, pushed commit, recorded file). Update `Status` / `Evidence` cells accordingly. Never mark done from a summary or a label alone.

### Step 4 — Project the finish date

Critical-path walk over the ledger: each remaining step starts when all its `Depends on` steps finish; its duration is `Estimate (d)` in working days (weekdays). Steps in `waiting-on-operator` count **from today** with their estimate — the clock is on the operator, so say so. The projected finish = the latest end date. Compare with yesterday's projection: state the slip or gain in days and the one step that caused it. If an estimate is blank, use 2 days and flag it.

### Step 4b — Turn waiting-on-you into Trinity asks (deployed agent only)

For every open issue in the project carrying `$L_NEEDS_OPERATOR`:
- **request_id** = `<slug>:<owner>/<repo>#<N>` (+ `:<sha-or-date>` when the issue's newest `### Approval needed` comment names a revision) — stable, so a daily re-raise **replays** and never duplicates.
- **Approval** when the newest `### Approval needed` comment exists: `type: approval`, `options` and `proposal` (JSON) copied from that comment verbatim, `question` = its prose. **Question** otherwise: `question` = the issue's Objective + Definition of done, with the defaults stated in the body.
- `to: primary`, `priority: high` when waiting ≥ 2 days, else `medium`.
- Read every earlier request_id back with `get_my_ask`. **Ended** (answered / cancelled / expired) and not yet relayed → post `### Operator answer YYYY-MM-DD` on the issue with the disposition and the answer verbatim, flip `$L_NEEDS_OPERATOR` → `$L_ACTIVE` (answered) or leave it (cancelled/expired, and say so in the report). Record relayed ids in `<workspace>/status/asks.json` so a relay happens once.
- A refusal naming the key (`requires a key that carries an agent identity`), or no Trinity tools at all, means a local session: skip this step silently; the issues still carry the request.

The "Waiting on you" section of the report names each ask by title and says it is in the Trinity operator queue.

### Step 5 — Write and deliver

Write `<workspace>/status/<today>.md`:

```
# <Project> — status <YYYY-MM-DD>
**Projected done:** <date> (<+N/-N days vs yesterday, cause> | unchanged | no ledger — no projection)
**Progress:** <done>/<total> steps · critical path: <step> → <step> → …
## Moved since yesterday
- <one line per real change, with issue/PR link> | nothing moved
## Waiting on you
- <issue> — <what exactly to do, one line> (waiting <N> days)
## Next 24h
- <what the steward / owners / this agent will do next>
## Risks
- <only real ones, max 3> | none
```

Commit only `<workspace>/` (`status(<slug>): <date> — projected <date>`), push. A canon-placed workspace publishes through `/canon-publish` instead.

Then publish `mcp__trinity__report` — `report_type: <agent_name_with_underscores>.project_status`, `title: "<Project> — <done>/<total>, done by <date>"`, `display_hint: markdown`, `payload: {markdown: <the file>, slug, projected_done, done, total}`, `to: operator`. Then one `mcp__trinity__send_notification` — `notification_type: status`, `category: progress`, `priority: high` only if something waits on the operator for ≥2 days, else `normal`; title = the report title; message = the "Waiting on you" lines, or "Nothing needs you today."

**Guard:** if the Trinity tools are unavailable or refuse (local session, user key), skip silently — the committed file is the record. Trinity is the upgrade, never the gate.

## Completion

Once the epic closes, deliver a final report (`title: "<Project> — done <date>"`) and print `project done — disable the project-status schedule` so the operator or an interactive session turns it off.
