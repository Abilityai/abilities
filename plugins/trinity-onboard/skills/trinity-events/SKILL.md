---
name: trinity-events
description: |
  Manage event subscriptions on the Trinity platform via MCP. Subscribe to events from other agents,
  emit events with structured payloads, and build inter-agent event-driven pipelines. Use when the
  user asks about events, wants to subscribe to another agent's events, emit events, or review
  event history and subscriptions.
argument-hint: "[subscribe|emit|list|history|delete] [agent-name] [event-type]"
disable-model-invocation: false
metadata:
  version: "1.0"
  created: 2026-03-26
  author: eugene
  changelog:
    - "1.0: Initial version — event subscription management"
---

# Event Subscription Manager

Manage inter-agent event-driven pipelines on the Trinity platform. Agents can emit named events
with structured payloads, and other agents can subscribe to receive automated tasks when matching
events fire.

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

### Event-Driven Pipelines

Trinity's event system is a lightweight pub/sub mechanism for inter-agent communication:

```
Agent A                         Trinity                          Agent B
   │                              │                                │
   │  emit_event("task.done",     │                                │
   │    {result: "success"})      │                                │
   │─────────────────────────────>│                                │
   │                              │  match subscriptions           │
   │                              │  interpolate template          │
   │                              │  dispatch task async           │
   │                              │───────────────────────────────>│
   │                              │  "Process result: success"     │
   │  {event_id, triggered: 1}   │                                │
   │<─────────────────────────────│                                │
```

**Key principles:**
- **Fire-and-forget delivery**: Events are dispatched asynchronously — the emitter doesn't wait for subscribers
- **Template interpolation**: Subscription messages use `{{payload.field}}` placeholders filled from the event payload
- **Permission-gated**: Cross-agent subscriptions require the subscriber to have `agent_permissions` for the source agent
- **Self-subscription always allowed**: An agent can always subscribe to its own events

### Event Types

Event types are dot-separated identifiers for namespacing:
- `prediction.resolved`
- `report.generated`
- `data.pipeline.completed`
- `alert.critical`

Format: letters, numbers, underscores, separated by dots. Pattern: `^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$`

### Trinity MCP Tools Available

The Trinity MCP server provides these event management tools:
- `emit_event` — Emit a named event from this agent with an optional JSON payload
- `subscribe_to_event` — Subscribe to events from another agent with a message template
- `list_event_subscriptions` — List subscriptions (as subscriber, source, or both)
- `delete_event_subscription` — Delete a subscription by ID

## Commands

### `/trinity-events subscribe <source-agent> <event-type> <message-template>`

Subscribe to events from another agent:

1. **Verify source agent exists** — The source agent must be a valid Trinity agent
2. **Check permissions** — This agent must have `agent_permissions` for the source agent (unless subscribing to own events)
3. **Create subscription** — Call `subscribe_to_event` with:
   - `source_agent`: The agent emitting events
   - `event_type`: The event type to listen for
   - `target_message`: Message template with `{{payload.field}}` placeholders
4. **Confirm** with subscription ID

**Arguments:**
- `source-agent`: Name of the agent to subscribe to (required)
- `event-type`: Dot-separated event type (required)
- `message-template`: Template with `{{payload.field}}` placeholders (required)

**Example:**
```
/trinity-events subscribe oracle-1 prediction.resolved "New prediction resolved: {{payload.pred_id}} — outcome: {{payload.outcome}}"
```

**Interactive Flow (if arguments not provided):**
```
Subscribe to events from which agent? oracle-1
Event type to listen for? prediction.resolved

Craft a message template. Use {{payload.field}} to reference event data.
Example: "Process {{payload.result}} from {{payload.source}}"

Template: New prediction: {{payload.pred_id}} outcome={{payload.outcome}}

Creating subscription...
  Subscriber: my-agent
  Source: oracle-1
  Event type: prediction.resolved
  Message: New prediction: {{payload.pred_id}} outcome={{payload.outcome}}

Subscription created: esub_abc123
When oracle-1 emits a "prediction.resolved" event, this agent will receive
an automated task with the interpolated message.
```

### `/trinity-events emit <event-type> [payload-json]`

Emit an event from this agent:

1. **Validate event type** — Must match dot-separated format
2. **Parse payload** — Optional JSON object
3. **Emit event** — Call `emit_event` with event_type and optional payload
4. **Report** — Show event ID and number of subscriptions triggered

**Arguments:**
- `event-type`: Dot-separated event type (required)
- `payload-json`: JSON object (optional)

**Example:**
```
/trinity-events emit report.generated {"report_id": "rpt-456", "format": "pdf", "pages": 12}
```

**Output:**
```
Event emitted successfully.
  Event ID: evt_xyz789
  Type: report.generated
  Payload: {"report_id": "rpt-456", "format": "pdf", "pages": 12}
  Subscriptions triggered: 2
```

### `/trinity-events list [direction]`

List event subscriptions:

