---
name: project-task
description: "On a Trinity instance with Projects (standard 3.0, §28–§37), creates a task in the platform project only — create_project_task with the §33 anatomy (objective, done_definition checklist, context with Validation: and Milestone: lines), refs to engineering issues (never copied, never written), parent / blocked_by, an assignee only from the project's agents, priority stated in context for a person; dedupes by meaning first. Interactive, or --headless for composed use (prints T-NNN). Without Trinity Projects, runs the frozen offline mode (standard 2.x): a GitHub task issue for an external project or a tasks/T-NNN.md file for an internal one, with full anatomy and the epic's Tasks checklist."
argument-hint: "[project id or name | project-slug | --headless --project=<slug> --title=\"...\" --objective=\"...\" --dod=\"item1|item2\" --owner=<actor> [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--context=\"...\"]]"
allowed-tools: Bash, Read, AskUserQuestion, mcp__trinity__list_projects, mcp__trinity__get_project, mcp__trinity__create_project_task, mcp__trinity__add_project_task_note, mcp__trinity__list_project_tasks, mcp__trinity__list_platform_files, mcp__trinity__read_platform_file, mcp__trinity__propose_project_changes
user-invocable: true
metadata:
  version: "2.0.0"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "2.0.0: Standard 3.0 (operator rulings P1–P11, 2026-11-11). On Trinity Projects a task is a platform task only: a new first section creates it with create_project_task and the §33 anatomy (Validation: and Milestone: lines in context, refs to engineering issues, parent / blocked_by, assignee only from the project's agents — else a proposal by the steward, owner only creator / member / role, for_person only by the steward, priority written into context for a person), after a dedupe by meaning over every task. Never writes to GitHub. The old body is kept unchanged as the frozen offline mode for agents without Projects"
    - "1.7.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.7: Platform mode (ent#788, ruling R38): for a platform-tracked project on a Trinity instance with Projects enabled the task is created in the platform's task list (create_project_task — same anatomy, the platform allocates T-NNN, priority stays a person's); linked projects keep their GitHub task issues. Without Trinity nothing changes"
    - "1.6: One lineage (ent#789): the standard is resolved at the repo root or at fleet/project-standard.md and its §0 Configuration supplies the label vocabulary by role — the task carries ${L_OWNER}<owner> and ${L_PRIORITY}pN (owner: / priority: by default; agent: / priority- on a fleet riding its tracker's labels) instead of hard-coded names"
    - "1.5: Internal tracking (ent#673): for a project whose charter resolves to `tracking: internal` (standard §16) the task is written as `<workspace>/tasks/T-NNN.md` — front matter for what labels hold, the same four body sections plus an append-only `## Log` for what comments hold — and listed in project.md's `## Tasks`; a waiting-on actor becomes `waiting_on:` + a `### Waiting on` Log entry. No GitHub access. Headless output is `<slug>/T-NNN`. Canon-placed internal projects publish through /canon-publish; an id collision on publish takes the next free id. External projects: unchanged"
    - "1.4: Shared projects (ruling R21, ent#588) — no behaviour change: a task belongs to an epic found by `project:<slug>` label whether the project lives in project_files/ or in the canon; the one rule added is that a workspace path, when one is passed through, is the epic body's Workspace field resolved per PROJECT_STANDARD §15, never derived from the slug"
    - "1.3: Read-the-standard guard — a missing PROJECT_STANDARD.md now stops with a run-/project-init-first message instead of failing on an unresolved registry; skill is now authored standalone (installer copies from here)"
    - "1.2: Loop closure — optional waiting-on actor (label + ### Waiting on comment) puts a task parked on an outside party into the steward's aging ladder; interactive output ends with the §14a closing statement (waiting on you / next without you)"
    - "1.1: Add --headless mode — all fields as arguments, no AskUserQuestion, returns issue number; callable from /project-intake and crons"
    - "1.0: Initial version — full anatomy enforcement including Validation section (approval chain), owner/agent label distinction, epic checklist update"
---

