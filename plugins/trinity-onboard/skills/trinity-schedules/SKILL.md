---
name: trinity-schedules
description: |
  Manage scheduled tasks on remote Trinity platform via MCP. Track which skills/procedures are scheduled,
  view execution status, sync local tracking with remote state, and present a unified view of what's
  running, what's scheduled, and what's completed. Use when the user asks about schedules, wants to
  schedule a skill/procedure, check execution status, or review autonomous operations.
argument-hint: "[status|sync|list|schedule|trigger|history] [skill-name]"
disable-model-invocation: false
metadata:
  version: "1.1"
  created: 2025-02-05
  author: eugene
  changelog:
    - "1.1: Genericized for any agent via dynamic name detection"
    - "1.0: Initial version"
---

# Schedule Manager

Manage and track scheduled autonomous executions on the remote Trinity platform. This skill bridges
local skill/procedure definitions with remote scheduled executions, maintaining a registry that
associates schedules with their corresponding skills.

## Agent Name Detection

This skill automatically detects the agent name using these methods (in order):

1. **template.yaml** (preferred):
   ```bash
   grep "^name:" template.yaml 2>/dev/null | cut -d: -f2 | tr -d ' '
   ```

2. **Directory name** (fallback):
   ```bash
   basename "$(pwd)"
   ```

3. **Environment variable** (override):
   ```bash
   echo "$TRINITY_AGENT_NAME"
   ```

## Core Concepts

### Schedule Registry

A local JSON file (`~/.schedule-registry.json`) tracks the relationship between:
- **Schedules**: Remote Trinity schedules (cron-based automation)
- **Skills/Procedures**: Local skill definitions that the schedules execute
- **Execution State**: Last known status, results, and timing

### Trinity MCP Tools Available

The Trinity MCP server provides these schedule management tools:
- `list_agent_schedules` - List all schedules for this agent
- `get_agent_schedule` - Get details of a specific schedule
- `create_agent_schedule` - Create a new schedule
- `update_agent_schedule` - Modify an existing schedule
- `delete_agent_schedule` - Remove a schedule
- `toggle_agent_schedule` - Enable/disable a schedule
- `trigger_agent_schedule` - Manually trigger execution now
- `get_schedule_executions` - Get execution history

## Commands

### `/trinity-schedules status`

Show the current state of all schedules:
1. Call `list_agent_schedules` for this agent
2. Load local registry from `~/.schedule-registry.json`
3. Present a unified view showing:
   - Schedule name and associated skill/procedure
   - Enabled/disabled state
   - Cron expression (human-readable)
   - Next scheduled run time
   - Last execution: status, time, duration, cost
   - Whether local registry is in sync with remote

**Output Format:**
```
=== Schedule Status Report ===

ACTIVE SCHEDULES (Enabled)
--------------------------
1. Daily Report (skill: procedure-daily-report)
   Cron: 0 9 * * * (Daily at 9:00 AM)
   Next: 2026-02-06 09:00:00 UTC
   Last: SUCCESS - 2026-02-05 09:00:12 (45s, $0.12)

2. Weekly Analysis (skill: procedure-weekly-analysis)
   Cron: 0 8 * * 1 (Every Monday at 8:00 AM)
   Next: 2026-02-10 08:00:00 UTC
   Last: SUCCESS - 2026-02-03 08:02:34 (2m 15s, $0.45)

PAUSED SCHEDULES (Disabled)
---------------------------
3. Hourly Check (skill: procedure-hourly-check)
   Cron: 0 * * * * (Every hour)
   Last: FAILED - 2026-02-04 14:00:05 (error: timeout)

UNTRACKED SCHEDULES (Not in local registry)
-------------------------------------------
4. Unknown Schedule (id: abc123)
   Cron: */30 * * * *
   Use `/trinity-schedules link abc123 <skill-name>` to associate

RUNNING NOW
-----------
- procedure-daily-report: Started 2026-02-05 15:32:00 (running 45s)

Registry: 3/4 schedules tracked | Last sync: 2026-02-05 15:00:00
```

### `/trinity-schedules sync`

Synchronize local registry with remote Trinity state:
1. Fetch all schedules from remote: `list_agent_schedules`
2. Fetch recent executions: `get_schedule_executions`
3. Update local registry with current state
4. Report any discrepancies (schedules deleted remotely, etc.)
5. Save updated registry to `~/.schedule-registry.json`

### `/trinity-schedules list`

Quick list of all schedules with minimal details:
```
ID          | Name               | Skill                    | Status  | Next Run
------------|--------------------|--------------------------|---------|-----------------
abc123      | Daily Report       | procedure-daily-report   | enabled | 2026-02-06 09:00
def456      | Weekly Analysis    | procedure-weekly-analysis| enabled | 2026-02-10 08:00
ghi789      | Hourly Check       | procedure-hourly-check   | paused  | -
```

### `/trinity-schedules schedule <skill-name> [cron] [name]`

Create or update a schedule for a skill/procedure:

1. **Verify skill exists** - Check `.claude/skills/<skill-name>/SKILL.md` exists
2. **Read skill description** - Extract purpose from skill file
3. **Determine schedule message** - Format as: "Execute skill: <skill-name>"
4. **Create/update schedule**:
   - If schedule for this skill exists: ask to update or create new
   - If new: call `create_agent_schedule`
5. **Update local registry** with schedule-skill association
6. **Confirm** with next run time