1. Call `list_event_subscriptions` with direction filter
2. Present subscriptions grouped by direction

**Arguments:**
- `direction`: `subscriber` (default), `source`, or `both`
  - `subscriber` — Events this agent listens for
  - `source` — Events other agents listen for from this agent
  - `both` — All subscriptions involving this agent

**Output Format:**
```
=== Event Subscriptions ===

LISTENING FOR (subscriber)
--------------------------
1. oracle-1 → prediction.resolved
   ID: esub_abc123
   Message: "New prediction: {{payload.pred_id}} outcome={{payload.outcome}}"
   Status: enabled

2. data-pipeline → batch.completed
   ID: esub_def456
   Message: "Batch {{payload.batch_id}} done, {{payload.records}} records processed"
   Status: enabled

OTHERS LISTENING TO YOU (source)
--------------------------------
3. dashboard-agent → report.generated
   ID: esub_ghi789
   Message: "Update dashboard with report {{payload.report_id}}"
   Status: enabled

Summary: 2 incoming subscriptions, 1 outgoing subscription
```

### `/trinity-events history [event-type] [--limit N]`

Show events emitted by this agent:

1. Fetch events via Trinity API
2. Optionally filter by event type
3. Present timeline

**Output Format:**
```
=== Event History ===

Date/Time             | Event Type           | Subscriptions | Payload
----------------------|----------------------|---------------|-----------------
2026-03-26 10:30:12  | prediction.resolved  | 2             | {pred_id: "p-1"}
2026-03-26 09:15:00  | report.generated     | 1             | {report_id: "r-5"}
2026-03-25 18:00:05  | heartbeat            | 0             | {}

Total: 3 events | 3 subscriptions triggered
```

### `/trinity-events delete <subscription-id>`

Delete an event subscription:

1. **Confirm with user** — Show subscription details before deleting
2. Call `delete_event_subscription` with the subscription ID
3. Confirm deletion

**Example:**
```
/trinity-events delete esub_abc123
```

**Interactive Flow:**
```
Subscription to delete:
  ID: esub_abc123
  Source: oracle-1
  Event type: prediction.resolved
  Message: "New prediction: {{payload.pred_id}} outcome={{payload.outcome}}"

Delete this subscription? (yes/no): yes

Subscription esub_abc123 deleted.
You will no longer receive tasks when oracle-1 emits prediction.resolved events.
```

## Common Patterns

### Pipeline Chain

Agent A processes data, Agent B generates reports, Agent C updates dashboards:

```
Agent A emits: data.processed → Agent B subscribes
Agent B emits: report.generated → Agent C subscribes
```

Setup:
```
# On Agent B:
/trinity-events subscribe agent-a data.processed "Generate report from batch {{payload.batch_id}}"

# On Agent C:
/trinity-events subscribe agent-b report.generated "Update dashboard with {{payload.report_id}}"

# On Agent A (when done processing):
/trinity-events emit data.processed {"batch_id": "batch-042", "records": 1500}
```

### Self-Subscription (State Machine)

An agent can subscribe to its own events to implement state transitions:

```
/trinity-events subscribe my-agent phase.completed "Start next phase: {{payload.next_phase}}"
/trinity-events emit phase.completed {"current": "analysis", "next_phase": "generation"}
```

### Combining Events with Schedules

Use `/trinity-schedules` to run a procedure on a cron, and have it emit events for downstream agents:

```
# Schedule a data collection procedure
/trinity-schedules schedule collect-data "0 */6 * * *"

# The collect-data skill emits events when done (built into the skill)
# Another agent subscribes to get notified:
/trinity-events subscribe collector-agent data.collected "Process new data: {{payload.source}}"
```

## Permission Requirements

For cross-agent subscriptions:
- The **subscribing agent** must have permission to communicate with the **source agent**
- Permissions are managed in the Trinity dashboard under the agent's Permissions tab
- Self-subscription (subscribing to your own events) always works without extra permissions

If you get a permission error:
```
Error 403: Agent 'my-agent' does not have permission to communicate with 'oracle-1'.
Grant permission in the Permissions tab first.
```

Go to the Trinity dashboard → Source Agent → Permissions → Add your agent.

## Error Handling

- **Permission denied (403)**: Subscriber needs `agent_permissions` entry for source agent
- **Source agent not found (400)**: Verify the agent name is correct
- **Duplicate subscription (409)**: A subscription for this agent/source/type already exists
- **Invalid event type (400)**: Must be dot-separated alphanumeric identifiers
- **Subscription not found (404)**: The subscription ID doesn't exist or was already deleted

## Integration with Other Skills

| Skill | How it relates to events |
|-------|------------------------|
| `/trinity-remote` | Run tasks that emit events as part of their workflow |
| `/trinity-schedules` | Scheduled procedures can emit events when they complete |
| `/create-heartbeat` | Heartbeat polling can be replaced by event subscriptions for push-based notification |
| `/credential-sync` | Credentials needed for MCP connection that powers event tools |
