# Trinity Onboard

Complete Trinity platform integration for Claude Code agents. This plugin provides the canonical Trinity skills for adopting, syncing, and operating agents on the Trinity Deep Agent Orchestration Platform.

## Prerequisites

**You need access to a Trinity instance before using this plugin.**

### Option 1: Self-Host (Open Source)

Trinity is open source. Deploy your own instance:

1. Visit: **https://github.com/abilityai/trinity**
2. Follow the installation instructions
3. Generate API keys from your dashboard

### Option 2: Managed by Ability AI

Want us to provision and manage a Trinity instance for you?

**Contact: trinity@ability.ai**

### What You'll Need

| Item | Description |
|------|-------------|
| **Trinity URL** | Your instance URL (e.g., `https://trinity.example.com`) |
| **API Key** | From Trinity dashboard > Settings > API Keys |

You'll be prompted for these when running `/trinity-onboard`.

## How It Works: Local-Remote Pairing

Trinity uses a **paired agent architecture**—the same agent runs both locally and remotely:

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub                               │
│           (Source of Truth for Agent State)                 │
│                                                             │
│    Skills, CLAUDE.md, template.yaml, memory/, scripts/      │
└────────────────────┬────────────────────┬───────────────────┘
                     │                    │
                git push              git pull
                     │                    │
                     ▼                    ▼
┌────────────────────────┐    ┌────────────────────────────┐
│     LOCAL AGENT        │    │      REMOTE AGENT          │
│   (Your Machine)       │    │       (Trinity)            │
│                        │    │                            │
│ • Interactive dev      │    │ • Always-on execution      │
│ • Quick iteration      │    │ • Scheduled tasks          │
│ • Orchestration        │    │ • Background processing    │
└───────────┬────────────┘    └─────────────┬──────────────┘
            │                               │
            └───────── MCP Connection ──────┘
```

**Key concepts:**

- **Same agent, two locations**: Both share identical skills and instructions, synced via Git
- **GitHub as state management**: Your agent's identity (skills, config) lives in Git
- **Local orchestrator**: Your local session can trigger and monitor remote execution
- **Heartbeat pattern**: Local agent polls remote for long-running task status
- **Credentials stay local**: `.env` and `.mcp.json` are gitignored, synced separately

**When to use each:**

| Local | Remote |
|-------|--------|
| Interactive development | Long-running batch jobs |
| Quick testing | Scheduled daily tasks |
| File exploration | Always-on availability |
| Orchestrating agents | Processing while laptop closed |

See the full architecture guide in `/trinity-onboard`.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install trinity-onboard@abilityai
```

## Skills Overview

### Core Trinity Skills (Canonical)

| Skill | Command | Description |
|-------|---------|-------------|
| **trinity-onboard** | `/trinity-onboard` | Convert any agent to Trinity-compatible format |
| **trinity-compatibility** | `/trinity-compatibility` | Read-only audit of agent structure |
| **trinity-sync** | `/trinity-sync` | Git-based synchronization with remote agent |
| **trinity-remote** | `/trinity-remote` | Remote agent operations (exec, run, notify) |
| **trinity-schedules** | `/trinity-schedules` | Manage scheduled autonomous executions |

### Extended Skills (Plugin Extras)

| Skill | Command | Description |
|-------|---------|-------------|
| **credential-sync** | `/credential-sync` | Push/pull credentials between local and remote |
| **create-heartbeat** | `/create-heartbeat` | Generate polling skills for long-running tasks |

## Workflow

```
ADOPT → DEVELOP → SYNC → REMOTE → SCHEDULE
  │        │        │       │        │
  │        │        │       │        └─ /trinity-schedules
  │        │        │       └─ /trinity-remote exec <prompt>
  │        │        └─ /trinity-sync push
  │        └─ Local development
  └─ /trinity-onboard
```

---

## Quick Start

### 1. Check Compatibility

```bash
/trinity-compatibility
```

