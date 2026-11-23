---
name: project-plan
description: Plan a managed project and keep the plan true per the project standard (PROJECT_STANDARD.md, or fleet/project-standard.md on an orchestrator; §0 configures it). Turns the project's goal into a tree — milestones with a measurable "reached", tasks under each in the uniform anatomy, one level of subtasks, and what waits on what — written to the project's plan.md ledger and its task list, behind one approval. `revise` re-reads the record and the environment after something changed, and rewrites only what no longer holds — with one "what changed and why" log entry. `check` says whether the plan still holds and writes nothing. On a Trinity instance with Projects (standard 3.0, §28–§37) the plan and the tasks live in the platform only; without Projects it plans a GitHub-epic or folder project the same way. It plans; it never starts, dispatches or verifies work — that is /project-steward.
argument-hint: "<project-slug> [kickoff | revise [--because=\"what changed\"] | check] [--headless]"
automation: gated
effort: high
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__list_project_tasks, mcp__trinity__get_project_log, mcp__trinity__read_project_context, mcp__trinity__list_project_executions, mcp__trinity__update_project_task, mcp__trinity__link_to_project, mcp__trinity__add_project_task_note, mcp__trinity__add_project_log_entry, mcp__trinity__list_platform_files, mcp__trinity__read_platform_file, mcp__trinity__write_platform_file, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__report
user-invocable: true
metadata:
  version: "2.1"
  created: 2026-03-09
  author: Ability.ai
  changelog:
    - "2.1: The approval ask now shows the plan itself. Its question lists every milestone with what reached means and every task under it by title, owner and what it waits on; the full ledger is also published as a report linked to the project and named in the ask. A milestone whose only measure is that its tasks are done is refused, kept tasks that cannot be worked yet are set back to todo at kickoff, and an owner that is not a person on the project is listed under Needs before start."
    - "2.0: Rewritten as the planner of the project-management family. It reads the project standard's §0 like its siblings, plans a managed project as milestones → tasks → subtasks with dependencies, writes the plan.md ledger /project-status reads, creates tasks only through /project-task, and works on Trinity Projects (standard 3.0 — the plan in the project file space, platform tasks with parent and blocked_by, one approval ask) as well as on GitHub-epic and folder projects. New `revise` mode re-plans after a change and logs what changed and why; `check` reports whether the plan still holds. It no longer executes work or splits a job into sessions — the 1.0 behaviour is frozen as /project-plan-v1. Directory renamed plan → project-plan (name now equals directory)"
    - "1.0: Initial version — plans and executes large multi-session projects, splitting scope into ordered sessions with approval gates and state tracking"
---

