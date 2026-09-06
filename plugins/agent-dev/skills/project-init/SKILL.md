---
name: project-init
description: Create or adopt a long-term managed project per PROJECT_STANDARD.md — GitHub epic issue with idempotent label creation and a project_files/<slug>/ workspace stub. Use when starting a new multi-session project or bringing an existing project folder under management.
argument-hint: "[project name | adopt <existing-folder>]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.1: Self-heal — when PROJECT_STANDARD.md is missing, materialize it from PROJECT_STANDARD.template.md shipped in this skill directory (resolving registry/operator/agent/max-age with sensible defaults). Makes the skill usable when assigned from the skills library without running the installer; the installer now copies from this directory instead of carrying its own copy"
    - "1.0: Initial version — owner/agent label distinction, unclassified quarantine, full Epic anatomy per PROJECT_STANDARD.md §4"
---

# Project Init

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `project-init v1.0 — recent: Initial version`. Then proceed.

## Purpose

Bring a long-term project under standardized management: create the GitHub epic issue (registry entry) and the local workspace stub, both conforming to `PROJECT_STANDARD.md`. After init, `/project-steward` manages the project autonomously.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Convention doc | `PROJECT_STANDARD.md` (repo root) | Yes | No |
| GitHub issues + labels | the `$REGISTRY` repo via `gh` | Yes | Yes |
| Project workspace | `project_files/<slug>/` | Yes | Yes |

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md` from the repo root. **If it is missing, materialize it first** — the standard's template ships next to this skill (`PROJECT_STANDARD.template.md` in this skill's directory: `.claude/skills/project-init/` when injected or installed, `${CLAUDE_PLUGIN_ROOT}/skills/project-init/` when run as a plugin command):

```bash
[ -f PROJECT_STANDARD.md ] && echo "standard: present" || echo "standard: MISSING — materializing from template"
```

When missing, resolve the four config values (ask only where nothing sensible resolves): registry repo (`gh repo view --json nameWithOwner -q .nameWithOwner`, default = this repo), operator (the human this deployment escalates to — ask), agent name (`grep '^name:' template.yaml | head -1 | awk '{print $2}'`, else the folder name), pending-verification max age (default `48` hours). Then:

```bash
TEMPLATE="$(ls .claude/skills/project-init/PROJECT_STANDARD.template.md "${CLAUDE_PLUGIN_ROOT:-/nonexistent}/skills/project-init/PROJECT_STANDARD.template.md" 2>/dev/null | head -1)"
sed -e "s|{{REGISTRY}}|$REGISTRY|g" -e "s|{{OPERATOR}}|$OPERATOR|g" -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{PV_MAX_AGE}}|$PV_MAX_AGE|g" -e "s|{{DATE}}|$(date -u +%Y-%m-%d)|g" "$TEMPLATE" > PROJECT_STANDARD.md
git add PROJECT_STANDARD.md && git commit -m "chore: materialize PROJECT_STANDARD.md from the project-init template" 2>/dev/null || true
```

The standard is the deployer's live configuration — edit that file to change behavior, never this skill. Then resolve `$REGISTRY`, `$AGENT_NAME`, and `$OPERATOR` from §1 and §2. These override any remembered values.

### Step 2: Verify gh access

```bash
gh api "repos/$REGISTRY/labels" -q '.[0].name' 2>&1
```

If this returns an error (403, 404, or "Resource not accessible"), stop and report exactly what failed. The PAT must have `repo` + `issues` scope on `$REGISTRY`.

### Step 3: Gather inputs

Determine mode from the argument: `adopt` (argument starts with "adopt" or names an existing `project_files/` folder) or `new` (default).

For `adopt` mode: read the existing folder (look for `project.md`, `README.md`, any status files) and draft goal/criteria from what's there.

Use AskUserQuestion for inputs that cannot be determined from context:
- **Name** (derive slug as kebab-case; confirm no collision with existing epics)
- **Goal** (one paragraph)
- **Success criteria** (2–5 checkable items)
- **Owner(s)** — who is accountable (human names and/or agent names)
- **Priority** — default `p2`
- **Cadence** — default "as needed"

### Step 4: Check for collisions

```bash
gh issue list --repo "$REGISTRY" --label project --state all --search "$NAME" --json number,title,labels
ls -d project_files/$SLUG 2>/dev/null
```

If an epic already exists for this project, stop and show it — offer to update instead.

### Step 5: Ensure labels exist (idempotent)

Create any missing labels from the standard's taxonomy. All `2>/dev/null || true` so re-runs are safe:

```bash
gh label create "project" --repo "$REGISTRY" --color "0e8a16" --description "Project epic issue" 2>/dev/null || true
gh label create "task" --repo "$REGISTRY" --color "c2e0c6" --description "Task belonging to a project" 2>/dev/null || true
gh label create "status:active" --repo "$REGISTRY" --color "1d76db" --description "Being worked" 2>/dev/null || true
gh label create "status:blocked" --repo "$REGISTRY" --color "d93f0b" --description "External dependency blocking progress" 2>/dev/null || true
gh label create "status:needs-decision" --repo "$REGISTRY" --color "fbca04" --description "Blocked on owner decision" 2>/dev/null || true
gh label create "status:paused" --repo "$REGISTRY" --color "cccccc" --description "Deliberately on hold" 2>/dev/null || true
gh label create "status:pending-verification" --repo "$REGISTRY" --color "e4e669" --description "Agent claimed done; awaiting DoD verification" 2>/dev/null || true
gh label create "status:done" --repo "$REGISTRY" --color "6e5494" --description "Verified complete (absorbing; only a human reopens)" 2>/dev/null || true
gh label create "status:unclassified" --repo "$REGISTRY" --color "f9d0c4" --description "Auto-stubbed workspace folder not yet classified" 2>/dev/null || true
gh label create "priority:p1" --repo "$REGISTRY" --color "b60205" --description "High priority" 2>/dev/null || true
gh label create "priority:p2" --repo "$REGISTRY" --color "ff9f1c" --description "Normal priority" 2>/dev/null || true
gh label create "priority:p3" --repo "$REGISTRY" --color "c5def5" --description "Low priority" 2>/dev/null || true
# Project-specific labels
gh label create "project:$SLUG" --repo "$REGISTRY" --color "5319e7" --description "Membership: project $NAME" 2>/dev/null || true
for OWNER in $OWNERS; do
  gh label create "owner:$OWNER" --repo "$REGISTRY" --color "0052cc" --description "Accountable: $OWNER" 2>/dev/null || true