# Project Task

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-task v2.0.0 — recent: on Trinity Projects a task is a platform task only`. Then proceed.

## On Trinity Projects — the only mode there (standard 3.0, §28–§37)

On a Trinity instance with Projects, a project lives in the platform and nowhere else (§28). A task is a platform task. No epic, no labels, no `tasks/` folder, no `log.md`. Engineering issues stay in their repo; a task links to them with `refs`. This skill never writes to GitHub. The standard's §29, §30 and §33 are the contract; this section is the procedure.

### Step 0: Detect

Resolve §0 with the resolver in the offline mode's Step 1. Read only `agent` and `platform`. No standard file → use the defaults; do not stop. Then call `mcp__trinity__list_projects` once.

- `enabled: true` → run this section.
- `enabled: false`, no such tool, or `platform: off` in §0 → go to **Offline mode** below.
- Refused with `external_audience` or `turn_unknown` → this turn is not an internal one. Stop. Use nothing from the platform and repeat no project detail.

### Arguments

Interactive: `/project-task [<project id or name>]`. Missing fields are asked with AskUserQuestion.

Headless (`--headless`): every field is an argument; never ask.

| Argument | Required | Field |
|---|---|---|
| `--project=<id or name>` | yes | the project |
| `--title="..."` | yes | `title` — a plain imperative sentence |
| `--objective="..."` | yes | `objective` |
| `--dod="item1\|item2"` | yes | `done_definition` — one `- [ ]` line per item |
| `--validation="..."` | no | the `Validation:` line; default below |
| `--milestone=M<n>` | no | the `Milestone:` line |
| `--context="..."` | no | the rest of `context` |
| `--refs="owner/repo#N,..."` | no | `refs` — engineering issues or PRs, at most 10 |
| `--parent=T-NNN` | no | `parent` — one level only |
| `--blocked-by="T-NNN,..."` | no | `blocked_by` — at most 20 |
| `--agent=<name>` | no | `assignee` |
| `--owner=<person or role:<id>>` | no | `owner` |
| `--for-person` | no | `for_person: true` (needs a person `--owner`, no `--agent`) |
| `--waiting-on=<actor>` | no | `waiting_on` |
| `--priority=pN` | no | written into `context` (priority is a person's) |

A missing required argument in headless mode → print `ERROR: --<field> is required in headless mode` and exit.

### Step 1: Resolve the project

Match `--project` against the `list_projects` result: an exact id first, then the name (case-insensitive). Interactive with no argument: list the projects by name and ask which. No match, or more than one → interactive: ask; headless: `ERROR: no project <value>`.

Call `mcp__trinity__get_project`. Keep its `agents`, `members`, steward, status and mode. A stopped, done or archived project still takes tasks; say its status in the output.

### Step 2: Dedupe by meaning

Call `mcp__trinity__list_project_tasks(project_id, status: all)`. Compare the new title and objective with each task's title and objective, by meaning, not by exact words.

- An open task means the same thing → create nothing. Interactive: show it and offer to add the new detail as a note (`add_project_task_note`). Headless: print `DUPLICATE:T-NNN` and exit.
- A done task means the same thing → say so. Interactive: ask whether this is new work. Headless: print `DUPLICATE:T-NNN` and exit.

### Step 3: Build the fields (§33)

- `title`, `objective`, `done_definition` (a markdown checklist of 2–5 checkable items).
- `context`: the free text, then the line `Validation: <how a stranger checks the done claim>`. Default: `Validation: the steward checks each Definition of Done item against the evidence named in the done claim (§34)`.
- **Milestone.** List the space `project:<id>` with `list_platform_files`. If `plan.md` is there, read it with `read_platform_file`. When it has milestones (`## M<n> …` headings), add `Milestone: M<n>` to `context`. Interactive: ask which milestone. Headless: use `--milestone`; without it, add no line and say so in stderr.
- **Priority.** Priority is a person's (§30). A wanted priority goes into `context` as `Requested priority: pN`. Say in the output that a person sets it on the project page.
- **`refs`.** The engineering issues or PRs the work happens in, at most 10. Trinity reads their state; nothing is written to GitHub. Never copy an issue's body into the task.
- **`parent` and `blocked_by`.** Only ids from Step 2's list. One level of subtasks. At most 20 blockers. A link that closes a circle is refused.
- **`assignee`.** Only an agent in `get_project`.`agents`. An agent that is not on the project gets no assignee (§33):
  - this agent is the project's steward → call `mcp__trinity__propose_project_changes` with `agents` adding it (one proposal; `already_pending` or `proposal_pending` → send nothing more);
  - else → say the steward must propose adding the agent.
  - Either way, add `Wanted assignee: <agent>` to `context`. The steward sets `assignee` once the change is applied.