# Project Plan

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-plan v2.1 — recent: the approval ask now shows the plan itself`. Then proceed.

## Purpose

Give a managed project a plan a stranger can follow, and keep that plan true as the world moves.

- **The plan is a tree.** Goal → milestones (each with what "reached" means, as a metric and a target) → tasks in the uniform anatomy → at most one level of subtasks. What waits on what is a dependency between tasks, never a deeper level.
- **The plan lives in two places that must agree:** the project's `plan.md` ledger (the order, the estimates, the milestones, the revision history) and the project's task list (the work itself). This skill is the only writer of the ledger's structure; `/project-status` writes its `Status` and `Evidence` cells; `/project-steward` runs the work.
- **Planning is separate from running.** This skill never starts a task, never dispatches to an agent, never verifies a done claim, never changes a priority, never changes the project's mode, and never deletes a task. A wrong plan therefore cannot start work by itself.

## Modes

| Call | Does | Writes |
|---|---|---|
| `/project-plan <slug> kickoff` | The first plan, from the project's goal and its kickoff documents | `plan.md`, the tasks, one approval ask, one log entry |
| `/project-plan <slug> revise [--because="…"]` | Re-reads the record and the environment, finds what no longer holds, rewrites only that | the changed part of `plan.md`, the changed tasks, one log entry — or one ask, see **Who approves** |
| `/project-plan <slug> check` | Says whether the plan still holds, and why not | nothing |
| `/project-plan <slug>` | `kickoff` when the project has no `plan.md`, else `check` | as above |

`--headless` never calls AskUserQuestion; it is how the steward, a schedule or another skill calls this one. `--because` carries what the caller saw change (a failed run, a merged PR, an answered ask) — the skill still reads the evidence itself and never plans from the sentence alone.

## Who approves

A plan changes what a whole project will do, so a person approves it — how often is the deployment's choice, read from the standard's §0 as `replan:` (default `manual`):

| `replan:` | `kickoff` | `revise` called by a person | `revise --headless` |
|---|---|---|---|
| `manual` (default) | one approval | shown, approved in the conversation | not run — prints `replan: manual — a person calls revise` and stops |
| `propose` | one approval | shown, approved in the conversation | writes the revision as `plan-proposed.md`, raises **one** ask, applies nothing |
| `auto` | one approval | shown, approved in the conversation | applies a revision that stays **inside the boundary**; anything outside it goes the `propose` way |

**Inside the boundary** means all of: the goal and every milestone's target are unchanged; no task for a person is added, changed or retired; no agent is added to the project; the projected finish moves by no more than `replan_max_slip_days` (default 5); the charter's delegation boundary (kickoff kit) allows it. Everything else is a decision and goes to a person.

The kickoff plan is always approved once, in every setting. Until it is, nothing in the project is offered to start (standard §35).

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | Yes | No |
| Plan ledger | `plan.md` — the project's file space on Trinity Projects (`project:<id>`); offline, the project's workspace folder | Yes | Yes (everything but kept rows' `Status` / `Evidence`) |
| Proposed revision | `plan-proposed.md`, beside `plan.md` | Yes | Yes |
| Kickoff documents | `intent.md`, `charter.md` / `project.md`, `rulings.md` beside the plan; briefs on a platform project | Yes | No |
| Tasks | the platform task list; offline, GitHub task issues or `tasks/T-NNN.md` | Yes | Yes — created only through `/project-task`; links, status `paused` and notes directly |
| Project log | the platform log; offline, epic comments or `log.md` | Yes | Yes — one entry per plan or revision |

## On Trinity Projects (standard 3.0, §28–§37)

On a Trinity instance with Projects a project lives in the platform and nowhere else (§28): the plan is a file in the project's file space, the tasks are platform tasks, the log is the platform's. No epic, no labels, no `tasks/` folder. This skill never writes to GitHub; engineering issues stay in their repo and a task links to them with `refs`.

**Detect, once per run.** Call `mcp__trinity__list_projects`:

- `enabled: true` → this section applies to every project it lists.
- `enabled: false`, no such tool, or `platform: off` in §0 → **offline**: the project is a GitHub epic or an internal folder (standard §1–§17, frozen), and the steps below use those.
- Refused with `external_audience` or `turn_unknown` → this turn is not an internal one. Stop. Use nothing from the platform and repeat no project detail.

**What that means for the steps below:**

- **The plan file** — `plan.md` and `plan-proposed.md` are read and written with `mcp__trinity__read_platform_file` / `mcp__trinity__write_platform_file` on the space `project:<id>`. A replace passes the `if_revision` it read; on `file_changed`, read again and redo from Step 4 — never overwrite blind.
- **The record** — `mcp__trinity__get_project` (goal, mode, members, agents, steward, `context` briefs — read each with `mcp__trinity__read_project_context`), `mcp__trinity__list_project_tasks` with `status: all`, `mcp__trinity__get_project_log`, `mcp__trinity__list_project_executions` for what ran and how it ended, and the kickoff files `intent.md`, `charter.md`, `rulings.md` in the file space.
- **The tree is native** — `parent` (one level) and `blocked_by`, set when the task is created or with `mcp__trinity__update_project_task` (`parent`, `blocked_by_add`, `blocked_by_remove`). A refusal (`blocker_cycle` with its path, `parent_is_subtask`, `owner_not_on_project`, `too_many_blockers`) is a fault in the plan: fix the plan, never work around the refusal.
- **Milestones** — the `Milestone: M<n>` line in a task's `context` (§33), and the platform's own milestone field as well where the task tools offer it.
- **An agent that is not on the project gets no task** (§33). The plan names it under **Needs before start**; the steward proposes adding it with `propose_project_changes`.
- **The approval** — one `mcp__trinity__ask_operator`, `type: approval`, `to: primary`, linked to the project with `mcp__trinity__link_to_project` (`kind: ask`). Kickoff: `request_id: plan-<project_id>`, options `Approve plan` · `Revise plan`. A revision: `request_id: plan-<project_id>-rev<N>`, options `Approve plan` · `Keep the current plan`. The steward reads the answer with `mcp__trinity__get_my_ask`; approved means the answer is `Approve plan`.
- **The mode is not this skill's** — Track / Propose / Auto decide what the steward may *start* (§32). A plan, new or revised, starts nothing in any mode.
- Where the instance offers the steward a kickoff-plan proposal tool (`propose_project_plan`), `kickoff` raises the approval through it instead of `ask_operator`, and still writes `plan.md`.

## Process

### Step 1: Read the standard

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration**:

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
cfg() { awk -v k="${1}" -v d="${2}" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$(0)~p{v=$(0);sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
REGISTRY=$(cfg registry ""); AGENT_NAME=$(cfg agent ""); OPERATOR=$(cfg operator "")
L_OWNER=$(cfg labels.owner_prefix "owner:"); L_PRIORITY=$(cfg labels.priority_prefix "priority:")
L_PAUSED=$(cfg labels.paused "status:paused"); L_DONE=$(cfg labels.done "status:done")
REPLAN=$(cfg replan manual); MAX_SLIP=$(cfg replan_max_slip_days 5); PLAN_MAX=$(cfg plan_max_tasks 40)
```

