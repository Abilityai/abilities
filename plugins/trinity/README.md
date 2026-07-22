# trinity

Set up, connect, deploy, and sync Claude Code agents to the Trinity Deep Agent Orchestration Platform.

## Installation

```
/plugin install trinity@abilityai
```

## Usage

```
/trinity:deploy-new-instance  # Set up a Trinity instance + create an ops agent to manage it
/trinity:connect              # One-time: authenticate and configure MCP
/trinity:onboard              # Per-agent: make compatible and deploy
/trinity:sync                 # Ongoing: sync changes between local and remote
/trinity:create-dashboard     # Add dashboard to existing agent
/trinity:loop                 # Run a remote agent in a sequential, bounded loop
```

## Skills

| Skill | Description |
|-------|-------------|
| **deploy-new-instance** | Deploy Trinity on any server (or connect to existing) and scaffold a full ops agent |
| **connect** | Authenticate with Trinity instance, configure MCP server connection |
| **onboard** | Full onboarding flow — compatibility check, file creation, deploy to remote |
| **sync** | Synchronize local/remote changes, supports multiple remotes |
| **create-dashboard** | Generate an `/update-dashboard` skill for existing agents |
| **loop** | Run a remote agent task sequentially — fixed N iterations or until a stop signal, with optional response chaining. The remote counterpart to Claude Code's local `/loop` |

## User Flow

### 0. Deploy Trinity (if you don't have an instance yet)

Run `/trinity:deploy-new-instance` to set up a Trinity instance and create an ops agent:
- Choose cloud (ability.ai) or self-hosted (remote SSH or local Docker)
- For fresh installs: generates secrets, configures `.env`, runs `start.sh`, verifies health
- Handles firewall/security group guidance for AWS, GCP, Hetzner, DigitalOcean
- Scaffolds a complete ops agent with 11 skills: `/status`, `/restart`, `/update`, `/logs`, `/agents`, `/cleanup`, `/diagnose`, `/rebuild-agent`, `/rollback`, `/telemetry`, `/provision`
- Works with any SSH-accessible server — provider-agnostic

### 1. Connect (One-time)

Run `/trinity:connect` to authenticate with your Trinity instance:
- Authenticate via email OTP flow
- Provision MCP API key
- Configure `.mcp.json` in current directory
- Verify connection works

### 2. Onboard (Per-agent)

Run `/trinity:onboard` in any agent directory to deploy:
- Check compatibility with Trinity
- Create required files (template.yaml, .env.example)
- Configure MCP connection
- Deploy to Trinity remote

### 3. Sync (Ongoing)

Run `/trinity:sync` to keep local and remote in sync:
- Push local changes to remote
- Pull remote changes to local
- Supports multiple remotes (production, staging, etc.)

## MCP Tools

Once connected, Trinity MCP tools are available directly:

| Tool | Description |
|------|-------------|
| `mcp__trinity__list_agents` | List all remote agents |
| `mcp__trinity__chat_with_agent` | Send messages to remote agents |
| `mcp__trinity__deploy_local_agent` | Deploy agent to Trinity |
| `mcp__trinity__get_agent` | Get agent details |
| `mcp__trinity__run_agent_loop` | Run an agent task sequentially up to N times (server-side; see `/trinity:loop`) |
| `mcp__trinity__get_loop_status` | Poll a loop's per-run progress |
| `mcp__trinity__stop_loop` | Request a graceful stop of a running loop |
| `mcp__trinity__create_agent_schedule` | Create a cron schedule on an agent (`list_agent_schedules`, `update_agent_schedule`, `toggle_agent_schedule`, `delete_agent_schedule`, `trigger_agent_schedule`, `get_schedule_executions`) |
| `mcp__trinity__report` | Publish a structured result to the agent's **Reports** tab (see *Reporting* below) |

### Schedules are declarative

Don't hand-create schedules ad hoc. Declare an agent's recommended schedules in a `schedules:` block in `template.yaml` (the design source of truth). `/trinity:onboard` and `/trinity:sync` **reconcile** that block onto the instance — creating missing schedules, updating drifted ones, and flagging live schedules that aren't declared. The per-schedule `enabled` flag is the recommended default; turning a schedule on or off on a live agent is the operator's call via `toggle_agent_schedule`.

**Best practice: a schedule should call one playbook and nothing else** — keep the cron prompt to a bare skill invocation (e.g. `/daily-briefing`), with no inline instructions, arguments, or business logic. That logic belongs in the playbook the schedule triggers, so changing what a scheduled run does is always an edit to the playbook, never to the schedule.

### Reporting — what the agent produced

A deployed agent publishes results by calling one MCP tool: **`mcp__trinity__report`**. There's no file-drop convention or polling — the tool resolves *which* agent is reporting from its own agent-scoped key, so an agent can only ever file a report as itself. The card appears on that agent's **Reports** tab and the fleet-wide **Operations → Reports** view in near real time.

