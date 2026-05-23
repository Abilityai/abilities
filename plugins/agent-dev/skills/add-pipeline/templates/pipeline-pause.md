---
name: pipeline-pause
description: Pause a pipeline instance — heartbeat will skip it until /pipeline-resume runs. Use during maintenance or external troubleshooting.
argument-hint: "<pipeline-slug> <instance-slug>"
allowed-tools: Bash, Read, Edit
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
  source: agent-dev:add-pipeline
---

# Pipeline Pause

Set `state.status = "paused"`. The heartbeat treats paused instances as `wait` regardless of stage state.

## Process

### Step 1: Parse arguments

Require `<pipeline-slug> <instance-slug>`. Validate that the state file exists.

### Step 2: Update state

```bash
STATE_FILE="projects/$PIPELINE_SLUG/instances/$INSTANCE_SLUG/state.json"
jq '.status = "paused" | .paused_at = "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"' \
  "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

# Sync to ~/.trinity/
mkdir -p "$HOME/.trinity/pipeline-state/$PIPELINE_SLUG"
cp "$STATE_FILE" "$HOME/.trinity/pipeline-state/$PIPELINE_SLUG/$INSTANCE_SLUG.json"
```

### Step 3: Confirm

`Paused $PIPELINE_SLUG/$INSTANCE_SLUG. Heartbeat will skip this instance. Run /pipeline-resume $PIPELINE_SLUG $INSTANCE_SLUG when ready.`

## Audit trail

Append `{ ts, action: "pause", reason: "<user-supplied or blank>" }` to `instances/<instance>/stage-logs/operator-$(date +%Y-%m-%d).json`.