`replan`, `replan_max_slip_days` and `plan_max_tasks` are optional §0 keys; a standard without them gets the defaults above. **On Trinity Projects a missing standard is not an error** — use the defaults and carry on. Offline, if no standard exists, stop and run `/project-init` first. Pre-1.3 standards: resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2 when the block returns them empty.

If this is `revise --headless` and `$REPLAN` is `manual`, print `replan: manual — a person calls revise` and stop here.

### Step 2: Find the project, its tracking mode and its plan

`<slug>` is the project's id or name on Trinity Projects, its slug offline. One of:

| Where | Record | Tasks | `plan.md` |
|---|---|---|---|
| **Trinity Projects** | the platform project (`get_project`) | the platform task list | the project's file space |
| Offline, external | the epic found by `project:<slug>` in `$REGISTRY` | task issues `#NN` | the workspace named by the epic's `## Workspace` field (standard §15 — read, never derived from the slug) |
| Offline, internal | the charter `project.md` (standard §16 finder: `charter_for`, `mode_of`) | `tasks/T-NNN.md` | the charter's folder |

No project → `ERROR: No project <slug>` and stop. `kickoff` on a project that already has an approved `plan.md` → stop and say `revise` is the call. `revise` or `check` with no `plan.md` → stop and say `kickoff` is the call.

For `kickoff`, an existing `plan.md` whose first line names an ask that is still pending is not planned again: print where the ask waits and stop.

### Step 3: Read everything the plan rests on

Read, in this order, and note for each what it says the project must achieve or must not do:

1. **The goal and success criteria** — the epic body, the charter, or `get_project`.
2. **The kickoff documents** — the one-page intent, the charter's delegation boundary, `rulings.md` (a ruling is a constraint on the plan; a `provisional` one is named as a risk). Missing documents are listed in the output; with `kickoff: blocking` in §0 a missing one stops `kickoff`.
3. **Briefs people prepared** — every `context` item on a platform project.
4. **Every task, all statuses** — with owner, agent, status, dependencies, and for done tasks whether the done claim was verified.
5. **The log since the last plan revision** — decisions, blockers, hand-offs.
6. **What ran** — executions and their endings, an engineering executor's ledger when the charter declares `chains:` (read it, never plan inside it), the state of every linked issue or PR.
7. **The current `plan.md`** — milestones, rows, the last revision line.

Read evidence from where it lives (a pushed branch, a merged PR, a file, a record id), never from an agent's summary of it.

### Step 4: `revise` and `check` — decide whether the plan still holds

Go through the plan row by row against Step 3 and mark each finding:

| Finding | Example |
|---|---|
| **Done differently** | a task closed by other work, or closed without its claim and its output is missing |
| **Blocked for good** | the approach failed twice, an access was refused, a dependency was withdrawn |
| **New fact** | a ruling, an answered ask, a changed brief, a decision in the log that the plan does not reflect |
| **Missing work** | a milestone whose tasks, all done, would still not reach its target |
| **Wrong order** | a task waiting on something it does not need, or not waiting on something it does |
| **Slip** | the projected finish moved past a committed date |
| **Dead weight** | an open task no milestone needs any more |

