---
name: project-intake
description: "Headless intake primitive. On a Trinity instance with Projects (standard 3.0, §28–§37) it routes an item into a platform project only — picks the project (explicit id or name, else by goal; none → NO_PROJECT, nothing created), dedupes by meaning over every task, then creates a task with the §33 anatomy, adds a note to an existing task, or writes one project log entry per outcome; a GitHub development issue is linked with refs, never copied. Returns T-NNN. Without Trinity Projects, runs the frozen offline mode (standard 2.x): GitHub Issues for an external project, the project's tasks/ folder for an internal one. Never interactive — called by other skills and crons."
argument-hint: "[--project=<id|name|slug>] --title=\"...\" --source=\"<url-or-note>\" [--owner=<actor>] [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--dod=\"item1|item2\"] [--objective=\"...\"] [--context=\"...\"] [--state-news [--kind=note]] [--task=T-NNN] [--refs=owner/repo#N]"
allowed-tools: Bash, Read, Grep, mcp__trinity__list_projects, mcp__trinity__list_project_tasks, mcp__trinity__create_project_task, mcp__trinity__add_project_task_note, mcp__trinity__add_project_log_entry, mcp__trinity__get_project, mcp__trinity__get_project_log, mcp__trinity__update_project_task, mcp__trinity__list_platform_files, mcp__trinity__read_platform_file, mcp__trinity__propose_project_changes
user-invocable: false
metadata:
  version: "2.0.0"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "2.0.0: Standard 3.0 (operator rulings P1–P11, 2026-11-11). On Trinity Projects intake writes only to the platform project: a new first section picks the project (explicit, or by goal — none fits → NO_PROJECT, nothing created), dedupes by meaning over every task, and routes new work to create_project_task (as /project-task --headless), news about a task to add_project_task_note, and project news to one add_project_log_entry per outcome. A GitHub development issue is linked with refs, never copied; nothing is written to GitHub. Outputs T-NNN, NOTE:T-NNN, LOG:<id>, DUPLICATE:…, NO_PROJECT:…. The old body is kept unchanged as the frozen offline mode"
    - "1.6.1: Fix — the skill runner replaces every dollar-digit placeholder in a skill body with the invocation's arguments, so a run with arguments (project-init platform <slug>, project-status <slug>, --headless task/intake) broke the §0 resolver and the awk field reads: every config key resolved empty. Shell positionals are now ${1}/${2}, awk fields $(0)/$(2). Found 2026-10-10 by the deployed trinity-pm on the first platform import"
    - "1.6: Platform mode (ent#788, ruling R38): for a platform-tracked project on a Trinity instance with Projects enabled intake dedupes against the platform's task list and creates the task there, and state news lands in the project's shared log (linked projects: the epic comment plus one log entry). Without Trinity nothing changes"
    - "1.5: One lineage (ent#789): the standard is resolved at the repo root or at fleet/project-standard.md and its §0 Configuration supplies the label vocabulary by role — owner and priority labels are ${L_OWNER}<owner> / ${L_PRIORITY}pN (defaults unchanged); the epic's owner/priority defaults are read through the same prefixes"
    - "1.4: Internal tracking (ent#673): a project whose charter resolves to `tracking: internal` (standard §16) takes intake as a task file — dedupe by meaning over the titles of its open tasks/*.md, create through the same internal path as /project-task (id allocation, front matter, Tasks list, commit / canon-publish), waiting-on as `waiting_on:` + a Log entry — and state news as one appended line in the project's log.md. Outputs `<slug>/T-NNN`, `DUPLICATE:<slug>/T-NNN`, `PROJECT:<slug>`. No GitHub access for internal projects. External: unchanged"
    - "1.3: Shared projects (ruling R21, ent#588) — no behaviour change: intake targets the epic by `project:<slug>` label exactly as before, at both visibility levels; the one rule added is that a workspace path, when one is passed through, is the epic body's Workspace field resolved per PROJECT_STANDARD §15 (canon: paths through the x-canon clone), never project_files/<slug>/ derived from the slug"
    - "1.2: Read-the-standard guard (missing PROJECT_STANDARD.md → run /project-init first); skill is now authored standalone (installer copies from here)"
    - "1.1: Loop closure — optional --waiting-on opens the loop explicitly (label + ### Waiting on comment), so an item captured as \"X owes us an answer\" enters the steward's aging ladder instead of sitting silently in the backlog"
    - "1.0: Initial version — headless intake primitive, dedupe by meaning, task creation with full anatomy, state-news comment path, epic Tasks checklist linkage"
