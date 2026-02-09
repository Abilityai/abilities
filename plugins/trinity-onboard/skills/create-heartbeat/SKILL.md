---
name: create-heartbeat
description: Create a scheduled task skill that monitors a remote agent and runs work at regular intervals. Generates a customized heartbeat SKILL.md from a template.
disable-model-invocation: false
user-invocable: true
argument-hint: "[skill-name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - AskUserQuestion
  - mcp__trinity__list_agents
  - mcp__trinity__get_agent
---

# Create Heartbeat Skill

Generate a scheduled task skill that monitors a remote Trinity agent and performs work at regular intervals. The generated skill follows the heartbeat pattern: poll → check status → act → schedule next.

## What This Creates

A new skill in `.claude/skills/{name}/SKILL.md` that:

- Monitors a remote agent on Trinity at configurable intervals
- Checks if work is needed and kicks it off if idle
- Tracks progress and estimates completion
- Stops automatically when complete or after repeated failures
- Logs all activity for observability

---

## STEP 1: Gather Information

If skill name not provided as argument, ask:

```
What should this scheduled task be called?
Examples: "production-monitor", "daily-sync", "batch-processor"
```

Then gather the following via AskUserQuestion or conversation:

### Required Information

| Field | Question | Example |
|-------|----------|---------|
| `skill_name` | Name for the skill (kebab-case) | `production-monitor` |
| `agent_name` | Which Trinity agent to monitor? | `storypipe` |
| `task_message` | What task to send when idle? | `/video-produce phi-noir --continue 10` |
| `status_query` | How to check current status? | `Run media_index.py status {book}` |
| `completion_check` | How do we know it's done? | `current_scenes >= 150` |
| `interval_minutes` | Check interval (default: 20) | `20` |

### Optional Information

| Field | Question | Default |
|-------|----------|---------|
| `completion_action` | What to do when complete? | Report completion |
| `max_errors` | Consecutive errors before halt | `2` |
| `state_file` | Where to track progress | `{skill_name}_log.md` |

---

## STEP 2: List Available Agents

Help user pick an agent:

```
mcp__trinity__list_agents()
```

Show running agents as options.

---

## STEP 3: Generate the Skill

Create `.claude/skills/{skill_name}/SKILL.md` using this template:

```markdown
---
name: {skill_name}
description: {description}
user-invocable: true
disable-model-invocation: true
argument-hint: "[interval-minutes]"
---

# {Skill Display Name}

{Brief description of what this heartbeat monitors and does.}

## Dependencies

- **Uses MCP**: trinity (for remote agent communication)
- **Requires agent**: {agent_name} running on Trinity

## Usage

```
/{skill_name}           # Default {interval_minutes} min interval
/{skill_name} 10        # Check every 10 minutes
```

---

## State Tracking

Track across heartbeats in `{state_file}`:

```yaml
last_check: 2026-02-08T13:15:00
last_status: "{status_description}"
consecutive_errors: 0
phase: "running"  # running | complete | error
```

---

## STEP 1: Check Remote Agent Status

```
mcp__trinity__get_agent(name: "{agent_name}")
```

**If not running:**
```
mcp__trinity__start_agent(name: "{agent_name}")
# Wait 10 seconds for startup
```

**If start fails:** Increment `consecutive_errors`. If >= {max_errors}, STOP and report.

---

## STEP 2: Query Status

```
mcp__trinity__chat_with_agent(
  agent_name: "{agent_name}",
  message: "{status_query}

Be brief. Report current state."
)
```

Parse response to determine:
- `is_active`: Is work currently running?
- `is_complete`: {completion_check}
- `current_status`: Summary for logging

---

## STEP 3: Decision Logic

```
if is_complete:
    → PHASE: COMPLETE (go to Step 4a)

elif is_active:
    → Report "RUNNING", set timer

elif consecutive_errors >= {max_errors}:
    → STOP: Report error, do NOT set timer

else:
    → Start work (Step 4b)
```

---

## STEP 4a: Completion

When complete:

```
## {Skill Display Name} COMPLETE!

**Status:** {completion_description}
**Total checks:** {count}

{completion_action}
```

Set `phase: "complete"` and stop the heartbeat loop.

---

## STEP 4b: Start Work if Idle

```
mcp__trinity__chat_with_agent(
  agent_name: "{agent_name}",
  message: "{task_message}",
  parallel: true,
  async: true,
  timeout_seconds: 600
)
```

**On success:** Reset `consecutive_errors = 0`
**On failure:** Increment `consecutive_errors`

---

## STEP 5: Error Handling

**If `consecutive_errors >= {max_errors}`:**

```
## TASK HALTED