**Arguments:**
- `skill-name`: Name of the skill/procedure to schedule (required)
- `cron`: Cron expression (optional, will prompt if not provided)
- `name`: Human-readable schedule name (optional, defaults to skill name)

**Example Usage:**
```
/trinity-schedules schedule procedure-daily-report "0 9 * * *" "Daily Report"
```

**Interactive Flow (if cron not provided):**
```
Scheduling skill: procedure-daily-report
Description: Generate daily status report and save to reports/

Select frequency:
1. Every hour (0 * * * *)
2. Daily at 9 AM (0 9 * * *)
3. Weekdays at 9 AM (0 9 * * 1-5)
4. Weekly on Monday (0 8 * * 1)
5. Custom cron expression

Choice or cron: _
```

### `/trinity-schedules trigger <skill-name-or-schedule-id>`

Manually trigger immediate execution:
1. Look up schedule ID from registry (by skill name) or use ID directly
2. Call `trigger_agent_schedule`
3. Report execution started
4. Optionally wait and report completion status

### `/trinity-schedules history [skill-name] [--limit N]`

Show execution history:
1. Call `get_schedule_executions` with optional limit
2. Filter by skill if specified (using registry mapping)
3. Present timeline of executions:

```
=== Execution History: procedure-daily-report ===

Date/Time           | Status  | Duration | Cost   | Triggered By
--------------------|---------|----------|--------|-------------
2026-02-05 09:00:12 | SUCCESS | 45s      | $0.12  | schedule
2026-02-04 09:00:08 | SUCCESS | 52s      | $0.14  | schedule
2026-02-03 15:30:00 | SUCCESS | 38s      | $0.10  | manual
2026-02-03 09:00:15 | FAILED  | 120s     | $0.08  | schedule
                    | Error: Context window exceeded

Total: 4 executions | Success: 75% | Avg Duration: 64s | Total Cost: $0.44
```

### `/trinity-schedules pause <skill-name-or-schedule-id>`

Disable a schedule:
1. Look up schedule ID from registry
2. Call `toggle_agent_schedule` with `enabled: false`
3. Update local registry
4. Confirm paused state

### `/trinity-schedules resume <skill-name-or-schedule-id>`

Enable a paused schedule:
1. Look up schedule ID from registry
2. Call `toggle_agent_schedule` with `enabled: true`
3. Update local registry
4. Report next scheduled run time

### `/trinity-schedules link <schedule-id> <skill-name>`

Associate an untracked schedule with a skill:
1. Verify schedule exists remotely
2. Verify skill exists locally
3. Add mapping to local registry
4. Confirm association

### `/trinity-schedules unlink <skill-name-or-schedule-id>`

Remove schedule-skill association from local registry (does not delete remote schedule):
1. Remove from local registry only
2. Note: schedule continues to run, just not tracked locally

### `/trinity-schedules delete <skill-name-or-schedule-id>`

Permanently delete a schedule:
1. Confirm deletion with user
2. Call `delete_agent_schedule`
3. Remove from local registry
4. Confirm deletion

## Registry File Format

Location: `~/.schedule-registry.json`

```json
{
  "version": "1.0",
  "agent_name": "my-agent",
  "last_sync": "2026-02-05T15:00:00Z",
  "schedules": {
    "abc123": {
      "schedule_id": "abc123",
      "skill_name": "procedure-daily-report",
      "schedule_name": "Daily Report",
      "cron_expression": "0 9 * * *",
      "timezone": "UTC",
      "enabled": true,
      "created_at": "2026-01-15T10:00:00Z",
      "last_execution": {
        "id": "exec-xyz",
        "status": "completed",
        "started_at": "2026-02-05T09:00:00Z",
        "completed_at": "2026-02-05T09:00:45Z",
        "duration_ms": 45000,
        "cost": 0.12,
        "triggered_by": "schedule"
      }
    }
  },
  "skill_to_schedule": {
    "procedure-daily-report": "abc123",
    "procedure-weekly-analysis": "def456"
  }
}
```

## Automatic Behavior

When this skill is loaded:
1. Check if registry file exists; if not, suggest running `/trinity-schedules sync`
2. If registry exists and is stale (>1 hour), suggest refreshing
3. Always check for running executions when showing status

## Error Handling

- **Network errors**: Report and suggest retry
- **Permission denied**: Explain agent access control limitations
- **Schedule not found**: Suggest sync to refresh local registry
- **Skill not found**: List available skills with `ls .claude/skills/`

## Cron Expression Reference

Common patterns for user convenience:
- `* * * * *` - Every minute
- `*/15 * * * *` - Every 15 minutes
- `0 * * * *` - Every hour (at minute 0)
- `0 9 * * *` - Daily at 9:00 AM
- `0 9 * * 1-5` - Weekdays at 9:00 AM
- `0 9 * * 1` - Weekly on Monday at 9:00 AM
- `0 0 1 * *` - Monthly on the 1st at midnight
- `0 9,17 * * *` - Daily at 9 AM and 5 PM

Format: `minute hour day-of-month month day-of-week`

## Integration Notes

### Running Execution Detection

To check if a schedule is currently running:
1. Call `get_schedule_executions` with `limit: 1`
2. Check if last execution has `completed_at: null` or `status: running`

### Skill Discovery

Find available skills to schedule:
```bash
ls -la ~/.claude/skills/
ls -la .claude/skills/
```

Procedure-type skills (prefixed with `procedure-`) are ideal candidates for scheduling
as they contain step-by-step instructions meant for autonomous execution.
