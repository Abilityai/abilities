---
name: project-steward
description: Autonomous sweep of all managed projects per PROJECT_STANDARD.md. Verifies pending-verification claims against Definition of Done, dispatches next work to explicitly-labeled owner agents (Trinity when available; triage-only when not), escalates stalls per the staleness policy, sweeps open loops (ages every waiting-on item and drafts the operator's follow-ups), runs the quarantine classification pass, and writes a digest that closes the loop with the operator. Never asks a human anything mid-run.
automation: autonomous
schedule: "0 7-19/2 * * 1-5"   # default: every 2h, weekdays UTC — adjust, or delete this line for manual-only (the installer substitutes your choice)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
effort: high
user-invocable: true
metadata:
  version: "1.2"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.2: Read-the-standard guard (missing PROJECT_STANDARD.md → exit with \"run /project-init first\", headless-safe); default `schedule:` in frontmatter replaces the installer-substituted placeholder; skill is now authored standalone (installer copies from here)"
    - "1.1: Loop closure (Invariant 7) — Step 3c open-loop pass ages every waiting-on:* task on the 3d/7d/14d ladder and drafts sendable nudges (never sends them), detects and records closes; digest opens with a closing statement and carries Your open loops + Loops closed; unanswered needs-decision asks get louder with age instead of aging out; operator-initiated results notify the operator directly; state.json gains open_loops (rebuildable from labels)"
    - "1.0: Initial version — completion lattice verification, owner/agent distinction, Invariant 4 escalation ladder (never mutates P1/P2), unclassified quarantine pass, Trinity-optional dispatch"
---

# Project Steward

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-steward v1.1 — recent: loop closure (Invariant 7)`. Then proceed.

## Purpose

Keep every managed project moving without the operator having to push it. Each run:
1. Reconcile outstanding dispatches (read agent replies, post relay comments, verify done claims)
2. Review every open project epic: verify pending-verification tasks, dispatch next work, escalate stalls
3. Sweep open loops (Invariant 7): age every `waiting-on:*` task, draft the operator's nudges, keep unanswered asks alive
4. Run the quarantine pass: auto-stub unregistered workspace folders
5. Write the digest (material runs only), opening with what the operator now knows and what is waiting on them

**This skill never asks a human anything mid-run.** Anything ambiguous gets `status:needs-decision` and moves on. It is the sole writer of steward update comments on GitHub issues.

**It does close loops, in both directions (standard §14).** Nothing it touched ends in silence: work the operator initiated is reported back to the operator, an unanswered ask is re-surfaced with its age rather than dropped, and every loop parked on a third party is aged in the digest with a ready-to-send nudge. It drafts those nudges; **it never sends them** — contacting a client, vendor, or outside colleague is the human's act, always.

**Deliberate non-composition:** this skill dispatches only to owners explicitly named by `agent:*` labels — no routing judgment. The interactive disambiguation that `/orchestrate` provides would hang an unattended run.

**Trinity is optional.** When Trinity MCP is unavailable, the skill runs in triage-only mode: all GitHub operations continue; dispatch is skipped and noted in the digest. Nothing is lost.

## Runtime resolution (do this first, once per run)

Read `PROJECT_STANDARD.md`. **If it is missing, exit (headless-safe, no prompt) and report: run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Resolve:
- `$REGISTRY` = the registry repo (§1)
- `$AGENT_NAME` = this agent's name (§2) — tasks labeled `agent:$AGENT_NAME` are inline-class, never dispatched
- `$OPERATOR` = the operator (§2)
- `$PV_MAX_AGE` = pending-verification max age in hours (§12)

## Prerequisites

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

**Derive GH_TOKEN from the git remote** (critical on Trinity — env wins over cached hosts.yml):
```bash
if [ -z "$GH_TOKEN" ]; then
  export GH_TOKEN=$(git remote get-url origin | sed -nE 's#https://[^:/@]+:([^@]+)@github.com/.*#\1#p')
fi
```

**PAT scope pre-flight** (use REST labels endpoint — issue list silently returns [] on missing scope):
```bash
PREFLIGHT=$(gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1)
```
If this returns a 403 or "Resource not accessible": abort immediately. Prepend a `FAILED` line to `project-steward/run_log.txt` (create the dir first). Attempt to notify the operator via Trinity `mcp__trinity__send_notification` if available. Stop.

**Detect Trinity MCP:** attempt `mcp__trinity__list_agents`. If it fails or is unavailable, set `TRINITY_MODE=triage-only` and continue.

## No-op discipline (high-frequency cadence)

Most runs will find nothing to do. Before writing anything, compute whether ANY actionable condition exists:
- An unreconciled dispatch with a reply or past a time threshold
- An active epic with a dispatchable/inline/verifiable task
- A staleness breach
- New/edited epics or label changes since last run
- A `pending-verification` task past max-age
- A `waiting-on:*` loop crossing a nudge threshold (3 days, then weekly, then 14 days) — a quiet loop still ages
- A `status:needs-decision` ask that has now gone unanswered across two digests
- Unclassified workspace folders not yet stubbed

**If none: stop.** Update `last_run` in `project-steward/state.json` only — do NOT commit, do NOT write a digest, do NOT notify, do NOT post any comment. Quiet runs leave no trace.

## Hard limits (45-minute rule)

- Max **10 projects** reviewed per run. If more are open, review `priority:p1` first, then least-recently-updated. Write the remainder to `state.json carry_over` and start there next run.
- Max **3 dispatches** per run; max **1 open dispatch per project**.
- Max **1 inline task** executed per run.

## Process

### Step 1: Read current state

1. Sync: `git pull --rebase --autostash origin main` (continue on failure; note it in the digest).
2. Read `PROJECT_STANDARD.md` (resolving runtime variables as above).
3. Read `project-steward/state.json` (create with empty defaults if missing: `{"last_run": null, "carry_over": [], "open_dispatches": [], "open_loops": []}`). Each `open_loops` entry is `{issue, actor, asked_at, last_nudge, digests_carried}` — bookkeeping only; the `waiting-on:*` labels on GitHub are the truth, so a lost state file costs nudge timing, never a loop.
4. Pull the registry:
   ```bash
   gh issue list --repo "$REGISTRY" --label project --state open \
     --json number,title,labels,updatedAt,body --limit 50
   ```
5. Check Trinity MCP availability.

### Step 2: Reconcile outstanding dispatches

For each entry in `open_dispatches` (skip in triage-only mode):

1. Use `mcp__trinity__get_chat_history` with the dispatched agent; look for a "Done claim" reply posted after `sent_at`.
2. **Reply found**: check DoD items against the claim (Step 3b verification protocol). If verified: close the task issue as done, check it off in the epic, post an agent-report relay comment. If failed: reopen with logged reason. Remove the tracker entry.
3. **No reply, 6+ hours since `sent_at`**: send one re-ping via `mcp__trinity__chat_with_agent` referencing the original dispatch; record `repinged_at`.
4. **No reply, 24+ hours since `sent_at`** (re-ping already sent): set the task issue to `status:blocked`, post a steward comment naming the silent agent, remove the tracker entry, flag in digest.
5. **Under threshold**: leave the tracker entry — not yet actionable.

### Step 3: Review each project (max 10)

Build the review list: `carry_over` first, then `priority:p1`, then least-recently-updated. Skip `status:paused` epics entirely. For each project:

1. Read the epic body + comments since the last steward update.
2. Read open `project:<slug>` task issues with their labels and bodies.
3. Compute: days since last activity, open/done/pending-verification task counts, current `status:*` label, whether an open dispatch exists.
4. Apply the staleness policy (§8 of the standard).

**`ultrathink` here** — determining the true state of a project and the single best next action is the judgment-heavy core of this skill.

### Step 3a: Pending-verification pass

For each task issue with `status:pending-verification`:

1. Compute age: `(now - pending_since_timestamp)` in hours (read from the label-change timestamp in the issue events).
2. If age > `$PV_MAX_AGE`: set `status:needs-decision`, post steward comment: "Pending-verification for {age}h — exceeds the {PV_MAX_AGE}h SLA. Operator decision required to close or reopen.", add to digest top section. Continue.
3. If age ≤ `$PV_MAX_AGE`: look for a "Done claim" comment on the task issue (format: `### Done claim ...`).
4. **Done claim found**: verify each `## Definition of Done` checklist item against the claim. If all verifiable: post `[Verified]` comment, set `status:done`, close issue, check off in epic. If any unverifiable: post `[Verification failed]` comment with specifics, remove `pending-verification` label, restore `status:active`.
5. **No done claim and still active**: this task shouldn't be in pending-verification — log a steward comment noting the inconsistency, restore `status:active`.

### Step 3b: Autonomy triage (per project, per actionable task)

Classify the project's next actionable task:

- **auto-dispatch**: has `agent:<fleet-agent>` label (not `agent:$AGENT_NAME`); Trinity available; owner resolvable; no human gate implied → eligible for Trinity dispatch.
- **auto-inline**: has `agent:$AGENT_NAME`; fits the remaining run budget (~15 min); touches only reading/analysis, workspace writes, or GitHub comments (no email, no external spend, no gated external effects) → execute it this run.
- **needs-human**: everything else (missing owner, judgment call, gated external effect, human approval required) → `status:needs-decision` + digest.

### Step 3c: Open-loop pass (Invariant 7 — standard §14)

Two sweeps, both cheap, both run every material run. Neither ever contacts anyone outside the registry.

**Outbound — loops the operator owes other people or agents.** Fetch every open task carrying a `waiting-on:*` label:
```bash
gh issue list --repo "$REGISTRY" --state open --json number,title,labels,url,updatedAt --limit 100 \
  --jq '[.[] | select(any(.labels[].name; startswith("waiting-on:")))]'
```

For each, resolve the actor from the label and the loop's age from `state.json.open_loops` (falling back to the date on the issue's `### Waiting on` comment, else the label-application event). Then:

| Age since asked | Action |
|---|---|
| < 3 days | List it in the digest's **Your open loops** section with its age. No nudge, no notification. |
| ≥ 3 days, and ≥ 7 days since the last nudge | Draft a short, sendable follow-up message to the actor (2–4 sentences: what was asked, when, why it matters now, what response closes it) and put it in the digest verbatim under that loop. Record `last_nudge` in `state.json.open_loops`. |
| ≥ 14 days | Set `status:needs-decision`, post one steward update asking the operator to chase harder, drop it, or route around it. Keep listing it. **Never auto-drop a loop.** |

Detect closure while you're here: if the task's comments show the awaited answer arrived (an `### Agent report`, a `### Loop closed`, or the operator's own comment saying it landed), post `### Loop closed YYYY-MM-DD — answered` per §7, remove the `waiting-on:*` label, drop the state entry, and note the close in the digest. A close nobody recorded reads exactly like a loop nobody remembered.

**Never send the nudge.** The steward drafts; the operator sends. Emailing a client, vendor, or outside colleague on the operator's behalf is out of scope for this skill under every configuration.

**Inbound — loops this agent owes the operator.** For every open `status:needs-decision` item, count how many digests have carried it since the ask was posted. At two or more, promote it to the top of the digest's **Needs decision** section with the age stated plainly ("asked 9 days ago, 4 digests"). An ask is never retired for going stale — it gets louder, not quieter.

### Step 4: Act (deterministic priority order, per project)

Take exactly one action per project, in this order:

1. **All success criteria checked** → post a closure-proposal steward update, flag for digest. Do not close the epic (closure is the operator's call).
2. **`status:needs-decision` or `status:blocked` already set** → no action; include in digest with age.
3. **auto-dispatch, no open dispatch, dispatch budget left** (Trinity available):
   ```
   a. mcp__trinity__get_agent_health(<agent>)
   b. If healthy: resolve callable name (deployed_name from system-map if available, else logical name)
   c. mcp__trinity__chat_with_agent(<agent>, <standard brief from PROJECT_STANDARD.md §10>)
   d. Post dispatch receipt on the task issue
   e. Add tracker entry to open_dispatches: {project_slug, task_number, agent, sent_at}
   ```
   If unhealthy: `status:blocked` + steward comment + digest.
4. **auto-dispatch, Trinity unavailable (triage-only mode)**: note in digest that dispatch was skipped; task remains open.
5. **auto-inline, run budget left**: execute the task now; post result as agent-report comment on the task issue; close if DoD met; check off in epic. Max one inline task per run.
6. **needs-human**: set `status:needs-decision`, post one steward update saying exactly what decision is needed.
   **Wait ≠ decision.** If what's missing is a *response from someone outside the registry* rather than a call only the operator can make, this is an open loop, not a decision: create the label idempotently, apply it, post the `### Waiting on` comment (§7), and let Step 3c age it. Don't spend a `needs-decision` on a wait — that's how a decision queue turns into noise the operator stops reading.
   ```bash
   gh label create "waiting-on:$ACTOR" --repo "$REGISTRY" --color "d4c5f9" \
     --description "Open loop: awaiting $ACTOR" 2>/dev/null || true
   gh issue edit "$ISSUE" --repo "$REGISTRY" --add-label "waiting-on:$ACTOR"
   ```
7. **Next task exists but no actionable path**: if active project with zero tasks, draft 1–3 candidate next tasks as a proposal in a steward comment, set `status:needs-decision`.
8. **Nothing to do** (work in flight, within staleness thresholds) → no comment, no label change. Silence is valid.

Post at most **one** steward update comment per project per run, and only if something changed since the last one.

### Step 5: Quarantine pass (Invariant 6)

List workspace folders and check each against the registry:
```bash
ls -d project_files/*/ 2>/dev/null | sed 's|project_files/||;s|/||'
```

For each folder `<slug>` with no corresponding `project:<slug>` epic in the registry: create a quarantine epic:
```bash
gh issue create --repo "$REGISTRY" \
  --title "[Project] $SLUG (unclassified)" \
  --label "project,project:$SLUG,status:unclassified" \
  --body "## Goal\nAuto-stubbed from unregistered workspace folder `project_files/$SLUG/`. Classify this project or close this epic.\n\n## Current status\n(maintained by /project-steward)"
```

Batch these into one digest line: "N unclassified folder(s) auto-stubbed: <names>". Never create per-item notifications.

### Step 6: Write the digest (material runs only)

Skipped entirely on no-op runs. One file per day — `project-steward/digests/YYYY-MM-DD.md` — created on the first material run and updated by later ones (append a `## Run HH:MM UTC` section).

Open with the **closing statement** (standard §14a) — three lines, before any section: what is now true, what is waiting on the operator, and what the steward will do next unprompted. A digest that opens with a table of statuses makes the operator do the reading; one that opens with these three lines has already closed the loop.

Then the sections:

- **Needs decision** (top): each `status:needs-decision` item with the one decision required; items unanswered across 2+ digests come first with their age stated
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
- **Carry-over + mode**: projects not reviewed; note if triage-only

If (and only if) there are needs-decision items, blockers, past-max-age pending-verification, a loop crossing a nudge threshold, or errors: send a short summary via `mcp__trinity__send_notification` (when Trinity available) linking the digest path. Standing open loops that crossed no threshold this run stay in the digest without a notification — the list is always visible, the interruption is not.

**Results the operator personally asked for go to the operator** (standard §14a.4): when this run finished work the operator initiated by name, `send_notification` with the outcome, even on an otherwise quiet day. The issue log is the record; the notification is the loop closing.

### Step 7: Write updated state

1. Update `project-steward/state.json`: `last_run`, `carry_over`, `open_dispatches`, `open_loops`.
2. Prepend one summary line to `project-steward/run_log.txt`:
   `YYYY-MM-DD HH:MM UTC | reviewed N | dispatched N | verified N | inline N | needs-decision N | loops N (nudged N, closed N) | quarantine N | mode`
3. Push steward state (scoped — never add any other path):
   ```bash
   git add project-steward && \
   git commit -m "steward: run $(date -u +%Y-%m-%d)" && \
   (git push origin main || (git pull --rebase --autostash origin main && git push origin main))
   ```
   If push fails, log it and stop — state is preserved locally; the next run's pull will carry it.

## Error recovery

- **`gh` auth/network failure**: abort before any writes; prepend a `FAILED` line to `project-steward/run_log.txt`; attempt `mcp__trinity__send_notification` if available.
- **Trinity MCP absent**: continue in triage-only mode; record in digest. Dispatch state is untouched — next healthy run resumes.
- **Single project fails mid-review**: post a steward update describing the defect, set `status:needs-decision`, continue with the next project.
- **Partial run (interrupted)**: safe to re-run — the changed-since-last-update check and dispatch tracker make all writes idempotent.
- **State file corrupt**: move to `state.json.bak-YYYY-MM-DD`, rebuild defaults, rebuild `open_dispatches` conservatively from recent dispatch receipt comments that lack a matching agent-report relay, and rebuild `open_loops` from the live `waiting-on:*` labels (ages from each issue's `### Waiting on` comment). Nudge timing resets; no loop is lost.
