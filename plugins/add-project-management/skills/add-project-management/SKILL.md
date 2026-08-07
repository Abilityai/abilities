---
name: add-project-management
description: Install cross-actor project management into this agent — GitHub Issues as single source of truth, uniform task anatomy with approval-ready completion lattice (open → pending-verification → done), loop closure in both directions (the agent closes loops with the user; the user is handed the loops only they can close with other people or agents), autonomous project steward, and projection sync with Google Tasks adapter v1. Writes PROJECT_STANDARD.md + five runtime skills. No dependency on fleet infrastructure.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.2"
  created: 2026-07-30
  author: Ability.ai
  changelog:
    - "1.2: Loop closure (Invariant 7) — §14 in PROJECT_STANDARD.md makes silence a failure mode in both directions: inbound, every run closes with what's true / what's waiting on the operator / what happens next unprompted, operator-initiated results notify the operator, and an unanswered ask gets louder with age; outbound, work parked on a person or agent outside the registry gets waiting-on:<actor>, ages in the digest's Your open loops on a 3d/7d/14d ladder, and comes with a drafted nudge the human sends (the agent never contacts third parties). /project-steward 1.1 (Step 3c open-loop pass), /project-task 1.2 + /project-intake 1.1 (--waiting-on), §3/§7/§8 additions, §14 upgrade path for existing standards"
    - "1.1: v1.1.0 — /project-intake (headless intake primitive), §13 Intake contract in PROJECT_STANDARD.md, headless mode for /project-task, reconciler unkeyed-item refinement (personal items excluded from sync-gap alerts), workspace visibility as deployment config"
    - "1.0: Initial version — corbin/Eugene PM-standard directive 2026-07-30; ships /project-init /project-task /project-steward /project-reconcile + PROJECT_STANDARD.md"
---

# Add Project Management

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-project-management v1.2 — recent: loop closure (Invariant 7)`. Then proceed.

Install a cross-actor project management standard into this agent. GitHub Issues become the single source of truth for all project and task state; humans, this agent, and fleet agents interact through a shared vocabulary of labels, task anatomy, and an approval-ready completion lattice.

It also installs a **loop-closure discipline** (standard §14), because tracked work still dies of silence: the agent closes every loop it owes the operator — reporting back to the person, not just to the issue log, and making an unanswered question louder rather than letting it expire — and it hands the operator the loops only a human can close, the ones parked on a client, a vendor, a colleague, or an agent in another fleet, aged and pre-drafted but never sent on the human's behalf.

**Altitude note:** this plugin governs *cross-actor* work (humans + multiple agents collaborating on projects). For a single agent's own dev-loop task backlog, use `agent-dev`'s `/add-backlog` instead.

**What gets installed:**

| Artifact | Location | Purpose |
|---|---|---|
| `PROJECT_STANDARD.md` | repo root | Convention doc — the deployer's config surface. All four skills read it at runtime. Edit this file to change behavior; don't edit the skills. |
| `/project-init` | `.claude/skills/project-init/SKILL.md` | Create or adopt a project: GitHub epic + idempotent labels + workspace stub |
| `/project-task` | `.claude/skills/project-task/SKILL.md` | The only sanctioned interactive task-creation path — enforces full anatomy including the Validation section; supports `--headless` for cron/compose use |
| `/project-steward` | `.claude/skills/project-steward/SKILL.md` | Autonomous sweep: verify pending-verification claims, dispatch, escalate, digest |
| `/project-reconcile` | `.claude/skills/project-reconcile/SKILL.md` | Projection sync — Google Tasks adapter v1 + adapter contract for other surfaces |
| `/project-intake` | `.claude/skills/project-intake/SKILL.md` | Headless intake primitive: route actionable items from any source into the registry, dedupe by meaning, return issue number. Called by other skills and crons — never interactive. |

---

## Process

### Step 1: Verify environment

Check git:
```bash
git remote get-url origin 2>/dev/null
```

If not a git repo or no GitHub remote, stop and explain: "This skill requires a GitHub repository. Initialize with `git init` and `gh repo create`."

Check gh CLI:
```bash
gh auth status 2>&1 | head -5
```

If not authenticated, stop and tell the user: "Run `! gh auth login` with `repo` and `issues` scope, then re-run `/add-project-management`."

### Step 2: Gather configuration

Use AskUserQuestion with a single question block covering all four inputs:

- **Header:** "Project Management Configuration"
- **Question:** "Answer these four questions to configure the standard:"
- **Options (multiline freeform):**
  1. **Registry repo** — Which GitHub repo will hold the project/task issues? (format: `Owner/repo`, e.g. `acme/projects`) Default: the current repo's remote origin.
  2. **Operator name** — The human this standard escalates to (GitHub username or display name, e.g. `alice`).
  3. **Agent name** — This managing agent's logical name (e.g. `corbin`, `chief-of-staff`). Default: the `name:` field in `template.yaml` if present.
  4. **Pending-verification max age (hours)** — How long a task can sit in `pending-verification` before escalating to the operator. Default: `48`.

Resolve defaults: for the registry repo, run `gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null`. For agent name, check `template.yaml` if it exists: `grep '^name:' template.yaml 2>/dev/null | head -1 | awk '{print $2}'`.

Set:
- `$REGISTRY` = the registry repo
- `$OPERATOR` = operator name
- `$AGENT_NAME` = this agent's name
- `$PV_MAX_AGE` = pending-verification max age in hours (default 48)
- `$DATE` = today's date (e.g. `2026-07-30`)

Ask one more question about the steward schedule:

- **Header:** "Steward Schedule"
- **Question:** "How often should the autonomous project steward sweep?"
- **Options:**
  1. Every 2 hours during business hours, weekdays (`0 7-19/2 * * 1-5`) — recommended for active teams
  2. Every 4 hours, all days (`0 */4 * * *`)
  3. Daily at 8am UTC (`0 8 * * *`)
  4. Manual only (no schedule)

Set `$SCHEDULE` from the chosen option (or empty for manual only).

### Step 3: Check for existing skills

```bash
ls .claude/skills/project-init 2>/dev/null && echo "project-init: EXISTS" || echo "project-init: missing"
ls .claude/skills/project-task 2>/dev/null && echo "project-task: EXISTS" || echo "project-task: missing"
ls .claude/skills/project-steward 2>/dev/null && echo "project-steward: EXISTS" || echo "project-steward: missing"
ls .claude/skills/project-reconcile 2>/dev/null && echo "project-reconcile: EXISTS" || echo "project-reconcile: missing"
ls .claude/skills/project-intake 2>/dev/null && echo "project-intake: EXISTS" || echo "project-intake: missing"
ls PROJECT_STANDARD.md 2>/dev/null && echo "PROJECT_STANDARD.md: EXISTS" || echo "PROJECT_STANDARD.md: missing"
```

If any exist, ask:
- **Overwrite all** — Replace with fresh versions (carries your config from Step 2)
- **Skip existing, install missing only**
- **Cancel**

**Upgrade path — §14 Loop closure.** `PROJECT_STANDARD.md` is the deployer's live configuration, so a kept file is never silently rewritten. But an install predating v1.2 has no `## 14. Loop closure` section, and the loop-closure behavior in `/project-steward` reads it. If the file exists and `grep -q '## 14. Loop closure' PROJECT_STANDARD.md` fails, offer to append just that section (plus the `waiting-on:<actor>` row in §3, the two comment formats in §7, and the four escalation rows in §8) with the deployer's existing config values. On no, skip and note that `/project-steward`'s open-loop pass will be inert until the section exists.

### Step 4: Create skill directories

```bash
mkdir -p .claude/skills/project-init
mkdir -p .claude/skills/project-task
mkdir -p .claude/skills/project-steward
mkdir -p .claude/skills/project-reconcile
mkdir -p .claude/skills/project-intake
```

### Step 5: Write PROJECT_STANDARD.md

Write `PROJECT_STANDARD.md` to the repo root with the values from Step 2 substituted for the `{{PLACEHOLDERS}}`:

