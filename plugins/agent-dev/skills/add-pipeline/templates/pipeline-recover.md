---
name: pipeline-recover
description: Manually recover a stuck pipeline instance — clears open escalations, resets stage attempt counter, optionally rewinds to an earlier stage, then triggers the next heartbeat.
argument-hint: "<pipeline-slug> <instance-slug> [--from-stage <stage-id>]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
  source: agent-dev:add-pipeline
---

# Pipeline Recover

Operator-driven recovery. The heartbeat is conservative — when it escalates, it refuses to retry the same stage repeatedly. This skill is the human's override.

## Process

### Step 1: Parse arguments

Expect two positional args: `<pipeline-slug> <instance-slug>`. Optional `--from-stage <stage-id>` to rewind.

If missing, prompt for them. Validate that `projects/<pipeline-slug>/instances/<instance-slug>/state.json` exists.

### Step 2: Show current state

Read `state.json`. Show:
- Current stage and status
- Open escalations (with queue ids and reasons)
- Last error from the failing stage's log

Ask the user to confirm before mutating state.

### Step 3: Determine recovery action

Use AskUserQuestion:

- **Retry current stage** — clear attempt counter, set status=`running`, leave current_stage alone
- **Rewind to earlier stage** — set `current_stage = <from-stage>`, clear that stage's status; subsequent stages' history kept for reference
- **Resume from idle** — set status=`idle`, current_stage=`null`; next heartbeat starts a fresh cycle

If `--from-stage` was passed, default to "Rewind". Otherwise default to "Retry current stage".

### Step 4: Resolve escalations

For each entry in `state.open_escalations[]`:

```bash
REQUEST_ID=<request_id>
# Resolve via Trinity MCP respond_to_operator_queue if available (find the item
# with list_operator_queue and match request_id), else just clear locally
```

Clear the array: `state.open_escalations = []`.

### Step 5: Apply the recovery

Update `state.json` atomically:
- Retry: `status = "running"`, `stage_attempt = 0`, `stages[current].consecutive_failures = 0`, `blockers = []`.
- Rewind: `current_stage = <from-stage>`, `stage_entered_at = now`, `stage_attempt = 0`, `stages[<from-stage>].last_status = null`.
- Resume from idle: `status = "idle"`, `current_stage = null`, `stage_attempt = 0`, `blockers = []`.

Sync to `~/.trinity/pipeline-state/<pipeline>/<instance>.json`.

### Step 6: Trigger next heartbeat

Invoke the `pipeline-tick` skill once explicitly so the user sees the immediate effect:

```
/pipeline-tick
```

Show the resulting state. Confirm: "Recovery applied. Heartbeat will re-evaluate on the next scheduled tick (`*/15 * * * *`)."

## Audit trail

Append to `instances/<instance>/stage-logs/recover-$(date +%Y-%m-%d).json`:

```json
{ "ts": "<now>", "action": "recover", "mode": "retry|rewind|idle", "from_stage": "...", "to_stage": "...", "cleared_escalations": [...] }
```
