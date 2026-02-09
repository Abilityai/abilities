# Schedule Manager Examples

## Quick Start

### First Time Setup

```
# Initialize the registry
/trinity-schedules sync

# View current state
/trinity-schedules status
```

### Schedule a Procedure

```
# Schedule a daily report at 9 AM
/trinity-schedules schedule procedure-daily-report "0 9 * * *" "Daily Report"

# Schedule weekday-only task
/trinity-schedules schedule procedure-standup-summary "0 8 * * 1-5" "Morning Standup"
```

### Check What's Running

```
# Full status with all details
/trinity-schedules status

# Quick list
/trinity-schedules list
```

### Manage Schedules

```
# Pause a schedule
/trinity-schedules pause procedure-daily-report

# Resume it
/trinity-schedules resume procedure-daily-report

# Run it now (manual trigger)
/trinity-schedules trigger procedure-daily-report
```

---

## Common Workflows

### Workflow 1: Setting Up a New Procedure for Automation

1. Create the procedure skill in `.claude/skills/procedure-my-task/SKILL.md`
2. Test it manually: `/procedure-my-task`
3. Schedule it: `/trinity-schedules schedule procedure-my-task "0 9 * * *"`
4. Verify: `/trinity-schedules status`

### Workflow 2: Debugging Failed Executions

```
# Check recent execution history
/trinity-schedules history procedure-my-task --limit 10

# Get details on specific execution
# (Use MCP tool directly for full logs)
get_schedule_executions agent_name="my-agent" limit=5
```

### Workflow 3: Syncing After Being Away

```
# Sync local registry with remote state
/trinity-schedules sync

# Check what happened while away
/trinity-schedules history --limit 50

# Review current status
/trinity-schedules status
```

### Workflow 4: Handling Untracked Schedules

If `status` shows untracked schedules:

```
# Link existing schedule to a skill
/trinity-schedules link abc123-schedule-id procedure-existing-task

# Or remove if no longer needed
/trinity-schedules delete abc123-schedule-id
```

---

## MCP Tool Examples

These are the raw Trinity MCP tools the skill uses. You can call them directly:

### List All Schedules

```json
{
  "tool": "list_agent_schedules",
  "arguments": {
    "agent_name": "my-agent"
  }
}
```

### Create a Schedule

```json
{
  "tool": "create_agent_schedule",
  "arguments": {
    "agent_name": "my-agent",
    "name": "Daily Report",
    "cron_expression": "0 9 * * *",
    "message": "Execute skill: procedure-daily-report\n\nRun the daily report procedure and save output to reports/",
    "timezone": "America/New_York",
    "enabled": true
  }
}
```

### Get Execution History

```json
{
  "tool": "get_schedule_executions",
  "arguments": {
    "agent_name": "my-agent",
    "schedule_id": "abc123",
    "limit": 20
  }
}
```

### Trigger Immediate Execution

```json
{
  "tool": "trigger_agent_schedule",
  "arguments": {
    "agent_name": "my-agent",
    "schedule_id": "abc123"
  }
}
```

---

## Cron Expression Reference

### Common Patterns

| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `*/5 * * * *` | Every 5 minutes |
| `*/15 * * * *` | Every 15 minutes |
| `0 * * * *` | Every hour (at :00) |
| `0 9 * * *` | Daily at 9:00 AM |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `0 0 1 * *` | Monthly on the 1st at midnight |
| `0 9,17 * * *` | Daily at 9 AM and 5 PM |

### Format

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6, Sunday = 0)
│ │ │ │ │
* * * * *
```

### Special Characters

- `*` - Any value
- `,` - Value list (e.g., `1,3,5`)
- `-` - Range (e.g., `1-5` = Mon-Fri)
- `/` - Step (e.g., `*/15` = every 15)

---

## Registry File Format

Located at `~/.schedule-registry.json`:

```json
{
  "version": "1.0",
  "agent_name": "my-agent",
  "last_sync": "2026-02-05T15:30:00Z",
  "schedules": {
    "sched_abc123": {
      "schedule_id": "sched_abc123",
      "skill_name": "procedure-daily-report",
      "schedule_name": "Daily Report",
      "cron_expression": "0 9 * * *",
      "timezone": "America/New_York",
      "enabled": true,
      "next_run_at": "2026-02-06T14:00:00Z",
      "created_at": "2026-01-15T10:00:00Z",
      "last_execution": {
        "id": "exec_xyz789",
        "status": "completed",
        "started_at": "2026-02-05T14:00:00Z",
        "completed_at": "2026-02-05T14:00:45Z",
        "duration_ms": 45000,
        "cost": 0.12,
        "triggered_by": "schedule"
      }
    }
  },
  "skill_to_schedule": {
    "procedure-daily-report": "sched_abc123"
  }
}
```

---

## Helper Script Usage

The `scripts/registry.py` helper can be used directly:

```bash
# Initialize registry
python ~/.claude/skills/trinity-schedules/scripts/registry.py init my-agent

# Show formatted status
python ~/.claude/skills/trinity-schedules/scripts/registry.py status

# Look up schedule for a skill
python ~/.claude/skills/trinity-schedules/scripts/registry.py lookup procedure-daily-report

# Parse cron expression
python ~/.claude/skills/trinity-schedules/scripts/registry.py cron "0 9 * * 1-5"
# Output: At 9:00 on weekdays

# Link schedule to skill
python ~/.claude/skills/trinity-schedules/scripts/registry.py link sched_abc123 procedure-daily-report
```