```markdown
# Project Management Standard

> The standardized approach for managing projects in this deployment.
> Every managed project follows this standard; `/project-init` creates projects that conform to it,
> `/project-task` creates tasks, `/project-steward` manages them autonomously,
> and `/project-reconcile` syncs projections against the registry.
> **{{AGENT_NAME}}** is the managing agent; **{{OPERATOR}}** is the operator (the human this standard escalates to).
>
> Version: 1.1 ({{DATE}})

## 1. Registry

| Thing | Location | Notes |
|---|---|---|
| Registry (single source of truth) | GitHub issues in `{{REGISTRY}}` | One **epic issue** per project (`project` label); one task issue per task (`task` + `project:<slug>`) |
| Workspace (files, drafts, outputs) | `project_files/<slug>/` in the managing agent's repo | Free-form except `project.md` (charter). Path recorded in the epic body. **Visibility is deployment config**: if git-synced to the agent's container, the steward reads workspaces directly; if local-only / gitignored, Trinity runs use the epic body as authoritative context. The quarantine pass is idempotent wherever workspaces are visible. |
| Steward state, digests, run log | `project-steward/` in the managing agent's repo | Written only by `/project-steward`; tracked in git after each material run |

**Invariant 1 — One registry, write-authoritative.** The registry (GitHub Issues) is the sole authoritative record for portfolio state: scope, status, and priority. No other system writes state back. Projections are read-only views; they do not own state.

## 2. Roles

- **{{AGENT_NAME}}** — managing agent. Sole writer of GitHub issues (labels, comments, status). Runs the steward, creates tasks via `/project-task`, relays agent reports to the issue log. Self-owned tasks may be executed inline by the steward.
- **{{OPERATOR}}** — the human decision-maker. Owns all priority changes (Invariant 2). Endorses project completion. Resolves `status:needs-decision`. Reopens closed tasks (done is absorbing; only a human can reopen).
- **Other agents / humans** — execute dispatched tasks; report results via chat; do not write to the registry directly.

## 3. Label taxonomy

| Label | Meaning |
|---|---|
| `project` | Epic issue (exactly one per project) |
| `task` | Task issue belonging to a project |
| `project:<slug>` | Membership — ties task issues to their project epic |
| `owner:<actor>` | Accountable party (human or agent name). Distinct from the executor. |
| `agent:<name>` | Currently executing agent (may differ from owner) |
| `waiting-on:<actor>` | **Open loop** — a person or agent *outside* this registry owes a response before this moves. Only the human can close it (§14); the standard drafts the chase, never sends it. |
| `status:active` | Being worked; steward manages normally |
| `status:blocked` | External dependency blocking progress (state blocker in a comment) |
| `status:needs-decision` | Blocked on the named owner's decision. Reserved for genuine blocks — never used simply because a human owns a task. |
| `status:paused` | Deliberately on hold; steward skips it (no staleness escalation) |
| `status:pending-verification` | Agent claimed completion; awaiting DoD verification by the steward |
| `status:unclassified` | Auto-stubbed workspace folder not yet classified. Excluded from all projections and priority. |
| `priority:p1` | High — steward reviews first, fastest escalation, never auto-demoted |
| `priority:p2` | Normal — standard tracking and escalation |
| `priority:p3` | Low — may appear in digest-only mode |

**Invariant 2 — Priority is human-only.** Portfolio priority (`priority:*`) changes ONLY by explicit human speech act (a conversation with the orchestrator, with the reason logged as a comment). Observed behavior (staleness, non-response, projection gestures) is an evidence stream — may trigger a question, never a silent priority write. Projections display priority read-only (e.g. `[P1]` prefix in the task view).

Rules: every epic carries `project`, exactly one `status:*`, one `priority:*`, and at least one `owner:*`. Task issues carry `task`, `project:<slug>`, `owner:*`, `priority:pN`, and optionally `agent:*` when assigned. Labels are created idempotently by `/project-init`.

## 4. Epic issue anatomy

Title: `[Project] <Name>`

Body (all sections required; `Current status` is steward-maintained — never hand-edit it):

```
## Goal
One paragraph: what done looks like and why it matters.

## Success criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2

## Workspace
`project_files/<slug>/`

## Owners
- <actor-name> — <what they own in this project>

## Cadence
Timing, deadlines, review rhythm, or "as needed".

## Current status
(maintained by /project-steward — do not hand-edit; latest steward update wins)

## Tasks
- [ ] #NN Task title (checked when the task issue closes)
```

## 5. Task issue anatomy

Title: plain imperative (`Draft the trademark response letter`), no prefix.

Labels: `task` + `project:<slug>` + `owner:<actor>` + `priority:pN` + optional `agent:<name>`.

Body (all sections required; created only via `/project-task`):

```
## Objective
What this task accomplishes.

## Definition of Done
- [ ] Concrete, checkable finish line item 1
- [ ] Concrete, checkable finish line item 2

## Context
Links: epic #NN, relevant files, prior work.

## Validation
- [ ] {{AGENT_NAME}} — verify all Definition of Done items against the done claim
```

**Completion lattice (Invariant 3):**
```
open → pending-verification → done
```
- **Human completion**: the operator (or human owner, on explicit instruction) closes the issue directly → writes `status:done`. Done is absorbing — only a human can reopen.
- **Agent completion**: agent posts a done claim comment → steward sets `status:pending-verification` → steward verifies against the Definition of Done → pass: closes done with verification comment; fail: reopens with reason.
- **Max-age on pending-verification**: if unverifiable after {{PV_MAX_AGE}} hours, escalate to operator (`status:needs-decision` + notify). Never pool silently.

The `## Validation` section is the approval chain. v1 default = single verifier (the managing agent). Enabling multi-step chains later = adding more rows, not a schema change.

## 6. Verification protocol

The steward verifies a `pending-verification` task:

1. Read the task's `## Definition of Done` checklist.
2. Check each item against the agent's done-claim comment.
3. **All items verifiable** → comment `[Verified] All DoD items confirmed: <summary>`, set `status:done`, close the issue, check it off in the epic's Tasks list.
4. **Any item unverifiable** → comment `[Verification failed] <which item and why>`, remove `pending-verification`, restore `status:active`, note in digest for owner.
5. **Past {{PV_MAX_AGE}}h with no verifiable evidence** → `status:needs-decision` + notify operator. Never let it pool silently.

## 7. Comment conventions (written only by the managing agent)

**Steward update** — posted only when something changed since the last update:
```
### Steward update YYYY-MM-DD HH:MM
- Status: active | blocked | needs-decision | paused | pending-verification
- Since last: <what happened, or "no activity">
- Dispatched: <agent> — task #NN | none
- Verified: task #NN pass | task #NN fail | none
- Blockers: <blocker> | none
- Next: <planned next action>
```

**Dispatch receipt** — on task issue at dispatch time:
```
### Dispatched YYYY-MM-DD
Sent to `<agent>` via Trinity chat. Expected deliverable: <summary>.
```

**Done claim** — posted by the executing agent when claiming completion:
```
### Done claim YYYY-MM-DD
<Summary of what was done>
DoD check:
- [x] <item 1>: <evidence or link>
- [x] <item 2>: <evidence or link>
```

**Agent report relay** — posted by the steward after reconciling a chat reply:
```
### Agent report YYYY-MM-DD (<agent>)
<verbatim or tightly summarized result, with links/paths>
```

**Waiting-on notice** — posted when a task parks on someone outside the registry (§14):
```
### Waiting on <actor> — YYYY-MM-DD
Asked: <what was asked, one line>
Channel: <email | Slack | call | letter | agent chat>
Expected back: <date, or "no commitment">
Closes when: <the observable answer or artifact that ends the wait>
```

**Loop closed** — posted when an open loop resolves, whichever way it resolved:
```
### Loop closed YYYY-MM-DD — <answered | dropped | routed around>
<what came back, or why we stopped waiting>
```

