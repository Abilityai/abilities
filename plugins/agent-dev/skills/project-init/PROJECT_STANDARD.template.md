# Project Management Standard

> The standardized approach for managing projects in this deployment.
> Every managed project follows this standard; `/project-init` creates projects that conform to it,
> `/project-task` creates tasks, `/project-intake` routes work in headlessly, `/project-steward` manages
> them autonomously, `/project-reconcile` syncs projections against the registry, and `/project-status`
> reports one project's progress and projected finish to the operator.
> **{{AGENT_NAME}}** is the managing agent; **{{OPERATOR}}** is the operator (the human this standard escalates to).
>
> Version: 2.0 ({{DATE}}) — rev 2 operating rules §18–§26 (two machines, kickoff kit, participation contract, build/dispatch/record rules) and six §0 keys (`kickoff`, `participation_check`, `chain.ledger`, `chain.stall_minutes`, `metrics`, `brief.evening_utc`); derived from a 2026-11 multi-agent project retrospective. 1.4 — §17 Platform mode: on a Trinity instance with Projects enabled the platform holds the project record and the same skills work against it (ruling R38); §0 gains `platform:`. 1.3 — §0 Configuration, one skill set for stand-alone agents and fleet orchestrators alike

## 0. Configuration

Every project skill reads this block first — it is **the only place the skills take their configuration from**. Edit the values, keep the keys. A standard without this block (written before 1.3) is read with the defaults shown here, so nothing changes until you opt in. Flat keys, one per line, `#` comments allowed after a value; an **empty value turns the matching feature off**.

```yaml
config_version: 1
registry: {{REGISTRY}}                        # GitHub owner/repo that holds the project epics, or `none` (every project internal, §16)
agent: {{AGENT_NAME}}                         # this agent's logical name — tasks labeled agent:<this> are executed inline, never dispatched
operator: {{OPERATOR}}                        # the human the needs-operator label escalates to
state_dir: project-steward                    # steward state, digests, run log, reconcile log, outputs for workspaces the run cannot see
pv_max_age_hours: {{PV_MAX_AGE}}              # pending-verification SLA (§12)
platform: auto                                # auto | off — auto: on a Trinity instance with Projects enabled the skills work against the platform's project record (§17); off: always folder + GitHub
quarantine: on                                # on | off — the steward auto-stubs unregistered project_files/ folders (§9); off on a repo whose project_files/ holds non-project folders
member_repos:                                 # extra owner/repo(s), comma-separated, whose `project:<slug>` issues count as project members (status reports); empty = the registry only
labels.owner_prefix: "owner:"                 # the accountable-party label. `agent:` on a fleet whose owners ARE the executing agents (one label, no GitHub assignee)
labels.live: status:active                    # comma-separated — any of these on an epic means "being worked"
labels.active: status:active                  # the live label the skills WRITE (new epic/task, restore after a failed verification)
labels.blocked: status:blocked
labels.needs_operator: status:needs-decision  # a decision or action only the operator can take
labels.paused: status:paused                  # the steward skips it — no staleness escalation
labels.pending_verification: status:pending-verification   # empty = no verification hold: a done claim is verified in the same run and closes directly
labels.done: status:done                      # empty = closing the issue is the done marker (no label written)
labels.unclassified: status:unclassified      # empty = the quarantine pass cannot stub (set quarantine: off)
labels.priority_prefix: "priority:"           # followed by p1 | p2 | p3
labels.epic_extra:                            # comma-separated labels added to every epic (e.g. type-epic so a product tracker's roll-ups see it); empty = none
fleet.system_map:                             # path to a fleet system map (fleet/system-map.yaml on an orchestrator) — owners resolve to their live deployed_name through it; empty = owners are called by their logical name
fleet.orchestration:                          # path to the orchestration narrative (fleet/orchestration.md) — its §5 edges gate dispatch, its §3b ownership matrix supplies default owners and consulted/informed etiquette; empty = no edge check
# rev 2 keys (standard 2.0) — read by project-init ≥ 1.6, project-steward ≥ 1.11, project-status ≥ 1.5; absent = the defaults shown
kickoff: blocking                             # blocking | advisory — a missing kickoff-kit item stops /project-init (§19); advisory creates the epic and lists the gaps
participation_check: on                       # on | off — an owner failing a machine-checkable row of §20 receives no dispatch until it passes
chain.ledger: run-log.md                      # the engineering executor's run log the steward reads in every chain folder the charter lists (§24.3)
chain.stall_minutes: 30                       # a dispatch queued longer than this is a stall line in status and digest (§24.5)
metrics: on                                   # on | off — record the declared project metrics of §24.4 with record_metrics (needs them declared in template.yaml)
brief.evening_utc: "18:00"                    # the two-half evening brief in the steward digest (§23.2); empty = no evening brief
```

