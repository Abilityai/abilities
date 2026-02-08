# Trinity Onboard

Zero-friction onboarding to deploy any Claude Code agent to the Trinity Deep Agent Orchestration Platform.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install trinity-onboard@abilityai
```

## Usage

```bash
/onboard
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

This skill is safe to run multiple times:
- Existing files are only updated if needed
- Git commits are skipped if no changes
- Agent deployment updates existing agent

## Files

- `skills/onboard/SKILL.md` - Main onboarding skill
- `templates/` - Template files for new agents
- `.mcp.json` - Trinity MCP server configuration

## Support

- **Documentation**: https://trinity.abilityai.dev/docs
- **Issues**: https://github.com/abilityai/abilities/issues

## License

MIT
