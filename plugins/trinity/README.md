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

### Schedules are declarative

Don't hand-create schedules ad hoc. Declare an agent's recommended schedules in a `schedules:` block in `template.yaml` (the design source of truth). `/trinity:onboard` and `/trinity:sync` **reconcile** that block onto the instance — creating missing schedules, updating drifted ones, and flagging live schedules that aren't declared. The per-schedule `enabled` flag is the recommended default; turning a schedule on or off on a live agent is the operator's call via `toggle_agent_schedule`.

**Best practice: a schedule should call one playbook and nothing else** — keep the cron prompt to a bare skill invocation (e.g. `/daily-briefing`), with no inline instructions, arguments, or business logic. That logic belongs in the playbook the schedule triggers, so changing what a scheduled run does is always an edit to the playbook, never to the schedule.

### Three execution patterns

Trinity exposes three ways to drive a remote agent:

| Pattern | Tool / skill | Shape |
|---------|--------------|-------|
| Single turn | `mcp__trinity__chat_with_agent` | One request, one response |
| Parallel batch | `mcp__trinity__fan_out` | The same task across many inputs at once |
| **Sequential loop** | **`/trinity:loop`** / `run_agent_loop` | N ordered iterations, optionally chained (`{{previous_response}}`), exits on a cap or a `[[DONE]]` stop signal |

`/trinity:loop` is the **remote** counterpart to Claude Code's built-in `/loop`: same two modes (fixed count vs run-until-a-signal), but the loop body runs server-side, so you fire once and disconnect.

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
