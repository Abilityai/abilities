---
name: project-intake
description: Headless intake primitive — routes actionable items from any source (meetings, email, Slack, issue trackers) into the project's registry — GitHub Issues for an external project, the project's own tasks/ folder for an internal one (standard §16). Dedupes by meaning (not exact title), creates tasks with full anatomy (Objective / Definition of Done / Context / Validation), or records one-line state news (epic comment / log.md). Returns the task reference. Never interactive — called by other skills and crons.
argument-hint: "--project=<slug> --title=\"...\" --source=\"<url-or-note>\" [--owner=<actor>] [--priority=p2] [--agent=<name>] [--waiting-on=<actor>] [--dod=\"item1|item2\"] [--objective=\"...\"] [--context=\"...\"] [--state-news]"
allowed-tools: Bash, Read, Grep, mcp__trinity__list_projects, mcp__trinity__list_project_tasks, mcp__trinity__create_project_task, mcp__trinity__add_project_task_note, mcp__trinity__add_project_log_entry
user-invocable: false
metadata:
  version: "1.6.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
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

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-intake v1.6.1 — recent: arguments no longer break the config resolver`. Then proceed.

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