done
```

### Step 6: Create the epic issue

Build the body per the standard's epic anatomy (§4). Use the inputs from Step 3. The `Current status` section says "(maintained by /project-steward — do not hand-edit)" as its initial value. The `Tasks` section starts empty.

```bash
cat > /tmp/epic-body.md << 'EOF'
## Goal
$GOAL

## Success criteria
$SUCCESS_CRITERIA_ITEMS

## Workspace
`project_files/$SLUG/`

## Owners
$OWNERS_LIST

## Cadence
$CADENCE

## Current status
(maintained by /project-steward — do not hand-edit; latest steward update wins)

## Tasks
<!-- tasks will be listed here as #NN items by /project-task -->
EOF

gh issue create --repo "$REGISTRY" \
  --title "[Project] $NAME" \
  --label "project,project:$SLUG,status:active,priority:$PRIORITY" \
  --body-file /tmp/epic-body.md
```

For each owner, add the `owner:<name>` label:
```bash
for OWNER in $OWNERS; do
  gh issue edit $ISSUE_NUMBER --repo "$REGISTRY" --add-label "owner:$OWNER"
done
```

### Step 7: Scaffold the workspace

**New mode:** create `project_files/$SLUG/` and write `project.md` mirroring the epic:

```bash
mkdir -p project_files/$SLUG
```

Write `project_files/$SLUG/project.md` with: the epic issue URL, goal, success criteria, owner list, cadence, and a note that the epic is the authoritative record.

**Adopt mode:** keep the existing folder; create or update `project.md` to add the epic URL and charter sections. Record the actual folder path in the epic body's Workspace field (may differ from the slug).

### Step 8: Summary

Print:
```
## Project initialized: $NAME

Epic:      $EPIC_URL
Workspace: project_files/$SLUG/
Labels:    project, project:$SLUG, status:active, priority:$PRIORITY, owner:<...>

Next steps:
  /project-task — create the first task
  /project-steward — run a sweep (or let the schedule do it)
```
