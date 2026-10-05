---
name: project-task
description: Create a task in the uniform format per PROJECT_STANDARD.md — the ONLY sanctioned task-creation path. A GitHub task issue for an external project, a tasks/T-NNN.md file for an internal one (standard §16). Enforces full anatomy (Objective / Definition of Done / Context / Validation) and adds the task to the project's Tasks checklist. Approval-ready from day one. Supports --headless for cron/compose use.
argument-hint: "[project-slug | --headless --project=<slug> --title=\"...\" --objective=\"...\" --dod=\"item1|item2\" --owner=<actor> [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--context=\"...\"]]"
allowed-tools: Bash, Read, AskUserQuestion
user-invocable: true
metadata:
  version: "1.5"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.5: Internal tracking (ent#673): for a project whose charter resolves to `tracking: internal` (standard §16) the task is written as `<workspace>/tasks/T-NNN.md` — front matter for what labels hold, the same four body sections plus an append-only `## Log` for what comments hold — and listed in project.md's `## Tasks`; a waiting-on actor becomes `waiting_on:` + a `### Waiting on` Log entry. No GitHub access. Headless output is `<slug>/T-NNN`. Canon-placed internal projects publish through /canon-publish; an id collision on publish takes the next free id. External projects: unchanged"
    - "1.4: Shared projects (ruling R21, ent#588) — no behaviour change: a task belongs to an epic found by `project:<slug>` label whether the project lives in project_files/ or in the canon; the one rule added is that a workspace path, when one is passed through, is the epic body's Workspace field resolved per PROJECT_STANDARD §15, never derived from the slug"
    - "1.3: Read-the-standard guard — a missing PROJECT_STANDARD.md now stops with a run-/project-init-first message instead of failing on an unresolved registry; skill is now authored standalone (installer copies from here)"
    - "1.2: Loop closure — optional waiting-on actor (label + ### Waiting on comment) puts a task parked on an outside party into the steward's aging ladder; interactive output ends with the §14a closing statement (waiting on you / next without you)"
    - "1.1: Add --headless mode — all fields as arguments, no AskUserQuestion, returns issue number; callable from /project-intake and crons"
    - "1.0: Initial version — full anatomy enforcement including Validation section (approval chain), owner/agent label distinction, epic checklist update"
---

# Project Task

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-task v1.2 — recent: loop closure (waiting-on + closing statement)`. Then proceed.

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
| Convention doc | `PROJECT_STANDARD.md` | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (new issue + epic edit) — external projects |
| Task files | `<workspace>/tasks/T-NNN.md`, `<workspace>/project.md` | Yes | Yes (new file + Tasks list) — internal projects |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. **If it is missing, stop and run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2.

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