---

# Project Intake

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-intake v2.0.0 — recent: on Trinity Projects intake writes only to the platform project`. Then proceed.

## On Trinity Projects — the only mode there (standard 3.0, §28–§37)

On a Trinity instance with Projects, a project lives in the platform and nowhere else (§28). Intake routes an item into a platform project: a new task, a note on an existing task, or one log entry. No epic, no labels, no `tasks/` folder, no `log.md`. A GitHub development issue is linked with `refs`, never copied, and nothing is written to GitHub. This skill stays headless: it never asks. The standard's §29 and §33 are the contract; this section is the procedure.

### Step 0: Detect

Resolve §0 with the resolver in the offline mode's Step 1. Read only `agent` and `platform`. No standard file → use the defaults; do not stop. Then call `mcp__trinity__list_projects` once.

- `enabled: true` → run this section.
- `enabled: false`, no such tool, or `platform: off` in §0 → go to **Offline mode** below.
- Refused with `external_audience` or `turn_unknown` → this turn is not an internal one. Print `ERROR: not an internal turn` and exit. Repeat no project detail.

### Arguments

The offline arguments, read this way:

| Argument | On the platform |
|---|---|
| `--project=<id or name>` | optional — without it the project is matched by goal (Step 1) |
| `--title`, `--source` | required, as offline |
| `--objective`, `--dod`, `--context` | as offline; defaults: the title, and one item `<title> completed and verified against the source` |
| `--agent`, `--owner`, `--waiting-on`, `--priority` | as `/project-task --headless` on the platform |
| `--refs="owner/repo#N,..."`, `--milestone=M<n>`, `--parent=T-NNN`, `--blocked-by="T-NNN,..."` | as `/project-task --headless` on the platform |
| `--task=T-NNN` | the item is news about this task |
| `--state-news` | the item is news about the project as a whole |
| `--kind=decision\|deliverable\|blocker\|handoff\|note` | the log entry kind for `--state-news`; default `note` |

A missing `--title` or `--source` → `ERROR: --<field> is required` and exit.

### Step 1: Pick the project

- `--project` given → match it against the `list_projects` result: exact id first, then the name (case-insensitive). No match → print `NO_PROJECT: <value>` and exit.
- Not given → compare the item (title, objective, source) with each listed project's name and goal (`get_project` for the goal when the list does not carry it). Exactly one project clearly fits → use it. None, or more than one → print `NO_PROJECT: <the candidates, or "none fits">` and exit. Create nothing.

Call `mcp__trinity__get_project` for the chosen project. Keep its `agents` and steward.

### Step 2: Classify and dedupe

Call `mcp__trinity__list_project_tasks(project_id, status: all)`.

- `--task` given → the item is task news: Step 3b.
- `--state-news` → project news: Step 3c.
- Otherwise compare the title and objective with every task, by meaning, not by exact words (the offline Step 4 tests are a floor, not the rule):
  - same work, and the item adds nothing the task does not already hold → print `DUPLICATE:T-NNN` and exit;
  - same work, and the item adds a fact, a date or a source → task news on that task: Step 3b;
  - new work → Step 3a.

### Step 3a: New work → a task

Create it exactly as `/project-task --headless` does on the platform (its Steps 3–4): the §33 anatomy, `Validation:` in `context`, `Milestone: M<n>` when `plan.md` has milestones, `Requested priority: pN` for a priority, an assignee only from the project's `agents`. Add `Source: <source>` to `context`.

When the source is a GitHub development issue or PR (engineering work on a code base), put it in `refs`. The task's objective says what the project needs from it. Do not copy the issue's body, labels or state.

Print the new task id `T-NNN` and exit.

### Step 3b: News about a task → a note

One `mcp__trinity__add_project_task_note(project_id, task_id, body)`. The body is one or two plain lines: the news and `Source: <source>`. A waiting-on actor named by the item → `mcp__trinity__update_project_task` with `waiting_on` as well.

Print `NOTE:T-NNN` and exit.

### Step 3c: News about the project → one log entry

Read the recent log with `mcp__trinity__get_project_log`. If an entry already records the same outcome, write nothing and print `DUPLICATE:LOG`. Otherwise one `mcp__trinity__add_project_log_entry(project_id, kind, body)` — the kind from `--kind`, the body one line with the source. One entry per outcome, never one per run (§29). Add `task_id` when the outcome belongs to a task.

Print `LOG:<project id>` and exit.

### Refusals

A refusal is printed as `ERROR: <code> <message>` and the run exits. Never work around it, and never fall back to a file or an issue.

## Offline mode (frozen — agents without Trinity Projects)

Runs only when `list_projects` is not enabled (standard §28). Written for standard 2.x; developed no further. Its §17 'linked project' passages are unreachable on Trinity.

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
| Convention doc | `PROJECT_STANDARD.md` (repo root) or `fleet/project-standard.md` (orchestrator) — §0 is the configuration | Yes | No |
| GitHub issues | `$REGISTRY` via `gh` | Yes | Yes (task issue + epic checklist or one-line comment) |

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

- **Linked project** — the task path is unchanged (GitHub issue). `--state-news` posts the epic comment as written **and** one `mcp__trinity__add_project_log_entry` (`kind: note`, the same line), so the project's members see it.
- **Platform-tracked project:**
  - **Dedupe (Step 4):** the candidates are the titles from `mcp__trinity__list_project_tasks` (open is the default). Same two tests. Duplicate → `DUPLICATE:<slug>/T-NNN`.
  - **Create (Steps 5–7):** one `mcp__trinity__create_project_task`, as in `/project-task`'s platform mode — `context` carries `Source: $SOURCE`; `--agent` → `assignee`; `--waiting-on` → `waiting_on` plus a `### Waiting on` note via `mcp__trinity__add_project_task_note`; a `--priority` other than p2 goes into `context` as `Requested priority: pN` (priority is a person's on the platform). Output `<slug>/T-NNN`.
  - **`--state-news`:** one `mcp__trinity__add_project_log_entry` (`kind: note`). Output `PROJECT:<slug>`.

