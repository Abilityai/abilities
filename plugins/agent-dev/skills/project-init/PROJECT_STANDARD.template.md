# Project Management Standard

> The standardized approach for managing projects in this deployment.
> Every managed project follows this standard; `/project-init` creates projects that conform to it,
> `/project-task` creates tasks, `/project-intake` routes work in headlessly, `/project-steward` manages
> them autonomously, `/project-reconcile` syncs projections against the registry, and `/project-status`
> reports one project's progress and projected finish to the operator.
> **{{AGENT_NAME}}** is the managing agent; **{{OPERATOR}}** is the operator (the human this standard escalates to).
>
> Version: 1.3 ({{DATE}}) — §0 Configuration: the machine-read block every project skill resolves at run time (where the standard lives, the label vocabulary, the steward's state directory, the fleet hooks); one skill set for stand-alone agents and fleet orchestrators alike

## 0. Configuration

Every project skill reads this block first — it is **the only place the skills take their configuration from**. Edit the values, keep the keys. A standard without this block (written before 1.3) is read with the defaults shown here, so nothing changes until you opt in. Flat keys, one per line, `#` comments allowed after a value; an **empty value turns the matching feature off**.

```yaml
config_version: 1
registry: {{REGISTRY}}                        # GitHub owner/repo that holds the project epics, or `none` (every project internal, §16)
agent: {{AGENT_NAME}}                         # this agent's logical name — tasks labeled agent:<this> are executed inline, never dispatched
operator: {{OPERATOR}}                        # the human the needs-operator label escalates to
state_dir: project-steward                    # steward state, digests, run log, reconcile log, outputs for workspaces the run cannot see
pv_max_age_hours: {{PV_MAX_AGE}}              # pending-verification SLA (§12)
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
```

**Label roles, not label names.** Every skill refers to a label by its role — *the needs-operator label*, *the blocked label* — and resolves the name from this block (`$L_NEEDS_OPERATOR`, `$L_BLOCKED`, … in their bash). The tables below document the **default** vocabulary; a deployment that rides an existing tracker's vocabulary (e.g. `status-needs-operator`, `priority-p1`) changes the values here and nothing else. `status:*` / `priority:*` in the prose below mean "whichever status / priority labels this block names".

**Resolver (what every skill runs first):**

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)   # repo root first, then an orchestrator's fleet/ placement
cfg() { awk -v k="$1" -v d="$2" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$0~p{v=$0;sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
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
tracking: external                  # external | internal (§16). Omitted → external when `epic:` names a real epic (#N, N > 0), else internal
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
CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $2}' template.yaml 2>/dev/null); CANON=${CANON:-canon}
SELF=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/folder:/{print $2}' template.yaml 2>/dev/null | sed 's#^agents/##; s#/$##'); SELF=${SELF:-{{AGENT_NAME}}}
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
