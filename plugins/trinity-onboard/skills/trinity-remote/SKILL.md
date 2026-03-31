---
name: trinity-remote
description: Remote agent operations - execute prompts, deploy-run workflows, and manage notifications for Trinity agents.
argument-hint: "[exec <prompt>|run <prompt>|notify <config>|status]"
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__chat_with_agent, mcp__trinity__get_agent, mcp__trinity__start_agent, mcp__trinity__get_agent_info
metadata:
  version: "1.2"
  created: 2025-02-05
  author: eugene
  changelog:
    - "1.2: Added fan-out, async execution polling, and activity summary sections"
    - "1.1: Genericized agent name detection - works with any agent"
    - "1.0: Initial version"
---

# Trinity Remote Operations

Collaborate with remote Trinity agents - execute prompts, sync-and-run, and configure notifications.

## Command Overview

| Command | Description |
|---------|-------------|
| `/trinity-remote` | Show status of remote agent |
| `/trinity-remote exec <prompt>` | Execute prompt on remote (no sync) |
| `/trinity-remote run <prompt>` | Sync local changes, then execute (deploy-run) |
| `/trinity-remote fan-out <prompt> [--tasks N]` | Fan out parallel tasks to self |
| `/trinity-remote activity [hours]` | Show recent execution activity summary |
| `/trinity-remote notify [config]` | Configure notifications |

## Arguments

$ARGUMENTS

---

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

---

## Status Check (default)

When called without arguments, show remote agent status.

### Workflow

1. **Determine agent name** (see detection methods above)

2. **Query remote status**
   ```
   mcp__trinity__list_agents()
   mcp__trinity__get_agent(name: "<agent-name>")
   ```

3. **Display status**
   ```
   ## Remote Agent Status

   | Property | Value |
   |----------|-------|
   | Name | <agent-name> |
   | Status | running |
   | Uptime | 3h 24m |
   | Last activity | 2 minutes ago |
   | Git branch | main |
   | Git HEAD | 1cb2c9a |
   ```

---

## Remote Execution (`exec`)

Execute a prompt on the remote agent without syncing local changes.

**Use when:** You want to run something on the always-on remote version without pushing local work.

### Workflow

1. **Verify remote agent exists and is running**
   ```
   mcp__trinity__list_agents()
   ```
   If not running:
   ```
   mcp__trinity__start_agent(name: "<agent-name>")
   ```

2. **Extract prompt** from arguments (everything after "exec ")

3. **Execute on remote**
   ```
   mcp__trinity__chat_with_agent(
     agent_name: "<agent-name>",
     message: "<the prompt>"
   )
   ```

4. **Return results** directly to user

### Example

```
User: /trinity-remote exec check my calendar for tomorrow

Agent:
→ Remote agent: my-agent
→ Status: running
→ Executing...

[Response from remote agent appears here]
```

---

## Deploy and Run (`run`)

Sync local changes to remote, then execute a task.

**Use when:** You've made local changes (skills, CLAUDE.md, etc.) and want to test them on the remote agent.

### Workflow

1. **Check for uncommitted changes**
   ```bash
   git status --porcelain
   ```

2. **If changes exist, commit and push**
   ```bash
   # Stage skill/policy/procedure changes
   git add .claude/skills/ .claude/agents/ .claude/rules/ CLAUDE.md memory/

   # Commit with auto-message
   git commit -m "[deploy-run] Auto-sync before remote execution"

   # Push to origin
   git push origin $(git branch --show-current)
   ```

3. **Tell remote to pull**
   ```
   mcp__trinity__chat_with_agent(
     agent_name: "<agent-name>",
     message: "Run: git fetch origin && git pull origin main --ff-only"
   )
   ```
   Wait for confirmation.

4. **Execute the task**
   Extract prompt (everything after "run "):
   ```
   mcp__trinity__chat_with_agent(
     agent_name: "<agent-name>",
     message: "<the prompt>"
   )
   ```