**No finding → the plan holds.** Print `plan holds — rev N, <open> open, next: <the tasks that can be worked now>` and stop. Write nothing: no file, no log entry, no ask. A revision that changes nothing is noise.

`check` stops here in every case, printing the findings.

### Step 5: Build the tree

For `kickoff`, build all of it. For `revise`, rebuild **only the part the findings touch** and leave every other row byte-for-byte.

1. **Milestones** — two to seven. Each has a one-line name, what "reached" means as a metric with a target a stranger can read off, and no date unless a person committed one. The metric is an outcome that can be observed outside the task list (a document exists and says X, a number reads Y, a person ruled); "its tasks are done" is not a metric, and a milestone that has only that is rewritten before the gate. `revise` never changes a milestone's target inside the boundary.
2. **Tasks under each milestone** — each with the uniform anatomy: a plain imperative title, an Objective, a Definition of Done of 2–5 checkable items, and a `Validation:` line saying how a stranger checks the done claim. Each names an accountable owner, the agent that does it (only an agent on the project; otherwise it goes under **Needs before start**), an estimate in working days, and the tasks it waits on.
3. **Subtasks** — only where a task is really several hand-offs; one level. If a subtask wants subtasks, the parent is a milestone.
4. **Tasks for a person** — every grant, seat, credential, send or decision the plan needs from a person is its own task for that person, placed so the tasks that need it wait on it. An open loop that is only a sentence in the plan is a defect.
5. **Owners are people on the project.** An owner that is a handle, a name or anyone who is not the project's creator or a member reaches nobody. `kickoff` lists each such task under **Needs before start** with the person to add, and says so in the ask.
6. **Statuses say what can be worked.** At `kickoff`, a kept task that is `active` with no run, no note and no evidence, and that waits on an open task, is set to `todo` with the note `Plan rev 1: not started, waits on <refs>`. Work a person or agent has really begun is never touched.
7. **Order** — dependencies only where the work truly cannot start. Aim for at least two tasks that can be worked at once; a plan that is one long chain stalls on its first block.

**Rules a revision keeps:**

- A **done** task is never reopened, renamed or re-estimated. If its output turned out missing, add a new task that says so.
- A task **in progress or awaiting verification** is not rewritten. Change what waits on it, or add a follow-up.
- A task the plan no longer needs is **retired, never deleted**: status `paused` with a note `Retired by plan rev N: <why>`, and its row moves to the ledger's Retired section.
- No more than `$PLAN_MAX` open tasks. More than that is two projects, or a milestone planned too early — plan the next milestone in full and later ones as one placeholder task each (`Plan milestone M<n>`), which a later `revise` expands.
- Every change traces to a finding from Step 4. A change with no finding behind it is taste — leave it out.

Then compute the projected finish: the longest path through open tasks by estimate and dependency, in working days from today. For `revise`, the slip is the difference from the last revision's finish.

### Step 6: The gate

Compose the summary a person decides from — it must stand alone:

```
Plan for <project> — rev N (kickoff | revision of rev N-1)
Why now:   <the findings, one line each — revise only>
Milestones: M1 <name> — reached when <metric · target> …
Tasks:      <a> added · <c> changed · <r> retired · <k> kept
Needs from people: <each person task — who, what>   | none
Needs before start: <agents to add, access to grant> | none
Projected finish: <date> (<±d> vs rev N-1)
Risks:     <provisional rulings, single points of failure> | none
```

- **Interactive** (a person called it): show the summary and the changed rows, ask once — approve, change, or drop. Apply on approve.
- **Headless `kickoff`:** apply Step 7 (tasks are created in `todo`, nothing can start), then raise the one approval ask in the shape of **The approval ask** below, and record its id as the first line of `plan.md`. An answer of `Revise plan` is a call for `revise` by a person, with what they want changed.
- **Headless `revise`, `replan: propose`, or `auto` outside the boundary:** write the whole revised ledger to `plan-proposed.md`, raise **one** ask whose title is the decision (`Approve the revised plan for <project>?`), whose body follows **The approval ask** below (the plan as proposed, with each changed row marked `new`, `changed` or `retired`), and whose options are `Approve plan` · `Keep the current plan` (each with its one-line "what I do next"); record `proposed_ask: <id>` as the first line of `plan-proposed.md`. Apply nothing. A later run that finds the ask answered `Approve plan` applies the proposal (Step 7) and removes the file; `Keep the current plan` removes the file and logs the decision. Never raise a second ask while one is pending — replace the proposal file and say so in a note on the same ask's thread.
- **Headless `revise`, `replan: auto`, inside the boundary:** apply Step 7.