- **`owner`.** The accountable person: the creator, a member, or `role:<id>`. Anyone else is refused `owner_not_on_project`. Leave it empty when no one was named.
- **`for_person`.** Only the steward assigns a task to a person (`only_the_steward_assigns_people`). It needs a person `owner` and no `assignee`. Only a person marks it done.
- **`waiting_on`.** The actor the task waits on. Anything that waits on a person is a person's task or a `waiting_on`, never only a line elsewhere (§33).
- `status`: leave it; a new task starts `todo`.

### Step 4: Create

One call: `mcp__trinity__create_project_task(project_id, title, objective, done_definition, context, assignee, owner, for_person, parent, blocked_by, refs, waiting_on)`. Leave out the fields that are empty.

A refusal is reported as it came, with its code, and never worked around. For a code that names one field (`owner_not_on_project`, `parent_is_subtask`, `blocker_cycle`, `too_many_blockers`, `refs_refused`, `only_the_steward_assigns_people`): interactive → show it and ask how to fix it; headless → print `ERROR: <code> <message>` and exit. Never fall back to a file or an issue.

### Step 5: Output

Headless: print exactly one line, the new task id `T-NNN`, and exit.

Interactive:
```
Task created: T-NNN — <title>
Project:      <name> (<id>, <status>, mode <mode>)
Assignee:     <agent> | none — wanted <agent>, proposal <sent | the steward's to send>
Owner:        <person or role> | none
Milestone:    M<n> | none
Refs:         <refs> | none
Blocked by:   <ids> | nothing

Waiting on you: <the priority to set, the proposal to approve, or "nothing">
Next without you: <the steward picks it up on its next wake — under the project's mode>
```

## Offline mode (frozen — agents without Trinity Projects)

Runs only when `list_projects` is not enabled (standard §28). Written for standard 2.x; developed no further. Its §17 'linked project' passages are unreachable on Trinity.

## Purpose

Create a task in the uniform format — a GitHub task issue (external project) or a task file in the project's workspace (internal project, standard §16). This is the **only sanctioned way to create tasks** in a managed project — it enforces the full anatomy including the `## Validation` section (the approval chain), applies the correct labels, and links the task into the parent epic's checklist.

**Never create task issues directly via `gh issue create` outside this skill.** The anatomy enforcement and epic linkage are the point.


### Workspace path (standard §15 — read, never derived)

This skill writes GitHub, not workspaces. If a caller hands it — or it hands a caller — a workspace path, that path is the epic body's `## Workspace` field resolved through the standard's §15 resolver (`canon:projects/<slug>/` → through the x-canon clone; anything else → repo-relative; missing → no workspace), **never `project_files/<slug>/` derived from the slug**. A shared project (ruling R21) sits in the canon and is otherwise identical: same epic, same task anatomy, same intake path.

## Modes

**Interactive mode** (default): run as `/project-task [project-slug]`. Collects missing fields via AskUserQuestion. For human use.

**Headless mode**: run with `--headless` and all fields as arguments. Never calls AskUserQuestion. Returns just the created task reference on stdout (`#NN`, or `<slug>/T-NNN` for an internal project). For use by `/project-intake`, crons, and other skills that compose task creation programmatically.

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
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (new issue + epic edit) — external projects |
| Task files | `<workspace>/tasks/T-NNN.md`, `<workspace>/project.md` | Yes | Yes (new file + Tasks list) — internal projects |

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

- **Linked project** — unchanged: the task is a GitHub issue (Steps 5–6).
- **Platform-tracked project** — Steps 3 and 4 are the same; then, instead of Steps 5 and 6, one call to `mcp__trinity__create_project_task`:

  | Field | From |
  |---|---|
  | `project_id` | the charter's `platform_project:`, or the listed project |
  | `title`, `objective` | as gathered |
  | `done_definition` | the Definition of Done checklist |
  | `context` | the context, then `Validation:` and the Step 4 rows when there are validators beyond the default |
  | `owner` | the accountable party |
  | `assignee` | the executing agent, when it is not this agent |
  | `waiting_on` | the actor, when the task is parked on someone |

  The platform allocates the id. With a waiting-on actor, follow with `mcp__trinity__add_project_task_note` carrying the `### Waiting on <actor> — YYYY-MM-DD` text (standard §7). **Priority is a person's on the platform:** the task starts at `p2`; when another priority was asked for, add `Requested priority: pN` to `context` and say in the output that a person sets it on the project page. There is no checklist to edit and nothing to commit. A refusal is reported as it came — never fall back to a task file.

  Output: `<slug>/T-NNN` (headless), or the Step 7 summary with `Project: <name> (platform — <id>)`.

## Process