## 8. Staleness and escalation policy (Invariant 4)

**Escalation never mutates P1/P2 priority.** The system may change how it asks (channel, framing, frequency) — never what it claims the human values.

| Condition | Action |
|---|---|
| Active project, 7 days no activity | Steward investigates: reads workspace + open tasks, dispatches or explains the stall |
| Active project, 14 days no activity | `status:needs-decision` + top of digest + notify operator (still P1/P2 — no auto-demotion) |
| P1/P2, repeated no response | Surface again next run (×2 total), then out-of-band diagnostic ping: "bounced 3×: blocked, mis-framed, or delegable?" Still P1/P2. |
| Dispatch, 6h no reply | One re-ping via chat |
| Dispatch, 24h no reply (re-ping sent) | `status:blocked` + digest escalation; no further auto-pings |
| `pending-verification` past {{PV_MAX_AGE}}h | `status:needs-decision` + notify operator |
| P3 only, 21 days no activity | Digest-only mention; no notification |
| `waiting-on:*` unanswered 3 days | Digest "Your open loops" + a drafted nudge for {{OPERATOR}} to send. The system never contacts the third party itself (§14). |
| `waiting-on:*` unanswered, every 7 days after that | Re-draft the nudge, age called out, notify |
| `waiting-on:*` unanswered 14 days | `status:needs-decision` — chase harder, drop it, or route around it. Never auto-dropped. |
| Operator ask (`status:needs-decision`) unanswered across 2 digests | Move to the top of the digest with its age stated. An ask is never retired by going stale (§14). |

## 9. Workspace discovery and quarantine (Invariant 6)

The steward auto-stubs any `project_files/<slug>/` folder with no corresponding epic into a quarantine epic (`status:unclassified`). The quarantine pass runs wherever `project_files/` is visible — it is idempotent and safe on any deployment config (local-only, git-synced container, or absent entirely when workspaces live elsewhere). Unclassified projects are:
- Excluded from all projections
- Excluded from priority tracking (no priority label)
- Classified lazily: one batch line in the weekly digest ("N unclassified folders: <names>"), never per-item interrupts
- Never attention-dependent between classification passes

## 10. Dispatch protocol (Invariant 1 + cross-actor)

1. **Explicit ownership only.** Dispatch only to the agent named by the task's `agent:*` label. Never fuzzy-match at runtime; ambiguity → `status:needs-decision`.
2. **Health check first.** `mcp__trinity__get_agent_health` before dispatch when Trinity is available; unhealthy → `status:blocked`, digest.
3. **One open dispatch per project, max 3 per steward run.**
4. **Standard dispatch brief:**
```
[PROJECT DISPATCH] <project name> — <task title>
Issue: <task issue URL>
Objective: <from task body>
Definition of done: <from task body>
Context: <key links/paths>
Deliverable: reply in this chat with a done claim (format: "### Done claim YYYY-MM-DD / summary / DoD check with evidence").
{{AGENT_NAME}} relays your reply to the issue log — do not attempt to write GitHub issues.
```
5. **Self-dispatch rule.** Tasks labeled `agent:{{AGENT_NAME}}` are NEVER dispatched via Trinity (would loop). Execute inline if they fit the run budget; otherwise list in digest as manager to-dos.
6. **Trinity is optional.** When Trinity MCP is unavailable, the steward runs in triage-only mode: GitHub operations (labels, comments, verification) continue; dispatch is skipped and noted in the digest. No state is lost — next healthy run resumes.

## 11. Projection contract (Invariant 5)

Projections are external views of the registry (Google Tasks, Fibery, etc.). The registry is write-authoritative; projections are read-only displays with one-directional gesture processing.

**Projection key:** each projected item carries the registry issue number as a text contract: `[#NN]` prefix in the item title. The reconciler uses this as the join key.

**Gesture typing by reversibility:**
| Gesture | What it means | Registry effect |
|---|---|---|
| check / mark complete | Completion endorsement | If owner is human → close done directly. If owner is agent → set `pending-verification`. |
| date-push / reschedule | Defer acknowledgement | No registry write. Logged as evidence signal; surfaced in next reconcile report. |
| delete / remove | Soft-skip proposal | Not authoritative. Registry item survives. Logged; confirmed at next review. |

**Absence is never authoritative.** An item missing from a projection could be filtered, unsynced, or stale — never act on absence.

**Unkeyed items are personal and out of scope.** A projection item with no `[#NN]` key is treated as a personal reminder — the reconciler counts them but does not alert. Sync-gap alerts fire only for keyed items (`[#NN]`) whose issue number does not resolve in the registry.

**Adapter contract** (implement this to add a new projection surface):
```
read_projection() → list of {key: "[#NN]", title, status, due_date, raw}
write_item(key, title, priority_prefix, due_date, note) → void
mark_complete(key) → void
```
The reconciler calls these methods. See Google Tasks adapter v1 in `/project-reconcile` for a reference implementation.

## 12. Pending-verification max age

`PENDING_VERIFICATION_MAX_AGE_HOURS = {{PV_MAX_AGE}}`

Deployers: edit this number to match your team's review SLA.

## 13. Intake contract

Intake skills and domain skills may write workspace content freely (`project_files/<slug>/`). Work items enter the registry ONLY through `/project-intake`. Material state changes (decisions, status shifts, blockers) land as a one-line comment on the relevant epic. Intake skills NEVER write projection surfaces directly — only `/project-reconcile` touches projections.

| Writer | May write | Must not write |
|---|---|---|
| Intake / domain skills | `project_files/<slug>/` | GitHub task issues directly (use `/project-intake`) |
| `/project-intake` | GitHub task issues, epic one-line state-news comments | Projection surfaces |
| `/project-reconcile` | Projection surfaces, reconcile log | Registry task issues (read-only; gesture processing is the one exception) |
| `/project-steward` | GitHub issue labels, comments, steward state | Projection surfaces |

## 14. Loop closure (Invariant 7)

**Invariant 7 — No loop closes by silence.** Every request that enters this system leaves it with an explicit answer delivered to whoever opened it. A task that dies still gets a closing line; a question nobody answered gets re-asked, not forgotten; a wait nobody ended gets escalated, not quietly aged out. Silence is a failure mode, never an outcome.

Two directions, both tracked by {{AGENT_NAME}}.

### 14a. Inbound — loops {{AGENT_NAME}} owes {{OPERATOR}}

Anything {{OPERATOR}} asked for, and anything {{AGENT_NAME}} promised, stays open until {{OPERATOR}} has been told the outcome **in a channel they actually read**. A comment on an issue nobody opened is not closure.

1. **Every run ends with a closing statement** — what is now true, what is waiting on {{OPERATOR}}, and what {{AGENT_NAME}} will do next unprompted (or "nothing until you say"). Interactive skills print it as their last lines; the steward writes it as the digest's opening lines.
2. **Every ask is tracked until answered.** A `status:needs-decision` item carries its age in every subsequent digest. Unanswered across two digests → it moves to the top with the age stated. An ask is never retired for being stale.
3. **Dead work is closed out loud.** Superseded, rejected, or obsolete tasks get a `### Loop closed` comment naming why, then close. Nothing rots silently in `open`.
4. **Report to the person, not just to the record.** Results of work {{OPERATOR}} personally initiated go to them via notification *in addition to* the issue log.

### 14b. Outbound — loops {{OPERATOR}} owes other people or agents

Work regularly parks on someone this system cannot dispatch to: a client, a lawyer, a vendor, a colleague, an agent in another fleet. Only the human can close those — so {{AGENT_NAME}}'s job is to make them impossible to forget.

