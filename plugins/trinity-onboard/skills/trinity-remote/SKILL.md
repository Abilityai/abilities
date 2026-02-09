---
name: trinity-remote
description: Remote agent operations - execute prompts, deploy-run workflows, and manage notifications for Trinity agents.
argument-hint: "[exec <prompt>|run <prompt>|notify <config>|status]"
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__chat_with_agent, mcp__trinity__get_agent, mcp__trinity__start_agent
metadata:
  version: "1.1"
  created: 2025-02-05
  author: eugene
  changelog:
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
