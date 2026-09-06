---
name: project-reconcile
description: Sync projection adapters against the GitHub Issues registry per PROJECT_STANDARD.md. Processes projection gestures (check/date-push/delete) back into the registry with correct reversibility typing. Ships with Google Tasks adapter v1 (notes-field [#NN] key). Other adapters are per-deployment extensions. Reconciler is idempotent; refuses unkeyed items with a sync-gap alert.
argument-hint: "[adapter] — default: google-tasks"
allowed-tools: Bash, Read, Write, AskUserQuestion
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-30
  author: add-project-management
  changelog:
    - "1.1: Read-the-standard guard (missing PROJECT_STANDARD.md → run /project-init first); skill is now authored standalone (installer copies from here)"
    - "1.0: Initial version — generic adapter contract, Google Tasks adapter v1 with gesture typing, idempotent reconciler, sync-gap alerts for unkeyed items"
---

# Project Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — e.g. `project-reconcile v1.0 — recent: Initial version`. Then proceed.

## Purpose

Sync projection surfaces (personal task views, team tools) against the GitHub Issues registry. The registry is write-authoritative; projections are read-only displays with one-directional gesture processing.

**Key rules (Invariant 5):**
- Projections display state; they do not own it.
- `[#NN]` prefix in the projection item title is the join key — unkeyed items cannot be synced.
- Gestures are typed by reversibility: check (completion endorsement), date-push (defer signal, no registry write), delete (soft-skip proposal, registry item survives).
- Absence is never authoritative.

## Adapters

This skill ships with the **Google Tasks adapter v1**. Other adapters (Fibery, Notion, Linear, etc.) follow the adapter contract in `PROJECT_STANDARD.md §11` and are per-deployment extensions — copy this skill, implement the three adapter methods, and register your adapter in the dispatch block below.

## Process

### Step 1: Read the standard

Read `PROJECT_STANDARD.md`. **If it is missing, stop and run `/project-init` first** — it materializes the standard from its shipped template; every project skill reads that file as its configuration. Resolve `$REGISTRY`, `$AGENT_NAME`, and `$PV_MAX_AGE`.

### Step 2: Select adapter

If `$ARGUMENTS` names an adapter (`google-tasks`, `fibery`, etc.), use it.

Otherwise ask:
- **Header:** "Projection adapter"
- **Options:** "google-tasks" (built-in) or a custom adapter name (per PROJECT_STANDARD.md §11)

### Step 3: Load registry state

Fetch all open task issues from the registry:
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

Extract the `[#NN]` key from the title using: `echo "$TITLE" | grep -oP '(?<=\[#)\d+(?=\])'`

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

Read the last sync log (`project-steward/reconcile-log/google-tasks-YYYY-MM-DD.json` or the most recent) to detect deletions.

### Step 6: Apply registry updates (per gesture type)

**Check (completion endorsement):**
```bash
OWNER=$(gh issue view $NUMBER --repo "$REGISTRY" --json labels -q '.labels[].name | select(startswith("owner:"))' | head -1 | sed 's/owner://')
```

- If owner is a human (not in the agent list): this is a human endorsement → close the issue directly:
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection endorsement $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks by $OWNER. Closing as done per PROJECT_STANDARD.md §11 (human completion = direct done)."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "status:active" --add-label "status:done"
  gh issue close $NUMBER --repo "$REGISTRY" --reason completed
  ```
- If owner is an agent: set pending-verification:
  ```bash
  gh issue comment $NUMBER --repo "$REGISTRY" \
    --body "### Done claim — projection signal $(date -u +%Y-%m-%d)\nMarked complete in Google Tasks. Setting pending-verification for steward to verify against Definition of Done."
  gh issue edit $NUMBER --repo "$REGISTRY" --remove-label "status:active" --add-label "status:pending-verification"
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
  - Title: `[#NN] <issue title>`
  - Priority prefix: `[P1] ` / `[P2] ` / `[P3] ` based on the issue's priority label (read-only display)
  - Note: the GitHub issue URL

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

Write `project-steward/reconcile-log/google-tasks-$(date -u +%Y-%m-%d).json`:
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
git add project-steward/reconcile-log && \
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

Evidence log: project-steward/reconcile-log/google-tasks-YYYY-MM-DD.json
```

If there are sync-gap alerts (keyed but unresolvable) or soft-skip proposals, ask the user if they want to take action on them now. Personal items are never surfaced for action.