Produces a read-only audit report showing what's missing.

### 2. Adopt Trinity Methodology

```bash
/trinity-onboard
```

Creates required files:
- `template.yaml` - Agent metadata
- `.gitignore` - Security exclusions
- `.env.example` - Document required variables
- `.mcp.json.template` - MCP config with placeholders

### 3. Sync with Remote

```bash
/trinity-sync status    # Compare local vs remote
/trinity-sync push      # Push local changes to remote
/trinity-sync pull      # Pull remote changes locally
```

### 4. Remote Operations

```bash
/trinity-remote              # Check remote agent status
/trinity-remote exec <task>  # Execute on remote (no sync)
/trinity-remote run <task>   # Sync then execute (deploy-run)
```

### 5. Schedule Autonomous Tasks

```bash
/trinity-schedules status                          # View all schedules
/trinity-schedules schedule my-skill "0 9 * * *"   # Schedule daily at 9am
/trinity-schedules trigger my-skill                # Run now
/trinity-schedules history                         # View execution history
```

---

## Credential Management

For paired local-remote workflows where you develop locally and run on Trinity.

### Push Local Credentials to Remote

```bash
/credential-sync push              # Push .env and .mcp.json
/credential-sync push --files=.env # Push specific files
```

### Encrypted Git Storage

```bash
/credential-sync export    # Create .credentials.enc on remote (safe to commit)
/credential-sync import    # Restore from encrypted backup
```

### Check Status

```bash
/credential-sync status    # Show what credentials exist on remote
```

### Helper Scripts

```bash
# Local encryption/decryption
export CREDENTIAL_ENCRYPTION_KEY=<key-from-trinity>
python skills/credential-sync/scripts/encrypt_credentials.py
python skills/credential-sync/scripts/decrypt_credentials.py
```

---

## Heartbeat Pattern

For long-running or recurring tasks, create custom polling skills.

### Create a Heartbeat Skill

```bash
/create-heartbeat production-monitor
```

You'll be asked:
1. Which Trinity agent to monitor?
2. What task to run when idle?
3. How to check current status?
4. What indicates completion?
5. Check interval (default: 20 min)

### How It Works

```
Local Claude Code                    Remote Trinity Agent
┌─────────────┐                      ┌─────────────┐
│  Heartbeat  │───status check──────▶│             │
│   Skill     │◀──────response───────│   Agent     │
│             │                      │             │
│  (polling)  │───start task────────▶│  (working)  │
│             │      (async)         │             │
│  sleep...   │                      │             │
└─────────────┘                      └─────────────┘
```

The generated skill runs in your local session, polling the remote agent at intervals.

---

## Trinity Requirements Reference

### Required Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent instructions (the "brain") |
| `template.yaml` | Trinity deployment metadata |
| `.mcp.json.template` | MCP config with `${VAR}` placeholders |
| `.env.example` | Document required environment variables |
| `.gitignore` | Security-critical exclusions |

### .gitignore Must Exclude

```gitignore
# Credentials
.mcp.json
.env
*.pem
*.key

# Claude Code internals
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/

# Runtime
content/
session-files/
```

---

## Files in This Plugin

```
skills/
├── trinity-onboard/SKILL.md      # Onboarding workflow
├── trinity-compatibility/SKILL.md # Compatibility audit
├── trinity-sync/SKILL.md         # Git synchronization
├── trinity-remote/SKILL.md       # Remote operations
├── trinity-schedules/            # Schedule management
│   ├── SKILL.md
│   ├── registry-template.json
│   ├── scripts/registry.py
│   └── examples.md
├── credential-sync/              # Credential management
│   ├── SKILL.md
│   └── scripts/
│       ├── encrypt_credentials.py
│       └── decrypt_credentials.py
└── create-heartbeat/SKILL.md     # Heartbeat skill generator
```

## Support

- **Documentation**: See your Trinity instance dashboard
- **Issues**: https://github.com/abilityai/abilities/issues

## License

MIT