**Label roles, not label names.** Every skill refers to a label by its role — *the needs-operator label*, *the blocked label* — and resolves the name from this block (`$L_NEEDS_OPERATOR`, `$L_BLOCKED`, … in their bash). The tables below document the **default** vocabulary; a deployment that rides an existing tracker's vocabulary (e.g. `status-needs-operator`, `priority-p1`) changes the values here and nothing else. `status:*` / `priority:*` in the prose below mean "whichever status / priority labels this block names".

**Resolver (what every skill runs first):**

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)   # repo root first, then an orchestrator's fleet/ placement
cfg() { awk -v k="${1}" -v d="${2}" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$(0)~p{v=$(0);sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
```

## 1. Registry

| Thing | Location | Notes |
|---|---|---|
| Registry (single source of truth) | **Per project, declared in its charter's `tracking:` (§16).** *External:* GitHub issues in `{{REGISTRY}}` — one **epic issue** per project (`project` label), one task issue per task (`task` + `project:<slug>`). *Internal:* the project's own workspace — `project.md` stands in for the epic, `tasks/<id>.md` for each task issue, `log.md` for the epic's comment thread | A registry of `none` (set when this standard was materialized) means every project is internal and no GitHub access is needed |
| Workspace (files, drafts, outputs) | **Agent level:** `project_files/<slug>/` in the managing agent's repo. **Canon level (shared project, §15):** `agents/{{AGENT_NAME}}/projects/<slug>/` in the fleet's canon repo, read through the agent's clone (`x-canon.clone_path`, default `canon/`) | Free-form except `project.md` (charter — the linted envelope of the canon convention § Projects, at both levels) and the optional append-only `decisions.md` ledger. **The path is recorded in the epic body's `## Workspace` field and is always read from there — never derived from the slug** (§15). **Visibility is deployment config**: if git-synced to the agent's container, the steward reads workspaces directly; if local-only / gitignored, Trinity runs use the epic body as authoritative context. The quarantine pass is idempotent wherever `project_files/` is visible and never scans the canon. |
| Steward state, digests, run log, outputs | `state_dir` from §0 (`project-steward/` by default; `fleet/project-steward/` on an orchestrator) in the managing agent's repo | Written only by `/project-steward` and `/project-reconcile`; tracked in git and pushed after each material run (GitHub carries steward state between local and Trinity runs). When a workspace is not visible to the run (gitignored `project_files/` on a Trinity container), inline-task output lands in `<state_dir>/outputs/<slug>/` and the task comment says so |

**Invariant 1 — One registry per project, write-authoritative.** Each project's registry — its GitHub epic and task issues (external) or its own workspace files (internal, §16) — is the sole authoritative record for that project's state: scope, status, and priority. A project has exactly one registry; nothing mirrors it into the other mode, and no other system writes state back. Projections are read-only views; they do not own state.

## 2. Roles

- **{{AGENT_NAME}}** — managing agent. Sole writer of the registry — GitHub issues (labels, comments, status) for external projects, the task files and `log.md` for internal ones (§16). Runs the steward, creates tasks via `/project-task`, relays agent reports to the task's log. Self-owned tasks may be executed inline by the steward.
- **{{OPERATOR}}** — the human decision-maker. Owns all priority changes (Invariant 2). Endorses project completion. Resolves `status:needs-decision`. Reopens closed tasks (done is absorbing; only a human can reopen).
- **Other agents / humans** — execute dispatched tasks; report results via chat; do not write to the registry directly (in either mode — a person editing a task file by hand is the internal-mode equivalent of editing an issue: allowed for the operator, and the steward reads it as-is).

## 3. Label taxonomy

Default names — the live names are the §0 values (a tracker-native vocabulary such as `status-blocked` / `priority-p1` is configured there, never hard-coded in a skill).

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
`canon:projects/<slug>/`                             ← canon level (shared project, §15)

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

The steward auto-stubs any `project_files/<slug>/` folder that is not a registered project into quarantine. A folder is registered when it has an epic (external) **or** a `project.md` whose mode resolves to internal (§16) — an internal project is registered by its own charter. Quarantine is a stub epic (`status:unclassified`) when the registry is a GitHub repo, and a stub charter (`tracking: internal`, `status: paused`, `tldr: "(unclassified) …"`) when it is `none`. The quarantine pass runs wherever `project_files/` is visible — it is idempotent and safe on any deployment config (local-only, git-synced container, or absent entirely when workspaces live elsewhere). **It never scans the canon clone**: a canon-placed project (§15) is registered by its epic, never discovered from a folder — a `projects/<slug>/` folder in canon without an epic is the canon linter's `project-envelope` finding, not a quarantine case. Unclassified projects are:
- Excluded from all projections
- Excluded from priority tracking (no priority label)
- Classified lazily: one batch line in the weekly digest ("N unclassified folders: <names>"), never per-item interrupts
- Never attention-dependent between classification passes

## 10. Dispatch protocol (Invariant 1 + cross-actor)

1. **Explicit ownership only.** Dispatch only to the agent named by the task's `agent:*` label. Never fuzzy-match at runtime; ambiguity → `status:needs-decision`.
1b. **Resolve through the fleet map, respect its boundaries** (only when §0 names `fleet.system_map` / `fleet.orchestration`). The `agent:*` label is the *logical* name — resolve it to the live callable name via the map (`deployed_name`, falling back to the last segment of `ref:`); an owner absent from the map → `status:needs-decision`. If the narrative's §5 does not sanction a manager→owner edge, do **not** dispatch — `status:needs-decision` naming the missing edge (an autonomous run never silently violates the permission intent). Its §3b ownership matrix is etiquette, never a gate: name the domain's *consulted* agents in the brief's Context line, mention outcomes to its *informed* agents in the digest.
2. **Health check first.** `mcp__trinity__get_agent_health` before dispatch when Trinity is available; unhealthy → `status:blocked`, digest.
3. **One open dispatch per project, max 3 per steward run.**
4. **Standard dispatch brief:**
```
[PROJECT DISPATCH] <project name> — <task title>
Issue: <task issue URL>   (internal: Task: <slug>/T-NNN — <workspace>/tasks/T-NNN.md)
Objective: <from task body>
Definition of done: <from task body>
Context: <key links/paths>
Deliverable: reply in this chat with a done claim (format: "### Done claim YYYY-MM-DD / summary / DoD check with evidence").
{{AGENT_NAME}} relays your reply to the task's log — do not write GitHub issues or task files yourself.
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

Intake skills and domain skills may write workspace content freely (`project_files/<slug>/`) — except the registry files of an internal project (`project.md`, `log.md`, `tasks/`), which are the registry itself (§16). Work items enter the registry ONLY through `/project-intake`, in either mode. Material state changes (decisions, status shifts, blockers) land as a one-line comment on the relevant epic. Intake skills NEVER write projection surfaces directly — only `/project-reconcile` touches projections.

| Writer | May write | Must not write |
|---|---|---|
| Intake / domain skills | `project_files/<slug>/` (not an internal project's registry files) | Task issues or task files directly (use `/project-intake`) |
| `/project-intake` | Task issues or task files, one-line state news (epic comment / `log.md`) | Projection surfaces |
| `/project-reconcile` | Projection surfaces, reconcile log | Registry tasks (read-only; gesture processing is the one exception) |
| `/project-steward` | Issue labels and comments, or task files and `log.md`; steward state | Projection surfaces |

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

## 15. Visibility — one standard, two placements (operator rulings R21, 2026-09-10, and 2026-09-22)

A project is managed **the same way** whether it lives at agent level or at canon level:

| | Agent-level project | Shared (company) project |
|---|---|---|
| Workspace | `project_files/<slug>/` in the managing agent's repo | `projects/<slug>/` at the root of the fleet's canon repo — the shared zone every agent and human writes directly; pushed with `/canon-publish` |
| Charter | `project.md` | `project.md` — the **same** file, same envelope |
| Registry | the epic in `{{REGISTRY}}` (external) or the workspace itself (internal, §16) | the epic in `{{REGISTRY}}` (external) or the workspace itself (internal, §16) |
| Steward | `/project-steward` | `/project-steward` |
| Intake | `/project-intake` | `/project-intake` |
| Decision ledger | `decisions.md` (append-only) | `decisions.md` (append-only) |
| Who can read the definition | this agent + its operator | every agent and human on the canon |
| Who can write it | this agent | every agent and human on the canon — the charter's `owner:` stays the steward |

**Placement decides only who can read the definition and rely on it.** Company projects are shared projects by design and live in canon. Moving a project from agent level to canon changes its readers and nothing else — same epic, same steward, same intake, same ledger. Many contributors, one steward: in canon anyone may edit the workspace and append to the ledger, but the charter's `owner:` names the one agent that stewards the project, and git history records who changed what. Tandem (`projects/tandem/` in the Ability canon) is the first shared project and the reference instance. A project created before 2026-09-22 may still sit at the earlier placement, `agents/<owner>/projects/<slug>/`; the canon linter warns (`project-placement`) until its steward moves it (`/project-init adopt --canon <slug>` does the move).

**Charter envelope** (both levels; linted in canon by `project-envelope`, see the canon convention § Projects):

```yaml
---
owner: {{AGENT_NAME}}                # the steward — the one managing agent (in canon: must name an agents/<name>/ folder)
status: active                      # active | blocked | needs-decision | paused | pending-verification | done — mirrors the epic's status:* label (external); IS the project status (internal)
tracking: external                  # external | internal (§16) | platform (§17). Omitted → external when `epic:` names a real epic (#N, N > 0), else internal
platform_project: prj_…             # optional (§17) — the Trinity project this charter belongs to; written by /project-init, never by hand
epic: {{REGISTRY}}#<N>              # external: the registry epic this charter mirrors — the epic is the authoritative record. Internal: omit, or `none`
priority: p2                        # internal only — the project's priority (external keeps it on the epic's priority:* label)
updated: YYYY-MM-DD
review_by: YYYY-MM-DD               # /canon-reconcile re-verifies the charter — against the epic (external) or its own tasks/ (internal)
tldr: "One line — what this project is for"
---
```

**Workspace resolution (every project skill uses this, nothing derives a path from the slug):**

1. Read the epic body's `## Workspace` field — the **first backticked path** in the section (prose around it is fine: `` `canon/projects/tandem/` in the fleet canon repo`` resolves), else the first non-empty line.
2. `canon:<path>` → the workspace is `<clone_path>/<path>` where `clone_path` is `template.yaml → x-canon.clone_path` (default `canon/`); `git -C <clone_path> pull --ff-only` before reading (never force; on failure read the local copy and say so). A missing clone is self-healed the way the canon skills do it (`x-canon.repo`); no `x-canon:` block at all means this agent is not enrolled in the canon and the epic body is the authoritative context.
3. Any other value → a path relative to the managing agent's repo (`project_files/<slug>/` is the convention, but the field wins — a hand-written `canon/projects/<slug>/` is simply the clone-relative form and resolves through the same clone; an earlier-placement `canon:agents/<owner>/projects/<slug>/` resolves the same way until the project moves).
4. Field missing (an epic predating this section) → no workspace; the epic body is the authoritative context. Do **not** guess `project_files/<slug>/`.

`/project-init --canon` creates a shared project (writes the charter + ledger into the canon clone, records the canon path in the epic); `/project-init adopt --canon <slug>` adopts an existing canon project (moving it to the root if it is this agent's at the earlier placement). Reading a shared project is `/canon-consume projects [slug]`.

## 16. Tracking modes — external tracker or internal task files (operator ruling 2026-09-22)

A project tracks its tasks in **one** of two places, declared in the charter's `tracking:` key. Everything else in this standard — roles, the completion lattice, verification, staleness, dispatch, loop closure, placement (§15) — is the same in both modes; only where the registry lives changes.

**Resolving the mode** (every project skill uses this rule, nothing else):

1. `tracking: external` or `tracking: internal` in `project.md` → that mode.
2. No `tracking:` key → **external** if `epic:` names a real epic (`owner/repo#N`, N > 0), otherwise **internal**. Every charter written before this section has a real epic, so every existing project stays external untouched.
3. The registry configured in §1 is `none` → every project is internal; an external charter there is an error to report, never a reason to call GitHub.

**Finding projects** (every project skill uses this, never a path of its own):

```bash
CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $(2)}' template.yaml 2>/dev/null); CANON=${CANON:-canon}
SELF=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/folder:/{print $(2)}' template.yaml 2>/dev/null | sed 's#^agents/##; s#/$##'); SELF=${SELF:-{{AGENT_NAME}}}
# every charter this agent can see: agent level, the canon root zone, then its own earlier-placement canon folder (internal projects are registered by these files)
charters() { for f in project_files/*/project.md "$CANON"/projects/*/project.md "$CANON"/agents/"$SELF"/projects/*/project.md; do [ -f "$f" ] && echo "$f"; done; }
# the one charter for a slug — the first placement that has it, in the order above (a slug in two placements is a mistake to report)
charter_for() { charters | awk -v s="/$1/project.md" 'index($0,s)==length($0)-length(s)+1{print;exit}'; }
# a charter's mode, by the rule above
mode_of() { awk 'NR==1&&/^---/{f=1;next} f&&/^---/{exit} f&&/^tracking:/{t=$2} f&&/^epic:/{e=$2} END{ if(t) print t; else if(e ~ /#[1-9][0-9]*$/) print "external"; else print "internal" }' "$1"; }
```

Under `$CANON/projects/` (the top-level shared zone) only charters whose `owner:` is `$SELF` are this agent's to manage; the rest are read-only to it. An external project is still found the way it always was — by its epic's `project:<slug>` label — and its charter (if any) through the epic's `## Workspace` field (§15).

**Where each thing lives:**

| Concept | External (GitHub) | Internal (the workspace) |
|---|---|---|
| Project record | epic issue (`[Project] <Name>`) | `project.md` — the envelope plus the epic's body sections: Goal, Success criteria, Owners, Cadence, Current status, Tasks |
| Project status / priority | `status:*` / `priority:*` labels on the epic | `status:` / `priority:` in the charter envelope |
| Task | task issue `#NN` | `tasks/T-NNN.md` (below) |
| Task labels | `task`, `project:<slug>`, `owner:*`, `agent:*`, `priority:*`, `status:*`, `waiting-on:*` | the task file's front matter |
| Task comment thread (done claims, verification, dispatch receipts, relays, waiting-on, loop closed — §7) | issue comments | the task file's `## Log` section, same headings, **append-only**, newest last |
| Epic comment thread (steward updates, state news) | epic comments | `log.md` in the workspace, append-only, newest last |
| Closing a task | close the issue | `status: done` — the file stays |
| Reference | `#NN` | `<slug>/T-NNN` |
| Projection key (§11) | `[#NN]` | `[<slug>/T-NNN]` |

**Workspace layout (internal):**

```
<workspace>/            # project_files/<slug>/ or the canon folder (§15)
  project.md            # charter + the project record
  decisions.md          # append-only decision ledger (unchanged)
  log.md                # the project's comment thread
  tasks/
    T-001.md
    T-002.md
```

**Task file** — one per task, so two writers adding tasks to a shared project never touch the same file:

```markdown
---
id: T-001                  # = the file name; next id = highest existing + 1, zero-padded to 3
title: Draft the launch brief
status: active             # active | blocked | needs-decision | paused | pending-verification | done
owner: <actor>             # accountable (owner:* label)
agent: <name>              # executing agent, optional (agent:* label)
priority: p2               # p1 | p2 | p3
waiting_on: <actor>        # optional (waiting-on:* label, §14b)
created: YYYY-MM-DD
updated: YYYY-MM-DD        # moves on every write to this file
pending_since: YYYY-MM-DDTHH:MMZ   # set when status becomes pending-verification (the §12 clock); cleared when it leaves
---

## Objective
## Definition of Done
- [ ] ...
## Context
## Validation
- [ ] {{AGENT_NAME}} — verify all Definition of Done items against the done claim
## Log
### Done claim YYYY-MM-DD
...
```

The completion lattice is the task's `status:` read as a lattice: **open** is any value except `pending-verification` and `done`; `done` is absorbing exactly as in §5 — only a human sets a done task back to `active`, and says so in the Log.

**Rules that keep the file a registry:**
- **One writer path.** Tasks are created only by `/project-task` or `/project-intake` in both modes; the managing agent is the only automated writer of task files and `log.md`. Logs are append-only — never edit or delete a past entry.
- **Ids are never reused.** A task that is dropped is `done` with a `### Loop closed` entry, not deleted. In the canon, pull before allocating an id; if the publish is refused because another writer took the same id, take the next free id, rename the file, and publish again.
- **Absence is not deletion.** A missing task file is an error the steward reports, never a task it treats as closed.
- **Placement is unchanged (§15).** An internal project in the canon keeps its task files in its slug folder, `projects/<slug>/`; the steward (the charter's `owner:`) is the managing agent that writes them and pushes with `/canon-publish`, like the charter. Anyone may edit the folder by hand — the zone is shared — but only the steward's skills write tasks and `log.md`.
- **Switching modes is a deliberate act**, recorded as a decision in `decisions.md`: create the tasks in the new mode, close the old ones with a `### Loop closed` pointing at their new home, then change `tracking:`. Nothing converts automatically.

## 17. Platform mode — the project record on Trinity (operator ruling R38, 2026-09-29)

On a Trinity instance with **Projects** enabled, the platform owns the project record: its name and goal, who is on it, who can see it, the chats and rooms where the work happens, the shared log, the task list and the health. The six project skills stay the process and work against that record. Everything in §1–§16 is the **offline mode** and stays valid — Trinity is the upgrade, never the gate. Without Trinity, on an install without Projects, or with `platform: off` in §0, this section does nothing.

**Detecting it** (every project skill, once per run): the `list_projects` tool answering `enabled: true`. `enabled: false`, or no such tool, means folder + GitHub mode. A refusal coded `external_audience` or `turn_unknown` means the conversation is not an internal one — the skills then use nothing from the platform and repeat no project detail.

**Two kinds of platform project**, both marked by `platform_project: prj_…` in the charter envelope (§15):

| | Linked | Platform-tracked |
|---|---|---|
| Charter | `tracking: external` + `platform_project:` | `tracking: platform` + `platform_project:` (a project created in the Workspace may have no charter at all) |
| Tasks | GitHub task issues, as in §5 — the platform project's tracker link is the epic | the platform's task list — `T-NNN`, the §16 fields |
| Project record people see | the platform project (the epic stays the task registry) | the platform project |
| Log | epic and task comments (§7), **plus** one platform log entry per outcome | the platform's project log and task logs |
| Workspace folder | unchanged (§15) | optional — files and drafts only; never `tasks/` or `log.md` |

A project is matched to its platform record by `platform_project:`; lacking that line (or a visible charter), by the listed project whose tracker link is the epic URL.

**Where each thing lives (platform-tracked):**

| Concept (§16 column "Internal") | On the platform |
|---|---|
| Project record, goal | `get_project` — name, goal, status, steward, members, the latest log entries and open tasks |
| Task | `list_project_tasks` / `create_project_task` — title, objective, definition of done, context, owner, assignee (`agent`), waiting-on |
| Task status | `update_project_task` — the same six values as §16 |
| Task comment thread (done claims, verification, dispatch receipts, relays, waiting-on, loop closed — §7) | `add_project_task_note`, same headings; a `note` sent with a move to `pending-verification` is the done claim |
| Epic comment thread, steward updates | `add_project_log_entry` — `decision`, `deliverable`, `blocker`, `handoff` or `note`; **one entry per outcome, never one per run**. Task status changes are logged by the platform |
| Current status | `set_project_health` — `on-track`, `at-risk` or `off-track`, with one line saying why |
| What needs the steward | `get_steward_digest` — awaiting verification, blocked or waiting on a decision, untouched for a week, open asks, quiet, health update due |
| A report, file, decision or ask on the project | `link_to_project` |

**The lattice on the platform is the platform's, and it is §5's:** an agent moves a task to `pending-verification`; the steward agent or a person sets `done`; only a person reopens a done task. **Priority is a person's** — an agent's task starts at `p2`, and a different priority is stated in the task's context for a person to set (Invariant 2). **Members, visibility and the project's own status** (active, paused, done) are a person's too: the steward proposes a change through the needs-operator path and never works around a refusal.

**Health, from the steward's review:** `on-track` — nothing blocked, nothing waiting on a decision, nothing stale; `at-risk` — a task is blocked, waiting on a decision, stale, or past the §12 age; `off-track` — a success criterion or a committed date can no longer be met without a decision. Set it when it changes, and when the digest says an update is due.

**Starting a project on the platform** (`/project-init`): `create_project` with the name, the goal, and the epic URL as its tracker link when the project is external. It needs the *start projects* permission an instance admin grants the agent; the owner becomes the creator and first member, the agent the steward, and only members see it. Refused, or the tool not there → the project is created in offline mode as before, and the skill says what a person can do: grant the permission and run `/project-init platform <slug>`, or create or import it in Workspace → Projects.

**Bringing an existing folder project onto the platform** (`/project-init platform <slug>`): `import_project` with the folder path, once. The platform reads the charter, the task files with their logs, `log.md` and `decisions.md`, and keeps the task ids; an external charter's epic becomes the tracker link. Afterwards the platform is the home and nothing syncs back: an internal project's charter becomes `tracking: platform`, its `tasks/` and `log.md` are left as they were with a closing line saying where the project went, and the move is recorded in `decisions.md` (§16's switching rule). A second import of the same folder is refused; the skill then finds the project in `list_projects` and records its id.

**Invariant 1 holds.** A project still has exactly one registry for its tasks: GitHub (linked) or the platform (platform-tracked). A linked project's log entries and health on the platform are a report of what the registry already says, written by the managing agent — they never carry state back.

---

# Rev 2 — operating rules for any managed project

> Sections §18–§26 were derived from a retrospective of a multi-agent project run under version 1.4 of this standard (2026-11): the machinery existed and was not reachable from where the project ran, the rules lived in prose at two layers and bound nothing at run time, the setup was discovered one refusal at a time, and nothing woke anyone. Every rule below is general. A deployment may add a `## 27. Adoption status` of its own naming which rules its skills already enforce and which it applies by hand; `/reconcile-docs`-class drift checks compare §0–§17 and the §0 key set only.

## 18. Scope and the two machines

A **managed project** is work that more than one stateful agent does toward one outcome, with one managing agent ({{AGENT_NAME}}), one operator ({{OPERATOR}}), and one record. This standard applies to every such project, whatever the domain.

**One machine owns every project: the steward.** `/project-steward` is the record owner, the dispatcher for task work, and the reader of everything else. An **engineering executor** — a build-chain skill or an equivalent that drives issues through an engineer to reviewed pull requests with its own ledger — is not a kind of project; it executes the issues inside a project that the engineer implements, and the steward reads its ledger.

| unit inside a project | run by | dispatch | closure | the steward's part |
|---|---|---|---|---|
| **task**: work an agent finishes in one session | `/project-steward` (§10) | one open dispatch per project, reply-reconciled | the agent's done claim, verified (§6) | dispatches, reconciles, records |
| **engineering issue**: plan, checkpoints, review, PR | the engineering executor | its own calls, parallel up to the engineer's capacity | a commit, a test count, a PR state | reads the executor's ledger, posts status, ages its open asks, flags stalls, never dispatches into it (§24.3) |

A project declares at init which issues are engineering issues (`## Engineering issues` in the epic, §4) and lists its executor folders in the charter envelope (`chains:`); everything else is a task. Trinity is the upgrade, never the gate: everything below runs offline on GitHub and files, and uses the platform's Projects record when it is there (§17).

## 19. Day zero: the kickoff kit

**Nothing is dispatched until the kit exists** (`kickoff: blocking` in §0; `advisory` creates the epic and lists the gaps). `/project-init` produces it, in this order, and refuses to open the project on a missing item.

1. **One page of intent** (`intent.md`): a picture of the system after the project, the objects it creates and the objects it retires. Ruled before any repo or agent is created. A new truth artifact is created only with the named retirement of the one it replaces, in the same change.
2. **The charter with a delegation boundary**: one section, filled once — what the managing agent decides alone and reports, what needs the operator, what is a person-only act by platform rule. Inside the boundary the agent decides, writes "decided under rule N" to the ledger, and reports; it never asks.
3. **`rulings.md`**: one line per ruling, numbered, dated, with a `provisional` flag. A provisional ruling may produce a design note and nothing else; building needs a confirmed one. Every later proposal and every executor plan carries a "touches rulings" line read from this file.
4. **The setup manifest** (`setup.md`), declared and probed before the first create: every account, every token with the repos it must read or write, every vault item with which service account reads or writes it, every setting, subscription item, permission edge, skill assignment and model pin the project needs. Probed by machine where a probe exists (credential presence, token scope per repo, edges, the resolved model) and the result written into the epic's `## Setup`. Access the operator must grant by hand is listed here too, so it is granted in one sitting.
5. **The participation table**: each `agent:*` owner is checked against §20; the eleven rows per agent are written into the epic's `## Participation`. An agent that fails a machine-checkable row does not receive work until it passes (`participation_check: on`).
6. **The record, created once** (§24.1): the registry epic, and in platform mode the platform project created or imported **by the deployed managing agent** in the same step — a local session that cannot create one dispatches `/project-init platform <slug>` to the deployed agent rather than skipping it.
7. **Declared project metrics** (§24.4), so the retrospective is a readout, not a collection.
8. **Critique before a reversible build**: when a ruling changes where state lives, who holds a credential, or what is built new, and the plan will cost more than a few dollars, one independent critique bounded to the ruling text runs before the plan is dispatched; routine follow-ups skip it.

## 20. The participation contract

Eleven requirements an agent meets before it joins a project. Checked at kickoff by `/project-init` and re-checked by the steward when an `agent:*` label is added.

| # | requirement | declared in | checked by |
|---|---|---|---|
| 1 | Every unit of work it will receive is a named playbook with declared arguments; prose is the recorded exception | `template.yaml x-capabilities`, the fleet's playbook-call protocol | `get_agent_skills` or the slash list, matched against the task list |
| 2 | Its working state lives in a store another agent can read without opening its container: a repo it pushes to, a vault entry, a report, the project log | `template.yaml` state path and store | `get_git_status` ahead and dirty tree |
| 3 | It wakes its caller when it ends or asks; it never polls itself with reminders for a callee's outcome | per-playbook `wakes_on_ending`; the platform default | the ask receipt |
| 4 | Every closing reply names evidence a stranger can verify: a commit, a path, a record, a readiness verdict. An exit code is not evidence; a failed readiness row fails the run | the reply contract in the playbook-call protocol | the steward refuses a done claim without evidence |
| 5 | It owns exactly the repos it edits and holds a token that can push a branch, open a PR and file an issue on each; an edit to another repo is routed to that repo's agent | the system manifest member `repo` plus a token-scope line | a repository probe per repo with the agent's token |
| 6 | Its model is declared and read back as the resolved model on every channel it takes turns on, before its first turn | `template.yaml runtime.model` | a resolved-model read per channel |
| 7 | Every credential it needs is declared by name with its vault; kickoff refuses to start until each name resolves | `template.yaml credentials` | `get_credential_status` or env presence |
| 8 | Every edge it will call is declared and its key is proven to reach the target before the first dispatch | the system manifest `permissions.explicit` | `get_agent_permissions` plus one probe call |
| 9 | If it speaks to a person outside the fleet it carries a reply fence: no execution ids, no other agent's name or output, no credential or vault names, no run-status preamble | the skill, linted | a lint over the skill text |
| 10 | It reports its own readiness as rows, and a person-facing "ready" repeats the rows | a readiness script or equivalent | a dry run |
| 11 | It carries its standing rules in its own repo; a dispatch carries only the step | the callee's playbooks, `docs/rulings.md` | a rider-bytes check in the executor |

Two more: **the managing agent acts under its own identity** for project work, never on the operator's personal key, so the record can tell the agent's acts from the person's; and **a template repo an agent is created from is code only**, never carrying another instance's state.

## 21. Build rules

Binding on the engineering executor and on any agent that plans inside a managed project.

1. **The plan reads what is already known.** Before taste decisions, the plan lists every platform-state and contracts entry the feature touches, by id, and carries a "touches rulings" line read from `rulings.md`; a part that depends on a `provisional` ruling is not planned — the run parks and names the ruling.
2. **Independent issues start in parallel from the first dispatch.** Dependencies are declared at the scope check; only a declared dependency stacks.
3. **A limit or default scoped to one class of agents is never accepted as a platform default; a withdrawn cap is withdrawn, not re-expressed in another unit.** A plan decision of that shape is an out-of-authority decision for the operator, never an accepted recommendation.
4. **Stage fidelity over stage count.** Migrations are proved with the real migration tool on a merge-tree against the live base; git behaviour is proved on real git, never a fake.
5. **Nothing new reaches a person untested.** Any template, skill or ops-script change rides a scripted dry run on a staging seat before a real person sees it; a project whose agents face people runs a preflight of reach, execution-read scope, writable paths and the resolved model before the first person-facing agent exists.
6. **Readiness failures are fatal.** A playbook that ends with a readiness report fails on a failed row.
7. **Merges are the operator's; validation is the executor's.** A PR merged before the executor marked it ready gets a post-merge validation by rule.

## 22. Dispatch and state

Binding on every caller: the steward, the executor, any agent that dispatches.

1. **The callee carries the law; the dispatch carries the step.** Standing rules live in the callee's playbooks and its `docs/rulings.md`; the call line carries declared arguments, and a rider carries only the step's own content. A rider that restates a callee's standing rule is a finding, counted in bytes.
2. **Route to the owner on the first hop.** Repo work goes to the repo's agent; a chief-of-staff agent never edits someone else's skill.
3. **Fire once, read back by execution id.** Never retry a synchronous dispatch on a client timeout; never find a run by time or exit code.
4. **A configuration change closes on a read-back of the effective value** from the surface that uses it, never on the write's response.
5. **A callee's outcome lands where the caller can read it**: a journey, a vault entry's description, a report, a plan file's progress block, the project log. Never only behind an execution id the caller may not open.
6. **Wake on ending.** Callers wait on the callee's ending or on `agent.task.*` events, never on a reminder loop; one re-armed watchdog per run is the recorded fallback where the platform default is not yet on.
7. **Container-only state is a finding.** `ahead > 0` or a dirty tree is reported in every repo-touching reply and flagged by the steward.
8. **Asks are split by owner before they are sent** and merges are batched into one ordered list per sitting.

## 23. Approvals and the human's rhythm

1. **Decide-and-report inside the boundary**: anything covered by the charter's delegation boundary or an accepted recommendation is decided, ledgered as "decided under rule N" and reported, never asked.
2. **The evening brief has two halves** (`brief.evening_utc` in §0): the day's decisions with a recommendation and a default on each, and every access the night's work will need (tokens, vault grants, unlocks, merges). The fleet runs the defaults overnight; the operator overrules in the morning.
3. **An agent's approval is never a person's.** A callee's ask is answered by a person on the person's own key; the managing agent never answers it with its agent key.
4. **The record survives the session.** A pre-compaction hook in the managing agent's local workspace writes the active project's run-log and ledger mirror before every compaction, and the session that resumes reads them first.
5. **Loop closure applies to the project's own asks** (§14). The executor's open asks (a token, a grant, an unlock, a merge) register as open loops so the digest ages them.

## 24. The record and observability

1. **Two records, no more**: the registry epic for status and the executor's ledger (its run log plus the committed ledger mirror) for the build. On a Trinity instance with Projects, the platform project is the record people see (§17), created or imported at kickoff by the deployed managing agent, with the epic as its tracker link.
2. **The record is written by the machine that does the work.** The executor posts the §7 dispatch receipts and closures to the engineering issue and one platform log entry per outcome; the epic's `## Current status` is written by the steward from state; nothing is mirrored by hand.
3. **The steward owns the record and reads the executor.** For a project with a live executor run the steward reads each chain folder's `chain.ledger` and ledger mirror, posts status to the epic and the platform project, ages the executor's open asks as the project's loops, flags a dispatch older than `chain.stall_minutes`, reports container-only state, and never dispatches into the executor. Its cadence follows the executor's steps while one is live, the schedule otherwise.
4. **Declared project metrics**, recorded by the machine as it runs (`metrics: on`; declared in the managing agent's `template.yaml metrics:` with a `project` dimension, recorded with `record_metrics`): operator asks per day and the share inside the delegation boundary; median ask-to-answer wait; block time per hand-off; dispatches by form and per-call rider bytes; re-dispatch and duplicate rate; dispatch queue age; defects by catch stage; person-visible leaks; cost per agent per day.
   The ten names `/project-init` checks for (item 7 of §19), each with `dimensions: [project, …]`: `project_operator_asks` (counter; dims `inside_boundary`), `project_ask_wait_p50_minutes` (duration), `project_block_hours` (duration; dims `handoff`), `project_dispatches` (counter; dims `form` = playbook|prose), `project_rider_bytes_p50` (bytes), `project_redispatch_rate` (percentage), `project_dispatch_queue_age_p95_minutes` (duration), `project_defects` (counter; dims `stage` = review|validate|live), `project_person_visible_leaks` (counter), `project_cost_usd` (gauge; dims `agent`). Declared once on the managing agent's `template.yaml metrics:`; no cadence, so a quiet project never reads stale.
5. **Dispatch health is a first-class signal.** The executor reads queued age on every poll and reports a stall at `chain.stall_minutes`.

## 25. Knowledge the agents read

1. **A standard that is read or it does not exist.** The standards an agent is bound by are pinned by tag, named in the agent's template, and printed in the agent's receipts.
2. **Protocols bind roles.** A protocol index carries `binds:` per role, a provisioning receipt names the standard it read, and a linter refuses a `binds:` to an unmerged protocol.
3. **One rule, one home.** Where a rule exists at the protocol layer and the skill layer, only the skill copy runs and it drifts within days; the protocol says a rule must exist, the callee's skill holds it.
4. **The standard and the skills move together.** A drift check reports differences between §0–§17 of the deployment's copy and this template at the skills' installed version.

## 26. The retrospective is built in

Every project ends with a readout: the metrics of §24.4, the rulings file with its reversals, the participation table's end state, the cost ledger per agent per day, and the record itself — collected by the managing agent at close, not by hand.
