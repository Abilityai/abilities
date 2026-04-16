# trinity

Connect, deploy, and sync Claude Code agents to the Trinity Deep Agent Orchestration Platform.

## Installation

```
/plugin install trinity@abilityai
```

## Usage

```
/trinity:connect              # One-time: authenticate and configure MCP
/trinity:onboard              # Per-agent: make compatible and deploy
/trinity:sync                 # Ongoing: sync changes between local and remote
```

## Skills

| Skill | Description |
|-------|-------------|
| **connect** | Authenticate with Trinity instance, configure MCP server connection |
| **onboard** | Full onboarding flow — compatibility check, file creation, deploy to remote |
| **sync** | Synchronize local/remote changes, supports multiple remotes |

## User Flow

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
| `mcp__trinity__*` | Schedule and event management tools |

## Migrated Features

The following features from the old `trinity-onboard` plugin are now handled differently:

| Old Skill | New Approach |
|-----------|--------------|
| `trinity-compatibility` | Absorbed into `/trinity:onboard` as Phase 0 |
| `trinity-remote` | Use MCP directly: `mcp__trinity__chat_with_agent` |
| `trinity-schedules` | Use MCP directly: schedule management tools |
| `trinity-events` | Use MCP directly or Trinity dashboard |
| `credential-sync` | Absorbed into `/trinity:onboard` and `/trinity:sync` |
| `create-heartbeat` | Generated during `/trinity:onboard` |
| `create-dashboard-playbook` | Generated during `/trinity:onboard` |
| `create-fork-skill` | Generated during `/trinity:onboard` if requested |
| `request-trinity-access` | Absorbed into `/trinity:connect` |

## Source

This plugin is a simplified version of `trinity-onboard`, reducing 11 skills to 3 core workflows.