5. **Return results with sync summary**
   ```
   ## Deploy-Run Complete

   ### Sync
   - Committed: 3 files
   - Pushed to: origin/main
   - Remote pulled: ✓

   ### Execution
   [Response from remote agent]
   ```

### Example

```
User: /trinity-remote run generate the weekly analytics report

Agent:
→ Local changes detected: 2 files
→ Committing and pushing...
→ Remote pulling...
→ Executing task on remote...

## Weekly Analytics Report
[Full response from remote]
```

---

## Fan-Out Parallel Execution (`fan-out`)

Dispatch N independent tasks to this agent in parallel, collect aggregated results.

**Use when:** You have independent work items (e.g., analyze 5 datasets, process multiple reports) that can run concurrently.

### How It Works

The `fan_out` MCP tool dispatches 1-50 tasks to the agent simultaneously, each in its own fresh context window. Results are collected with per-task status, cost, and duration.

### Workflow

1. **Parse tasks** from the prompt. If `--tasks N` is provided, split the prompt into N tasks. Otherwise, identify natural task boundaries.

2. **Build task list** with unique IDs:
   ```json
   [
     {"id": "task-1", "message": "Analyze Q1 revenue"},
     {"id": "task-2", "message": "Analyze Q2 revenue"},
     {"id": "task-3", "message": "Analyze Q3 revenue"}
   ]
   ```

3. **Execute fan-out via MCP**
   ```
   mcp__trinity__chat_with_agent(
     agent_name: "<agent-name>",
     message: "fan_out",
     tasks: [task array],
     max_concurrency: 3,
     timeout_seconds: 300
   )
   ```

   **Parameters:**
   | Param | Default | Range | Description |
   |-------|---------|-------|-------------|
   | `tasks` | — | 1-50 | Array of `{id, message}` objects |
   | `max_concurrency` | 3 | 1-10 | Max simultaneous tasks |
   | `timeout_seconds` | 600 | 10-3600 | Overall deadline |
   | `model` | (agent default) | — | Optional model override |

4. **Display aggregated results**
   ```
   ## Fan-Out Results

   | Task | Status | Duration | Cost |
   |------|--------|----------|------|
   | task-1 | completed | 8.5s | $0.05 |
   | task-2 | completed | 7.9s | $0.05 |
   | task-3 | completed | 8.2s | $0.05 |

   **Total**: 3/3 completed | $0.15 total cost

   ### task-1: Q1 Revenue
   [response text]

   ### task-2: Q2 Revenue
   [response text]
   ...
   ```

### Constraints

- **Self-only (v1)**: Agent fans out to itself, not to other agents
- **Best-effort policy**: Partial results returned if some tasks fail or timeout
- **Each subtask** gets its own execution record visible in the Trinity dashboard

---

## Async Execution & Polling

For long-running tasks that exceed the MCP timeout (60s), use async execution with polling.

### Workflow

1. **Start async task**
   ```
   mcp__trinity__chat_with_agent(
     agent_name: "<agent-name>",
     message: "<prompt>",
     async: true
   )
   ```
   Returns: `{ status: "accepted", execution_id: "exec-abc123" }`

2. **Poll for results** (repeat until status != "running")
   ```
   mcp__trinity__get_execution_result(
     agent_name: "<agent-name>",
     execution_id: "exec-abc123"
   )
   ```
   Returns status, response, cost, duration, and optionally full transcript with `include_log: true`.

3. **List recent executions** (for overview)
   ```
   mcp__trinity__list_recent_executions(
     agent_name: "<agent-name>",
     limit: 20,
     status: "running"  // optional filter: pending, running, success, failed, cancelled
   )
   ```

**Use when:** Tasks take >60 seconds, or you want fire-and-forget with later result retrieval.

---

## Activity Summary (`activity`)

Show a high-level activity summary for monitoring and health checks.

### Workflow

1. **Parse hours** from arguments (default: 24, max: 168 = 7 days)

2. **Query activity**
   ```
   mcp__trinity__get_agent_activity_summary(
     agent_name: "<agent-name>",
     hours: 24
   )
   ```

