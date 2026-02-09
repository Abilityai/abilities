# Trinity Onboard

Complete Trinity platform integration for Claude Code agents. This plugin provides the canonical Trinity skills for adopting, syncing, and operating agents on the Trinity Deep Agent Orchestration Platform.

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
- Directory structure (`outputs/`, `scripts/`, `memory/`)

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

### Required Directories

| Directory | Commit? | Purpose |
|-----------|---------|---------|
| `.claude/skills/` | Yes | Agent capabilities |
| `.claude/agents/` | Yes | Sub-agent definitions |
| `memory/` | Yes | Persistent state, schedules |
| `scripts/` | Yes | Automation scripts |
| `outputs/` | Yes | Smaller deliverables |
| `content/` | No | Large generated assets |
| `session-files/` | No | Session-specific work |

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

- **Documentation**: https://trinity.abilityai.dev/docs
- **Issues**: https://github.com/abilityai/abilities/issues

## License

MIT
