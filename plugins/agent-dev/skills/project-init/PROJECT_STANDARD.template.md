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
| Workspace (files, drafts, outputs) | **Agent level:** `project_files/<slug>/` in the managing agent's repo. **Canon level (shared project, §15):** `agents/{{AGENT_NAME}}/projects/<slug>/` in the fleet's canon repo, read through the agent's clone (`x-canon.clone_path`, default `canon/`) | Free-form except `project.md` (charter — the linted envelope of the canon convention § Projects, at both levels) and the optional append-only `decisions.md` ledger. **The path is recorded in the epic body's `## Workspace` field and is always read from there — never derived from the slug** (§15). **Visibility is deployment config**: if git-synced to the agent's container, the steward reads workspaces directly; if local-only / gitignored, Trinity runs use the epic body as authoritative context. The quarantine pass is idempotent wherever `project_files/` is visible and never scans the canon. |
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
| `status:done` | Terminal — DoD verified (or the human closed directly). Absorbing: only a human reopens (§5). |
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
`project_files/<slug>/`                              ← agent level, or
`canon:agents/<owner>/projects/<slug>/`              ← canon level (shared project, §15)

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

The steward auto-stubs any `project_files/<slug>/` folder with no corresponding epic into a quarantine epic (`status:unclassified`). The quarantine pass runs wherever `project_files/` is visible — it is idempotent and safe on any deployment config (local-only, git-synced container, or absent entirely when workspaces live elsewhere). **It never scans the canon clone**: a canon-placed project (§15) is registered by its epic, never discovered from a folder — a `projects/<slug>/` folder in canon without an epic is the canon linter's `project-envelope` finding, not a quarantine case. Unclassified projects are:
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

## 15. Visibility — one standard, two placements (operator ruling R21, 2026-09-10)

A project is managed **the same way** whether it lives at agent level or at canon level:

| | Agent-level project | Shared (company) project |
|---|---|---|
| Workspace | `project_files/<slug>/` in the managing agent's repo | `agents/{{AGENT_NAME}}/projects/<slug>/` in the fleet's canon repo (own-folder write; pushed with `/canon-publish`) |
| Charter | `project.md` | `project.md` — the **same** file, same envelope |
| Registry epic | one, in `{{REGISTRY}}` | one, in `{{REGISTRY}}` |
| Steward | `/project-steward` | `/project-steward` |
| Intake | `/project-intake` | `/project-intake` |
| Decision ledger | `decisions.md` (append-only) | `decisions.md` (append-only) |
| Who can read the definition | this agent + its operator | every agent and human on the canon |

**Placement decides only who can read the definition and rely on it.** Company projects are shared projects by design and live in canon. Moving a project from agent level to canon changes its readers and nothing else — same epic, same steward, same intake, same ledger. Tandem (`agents/corbin/projects/tandem/` in the Ability canon) is the first shared project and the reference instance.

**Charter envelope** (both levels; linted in canon by `project-envelope`, see the canon convention § Projects):

```yaml
---
owner: {{AGENT_NAME}}                # the managing agent (= the enclosing canon folder)
status: active                      # mirrors the epic's status:* label — active | blocked | needs-decision | paused | pending-verification | done
epic: {{REGISTRY}}#<N>              # the registry epic this charter mirrors — the epic is the authoritative record
updated: YYYY-MM-DD
review_by: YYYY-MM-DD               # the canon's /canon-reconcile re-verifies the charter against the epic
tldr: "One line — what this project is for"
---
```

**Workspace resolution (every project skill uses this, nothing derives a path from the slug):**

1. Read the epic body's `## Workspace` field — the **first backticked path** in the section (prose around it is fine: `` `canon/agents/corbin/projects/tandem/` in the fleet canon repo`` resolves), else the first non-empty line.
2. `canon:<path>` → the workspace is `<clone_path>/<path>` where `clone_path` is `template.yaml → x-canon.clone_path` (default `canon/`); `git -C <clone_path> pull --ff-only` before reading (never force; on failure read the local copy and say so). A missing clone is self-healed the way the canon skills do it (`x-canon.repo`); no `x-canon:` block at all means this agent is not enrolled in the canon and the epic body is the authoritative context.
3. Any other value → a path relative to the managing agent's repo (`project_files/<slug>/` is the convention, but the field wins — a hand-written `canon/agents/<owner>/projects/<slug>/` is simply the clone-relative form and resolves through the same clone).
4. Field missing (an epic predating this section) → no workspace; the epic body is the authoritative context. Do **not** guess `project_files/<slug>/`.

`/project-init --canon` creates a shared project (writes the charter + ledger into the canon clone, records the canon path in the epic); `/project-init adopt --canon <path>` adopts an existing canon folder. Reading a shared project from another agent is `/canon-consume <agent> projects [slug]`.