| Field | Required | Notes |
|-------|----------|-------|
| `report_type` | ✅ | Namespaced `lower_snake` joined by `.` — `<agent>.<result>`, e.g. `recon.weekly_summary` |
| `title` | ✅ | One line, ≤ 300 chars |
| `payload` | ✅ | Arbitrary JSON, ≤ 256 KB |
| `display_hint` | optional | `table` (`{columns, rows}`) · `kpi` (`{tiles:[{label,value,unit?}]}`) · `markdown` (`{markdown}`) · `timeline` (`{events:[{ts,label,detail}]}`) · omit → raw-JSON viewer |
| `period_start` / `period_end` | optional | ISO-8601, for reports covering a window |

**Reports complement `dashboard.yaml`:** the dashboard is the *current* snapshot (overwritten each refresh); reports are an *append-only history* of what the agent accomplished (rolling — pruned past `agent_reports_retention_days`, default 90 days). The convention `/create-agent` bakes into every generated agent is: **result-producing and scheduled skills end with a guarded `report` call** — guarded so it's skipped silently when the tool is absent (i.e. running locally, off Trinity). Reporting is an upgrade, never a requirement.

### Three execution patterns

Trinity exposes three ways to drive a remote agent:

| Pattern | Tool / skill | Shape |
|---------|--------------|-------|
| Single turn | `mcp__trinity__chat_with_agent` | One request, one response |
| Parallel batch | `mcp__trinity__fan_out` | The same task across many inputs at once |
| **Sequential loop** | **`/trinity:loop`** / `run_agent_loop` | N ordered iterations, optionally chained (`{{previous_response}}`), exits on a cap or a `[[DONE]]` stop signal |

`/trinity:loop` is the **remote** counterpart to Claude Code's built-in `/loop`: same two modes (fixed count vs run-until-a-signal), but the loop body runs server-side, so you fire once and disconnect.

## Long-running jobs cannot live inside a headless run

A **scheduled/headless** execution is a single agent turn, and it cannot host a job longer than the synchronous Bash window (**~10 min** max tool timeout) — a hard platform ceiling, not a tuning problem. Past ~10 min the harness **auto-backgrounds** the job, active waiting is blocked, and **ending the turn reaps every background task and monitor** it spawned (the completion event fires as `killed`, not `completed`; the promised re-invoke never comes). Streaming heartbeat output only silences the 300s no-output stall watchdog — it does nothing about the ~10-min ceiling or the turn-end reaping. The async monitor/re-invoke model works in an **interactive** session (which persists) but **not** headless. So: run a >~10-min job (FAISS/index rebuild, bulk embedding, big migration) as an **OS-level cron/systemd/sidecar** that writes a **done-marker**, and let the scheduled run do only the fast parts — check the marker, verify the artifact actually moved (mtime + count, never the exit code or `business_status`), then run quick follow-ups. `/trinity:onboard` → *Long-running jobs inside a run* documents the full pattern; `/agent-dev:create-playbook` and `/agent-dev:add-pipeline` bake it into generated skills.

## Building multi-agent systems

A *system* is a coordinated group of agents. Declare one as a Trinity **`SystemManifest`** and deploy it in a single shot with the `deploy_system` MCP tool (`list_systems`, `get_system_manifest`, and `restart_system` round out the set). Trinity supplies the substrate — agent-to-agent messaging, shared folders, permissions, cron — but runs **no central DAG engine**: orchestration is owned by the agents themselves.

To make an agent that *discovers*, *composes*, and *drives* such a system, install **`/agent-dev:add-orchestrator`**. It adds `/discover-agents` (scan a repo list — local or `github:Org/repo` — into a system map), `/compose-system` (system map → `SystemManifest` → `deploy_system`), and `/orchestrate` (route work, fan out, or roll a catalog agent out ephemerally). It's the agent-side counterpart to these platform primitives.

## Migrated Features

The following features from the old `trinity-onboard` plugin are now handled differently:

| Old Skill | New Approach |
|-----------|--------------|
| `trinity-compatibility` | Absorbed into `/trinity:onboard` as Phase 0 |
| `trinity-remote` | Use MCP directly: `mcp__trinity__chat_with_agent` |
| `trinity-schedules` | Declare schedules in `template.yaml` (`schedules:`); `/trinity:onboard` and `/trinity:sync` reconcile them onto the instance |
| `trinity-events` | Use MCP directly or Trinity dashboard |
| `credential-sync` | Absorbed into `/trinity:onboard` and `/trinity:sync` |
| `create-heartbeat` | Generated during `/trinity:onboard` |
| `create-dashboard-playbook` | Restored as `/trinity:create-dashboard` |
| `create-fork-skill` | Generated during `/trinity:onboard` if requested |
| `request-trinity-access` | Absorbed into `/trinity:connect` |

## Source

This plugin is a simplified version of `trinity-onboard`, reducing 11 skills to 5 core workflows.
