---
name: project-reconcile
description: Sync projection adapters against the registry per the project standard (PROJECT_STANDARD.md, or fleet/project-standard.md on an orchestrator) — GitHub Issues for external projects, task files for internal ones (standard §16). Processes projection gestures (check/date-push/delete) back into the registry with correct reversibility typing. Ships with Google Tasks adapter v1 (notes-field [#NN] key). Other adapters are per-deployment extensions. Reconciler is idempotent; refuses unkeyed items with a sync-gap alert.
argument-hint: "[adapter] — default: google-tasks"
allowed-tools: Bash, Read, Write, AskUserQuestion, mcp__trinity__list_projects, mcp__trinity__list_project_tasks, mcp__trinity__update_project_task
user-invocable: true
metadata:
  version: "1.4"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.4: Platform mode (ent#788, ruling R38): on a Trinity instance with Projects enabled, platform-tracked projects feed the registry map from the platform's task list (keyed <slug>/T-NNN) and a completion gesture is written with update_project_task under the platform's lattice. Without Trinity nothing changes"
    - "1.3: One lineage (ent#789): the standard is resolved at the repo root or at fleet/project-standard.md; its §0 Configuration supplies the label vocabulary by role and the state directory — the reconcile log lives under $STATE_DIR/reconcile-log/ (project-steward/ by default, fleet/project-steward/ on an orchestrator); with the done label unset, closing the issue is the done marker; with the pending-verification label unset, an agent-owned completion gesture is verified against the Definition of Done right away instead of parked"
    - "1.2: Internal tracking (ent#673): internal projects' task files join the registry map under the key `[<slug>/T-NNN]` (external keeps `[#NN]`); a check gesture on one writes the task's front matter and an appended Log entry instead of labels and a comment (human owner → status: done; agent owner → pending-verification + pending_since), and the projection item's note carries the task file path. Everything else — gesture typing, absence never authoritative, unkeyed items personal — is unchanged"
    - "1.1: Read-the-standard guard (missing PROJECT_STANDARD.md → run /project-init first); skill is now authored standalone (installer copies from here)"
    - "1.0: Initial version — generic adapter contract, Google Tasks adapter v1 with gesture typing, idempotent reconciler, sync-gap alerts for unkeyed items"
---

# Project Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-reconcile v1.4 — recent: platform mode on Trinity Projects`. Then proceed.

## Purpose

Sync projection surfaces (personal task views, team tools) against the GitHub Issues registry. The registry is write-authoritative; projections are read-only displays with one-directional gesture processing.

**Key rules (Invariant 5):**
- Projections display state; they do not own it.
- `[#NN]` prefix in the projection item title is the join key — unkeyed items cannot be synced.
- Gestures are typed by reversibility: check (completion endorsement), date-push (defer signal, no registry write), delete (soft-skip proposal, registry item survives).
- Absence is never authoritative.

## Adapters

This skill ships with the **Google Tasks adapter v1**. Other adapters (Fibery, Notion, Linear, etc.) follow the adapter contract in `PROJECT_STANDARD.md §11` and are per-deployment extensions — copy this skill, implement the three adapter methods, and register your adapter in the dispatch block below.

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

**What this skill does in platform mode:** platform-tracked projects join the one registry map (Step 3). For each, `mcp__trinity__list_project_tasks` with `status: all`; every task becomes an entry keyed `<slug>/T-NNN` (projection key `[<slug>/T-NNN]`) with its title, status, priority and owner, `is_closed` = `done`. A **check** gesture on such an item is the same two decisions as §11, written with `mcp__trinity__update_project_task`: a human owner → `status: done` with the endorsement as `note` when this agent is the project's steward (otherwise `pending-verification` — the platform lets only the steward or a person set done); an agent owner → `pending-verification` with the note. Date-push and delete gestures write nothing, as before. Linked projects are unchanged — their tasks are GitHub issues.

## Process

### Step 1: Read the standard

Resolve the standard — repo root first, then an orchestrator's `fleet/` placement — and read its **§0 Configuration**. A standard without a §0 block (written before template 1.3) resolves to the defaults below, which are exactly the pre-1.3 behaviour (colon vocabulary, `project-steward/` state, no fleet hooks):

```bash
STANDARD=$(ls PROJECT_STANDARD.md fleet/project-standard.md 2>/dev/null | head -1)
cfg() { awk -v k="$1" -v d="$2" 'BEGIN{p="^"k":"} /^## 0\. Configuration/{s=1;next} s&&/^```yaml/{f=1;next} f&&/^```/{exit} f&&$0~p{v=$0;sub(p,"",v);sub(/[[:space:]]+#.*$/,"",v);gsub(/^[[:space:]"]+|[[:space:]"]+$/,"",v);print v;found=1;exit} END{if(!found)print d}' "$STANDARD"; }
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

**If no standard exists, stop and run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Pre-1.3 standards: resolve `$REGISTRY`, `$AGENT_NAME` and `$PV_MAX_AGE` from §1, §2 and §12 when the block returns them empty.

### Step 2: Select adapter

If `$ARGUMENTS` names an adapter (`google-tasks`, `fibery`, etc.), use it.

Otherwise ask:
- **Header:** "Projection adapter"
- **Options:** "google-tasks" (built-in) or a custom adapter name (per PROJECT_STANDARD.md §11)

### Step 3: Load registry state

Both modes feed one registry map. **Internal projects** (standard §16 — charters whose mode is internal): every `tasks/T-*.md` becomes an entry keyed `<slug>/T-NNN`, from its front matter (`title`, `status`, `priority`, `owner`) with the file path standing in for the URL, `is_closed` = `status: done`. **External** (skip when `$REGISTRY` is `none`) — fetch all open task issues from the registry:
```bash
gh issue list --repo "$REGISTRY" --label task --state open \
  --json number,title,labels,body,url --limit 200
```

Also fetch recently closed issues (to detect completion gestures for already-closed items):
```bash
gh issue list --repo "$REGISTRY" --label task --state closed \
  --json number,title,labels,closedAt --limit 50
```

Build a registry map: `{issue_number → {title, status, priority, owner, url, is_closed}}`.

### Step 4: Load projection (adapter-specific)

**Google Tasks adapter v1:**

Check for `GOOGLE_TASKS_TOKEN` env var:
```bash
echo "${GOOGLE_TASKS_TOKEN:-MISSING}"
```
If missing, stop and explain: "Set `GOOGLE_TASKS_TOKEN` in your `.env` to a valid OAuth2 access token with `tasks` scope. Get one with `gcloud auth print-access-token` or a service account."

Select the task list:
```bash
curl -sf "https://tasks.googleapis.com/tasks/v1/users/@me/lists" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" | \
  python3 -c "import sys,json; lists=json.load(sys.stdin).get('items',[]); [print(f\"{i}: {l['id']} — {l['title']}\") for i,l in enumerate(lists)]"
```

If `GOOGLE_TASKS_LIST_ID` is set in env, use it. Otherwise show the list and ask which one to sync.

Fetch tasks from the selected list:
```bash
curl -sf "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks?showCompleted=true&showHidden=true&maxResults=100" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN"
```

Parse each task into: `{id, title, notes, status ("needsAction"|"completed"), due, updated}`.

Extract the key from the title — `[#NN]` (external) or `[<slug>/T-NNN]` (internal):
```bash
echo "$TITLE" | grep -oP '(?<=\[)(#\d+|[a-z0-9][a-z0-9._-]*/T-\d{3,})(?=\])'
```

**Adapter contract (implement this for custom adapters):**
```python
# Three methods your adapter must expose:
def read_projection():
    # Returns: list of {key: "42"|None, title, status, due_date, raw}
    # key is None for unkeyed items (sync-gap alert)
    pass

def write_item(key, title, priority_prefix, due_date, note):
    # Push a registry item into the projection surface
    # priority_prefix: "[P1] " | "[P2] " | "[P3] " | ""
    pass

def mark_complete(key):
    # Mark the projection item as complete (used after registry closure confirmed)
    pass
```

### Step 5: Match and diff

For each projection item:
- **Unkeyed** (no `[#NN]` in title): personal reminder — increment `personal_count`, skip entirely. Do not add to sync-gap alerts. Personal items are out of scope for registry sync.
- **Keyed**: look up issue `#NN` in the registry map.
  - **Not in registry**: check recently-closed list. If not there either, this is a sync-gap (keyed but unresolvable — the issue number may be wrong or the issue was deleted). Add to `sync_gap_alerts`.
  - **Found**: record the pair for gesture detection.

For each matched pair, detect gestures:

| Condition | Gesture |
|---|---|
| Projection status = completed; registry not closed | **check** — completion endorsement |
| Projection has a due date and it changed since last sync | **date-push** — defer signal |
| Item was in last sync log but is now absent from projection | **delete** — soft-skip proposal |
| No change | no-op |

Read the last sync log (`$STATE_DIR/reconcile-log/google-tasks-YYYY-MM-DD.json` or the most recent) to detect deletions.

### Step 6: Apply registry updates (per gesture type)

**Check (completion endorsement):** — for an internal task (`<slug>/T-NNN`) make the same two decisions with file writes: read `owner:` from the front matter; human owner → append `### Done claim — projection endorsement YYYY-MM-DD` to its `## Log`, set `status: done` and `updated:`, check it off in project.md's `## Tasks`; agent owner → append `### Done claim — projection signal YYYY-MM-DD`, set `status: pending-verification` and `pending_since:`. Commit the file (canon: `/canon-publish`). For an external task:
```bash
OWNER=$(gh issue view $NUMBER --repo "$REGISTRY" --json labels -q ".labels[].name | select(startswith(\"$L_OWNER\"))" | head -1 | sed "s/^$L_OWNER//")
```

- If owner is a human (not in the agent list): this is a human endorsement → close the issue directly:
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection endorsement $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks by $OWNER. Closing as done per PROJECT_STANDARD.md §11 (human completion = direct done)."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "$L_ACTIVE" ${L_DONE:+--add-label "$L_DONE"}   # no done label configured → closing is the marker
  gh issue close $NUMBER --repo "$REGISTRY" --reason completed
  ```
- If owner is an agent: set pending-verification. **If `$L_PENDING` is empty** (no verification hold configured) there is nothing to park it in: verify the Definition of Done against the projection evidence now, exactly as the steward's verification pass would, and close it or log `[Verification failed]` — never leave it half-done.
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection signal $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks. Setting pending-verification for steward to verify against Definition of Done."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "$L_ACTIVE" --add-label "$L_PENDING"
  ```

**Date-push (defer signal):**
- No registry write.
- Log the event: `{issue_number, old_due, new_due, observed_at}` → append to reconcile log.
- Surface in the reconcile report as an evidence signal.

**Delete (soft-skip proposal):**
- No registry write (Invariant 5: registry item survives).
- Log the proposal: `{issue_number, title, proposed_at}` → append to reconcile log.
- Report for human confirmation in the reconcile summary.

**No-op:**
- Log that the item was checked and found in sync.

### Step 7: Push projection updates (registry → projection)

For each open registry task issue NOT in the projection:
- This is an item the projection is missing. Add it to the projection using `write_item`:
  - Title: `[#NN] <issue title>` (internal: `[<slug>/T-NNN] <title>`)
  - Priority prefix: `[P1] ` / `[P2] ` / `[P3] ` based on the issue's priority label (read-only display)
  - Note: the GitHub issue URL (internal: the task file path)

For each registry issue now closed but still open in the projection:
- Call `mark_complete(key)` in the projection.

**Google Tasks — write item:**
```bash
curl -sf -X POST "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"[#$NUMBER] $PRIORITY_PREFIX$TITLE\", \"notes\": \"$ISSUE_URL\"}"
```

**Google Tasks — mark complete:**
```bash
curl -sf -X PATCH "https://tasks.googleapis.com/tasks/v1/lists/$LIST_ID/tasks/$TASK_ID" \
  -H "Authorization: Bearer $GOOGLE_TASKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"status\": \"completed\"}"
```

### Step 8: Write sync log and report

Write `$STATE_DIR/reconcile-log/google-tasks-$(date -u +%Y-%m-%d).json`:
```json
{
  "adapter": "google-tasks",
  "list_id": "$LIST_ID",
  "run_at": "<ISO timestamp>",
  "matched": N,
  "personal_items": N,
  "gestures": {
    "check": [...],
    "date_push": [...],
    "delete_proposal": [...]
  },
  "sync_gap_alerts": [...],
  "registry_writes": [...],
  "projection_writes": [...]
}
```

Commit and push:
```bash
git add "$STATE_DIR/reconcile-log" && \
git commit -m "reconcile: google-tasks sync $(date -u +%Y-%m-%d)" && \
(git push origin main || (git pull --rebase --autostash origin main && git push origin main))
```

Print the reconcile report:
```
## Reconcile: google-tasks

Matched:        N of M projection items to registry issues
Personal items: N items skipped — no [#NN] key; out of scope for registry sync
Synced:         N items updated in projection (new/closed)

Gestures processed:
  check (completion endorsements): N
    → N human endorsements → closed done
    → N agent completions → pending-verification set
  date-push (defer signals): N (no registry writes — logged as evidence)
  delete (soft-skip proposals): N (registry items survive — confirm to action)

Sync-gap alerts (keyed items whose [#NN] number does not resolve in registry):
  - "[#NN] <title>" — issue #NN not found; check if deleted or number is wrong

Soft-skip proposals (awaiting confirmation):
  - #NN <title> — deleted from projection; confirm to close or ignore

Evidence log: $STATE_DIR/reconcile-log/google-tasks-YYYY-MM-DD.json
```

If there are sync-gap alerts (keyed but unresolvable) or soft-skip proposals, ask the user if they want to take action on them now. Personal items are never surfaced for action.