This skill stays headless: a platform refusal is printed as `ERROR: <message>` and the run exits — never a task file instead.

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

### Step 2: Parse and validate arguments

Parse all `--key=value` and flag arguments from `$ARGUMENTS`.

Validate:
- `--project` present → **resolve the mode first** (standard §16 finder): if `charter_for "$PROJECT_SLUG"` returns a charter whose `mode_of` is **internal**, the project is internal — its workspace is that charter's folder, and Steps 3–7 take their **Internal** branches below; never call `gh`. Otherwise look up the epic:
  ```bash
  gh issue list --repo "$REGISTRY" --label "project:$PROJECT_SLUG" --label project --state open \
    --json number,title,labels,body -q '.[0]'
  ```
  If no epic found: exit with `ERROR: No open epic for project:$PROJECT_SLUG`
- `--title` present. If missing: exit with `ERROR: --title is required`
- `--source` present. If missing: exit with `ERROR: --source is required`

Resolve defaults from the epic (internal: from the charter — `owner:` for OWNER when no `## Owners` entry is clearer, `priority:` for PRIORITY):
- `OWNER`: if not provided, extract from the epic's `${L_OWNER}*` labels (first match).
- `PRIORITY`: if not provided, read from the epic's `${L_PRIORITY}*` label.
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
for f in "$WS"/tasks/T-*.md; do awk -v f="$(basename "$f" .md)" 'NR==1&&/^---/{m=1;next} m&&/^---/{exit} m&&/^status:/{st=$(2)} m&&/^title:/{sub(/^title: */,"");t=$(0)} END{if(st!="done")print f"\t"t}' "$f"; done
```
Same two tests.

On duplicate detected: output `DUPLICATE:#$EXISTING_NUMBER` (internal: `DUPLICATE:$PROJECT_SLUG/T-NNN`) and exit.

If no duplicate, proceed.

### Internal: create the task file

For an internal project, Steps 5–7 are replaced by the **Internal path** of `/project-task` (standard §16): allocate the next id, write `tasks/T-NNN.md` with the body built below (Objective / Definition of Done / Context with `Source: $SOURCE` / Validation, then an empty `## Log`), put `--agent` and `--waiting-on` in the front matter (and a `### Waiting on` Log entry for the latter), list it in project.md's `## Tasks`, and commit (canon: `/canon-publish`). Then output `$PROJECT_SLUG/T-NNN` (Step 8).

### Step 5: Ensure owner label exists

```bash
gh label create "${L_OWNER}$OWNER" --repo "$REGISTRY" \
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
  --label "task,project:$PROJECT_SLUG,${L_OWNER}$OWNER,${L_PRIORITY}$PRIORITY" \
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