1. **Name the loop.** Label the task `waiting-on:<actor>` and post the `### Waiting on` comment (§7): who, what was asked, what closing it looks like.
2. **Age it in public.** Every digest carries a **Your open loops** section — every `waiting-on:*` task, oldest first, with its age and the one sentence that would close it.
3. **Hand over a ready-to-send nudge.** At 3 days unanswered, and weekly after that, the digest includes a drafted follow-up message {{OPERATOR}} can send as-is. **Drafting is the agent's job; sending is the human's** — {{AGENT_NAME}} never contacts a third party on {{OPERATOR}}'s behalf under this standard. External effects stay gated behind a human.
4. **Force the call at 14 days.** A loop nobody answered in two weeks is usually dead: `status:needs-decision` asking {{OPERATOR}} to chase harder, drop it, or route around it. Never auto-dropped.
5. **Fleet agents are dispatches, not waiting-on.** If the counterpart is an agent this system can reach, it is a dispatch (§10) with its own re-ping ladder. `waiting-on:` is only for actors outside the dispatch protocol.

**Closing is a write.** When a loop resolves — answered, dropped, or routed around — post `### Loop closed` (§7), remove the `waiting-on:*` label, and note it in the next digest. An unrecorded close is indistinguishable from a forgotten one.

*Deployers: the 3-day nudge / 7-day re-nudge / 14-day decision ladder is the default. Edit these numbers to match how your counterparties actually respond.*
```

Substitute all `{{AGENT_NAME}}` with `$AGENT_NAME`, `{{OPERATOR}}` with `$OPERATOR`, `{{REGISTRY}}` with `$REGISTRY`, `{{DATE}}` with `$DATE`, `{{PV_MAX_AGE}}` with `$PV_MAX_AGE` before writing.

### Step 6: Write /project-init skill

Write `.claude/skills/project-init/SKILL.md`:

````markdown
---
name: project-init
description: Create or adopt a long-term managed project per PROJECT_STANDARD.md — GitHub epic issue with idempotent label creation and a project_files/<slug>/ workspace stub. Use when starting a new multi-session project or bringing an existing project folder under management.
argument-hint: "[project name | adopt <existing-folder>]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.0: Initial version — owner/agent label distinction, unclassified quarantine, full Epic anatomy per PROJECT_STANDARD.md §4"
---

# Project Init

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-init v1.0 — recent: Initial version`. Then proceed.

## Purpose

Bring a long-term project under standardized management: create the GitHub epic issue (registry entry) and the local workspace stub, both conforming to `PROJECT_STANDARD.md`. After init, `/project-steward` manages the project autonomously.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) | Yes | No |
| GitHub issues + labels | the `$REGISTRY` repo via `gh` | Yes | Yes |
| Project workspace | `project_files/<slug>/` | Yes | Yes |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. Resolve `$REGISTRY`, `$AGENT_NAME`, and `$OPERATOR` from §1 and §2. These override any remembered values.

### Step 2: Verify gh access

```bash
gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1
```

If this returns an error (403, 404, or "Resource not accessible"), stop and report exactly what failed. The PAT must have `repo` + `issues` scope on `$REGISTRY`.

### Step 3: Gather inputs

Determine mode from the argument: `adopt` (argument starts with "adopt" or names an existing `project_files/` folder) or `new` (default).

For `adopt` mode: read the existing folder (look for `project.md`, `README.md`, any status files) and draft goal/criteria from what's there.

Use AskUserQuestion for inputs that cannot be determined from context:
- **Name** (derive slug as kebab-case; confirm no collision with existing epics)
- **Goal** (one paragraph)
- **Success criteria** (2–5 checkable items)
- **Owner(s)** — who is accountable (human names and/or agent names)
- **Priority** — default `p2`
- **Cadence** — default "as needed"

### Step 4: Check for collisions

```bash
gh issue list --repo "$REGISTRY" --label project --state all --search "$NAME" --json number,title,labels
ls -d project_files/$SLUG 2>/dev/null
```

If an epic already exists for this project, stop and show it — offer to update instead.

### Step 5: Ensure labels exist (idempotent)

Create any missing labels from the standard's taxonomy. All `2>/dev/null || true` so re-runs are safe:

```bash
gh label create "project" --repo "$REGISTRY" --color "0e8a16" --description "Project epic issue" 2>/dev/null || true
gh label create "task" --repo "$REGISTRY" --color "c2e0c6" --description "Task belonging to a project" 2>/dev/null || true
gh label create "status:active" --repo "$REGISTRY" --color "1d76db" --description "Being worked" 2>/dev/null || true
gh label create "status:blocked" --repo "$REGISTRY" --color "d93f0b" --description "External dependency blocking progress" 2>/dev/null || true
gh label create "status:needs-decision" --repo "$REGISTRY" --color "fbca04" --description "Blocked on owner decision" 2>/dev/null || true
gh label create "status:paused" --repo "$REGISTRY" --color "cccccc" --description "Deliberately on hold" 2>/dev/null || true
gh label create "status:pending-verification" --repo "$REGISTRY" --color "e4e669" --description "Agent claimed done; awaiting DoD verification" 2>/dev/null || true
gh label create "status:unclassified" --repo "$REGISTRY" --color "f9d0c4" --description "Auto-stubbed workspace folder not yet classified" 2>/dev/null || true
gh label create "priority:p1" --repo "$REGISTRY" --color "b60205" --description "High priority" 2>/dev/null || true
gh label create "priority:p2" --repo "$REGISTRY" --color "ff9f1c" --description "Normal priority" 2>/dev/null || true
gh label create "priority:p3" --repo "$REGISTRY" --color "c5def5" --description "Low priority" 2>/dev/null || true
# Project-specific labels
gh label create "project:$SLUG" --repo "$REGISTRY" --color "5319e7" --description "Membership: project $NAME" 2>/dev/null || true
for OWNER in $OWNERS; do
  gh label create "owner:$OWNER" --repo "$REGISTRY" --color "0052cc" --description "Accountable: $OWNER" 2>/dev/null || true
done
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
`project_files/$SLUG/`

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
  --label "project,project:$SLUG,status:active,priority:$PRIORITY" \
  --body-file /tmp/epic-body.md
```

For each owner, add the `owner:<name>` label:
```bash
for OWNER in $OWNERS; do
  gh issue edit $ISSUE_NUMBER --repo "$REGISTRY" --add-label "owner:$OWNER"
done
```

### Step 7: Scaffold the workspace

**New mode:** create `project_files/$SLUG/` and write `project.md` mirroring the epic:

```bash
mkdir -p project_files/$SLUG
```

Write `project_files/$SLUG/project.md` with: the epic issue URL, goal, success criteria, owner list, cadence, and a note that the epic is the authoritative record.

**Adopt mode:** keep the existing folder; create or update `project.md` to add the epic URL and charter sections. Record the actual folder path in the epic body's Workspace field (may differ from the slug).

### Step 8: Summary

Print:
```
## Project initialized: $NAME

Epic:      $EPIC_URL
Workspace: project_files/$SLUG/
Labels:    project, project:$SLUG, status:active, priority:$PRIORITY, owner:<...>

Next steps:
  /project-task — create the first task
  /project-steward — run a sweep (or let the schedule do it)
```
````

### Step 7: Write /project-task skill

Write `.claude/skills/project-task/SKILL.md`:

````markdown
---
name: project-task
description: Create a task issue in the uniform format per PROJECT_STANDARD.md — the ONLY sanctioned task-creation path. Enforces full anatomy (Objective / Definition of Done / Context / Validation) and adds the task to the parent epic's Tasks checklist. Approval-ready from day one. Supports --headless for cron/compose use.
argument-hint: "[project-slug | --headless --project=<slug> --title=\"...\" --objective=\"...\" --dod=\"item1|item2\" --owner=<actor> [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--context=\"...\"]]"
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
metadata:
  version: "1.2"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.2: Loop closure — optional waiting-on actor (label + ### Waiting on comment) puts a task parked on an outside party into the steward's aging ladder; interactive output ends with the §14a closing statement (waiting on you / next without you)"
    - "1.1: Add --headless mode — all fields as arguments, no AskUserQuestion, returns issue number; callable from /project-intake and crons"
    - "1.0: Initial version — full anatomy enforcement including Validation section (approval chain), owner/agent label distinction, epic checklist update"
---

# Project Task

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-task v1.2 — recent: loop closure (waiting-on + closing statement)`. Then proceed.

## Purpose

Create a task issue in the uniform format. This is the **only sanctioned way to create task issues** in a managed project — it enforces the full anatomy including the `## Validation` section (the approval chain), applies the correct labels, and links the task into the parent epic's checklist.

**Never create task issues directly via `gh issue create` outside this skill.** The anatomy enforcement and epic linkage are the point.

## Modes

**Interactive mode** (default): run as `/project-task [project-slug]`. Collects missing fields via AskUserQuestion. For human use.

**Headless mode**: run with `--headless` and all fields as arguments. Never calls AskUserQuestion. Returns just the created issue number on stdout. For use by `/project-intake`, crons, and other skills that compose task creation programmatically.

Headless arguments:
| Argument | Required | Notes |
|---|---|---|
| `--project=<slug>` | yes | Project slug from `project:<slug>` label |
| `--title="..."` | yes | Plain imperative title |
| `--objective="..."` | yes | What this task accomplishes |
| `--dod="item1\|item2"` | yes | Pipe-separated DoD items |
| `--owner=<actor>` | yes | Accountable party |
| `--priority=pN` | no | Default: inherit from epic |
| `--agent=<name>` | no | Executing agent label (if immediately assignable) |
| `--waiting-on=<actor>` | no | Parks the task as an open loop on an actor outside the registry — applies `waiting-on:<actor>` and posts the `### Waiting on` comment (standard §14b) |
| `--context="..."` | no | Additional context beyond the epic link |

In headless mode, if any required argument is missing, exit immediately with: `ERROR: --<field> is required in headless mode`

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (new issue + epic edit) |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. Resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2.

### Step 2: Select parent project

**Headless mode**: parse `--project` from `$ARGUMENTS`. Fetch the epic directly:
```bash
gh issue list --repo "$REGISTRY" --label "project:$PROJECT_SLUG" --label project --state open \
  --json number,title,labels,body -q '.[0]'
```
If not found, exit with `ERROR: No open epic found for project:$PROJECT_SLUG`.

**Interactive mode**: if `$ARGUMENTS` names a project slug, use it. Otherwise list active projects:
```bash
gh issue list --repo "$REGISTRY" --label project --state open \
  --json number,title,labels --limit 20
```
Ask the user which project this task belongs to. Resolve the slug from the `project:<slug>` label on the chosen epic.

### Step 3: Gather task inputs

**Headless mode**: read all fields directly from `--` arguments (no AskUserQuestion). If a required argument is missing, exit with `ERROR: --<field> is required in headless mode`. Parse `--dod` by splitting on `|` to produce the checklist items.

**Interactive mode**: use AskUserQuestion:
- **Title** — plain imperative sentence (e.g. "Draft the trademark response letter")
- **Objective** — what this task accomplishes (1–2 sentences)
- **Definition of Done** — 2–5 concrete, checkable finish-line items
- **Context** — links to epic, relevant files, prior work
- **Owner** — who is accountable (human or agent name)
- **Assigned agent** (optional) — if ready to dispatch now, which agent executes it? Leave blank if not yet assigned.
- **Priority** — default: inherit from the parent epic
- **Waiting on** (optional) — is this parked on a response from someone *outside* this registry (a client, vendor, colleague, another fleet's agent)? Name them. This applies `waiting-on:<actor>` and posts the `### Waiting on` comment, which is what puts the loop into the steward's aging ladder and the operator's digest (standard §14b). A loop nobody named is a loop nobody chases.

### Step 4: Build the Validation section

The `## Validation` section is the approval chain. v1 default = one row: the managing agent verifies all DoD items against the done claim. If the user specifies additional validators (humans or agents), add them as additional rows in the checklist. Each row format: `- [ ] <validator> — <what they check>`.

Default (v1):
```
## Validation
- [ ] $AGENT_NAME — verify all Definition of Done items against the done claim
```

Multi-step example (when user requests):
```
## Validation
- [ ] $AGENT_NAME — verify all Definition of Done items against the done claim
- [ ] $HUMAN_REVIEWER — final approval before closing
```

### Step 5: Create the task issue

```bash
cat > /tmp/task-body.md << 'EOF'
## Objective
$OBJECTIVE

## Definition of Done
$DOD_ITEMS

## Context
Epic: $EPIC_URL
$CONTEXT

## Validation
$VALIDATION_ROWS
EOF

gh issue create --repo "$REGISTRY" \
  --title "$TITLE" \
  --label "task,project:$SLUG,owner:$OWNER,priority:$PRIORITY" \
  --body-file /tmp/task-body.md
```

If an assigned agent was named, add the `agent:*` label:
```bash
gh issue edit $TASK_NUMBER --repo "$REGISTRY" --add-label "agent:$ASSIGNED_AGENT"
```

If a **waiting-on** actor was named, create the label idempotently, apply it, and post the `### Waiting on` comment per standard §7 (who, what was asked, channel, what closes it):
```bash
gh label create "waiting-on:$WAITING_ON" --repo "$REGISTRY" --color "d4c5f9" \
  --description "Open loop: awaiting $WAITING_ON" 2>/dev/null || true
gh issue edit $TASK_NUMBER --repo "$REGISTRY" --add-label "waiting-on:$WAITING_ON"
```

### Step 6: Link into parent epic

Add the task to the epic's `## Tasks` checklist:

```bash
# Get current epic body
gh issue view $EPIC_NUMBER --repo "$REGISTRY" --json body -q .body > /tmp/epic-current.md

# Append to Tasks section
# Find the ## Tasks line and append after the last checklist item (or after the header if empty)
# Then update the epic body
gh issue edit $EPIC_NUMBER --repo "$REGISTRY" --body-file /tmp/epic-updated.md
```

The appended line format: `- [ ] #$TASK_NUMBER $TITLE`

### Step 7: Output

**Headless mode**: print exactly one line — the issue number — and exit:
```
#$TASK_NUMBER
```

**Interactive mode**: print the full summary, ending with the closing statement required by standard §14a — what is now true, what is waiting on the human, and what happens next without them:
```
Task created: #$TASK_NUMBER — $TITLE
Project:      [Project] $PROJECT_NAME (epic #$EPIC_NUMBER)
Owner:        $OWNER
Priority:     $PRIORITY
Validation:   $VALIDATION_SUMMARY
Waiting on:   $WAITING_ON (open loop — you close this one) | nobody

Waiting on you: <the one thing, or "nothing">
Next without you: <what the steward will do on its own, or "nothing until you say">
```
````

### Step 8: Write /project-steward skill

Write `.claude/skills/project-steward/SKILL.md`. Substitute `$SCHEDULE` for the schedule from Step 2 (omit the `schedule:` line entirely if manual-only was chosen):

````markdown
---
name: project-steward
description: Autonomous sweep of all managed projects per PROJECT_STANDARD.md. Verifies pending-verification claims against Definition of Done, dispatches next work to explicitly-labeled owner agents (Trinity when available; triage-only when not), escalates stalls per the staleness policy, sweeps open loops (ages every waiting-on item and drafts the operator's follow-ups), runs the quarantine classification pass, and writes a digest that closes the loop with the operator. Never asks a human anything mid-run.
automation: autonomous
schedule: "$SCHEDULE"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
effort: high
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
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

Read `PROJECT_STANDARD.md`. Resolve:
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
````

### Step 9: Write /project-reconcile skill

Write `.claude/skills/project-reconcile/SKILL.md`:

````markdown
---
name: project-reconcile
description: Sync projection adapters against the GitHub Issues registry per PROJECT_STANDARD.md. Processes projection gestures (check/date-push/delete) back into the registry with correct reversibility typing. Ships with Google Tasks adapter v1 (notes-field [#NN] key). Other adapters are per-deployment extensions. Reconciler is idempotent; refuses unkeyed items with a sync-gap alert.
argument-hint: "[adapter] — default: google-tasks"
allowed-tools: Bash, Read, Write, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.0: Initial version — generic adapter contract, Google Tasks adapter v1 with gesture typing, idempotent reconciler, sync-gap alerts for unkeyed items"
---

# Project Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-reconcile v1.0 — recent: Initial version`. Then proceed.

## Purpose

Sync projection surfaces (personal task views, team tools) against the GitHub Issues registry. The registry is write-authoritative; projections are read-only displays with one-directional gesture processing.

**Key rules (Invariant 5):**
- Projections display state; they do not own it.
- `[#NN]` prefix in the projection item title is the join key — unkeyed items cannot be synced.
- Gestures are typed by reversibility: check (completion endorsement), date-push (defer signal, no registry write), delete (soft-skip proposal, registry item survives).
- Absence is never authoritative.

## Adapters

This skill ships with the **Google Tasks adapter v1**. Other adapters (Fibery, Notion, Linear, etc.) follow the adapter contract in `PROJECT_STANDARD.md §11` and are per-deployment extensions — copy this skill, implement the three adapter methods, and register your adapter in the dispatch block below.

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. Resolve `$REGISTRY`, `$AGENT_NAME`, and `$PV_MAX_AGE`.

### Step 2: Select adapter

If `$ARGUMENTS` names an adapter (`google-tasks`, `fibery`, etc.), use it.

Otherwise ask:
- **Header:** "Projection adapter"
- **Options:** "google-tasks" (built-in) or a custom adapter name (per PROJECT_STANDARD.md §11)

### Step 3: Load registry state

Fetch all open task issues from the registry:
```bash
gh issue list --repo "$REGISTRY" --label task --state open \
  --json number,title,labels,body,url --limit 200
```

Also fetch recently closed issues (to detect completion gestures for already-closed items):
```bash
gh issue list --repo "$REGISTRY" --label task --state closed \
  --json number,title,labels,closedAt --limit 50
```

Build a registry map: `{issue_number → {title, status, priority, owner, url, is_closed}}`.

### Step 4: Load projection (adapter-specific)

**Google Tasks adapter v1:**

Check for `GOOGLE_TASKS_TOKEN` env var:
```bash
echo "${GOOGLE_TASKS_TOKEN:-MISSING}"
```
If missing, stop and explain: "Set `GOOGLE_TASKS_TOKEN` in your `.env` to a valid OAuth2 access token with `tasks` scope. Get one with `gcloud auth print-access-token` or a service account."

Select the task list:
```bash
curl -sf "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" | \
  python3 -c "import sys,json; lists=json.load(sys.stdin).get('items',[]); [print(f\"{i}: {l['id']} — {l['title']}\") for i,l in enumerate(lists)]"
```

If `GOOGLE_TASKS_LIST_ID` is set in env, use it. Otherwise show the list and ask which one to sync.

Fetch tasks from the selected list:
```bash
curl -sf "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks?showCompleted=true&showHidden=true&maxResults=100" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN"
```

Parse each task into: `{id, title, notes, status ("needsAction"|"completed"), due, updated}`.

Extract the `[#NN]` key from the title using: `echo "$TITLE" | grep -oP '(?<=\[#)\d+(?=\])'`

**Adapter contract (implement this for custom adapters):**
```python
# Three methods your adapter must expose:
def read_projection():
    # Returns: list of {key: "42"|None, title, status, due_date, raw}
    # key is None for unkeyed items (sync-gap alert)
    pass

def write_item(key, title, priority_prefix, due_date, note):
    # Push a registry item into the projection surface
    # priority_prefix: "[P1] " | "[P2] " | "[P3] " | ""
    pass

def mark_complete(key):
    # Mark the projection item as complete (used after registry closure confirmed)
    pass
```

### Step 5: Match and diff

For each projection item:
- **Unkeyed** (no `[#NN]` in title): personal reminder — increment `personal_count`, skip entirely. Do not add to sync-gap alerts. Personal items are out of scope for registry sync.
- **Keyed**: look up issue `#NN` in the registry map.
  - **Not in registry**: check recently-closed list. If not there either, this is a sync-gap (keyed but unresolvable — the issue number may be wrong or the issue was deleted). Add to `sync_gap_alerts`.
  - **Found**: record the pair for gesture detection.

For each matched pair, detect gestures:

| Condition | Gesture |
|---|---|
| Projection status = completed; registry not closed | **check** — completion endorsement |
| Projection has a due date and it changed since last sync | **date-push** — defer signal |
| Item was in last sync log but is now absent from projection | **delete** — soft-skip proposal |
| No change | no-op |

Read the last sync log (`project-steward/reconcile-log/google-tasks-YYYY-MM-DD.json` or the most recent) to detect deletions.

### Step 6: Apply registry updates (per gesture type)

**Check (completion endorsement):**
```bash
OWNER=$(gh issue view $NUMBER --repo "$REGISTRY" --json labels -q '.labels[].name | select(startswith("owner:"))' | head -1 | sed 's/owner://')
```

- If owner is a human (not in the agent list): this is a human endorsement → close the issue directly:
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection endorsement $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks by $OWNER. Closing as done per PROJECT_STANDARD.md §11 (human completion = direct done)."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "status:active" --add-label "status:done"
  gh issue close $NUMBER --repo "$REGISTRY" --reason completed
  ```
- If owner is an agent: set pending-verification:
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection signal $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks. Setting pending-verification for steward to verify against Definition of Done."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "status:active" --add-label "status:pending-verification"
  ```

**Date-push (defer signal):**
- No registry write.
- Log the event: `{issue_number, old_due, new_due, observed_at}` → append to reconcile log.
- Surface in the reconcile report as an evidence signal.

**Delete (soft-skip proposal):**
- No registry write (Invariant 5: registry item survives).
- Log the proposal: `{issue_number, title, proposed_at}` → append to reconcile log.
- Report for human confirmation in the reconcile summary.

**No-op:**
- Log that the item was checked and found in sync.

### Step 7: Push projection updates (registry → projection)

For each open registry task issue NOT in the projection:
- This is an item the projection is missing. Add it to the projection using `write_item`:
  - Title: `[#NN] <issue title>`
  - Priority prefix: `[P1] ` / `[P2] ` / `[P3] ` based on the issue's priority label (read-only display)
  - Note: the GitHub issue URL

For each registry issue now closed but still open in the projection:
- Call `mark_complete(key)` in the projection.

**Google Tasks — write item:**
```bash
curl -sf -X POST "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"[#$NUMBER] $PRIORITY_PREFIX$TITLE\", \"notes\": \"$ISSUE_URL\"}"
```

**Google Tasks — mark complete:**
```bash
curl -sf -X PATCH "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"status\": \"completed\"}"
```

### Step 8: Write sync log and report

Write `project-steward/reconcile-log/google-tasks-$(date -u +%Y-%m-%d).json`:
```json
{
  "adapter": "google-tasks",
  "list_id": "$LIST_ID",
  "run_at": "<ISO timestamp>",
  "matched": N,
  "personal_items": N,
  "gestures": {
    "check": [...],
    "date_push": [...],
    "delete_proposal": [...]
  },
  "sync_gap_alerts": [...],
  "registry_writes": [...],
  "projection_writes": [...]
}
```

Commit and push:
```bash
git add project-steward/reconcile-log && \
git commit -m "reconcile: google-tasks sync $(date -u +%Y-%m-%d)" && \
(git push origin main || (git pull --rebase --autostash origin main && git push origin main))
```

Print the reconcile report:
```
## Reconcile: google-tasks

Matched:        N of M projection items to registry issues
Personal items: N items skipped — no [#NN] key; out of scope for registry sync
Synced:         N items updated in projection (new/closed)

Gestures processed:
  check (completion endorsements): N
    → N human endorsements → closed done
    → N agent completions → pending-verification set
  date-push (defer signals): N (no registry writes — logged as evidence)
  delete (soft-skip proposals): N (registry items survive — confirm to action)

Sync-gap alerts (keyed items whose [#NN] number does not resolve in registry):
  - "[#NN] <title>" — issue #NN not found; check if deleted or number is wrong

Soft-skip proposals (awaiting confirmation):
  - #NN <title> — deleted from projection; confirm to close or ignore

Evidence log: project-steward/reconcile-log/google-tasks-YYYY-MM-DD.json
```

If there are sync-gap alerts (keyed but unresolvable) or soft-skip proposals, ask the user if they want to take action on them now. Personal items are never surfaced for action.
````

### Step 10: Write /project-intake skill

Write `.claude/skills/project-intake/SKILL.md`:

````markdown
---
name: project-intake
description: Headless intake primitive — routes actionable items from any source (meetings, email, Slack, issue trackers) into the GitHub Issues registry. Dedupes by meaning (not exact title), creates task issues with full anatomy (Objective / Definition of Done / Context / Validation), or posts one-line state-news comments on the relevant epic. Returns the issue number. Never interactive — called by other skills and crons.
argument-hint: "--project=<slug> --title=\"...\" --source=\"<url-or-note>\" [--owner=<actor>] [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--dod=\"item1|item2\"] [--objective=\"...\"] [--context=\"...\"] [--state-news]"
allowed-tools: Bash, Read, Grep
user-invocable: false
metadata:
  version: "1.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.1: Loop closure — optional --waiting-on opens the loop explicitly (label + ### Waiting on comment), so an item captured as \"X owes us an answer\" enters the steward's aging ladder instead of sitting silently in the backlog"
    - "1.0: Initial version — headless intake primitive, dedupe by meaning, task creation with full anatomy, state-news comment path, epic Tasks checklist linkage"
---

# Project Intake

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-intake v1.1 — recent: --waiting-on opens the loop explicitly`. Then proceed.

## Purpose

Route any actionable item from any source into the managed registry. **This skill is headless** — it never calls AskUserQuestion. It is called by domain skills, meeting-summary flows, crons, and composed pipelines. Output: the created or duplicate issue number.

**This skill is the only sanctioned programmatic path for creating task issues.** `/project-task` is for interactive human creation; `/project-intake` is for automated and composed creation.

## Arguments

| Argument | Required | Description |
|---|---|---|
| `--project=<slug>` | yes | Target project slug (from `project:<slug>` label) |
| `--title="..."` | yes | Plain imperative title for the actionable item |
| `--source="..."` | yes | URL or short description of origin (meeting link, email subject, Slack permalink, ticket URL) |
| `--owner=<actor>` | no | Accountable party. Defaults to the project's primary owner from the epic. |
| `--priority=pN` | no | p1/p2/p3. Inherits from epic if omitted. |
| `--agent=<name>` | no | Executing agent label if immediately assignable. |
| `--waiting-on=<actor>` | no | The item is parked on an actor outside the registry — applies `waiting-on:<actor>` and posts the `### Waiting on` comment so the steward ages it and the operator sees it in "Your open loops" (standard §14b). Use this whenever intake captures "X owes us an answer". |
| `--dod="item1\|item2"` | no | Pipe-separated DoD items. Default: single item derived from title. |
| `--objective="..."` | no | Objective text. Defaults to the title. |
| `--context="..."` | no | Additional context beyond the source link. |
| `--state-news` | no | Flag: item is project-state news, not a task. Post a one-line comment on the epic; return `EPIC:#NN`. |

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (task issue + epic checklist or one-line comment) |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. Resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2.

### Step 2: Parse and validate arguments

Parse all `--key=value` and flag arguments from `$ARGUMENTS`.

Validate:
- `--project` present → look up the epic:
  ```bash
  gh issue list --repo "$REGISTRY" --label "project:$PROJECT_SLUG" --label project --state open \
    --json number,title,labels,body -q '.[0]'
  ```
  If no epic found: exit with `ERROR: No open epic for project:$PROJECT_SLUG`
- `--title` present. If missing: exit with `ERROR: --title is required`
- `--source` present. If missing: exit with `ERROR: --source is required`

Resolve defaults from the epic:
- `OWNER`: if not provided, extract from epic's `owner:*` labels (first match).
- `PRIORITY`: if not provided, read from epic's `priority:*` label.
- `OBJECTIVE`: if not provided, use the title.
- `DOD`: if not provided, generate: `- [ ] $TITLE completed and verified against source`

### Step 3: State-news path

If `--state-news` flag is set:

Post a one-line comment on the epic:
```bash
gh issue comment $EPIC_NUMBER --repo "$REGISTRY" \
  --body "**State update** ($(date -u +%Y-%m-%d)): $TITLE — source: $SOURCE"
```

Output exactly: `EPIC:$EPIC_NUMBER`

Exit.

### Step 4: Deduplicate by meaning

Fetch all open task issues for this project:
```bash
gh issue list --repo "$REGISTRY" \
  --label "task" --label "project:$PROJECT_SLUG" \
  --state open --json number,title --limit 100
```

For each existing issue title, check if the incoming title means the same thing:

1. **Exact title match** (case-insensitive) → definite duplicate.
2. **Semantic overlap**: tokenize both titles, strip common stop words (a, an, the, and, or, for, to, of, in, on, at, by, with, from, into), compare the core verb+noun tokens. If ≥ 70% of the incoming tokens appear in an existing title (or vice versa), treat as duplicate.

On duplicate detected: output `DUPLICATE:#$EXISTING_NUMBER` and exit.

If no duplicate, proceed.

### Step 5: Ensure owner label exists

```bash
gh label create "owner:$OWNER" --repo "$REGISTRY" \
  --color "0052cc" --description "Accountable: $OWNER" 2>/dev/null || true
```

### Step 6: Create the task issue

Build the body:

```bash
cat > /tmp/intake-body.md << 'INTAKEBODY'
## Objective
$OBJECTIVE

## Definition of Done
$DOD_ITEMS

## Context
Epic: $EPIC_URL
Source: $SOURCE
$EXTRA_CONTEXT

## Validation
- [ ] $AGENT_NAME — verify all Definition of Done items against the done claim
INTAKEBODY
```

(Substitute all variables before writing; omit `$EXTRA_CONTEXT` line if `--context` was not provided.)

Create the issue:
```bash
gh issue create --repo "$REGISTRY" \
  --title "$TITLE" \
  --label "task,project:$PROJECT_SLUG,owner:$OWNER,priority:$PRIORITY" \
  --body-file /tmp/intake-body.md
```

Capture `$TASK_NUMBER` from the output URL (`...issues/NN`).

If `--agent` was provided:
```bash
gh issue edit $TASK_NUMBER --repo "$REGISTRY" --add-label "agent:$ASSIGNED_AGENT"
```

If `--waiting-on` was provided, open the loop explicitly (label + `### Waiting on` comment per standard §7) so it enters the steward's aging ladder rather than sitting silently:
```bash
gh label create "waiting-on:$WAITING_ON" --repo "$REGISTRY" --color "d4c5f9" \
  --description "Open loop: awaiting $WAITING_ON" 2>/dev/null || true
gh issue edit $TASK_NUMBER --repo "$REGISTRY" --add-label "waiting-on:$WAITING_ON"
gh issue comment $TASK_NUMBER --repo "$REGISTRY" --body "### Waiting on $WAITING_ON — $(date -u +%Y-%m-%d)
Asked: $TITLE
Channel: $SOURCE
Expected back: no commitment recorded
Closes when: $WAITING_ON responds — see Definition of Done"
```

### Step 7: Link into parent epic

Read the current epic body, append the new task to the `## Tasks` checklist, and update:
```bash
gh issue view $EPIC_NUMBER --repo "$REGISTRY" --json body -q .body > /tmp/intake-epic.md
# Append the new task line to the Tasks section
printf '\n- [ ] #%s %s' "$TASK_NUMBER" "$TITLE" >> /tmp/intake-epic.md
gh issue edit $EPIC_NUMBER --repo "$REGISTRY" --body-file /tmp/intake-epic.md
```

(Insert the line after the last existing checklist item in `## Tasks`, or directly after the `## Tasks` header if the section is empty.)

### Step 8: Output

Print exactly one line and exit:
```
#$TASK_NUMBER
```
````

### Step 11: Create GitHub labels

Create all labels needed by the standard. All operations are idempotent (`2>/dev/null || true`):

```bash
gh label create "project" --repo "$REGISTRY" --color "0e8a16" --description "Project epic issue" 2>/dev/null || true
gh label create "task" --repo "$REGISTRY" --color "c2e0c6" --description "Task belonging to a project" 2>/dev/null || true
gh label create "status:active" --repo "$REGISTRY" --color "1d76db" --description "Being worked" 2>/dev/null || true
gh label create "status:blocked" --repo "$REGISTRY" --color "d93f0b" --description "External dependency blocking progress" 2>/dev/null || true
gh label create "status:needs-decision" --repo "$REGISTRY" --color "fbca04" --description "Blocked on owner decision" 2>/dev/null || true
gh label create "status:paused" --repo "$REGISTRY" --color "cccccc" --description "Deliberately on hold" 2>/dev/null || true
gh label create "status:pending-verification" --repo "$REGISTRY" --color "e4e669" --description "Agent claimed done; awaiting DoD verification" 2>/dev/null || true
gh label create "status:unclassified" --repo "$REGISTRY" --color "f9d0c4" --description "Auto-stubbed; not yet classified" 2>/dev/null || true
gh label create "priority:p1" --repo "$REGISTRY" --color "b60205" --description "High priority" 2>/dev/null || true
gh label create "priority:p2" --repo "$REGISTRY" --color "ff9f1c" --description "Normal priority" 2>/dev/null || true
gh label create "priority:p3" --repo "$REGISTRY" --color "c5def5" --description "Low priority" 2>/dev/null || true
```

Note: `owner:*`, `agent:*`, `waiting-on:*`, and `project:<slug>` labels are per-actor/per-project and are created dynamically — `owner:*`/`project:<slug>` by `/project-init`, `waiting-on:<actor>` by whichever skill first parks a task on that actor.

### Step 12: Update CLAUDE.md

Read the current CLAUDE.md and append a Project Management section if it doesn't already exist:

```markdown
## Project Management

This agent manages projects via GitHub Issues in `$REGISTRY`. Issues are the single source of truth for all project and task state.

**Skills:**
| Skill | Purpose |
|---|---|
| `/project-init` | Create or adopt a managed project (epic + labels + workspace stub) |
| `/project-task` | Create task issues interactively — the sanctioned interactive task-creation path; use `--headless` for composed/cron use |
| `/project-intake` | Headless intake primitive — route actionable items from any source into the registry, dedupe by meaning, return issue number |
| `/project-steward` | Autonomous sweep: verify completions, dispatch work, escalate stalls, write digest |
| `/project-reconcile` | Sync projection surfaces (Google Tasks, etc.) against the registry |

**Convention doc:** `PROJECT_STANDARD.md` — edit this file to change standard behavior without touching skills.

**Label taxonomy:** `project`, `task`, `project:<slug>`, `owner:<actor>`, `agent:<name>`, `waiting-on:<actor>`, `status:active|blocked|needs-decision|paused|pending-verification|unclassified`, `priority:p1|p2|p3`.

**Completion lattice:** open → pending-verification → done. Done is absorbing; only the operator can reopen.

**Priority changes:** only by explicit human speech act, logged with a reason.

**Loop closure (§14):** nothing here ends in silence. Every run closes with what is now true, what is waiting on you, and what happens next without you. Work you asked for is reported back to you, not just filed on an issue; an unanswered question gets louder with age instead of disappearing. Work parked on someone outside this registry is labeled `waiting-on:<actor>`, aged in every digest under **Your open loops**, and comes with a drafted follow-up you can send — **you send it; the agent never contacts a third party for you**.
```

### Step 13: Create steward state directories

```bash
mkdir -p project-steward/digests
mkdir -p project-steward/reconcile-log
touch project-steward/run_log.txt
echo '{"last_run": null, "carry_over": [], "open_dispatches": [], "open_loops": []}' > project-steward/state.json
```

Commit the scaffolding:
```bash
git add project-steward && git commit -m "chore: scaffold project-steward state directory" 2>/dev/null || true
```

### Step 14: Register steward schedule (if scheduled)

If `$SCHEDULE` was chosen (not manual-only), add the schedule to `template.yaml` if it exists:

```bash
if [ -f template.yaml ]; then
  # Append under schedules: block
  grep -q "project-steward-sweep" template.yaml || \
    printf '\n  project-steward-sweep:\n    cron: "%s"\n    skill: project-steward\n    message: "Run the project steward sweep"\n' "$SCHEDULE" >> template.yaml
  echo "Schedule added to template.yaml. Run /trinity:sync to deploy it."
fi
```

### Step 15: Summary

Print:

```
## Project Management Installed

### Files created
| File | Purpose |
|---|---|
| `PROJECT_STANDARD.md` | Convention doc — edit to change behavior |
| `.claude/skills/project-init/SKILL.md` | /project-init |
| `.claude/skills/project-task/SKILL.md` | /project-task (interactive + --headless) |
| `.claude/skills/project-steward/SKILL.md` | /project-steward |
| `.claude/skills/project-reconcile/SKILL.md` | /project-reconcile |
| `.claude/skills/project-intake/SKILL.md` | /project-intake (headless intake primitive) |

### Configuration
- Registry: $REGISTRY
- Operator: $OPERATOR
- Agent: $AGENT_NAME
- Pending-verification max age: $PV_MAX_AGE h
- Steward schedule: $SCHEDULE (or "manual only")

### Labels created
`project`, `task`, `status:active`, `status:blocked`, `status:needs-decision`, `status:paused`, `status:pending-verification`, `status:unclassified`, `priority:p1`, `priority:p2`, `priority:p3`

(`owner:*`, `agent:*`, `project:<slug>` created per project by /project-init; `waiting-on:<actor>` created on first use when a task parks on someone outside the registry)

### Loop closure (standard §14)
Nothing in this system ends in silence, in either direction:
- **Toward you** — every run closes with what is now true, what is waiting on you, and what happens next without you. Work you asked for gets reported back to you, not just filed on an issue. An unanswered question gets louder with age instead of quietly expiring.
- **Toward everyone else** — work parked on a person or agent outside the registry gets `waiting-on:<actor>`, appears in every digest under **Your open loops** with its age, and comes with a drafted follow-up at 3 days (then weekly) that you can send as-is. At 14 days it forces a call: chase, drop, or route around. **The agent drafts; you send** — it never contacts a third party on your behalf.

### Next steps
1. Create your first project:
   ```
   /project-init
   ```
2. Add a task to it:
   ```
   /project-task
   ```
3. Run a steward sweep:
   ```
   /project-steward
   ```
4. (Optional) Sync with Google Tasks:
   Set `GOOGLE_TASKS_TOKEN` in `.env`, then run `/project-reconcile`

5. (Optional) Deploy the steward schedule to Trinity:
   ```
   /trinity:sync
   ```

Your agent now manages cross-actor projects with an approval-ready completion lattice.
```

---

## Error handling

| Situation | Action |
|---|---|
| Not a git repo | Stop, explain `git init` + `gh repo create` |
| `gh` not authenticated | Stop, explain `! gh auth login` with repo+issues scope |
| Registry repo not accessible (403) | Stop, show exact error; token must have repo+issues scope on the registry repo |
| Skills already exist | Ask: overwrite, skip existing, or cancel |
| `PROJECT_STANDARD.md` already exists | Ask: overwrite (with new config) or keep existing. If kept and it predates §14, offer the loop-closure section insert (Step 3) — the steward's open-loop pass is inert without it |
| `template.yaml` not found | Skip the schedule-registration step; note it in the summary |
| Label creation fails | Continue, note which failed (they can be created manually later) |
