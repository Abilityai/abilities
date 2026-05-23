---
name: pipeline-resume
description: Resume a paused pipeline instance — sets state.status back to running or idle depending on where it was paused. Heartbeat will re-evaluate on the next tick.
argument-hint: "<pipeline-slug> <instance-slug>"
allowed-tools: Bash, Read, Edit, Skill
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
  source: agent-dev:add-pipeline
---

# Pipeline Resume

Undo `/pipeline-pause`. Restores the prior status (or `idle` if unknown).

## Process

### Step 1: Parse arguments

Require `<pipeline-slug> <instance-slug>`. Validate the state file exists and `status == "paused"`. If not paused, warn and exit.

### Step 2: Determine resume target

If `current_stage` is non-null and that stage's `last_status == "in_progress"`: restore to `running`. Otherwise restore to `idle` (next heartbeat starts a cycle).

### Step 3: Update state

```bash
STATE_FILE="projects/$PIPELINE_SLUG/instances/$INSTANCE_SLUG/state.json"
jq --arg new_status "$NEW_STATUS" \
  '.status = $new_status | del(.paused_at)' \
  "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
cp "$STATE_FILE" "$HOME/.trinity/pipeline-state/$PIPELINE_SLUG/$INSTANCE_SLUG.json"
```

### Step 4: Optionally tick

Ask: "Run /pipeline-tick now to advance immediately?" If yes, invoke `pipeline-tick`.

### Step 5: Confirm

`Resumed $PIPELINE_SLUG/$INSTANCE_SLUG (status=$NEW_STATUS). Next heartbeat tick will evaluate.`

## Audit trail

Append `{ ts, action: "resume", new_status }` to `instances/<instance>/stage-logs/operator-$(date +%Y-%m-%d).json`.