3. **Display summary**
   ```
   ## Activity Summary: <agent-name> (Last 24h)

   **Total activities**: 42

   | Trigger Type | Success | Failed | Running |
   |-------------|---------|--------|---------|
   | Chat        | 38      | 2      | 1       |
   | Schedule    | 35      | 1      | 0       |
   | MCP         | 5       | 0      | 0       |

   Tip: Use `/trinity-schedules history` for detailed execution logs.
   ```

   Omit `agent_name` to get fleet-wide summary across all agents (includes `by_agent` breakdown).

---

## Notification Configuration (`notify`)

Configure how to receive notifications from remote executions.

### Sub-commands

| Command | Action |
|---------|--------|
| `/trinity-remote notify` | Show current notification config |
| `/trinity-remote notify status` | Same as above |
| `/trinity-remote notify email <address>` | Set email notification |
| `/trinity-remote notify webhook <url>` | Set webhook notification |
| `/trinity-remote notify disable` | Disable notifications |

### Storage

Store notification config in `memory/trinity_notifications.json`:

```json
{
  "agent_name": "<agent-name>",
  "notifications": {
    "email": "user@example.com",
    "webhook": null,
    "enabled": true
  },
  "subscriptions": [
    {
      "trigger": "schedule_complete",
      "notify": ["email"]
    },
    {
      "trigger": "error",
      "notify": ["email", "webhook"]
    }
  ]
}
```

### Workflow for `notify status`

1. Read `memory/trinity_notifications.json`
2. Display current configuration:

```
## Notification Status

| Setting | Value |
|---------|-------|
| Email | user@example.com |
| Webhook | (not configured) |
| Enabled | ✓ |

### Active Subscriptions
- Schedule completions → Email
- Errors → Email
```

### Workflow for `notify email <address>`

1. Validate email format
2. Update `memory/trinity_notifications.json`
3. Confirm:

```
✓ Email notifications set to: user@example.com

You'll receive notifications for:
- Scheduled task completions
- Execution errors
- Agent status changes
```

### Workflow for `notify webhook <url>`

1. Validate URL format
2. Test webhook with a ping:
   ```bash
   curl -X POST "<url>" -H "Content-Type: application/json" \
     -d '{"type": "test", "agent": "<agent-name>", "message": "Webhook configured"}'
   ```
3. Update config if successful
4. Confirm:

```
✓ Webhook configured: https://your-endpoint.com/notify
✓ Test ping successful

Webhook payload format:
{
  "type": "schedule_complete|error|status_change",
  "agent": "agent-name",
  "task": "task description",
  "result": "success|failure",
  "message": "details...",
  "timestamp": "ISO-8601"
}
```

---

## Quick Reference

| Goal | Command |
|------|---------|
| Check remote status | `/trinity-remote` |
| Run task on remote | `/trinity-remote exec <prompt>` |
| Sync and run | `/trinity-remote run <prompt>` |
| Parallel batch tasks | `/trinity-remote fan-out <prompt> --tasks 5` |
| Recent activity | `/trinity-remote activity 24` |
| Check notifications | `/trinity-remote notify` |
| Set email alerts | `/trinity-remote notify email <addr>` |
| Set webhook | `/trinity-remote notify webhook <url>` |

---

## Error Handling

| Error | Resolution |
|-------|------------|
| Remote agent not found | Run `/trinity-onboard` first to deploy agent |
| Remote agent stopped | This skill will auto-start the agent |
| Git push failed | Check remote permissions, resolve conflicts |
| Webhook test failed | Verify URL is accessible and accepts POST |

---

## Related Skills

- [trinity-onboard](../trinity-onboard/SKILL.md) - Initial agent setup
- [trinity-sync](../trinity-sync/SKILL.md) - Manual git sync operations
- [trinity-schedules](../trinity-schedules/SKILL.md) - Scheduled task management
- [trinity-compatibility](../trinity-compatibility/SKILL.md) - Compatibility audit