### Step 1: Read the standard

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration**. A standard without a §0 block (written before template 1.3) resolves to the defaults below, which are exactly the pre-1.3 behaviour (colon vocabulary, `project-steward/` state, no fleet hooks):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
cfg() { awk -v k="${1}" -v d="${2}" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$(0)~p{v=$(0);sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
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

**If no standard exists, stop and run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Pre-1.3 standards: resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2 when the block returns them empty.

### Step 2: Select parent project and its mode

Resolve the mode first, with the standard's §16 finder (`charter_for`, `mode_of`): if `charter_for "$PROJECT_SLUG"` returns a charter whose mode is **internal**, this is an internal project — its workspace is that charter's folder; skip to **Internal path** below and never call `gh`. Otherwise it is external — continue here. If `$REGISTRY` is `none` and no internal charter matches, exit with `ERROR: No project $PROJECT_SLUG`.

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
Ask the user which project this task belongs to — list internal projects too (`charters`, those whose mode is internal, by slug and tldr). Resolve the slug from the `project:<slug>` label on the chosen epic, or from the chosen charter's folder.

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
  --label "task,project:$SLUG,${L_OWNER}$OWNER,${L_PRIORITY}$PRIORITY" \
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

### Internal path (standard §16)

Steps 3 and 4 are the same in both modes — gather the inputs and build the Validation rows. Then, instead of Steps 5 and 6:

1. **Canon placement only:** `git -C "$CANON" pull --ff-only` before allocating an id (an internal project in the canon is shared — someone may have added a task since your last pull). Write only inside the project's slug folder (`projects/<slug>/`, or this agent's earlier-placement `agents/<self>/projects/<slug>/`), and only for a project whose charter `owner:` is this agent — the steward is the one automated writer of its tasks.
2. **Allocate the id** — highest existing + 1, zero-padded to 3:
   ```bash
   N=$(ls "$WS"/tasks/T-*.md 2>/dev/null | sed -E 's#.*/T-0*([0-9]+)\.md#\1#' | sort -n | tail -1)
   ID=$(printf 'T-%03d' $(( ${N:-0} + 1 )))
   ```
3. **Write `$WS/tasks/$ID.md`** — front matter for what the labels would hold, then the four sections and an empty Log:
   ```markdown
   ---
   id: $ID
   title: $TITLE
   status: active
   owner: $OWNER
   agent: $ASSIGNED_AGENT          # omit the line when none
   priority: $PRIORITY             # default: the charter's priority:
   waiting_on: $WAITING_ON         # omit the line when none
   created: $TODAY
   updated: $TODAY
   ---

   ## Objective
   $OBJECTIVE

   ## Definition of Done
   $DOD_ITEMS

   ## Context
   Project: $SLUG ($WS/project.md)
   $CONTEXT

   ## Validation
   $VALIDATION_ROWS

   ## Log
   ```
   With a waiting-on actor, append the `### Waiting on $WAITING_ON — $TODAY` entry (standard §7: asked / channel / expected back / closes when) under `## Log`.
4. **List it in the charter:** append `- [ ] $ID $TITLE` to project.md's `## Tasks` section (after the last item, or directly under the header), and set the envelope's `updated:` to today.
5. **Commit** the two files — they are the registry. Agent level: `git add "$WS/tasks/$ID.md" "$WS/project.md" && git commit -m "task: $SLUG/$ID $TITLE"`. Canon: `/canon-publish`; if it is refused because another writer published the same id, re-run from 1 with the next free id (rename the file, fix the Tasks line) — ids are never shared or reused.

The reference for this task everywhere (dispatch, digest, projections) is `$SLUG/$ID`.

### Step 7: Output

**Headless mode**: print exactly one line — the task reference — and exit:
```
#$TASK_NUMBER            (external)
$SLUG/$ID                (internal)
```

**Interactive mode**: print the full summary, ending with the closing statement required by standard §14a — what is now true, what is waiting on the human, and what happens next without them:
```
Task created: #$TASK_NUMBER — $TITLE        (internal: $SLUG/$ID — $WS/tasks/$ID.md)
Project:      [Project] $PROJECT_NAME (epic #$EPIC_NUMBER | internal — $WS)
Owner:        $OWNER
Priority:     $PRIORITY
Validation:   $VALIDATION_SUMMARY
Waiting on:   $WAITING_ON (open loop — you close this one) | nobody

Waiting on you: <the one thing, or "nothing">
Next without you: <what the steward will do on its own, or "nothing until you say">
```