**Error:** Remote agent failed {max_errors} consecutive times
**Last status:** {current_status}

Action required: Check agent logs manually.

mcp__trinity__get_agent_logs(agent_name: "{agent_name}", lines: 100)
```

**DO NOT** attempt automatic recovery. Report and stop.

---

## STEP 6: Log Status

Append to `{state_file}`:

```bash
echo "$(date '+%Y-%m-%d %H:%M') | {status_summary} | {action}" >> {state_file}
```

Actions: `STARTED`, `RUNNING`, `COMPLETE`, `ERROR`

---

## STEP 7: Set Next Timer

**Only if not complete and no fatal errors:**

```bash
PERIOD=${1:-{interval_minutes}}
sleep $((PERIOD * 60)) && echo "HEARTBEAT: {skill_name} check"
```

Run with `run_in_background: true`.

---

## Stopping the Loop

**Automatic stop:**
- Task complete
- {max_errors}+ consecutive errors

**Manual stop:**
- Don't respond to "HEARTBEAT:" prompt
- Or say "stop"
```

---

## STEP 4: Confirm and Write

Show the user a preview of what will be created:

```
## Heartbeat Skill Preview

**Skill name:** {skill_name}
**Location:** .claude/skills/{skill_name}/SKILL.md
**Monitors:** {agent_name} on Trinity
**Task:** {task_message}
**Interval:** {interval_minutes} minutes
**Stops when:** {completion_check}

Create this skill? [Y/n]
```

On confirmation, write the file.

---

## STEP 5: Completion Report

```
## Heartbeat Skill Created!

**Skill:** /{skill_name}
**Location:** .claude/skills/{skill_name}/SKILL.md

### Usage

Start monitoring:
```
/{skill_name}           # Check every {interval_minutes} minutes
/{skill_name} 5         # Check every 5 minutes
```

Stop monitoring:
- Don't respond to "HEARTBEAT:" prompts
- Or say "stop"

### Customization

Edit `.claude/skills/{skill_name}/SKILL.md` to:
- Change status queries
- Modify completion criteria
- Add custom actions
- Adjust error thresholds

### How It Works

The heartbeat pattern:
1. Check if remote agent is running
2. Query current status
3. If idle and work remains → start task
4. If complete → report and stop
5. If error threshold reached → halt
6. Otherwise → schedule next check

This runs in YOUR local Claude Code session. You control it by
responding (or not) to "HEARTBEAT:" prompts.
```

---

## Examples

### Example 1: Video Production Monitor

```
/create-heartbeat production-monitor

Agent: storypipe
Task: /video-produce phi-noir --continue 10
Status query: Run media_index.py status phi-noir
Complete when: 150 scenes generated
Interval: 20 minutes
```

### Example 2: Daily Report Generator

```
/create-heartbeat daily-report

Agent: analytics-agent
Task: /generate-report --date today
Status query: Check if today's report exists
Complete when: Report file exists for today
Interval: 60 minutes (checks hourly until done)
```

### Example 3: Batch Data Processor

```
/create-heartbeat batch-processor

Agent: data-pipeline
Task: /process-batch --next 100
Status query: How many items remain in queue?
Complete when: Queue is empty
Interval: 15 minutes
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity-onboard` | Initial agent setup and Trinity adoption |
| `/trinity-remote` | Ad-hoc remote agent operations |
| `/trinity-schedules` | Cron-based scheduling via Trinity platform |
| `/credential-sync` | Sync credentials between local and remote |

**Note:** `/trinity-schedules` uses Trinity's server-side cron scheduler. `/create-heartbeat` creates client-side polling skills that run in your local Claude Code session. Choose based on whether you want server-managed or client-controlled scheduling.

---

## The Heartbeat Pattern

This skill generates skills following the **heartbeat pattern**:

```
Local Claude Code                    Remote Trinity Agent
┌─────────────┐                      ┌─────────────┐
│  Heartbeat  │───status check──────▶│             │
│   Skill     │◀──────response───────│   Agent     │
│             │                      │             │
│  (polling)  │───start task────────▶│  (working)  │
│             │      (async)         │             │
│  sleep...   │                      │             │
│             │───status check──────▶│             │
│  ...        │◀──────complete───────│             │
└─────────────┘                      └─────────────┘
```

**Key principles:**
- Local session = scheduler (no server cron needed)
- Async task dispatch (fire and forget)
- State tracked in local file
- Circuit breaker on repeated failures
- User controls via prompt response
