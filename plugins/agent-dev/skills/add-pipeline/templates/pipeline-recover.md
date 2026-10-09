---
name: pipeline-recover
description: Manually recover a stuck pipeline instance — clears open escalations, resets stage attempt counter, optionally rewinds to an earlier stage, then triggers the next heartbeat.
argument-hint: "<pipeline-slug> <instance-slug> [--from-stage <stage-id>]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Skill, mcp__trinity__get_my_ask
user-invocable: true
metadata:
  version: "1.2"
  author: agent-dev
  source: agent-dev:add-pipeline
  changelog:
    - "1.2: Platform-truth refresh (Trinity dev ed5904906, 1.0.0-aws.2) — asks can end dismissed — recorded alongside answered / cancelled / expired, never proceeded on or re-filed straight away"
    - "1.1: Escalations are not self-resolved — only a person ends an ask (Trinity ent#611: respond_to_operator_queue refuses agent keys with 403 person_required). Recovery reads each one with get_my_ask, records its disposition, and hands a still-pending one to the operator."
    - "1.0: Initial version — clear escalations, reset attempts, optional rewind, trigger the next heartbeat"
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

Read it with `mcp__trinity__get_my_ask(request_id)` when the tool is available and record the disposition (`answered` / `cancelled` / `dismissed` / `expired`) in the recovery note — `dismissed` = the person chose not to answer: do not proceed on it, do not re-file straight away. An ask still `pending` is the operator's to close: tell them to answer or cancel it in the Operating Room. Never call `respond_to_operator_queue` — only a person ends an ask, and an agent key gets `403 person_required`. Without Trinity, just clear locally.

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
