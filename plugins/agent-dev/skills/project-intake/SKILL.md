---
name: project-intake
description: Headless intake primitive — routes actionable items from any source (meetings, email, Slack, issue trackers) into the project's registry — on Trinity the platform project's tasks (standard §17); offline, GitHub Issues for an external project or the project's own tasks/ folder for an internal one (standard §16). Dedupes by meaning (not exact title), creates tasks with full anatomy (Objective / Definition of Done / Context / Validation), or records one-line state news (epic comment / log.md). Returns the task reference. Never interactive — called by other skills and crons.
argument-hint: "--project=<slug> --title=\"...\" --source=\"<url-or-note>\" [--owner=<actor>] [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--dod=\"item1|item2\"] [--objective=\"...\"] [--context=\"...\"] [--state-news]"
allowed-tools: Bash, Read, Grep
user-invocable: false
metadata:
  version: "1.5"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.5: On Trinity the platform is the home (ent#673 re-scope; standard §17): for a platform project the dedupe reads `list_project_tasks` (open tasks), a new task is created through `/project-task`'s Platform path (`create_project_task`), and state news is one `add_project_log_entry` — output `<project id>/T-NNN`, `DUPLICATE:<project id>/T-NNN` or `PROJECT:<project id>`. `--project=` takes the project id or its name. Off Trinity, unchanged"
    - "1.4: Internal tracking (ent#673): a project whose charter resolves to `tracking: internal` (standard §16) takes intake as a task file — dedupe by meaning over the titles of its open tasks/*.md, create through the same internal path as /project-task (id allocation, front matter, Tasks list, commit / canon-publish), waiting-on as `waiting_on:` + a Log entry — and state news as one appended line in the project's log.md. Outputs `<slug>/T-NNN`, `DUPLICATE:<slug>/T-NNN`, `PROJECT:<slug>`. No GitHub access for internal projects. External: unchanged"
    - "1.3: Shared projects (ruling R21, ent#588) — no behaviour change: intake targets the epic by `project:<slug>` label exactly as before, at both visibility levels; the one rule added is that a workspace path, when one is passed through, is the epic body's Workspace field resolved per PROJECT_STANDARD §15 (canon: paths through the x-canon clone), never project_files/<slug>/ derived from the slug"
    - "1.2: Read-the-standard guard (missing PROJECT_STANDARD.md → run /project-init first); skill is now authored standalone (installer copies from here)"
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
| `--project=<slug>` | yes | Target project slug (from `project:<slug>` label, or an internal project's folder name) |
| `--title="..."` | yes | Plain imperative title for the actionable item |
| `--source="..."` | yes | URL or short description of origin (meeting link, email subject, Slack permalink, ticket URL) |
| `--owner=<actor>` | no | Accountable party. Defaults to the project's primary owner from the epic. |
| `--priority=pN` | no | p1/p2/p3. Inherits from epic if omitted. |
| `--agent=<name>` | no | Executing agent label if immediately assignable. |
| `--waiting-on=<actor>` | no | The item is parked on an actor outside the registry — applies `waiting-on:<actor>` and posts the `### Waiting on` comment so the steward ages it and the operator sees it in "Your open loops" (standard §14b). Use this whenever intake captures "X owes us an answer". |
| `--dod="item1\|item2"` | no | Pipe-separated DoD items. Default: single item derived from title. |
| `--objective="..."` | no | Objective text. Defaults to the title. |
| `--context="..."` | no | Additional context beyond the source link. |
| `--state-news` | no | Flag: item is project-state news, not a task. Post a one-line comment on the epic (return `EPIC:#NN`), or append it to an internal project's `log.md` (return `PROJECT:<slug>`). |


### Workspace path (standard §15 — read, never derived)

This skill writes GitHub, not workspaces. If a caller hands it — or it hands a caller — a workspace path, that path is the epic body's `## Workspace` field resolved through the standard's §15 resolver (`canon:projects/<slug>/` → through the x-canon clone; anything else → repo-relative; missing → no workspace), **never `project_files/<slug>/` derived from the slug**. A shared project (ruling R21) sits in the canon and is otherwise identical: same epic, same task anatomy, same intake path.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (task issue + epic checklist or one-line comment) |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. **If it is missing, stop and run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Resolve `$REGISTRY` and `$AGENT_NAME` from §1 and §2.

### Step 2: Parse and validate arguments

Parse all `--key=value` and flag arguments from `$ARGUMENTS`.

Validate:
- `--project` present → **on Trinity first (standard §17)**: unless `--offline`, call `list_projects`; on `success: true` resolve `--project` against it (the project id, or exactly one project name, case-insensitive — none or several: `ERROR: No project $PROJECT`) and take the **Platform** branches of Steps 3–4 below; defaults come from the project (`get_project`: steward for OWNER). Never call `gh` and never write files for a platform project. Otherwise **resolve the mode** (standard §16 finder): if `charter_for "$PROJECT_SLUG"` returns a charter whose `mode_of` is **internal**, the project is internal — its workspace is that charter's folder, and Steps 3–7 take their **Internal** branches below; never call `gh`. Otherwise look up the epic:
  ```bash
  gh issue list --repo "$REGISTRY" --label "project:$PROJECT_SLUG" --label project --state open \
    --json number,title,labels,body -q '.[0]'
  ```
  If no epic found: exit with `ERROR: No open epic for project:$PROJECT_SLUG`
- `--title` present. If missing: exit with `ERROR: --title is required`
- `--source` present. If missing: exit with `ERROR: --source is required`

Resolve defaults from the epic (internal: from the charter — `owner:` for OWNER when no `## Owners` entry is clearer, `priority:` for PRIORITY):
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

**Internal:** append one line to the project's log instead, then commit it (canon: `/canon-publish`) and output `PROJECT:$PROJECT_SLUG`:
```bash
printf '\n**State update** (%s): %s — source: %s\n' "$(date -u +%Y-%m-%d)" "$TITLE" "$SOURCE" >> "$WS/log.md"
```

**Platform:** one `add_project_log_entry` with `kind: note` and the same line as the body; output `PROJECT:$PROJECT_ID`.

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

**Internal:** the candidates are the `title:` values of the project's task files whose `status:` is not `done`:
```bash
for f in "$WS"/tasks/T-*.md; do awk -v f="$(basename "$f" .md)" 'NR==1&&/^---/{m=1;next} m&&/^---/{exit} m&&/^status:/{st=$2} m&&/^title:/{sub(/^title: */,"");t=$0} END{if(st!="done")print f"\t"t}' "$f"; done
```
Same two tests.

**Platform:** the candidates are the titles from `list_project_tasks` (default `open`). Same two tests.

On duplicate detected: output `DUPLICATE:#$EXISTING_NUMBER` (internal: `DUPLICATE:$PROJECT_SLUG/T-NNN`; platform: `DUPLICATE:$PROJECT_ID/T-NNN`) and exit.

If no duplicate, proceed.

### Internal: create the task file

For an internal project, Steps 5–7 are replaced by the **Internal path** of `/project-task` (standard §16): allocate the next id, write `tasks/T-NNN.md` with the body built below (Objective / Definition of Done / Context with `Source: $SOURCE` / Validation, then an empty `## Log`), put `--agent` and `--waiting-on` in the front matter (and a `### Waiting on` Log entry for the latter), list it in project.md's `## Tasks`, and commit (canon: `/canon-publish`). Then output `$PROJECT_SLUG/T-NNN` (Step 8).

### Platform: create the task

For a platform project, Steps 5–7 are replaced by the **Platform path** of `/project-task` (standard §17): one `create_project_task` with the body built below (Objective / Definition of Done / Context with `Source: $SOURCE` and the Validation rows), `assignee` for `--agent` and `waiting_on` for `--waiting-on`. Then output `$PROJECT_ID/T-NNN` (Step 8).

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
#$TASK_NUMBER             (external)
$PROJECT_SLUG/T-NNN       (internal)
```