#### The approval ask

A person approves from the ask alone. They must never have to open a file, a task list or an execution to see what they are approving. An ask that names task ids without titles, or milestones without what "reached" means, is a defect: fix it before raising it.

1. **Publish the ledger as a report first**, where the tool exists: `mcp__trinity__report` with `report_type: <agent>.project_plan`, `title: Plan for <project> — rev N`, `display_hint: markdown`, payload `{project_id, revision, markdown: <the full plan.md text>}`, then link it to the project (`mcp__trinity__link_to_project`). Keep the report id. No report tool, or a refusal: carry on and say `full plan: plan.md in the project's files` instead.
2. **`title`** — `Approve the plan for <project>?` (`Approve the revised plan for <project>?` for a revision).
3. **`question`** — the plan, in plain lines, nothing a reader has to decode:

   ```
   From: /project-plan <slug> <mode>, <date>. Finish <date>. <n> tasks, <m> milestones.
   M1 <name> — reached when <metric and target>
     T-001 <title> · <owner> · can start now
     T-002 <title> · <owner> · after T-001
   M2 <name> — reached when …
     …
   Yours: <each task for the approver, by title> | nothing
   Before start: <what is missing, one line each> | nothing
   ```

   One line per task, titles cut at 70 characters, never an id alone. A plan too long for the ask's size limit keeps every milestone line and the tasks of the first open milestone in full, then `M<n>: <k> tasks, see the full plan` for the rest.
