---
name: project-init
description: Create or adopt a long-term managed project per fleet/project-standard.md — GitHub epic issue with labels in the standard's registry repo plus a project_files/<slug>/ workspace. Use when starting a new multi-session project or bringing an existing project folder under fleet management.
argument-hint: "[project name | adopt <existing-folder>]"
automation: manual
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-03
  author: orchestrator
  changelog:
    - "1.1: Ownership-matrix awareness — when orchestration.md §3b has a domain row matching the project, offer its R as the default owner (operator can override); informational default, not a gate"
    - "1.0: Initial bundle version — adopted from a production orchestrator's project-init v1.0 and universalized: registry repo read from fleet/project-standard.md §1 at runtime (not hardcoded), needs-operator label in the base set, owner validation against the system map"
---

# Project Init

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-init vX.Y — recent: <summary>`. Then proceed.

## Purpose

Bring a long-term project under standardized fleet management: create the GitHub epic
issue (registry entry) and the local workspace folder, both conforming to
`fleet/project-standard.md`. After init, `/project-steward` manages the project
autonomously.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Fleet project standard | `fleet/project-standard.md` | Yes | No |
| Fleet system map (valid agent names) | `fleet/system-map.yaml` | Yes | No |
| GitHub issues + labels | the standard's registry repo (`$REGISTRY`, §1) via `gh` | Yes | Yes |
| Project workspace | `project_files/<slug>/` | Yes | Yes |

## Prerequisites

- `fleet/project-standard.md` exists — it is the single source of conventions. If missing,
  abort (run `/add-orchestrator` and opt into the project-management layer first).
  Resolve **`$REGISTRY`** = the registry repo named in its §1 "Registry" row.
- `gh` authenticated with repo scope on `$REGISTRY` (`gh auth status`).

## Process

### Step 1: Read the standard

Read `fleet/project-standard.md`. Its label taxonomy, epic anatomy, and folder standard
override anything remembered from training or prior runs.

### Step 2: Gather inputs

From the argument and conversation context, determine:

- **Mode**: `new` (default) or `adopt` (argument starts with `adopt` or names an existing
  `project_files/` folder).
- **Name** and **slug** (kebab-case; derive from name, confirm no collision).
- **Goal** (one paragraph) and **success criteria** (2-5 checkable items).
- **Owner agent(s)** — must exist in `fleet/system-map.yaml` (or be the managing agent
  itself, per standard §3).
- **Priority** — default `priority:p2`.

For adopt-mode, read the existing folder (especially any `project.md`, `README`, or status
files) and draft goal/criteria from what is there.

Ask via `AskUserQuestion` only for what cannot be determined: typically goal and owner
agent. Do not ask about things with sensible defaults (priority, slug). For the owner:
if `fleet/orchestration.md` §3b (ownership matrix) has a domain row matching the
project's work, offer that domain's **responsible** agent as the default — the operator
can override; it's an informational default, not a gate.

### Step 3: Check for collisions

```bash
gh issue list --repo "$REGISTRY" --label project --state all --search "<name>" --json number,title
ls -d project_files/<slug> 2>/dev/null
```

If an epic already exists for this project, stop and report it — offer to update instead.

### Step 4: Ensure labels exist (idempotent)

Create any missing labels from the standard's taxonomy plus the project-specific ones:

```bash
# base set (no-op if present)
for L in "project:0e8a16" "task:c2e0c6" "status:active:1d76db" "status:blocked:d93f0b" \
         "status:needs-operator:fbca04" "status:paused:cccccc" \
         "priority:p1:b60205" "priority:p2:ff9f1c" "priority:p3:c5def5"; do
  name="${L%:*}"; color="${L##*:}"
  gh label create "$name" --repo "$REGISTRY" --color "$color" 2>/dev/null || true
done
gh label create "project:<slug>" --repo "$REGISTRY" --color "5319e7" 2>/dev/null || true
gh label create "agent:<owner>" --repo "$REGISTRY" --color "0052cc" 2>/dev/null || true
```

### Step 5: Create the epic issue

Build the body exactly per the standard's epic anatomy (Goal, Success criteria, Workspace,
Owner agents, Cadence notes, Current status, Tasks). Then:

```bash
gh issue create --repo "$REGISTRY" \
  --title "[Project] <Name>" \
  --label "project,project:<slug>,status:active,priority:<pN>,agent:<owner>" \
  --body-file <tmpfile>
```

### Step 6: Scaffold the workspace

- New mode: `mkdir -p project_files/<slug>/` and write `project.md` — the charter
  mirroring the epic (goal, criteria, owner agents) plus the epic issue URL.
- Adopt mode: keep the folder as-is; create or update `project.md` to add the charter
  sections and the epic URL. Record the folder's actual path in the epic body (it may not
  match the slug — the epic's Workspace field is authoritative).

### Step 7: Optional initial tasks

If the conversation already defines concrete first tasks, create task issues per the
standard (label `task` + `project:<slug>` + `agent:<name>`) and check-list them in the
epic body. Otherwise leave the Tasks section empty — the steward will flag an empty
active project for task definition.

## Outputs

- Epic issue URL (print it).
- Workspace path `project_files/<slug>/` with `project.md`.
- Confirmation line listing labels applied and any task issues created.
