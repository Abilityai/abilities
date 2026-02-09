# Trinity Onboard

Zero-friction onboarding to deploy any Claude Code agent to the Trinity Deep Agent Orchestration Platform, plus credential synchronization for paired local-remote agent workflows.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install trinity-onboard@abilityai
```

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **onboard** | `/onboard` | Deploy agent to Trinity platform |
| **credential-sync** | `/credential-sync` | Sync credentials between local and remote |

## Usage

### Deploy to Trinity
```bash
/onboard
```

### Sync Credentials
```bash
/credential-sync push              # Push local .env to remote agent
/credential-sync pull              # Pull remote credentials locally
/credential-sync status            # Check credential status on remote
/credential-sync export            # Create encrypted backup on remote
/credential-sync import            # Restore from encrypted backup
```

## What It Does

1. **Discovery** - Analyzes your current agent structure
2. **Compatibility Check** - Compares against Trinity requirements
3. **User Confirmation** - Shows what will be created/changed
4. **Create Files** - Generates required configuration files
5. **Git Setup** - Initializes git, commits, pushes
6. **Deploy** - Creates agent on Trinity platform
7. **Report** - Shows completion status and next steps

## Files Created

| File | Purpose |
|------|---------|
| `template.yaml` | Agent metadata for Trinity |
| `.gitignore` | Security-critical exclusions |
| `.env.example` | Documents required environment variables |
| `.mcp.json.template` | MCP server config with placeholders |

## Requirements

- Claude Code with plugin support
- GitHub repository (created during onboarding if needed)
- Trinity account with API key

## Example Flow

```
$ /onboard

## Trinity Onboarding Analysis

### Agent: my-business-agent
### Directory: /Users/me/agents/my-business-agent

### Current State
| Item | Status |
|------|--------|
| template.yaml | MISSING |
| CLAUDE.md | EXISTS |
| .mcp.json.template | MISSING |
| .env.example | MISSING |
| .gitignore | INCOMPLETE |
| Git repository | INITIALIZED |
| Remote origin | SET |

### Actions Required
1. Create template.yaml
2. Create .env.example
3. Create .mcp.json.template
4. Update .gitignore with required entries

Proceed? [Y/n]
```

After confirmation:

```
## Trinity Onboarding Complete!

### Agent Deployed
- **Name**: my-business-agent
- **Platform**: Trinity (https://trinity.abilityai.dev)
- **Status**: Running

### Files Created/Updated
- [x] template.yaml
- [x] .gitignore
- [x] .env.example
- [x] .mcp.json.template

### Next Steps

1. Configure credentials in Trinity dashboard
2. Test remote execution
3. Set up scheduled tasks (optional)
```

## Idempotency

Both skills are safe to run multiple times:
- Existing files are only updated if needed
- Git commits are skipped if no changes
- Agent deployment updates existing agent
- Credential sync overwrites remote credentials

---

## Credential Sync

For paired local-remote agent workflows where you develop locally and run on Trinity.

### Workflow: Push Local to Remote

```
Local Agent                     Trinity Remote
┌─────────────┐                 ┌─────────────┐
│  .env       │────push────────▶│  .env       │
│  (secrets)  │                 │  (running)  │
└─────────────┘                 └─────────────┘
```

1. Edit `.env` locally with your credentials
2. Run `/credential-sync push` to inject to remote
3. Remote agent immediately has your credentials

### Workflow: Encrypted Git Storage

```
.env ──encrypt──▶ .credentials.enc ──git──▶ Remote
                  (safe to commit)          ──import──▶ .env
```

1. Create `.env` locally
2. Run `/credential-sync export` to create encrypted backup on remote
3. Commit `.credentials.enc` to git (it's encrypted)
4. On fresh deploy, `/credential-sync import` restores credentials

### Helper Scripts

The plugin includes Python scripts for local encryption/decryption:

```bash
# Encrypt local credentials
export CREDENTIAL_ENCRYPTION_KEY=<key-from-trinity>
python ~/.claude/plugins/trinity-onboard/skills/credential-sync/scripts/encrypt_credentials.py

# Decrypt credentials locally
python ~/.claude/plugins/trinity-onboard/skills/credential-sync/scripts/decrypt_credentials.py
```

Get the encryption key via MCP: `get_credential_encryption_key` tool

---

## Files

- `skills/onboard/SKILL.md` - Main onboarding skill
- `skills/credential-sync/SKILL.md` - Credential synchronization skill
- `skills/credential-sync/scripts/` - Encryption/decryption helpers
- `templates/` - Template files for new agents
- `.mcp.json` - Trinity MCP server configuration

## Support

- **Documentation**: https://trinity.abilityai.dev/docs
- **Issues**: https://github.com/abilityai/abilities/issues

## License

MIT