4. **`options`** — `Approve plan` · `Revise plan` (`Keep the current plan` for a revision); **`proposal`** — one line each: what happens next and where it lands.
5. **`context`** — at most four facts: `Full plan` (the report's title and id, or the file), `Projected finish`, `Risks` (provisional rulings, single points of failure), `Changed since rev N-1` (revisions only).

### Step 7: Apply

In this order, so a run cut short leaves a plan that still reads true:

1. **Create new tasks** — one `/project-task --headless` call per task, parents before their subtasks and blockers before what waits on them; keep each returned reference. `/project-task` is the only way a task is created.
   - Trinity Projects: `--project=<id> --title=… --objective=… --dod="a|b" --validation="…" --milestone=M<n> [--parent=T-NNN] [--blocked-by="T-NNN,…"] [--refs="owner/repo#N,…"] [--agent=<name>] [--owner=…] [--for-person] [--waiting-on=…] --context="Estimate: <d>d. Plan rev N."` — `--agent` only for an agent already on the project.
   - Offline: `--project=<slug> --title=… --objective=… --dod="a|b" --owner=… [--agent=…] [--waiting-on=…] --context="Milestone: M<n>. Validation: <…>. Estimate: <d>d. Plan rev N."`
2. **Link the tree** — Trinity Projects: links that could not be given at creation, and every changed link, with `mcp__trinity__update_project_task` (`parent`, `blocked_by_add`, `blocked_by_remove`). Offline: the `Depends on` cell of the ledger is the link, and each waiting task gets a `Blocked by: <refs>` line in its Context (a comment on the issue, or the task file's Context section).
3. **Change kept tasks** the findings touch — title, objective, Definition of Done, owner, agent, links — each with a note `Plan rev N: <what changed and why>`.
4. **Retire** — status `paused` (`update_project_task`; offline `$L_PAUSED` on an issue or `status: paused` in the task file) with the retirement note.
5. **Write `plan.md`** in the ledger format below — the new revision line on top of **Revisions**, `Status` and `Evidence` of kept rows copied as they were.
6. **One log entry** — `mcp__trinity__add_project_log_entry`, kind `decision` (offline: a comment on the epic, or an entry in `log.md`):
   `Plan rev N (<kickoff | revised>): <why, one sentence>. Added <refs>; changed <refs>; retired <refs>. Projected finish <date> (<±d>). Waiting on <person> for <what> | waiting on nobody.`
7. Offline internal projects: commit the changed files (`plan: <slug> rev N`); a canon-placed project publishes through `/canon-publish`.

A refusal at any step is reported as it came and the run stops there; what was already written stays, and the ledger is written last so it never describes tasks that do not exist. Re-running `revise` picks up from the record — tasks that already carry `Plan rev N` in their context are not created twice.

## The ledger — `plan.md`

```markdown
approval_ask: <request id, or none>
# Plan — <Project name>
Goal: <one sentence>
Revision: N · <YYYY-MM-DD> · projected finish <YYYY-MM-DD>

## Milestones
| M | Name | Reached when | Metric · target | State |
|---|---|---|---|---|
| M1 | … | … | … | open · reached <date> |

## Tasks
| Step | Milestone | Issue | Task | Owner | Agent | Estimate (d) | Depends on | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | M1 | T-001 | … | … | … | 2 | | todo | |
| 1.1 | M1 | T-002 | … (subtask of 1) | … | … | 1 | | todo | |
| 2 | M1 | T-003 | … | <person> | — (person) | 0.5 | 1 | todo | |

## Needs before start
- <agent to add to the project · access to grant> — or "nothing"

## Retired
| Step | Issue | Task | Retired in | Why |

## Revisions
- rev N · <date> · <why> · +<a> added, <c> changed, <r> retired · finish <±d>
- rev 1 · <date> · kickoff
```

This is the table `/project-status` reads: `Step`, `Issue` (`#NN`, `T-NNN` or `owner/repo#N`), `Estimate (d)`, `Depends on` (step ids) and `Status` (`todo · in-progress · waiting-on-operator · done`) keep exactly those names and values. `/project-status` owns the `Status` and `Evidence` cells; this skill reads them and never overwrites them on a kept row. Step ids are never reused — a retired step keeps its number.

### Step 8: Output

**Headless:** one line —
```
<slug>: plan rev N applied — +a ~c -r, finish <date>      (applied)
<slug>: plan rev N proposed — ask <id>                    (waiting on a person)
<slug>: plan holds — rev N                                (nothing written)
```

**Interactive:** the Step 6 summary, then the closing statement the standard's §14a requires:
```
Waiting on you: <the approval, the person tasks — or "nothing">
Next without you: <what the steward can now start, or "nothing until the plan is approved">
```

## Calling it from the steward or a schedule

- A steward that finds the plan no longer holds — a task blocked for good, a second rejected done claim, an answered ask that changes scope, a milestone that cannot be reached — calls `/project-plan <slug> revise --headless --because="<what it saw>"`, at most once per project per day, and carries on with what can still be worked. It does not re-plan on every wake: `check` is cheap, `revise` is not.
- A schedule carries the call and nothing else: `/project-plan <slug> check --headless` or `revise --headless`.
- Planning needs the strongest model the deployment has; give this skill's schedule or call its own model rather than the sweep's.

## Error recovery

- **Standard missing, offline** → run `/project-init`. On Trinity Projects the defaults apply.
- **`gh` or platform refusal while reading** → stop before any write; say what could not be read. A plan made from a partial read is worse than no plan.
- **Cut short while applying** → re-run the same call; created tasks are recognised by their `Plan rev N` context line, the ledger is rewritten whole.
- **`file_changed` on `plan.md`** → someone else wrote it; read again and redo from Step 4.
- **A proposal nobody answered** → it stays one ask; the steward ages it like any open loop (standard §14). This skill never re-asks.

## Completion checklist

- [ ] Trinity Projects detected or offline mode resolved; the plan's location found, never derived from the slug
- [ ] Goal, kickoff documents, briefs, all tasks, the log and the run evidence read
- [ ] `revise` / `check`: every change traces to a named finding; no finding → nothing written
- [ ] Milestones have a metric and a target; every task has the full anatomy and a `Validation:` line
- [ ] Every need from a person is that person's task
- [ ] Done and in-flight tasks untouched; retired tasks paused with a note, none deleted
- [ ] Tasks created only through `/project-task`; ledger written last
- [ ] One approval for the kickoff; revisions gated per `replan:`
- [ ] One log entry saying what changed and why
