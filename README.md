# Abilities

A curated collection of Claude Code plugins from [Ability.ai](https://ability.ai).

## Quick Start

```bash
# Add the abilities marketplace (one-time)
/plugin marketplace add abilityai/abilities

# List available plugins
/plugin list abilityai

# Install a plugin
/plugin install trinity-onboard@abilityai
```

## Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| [trinity-onboard](plugins/trinity-onboard/) | Deploy agents to Trinity platform | `/trinity-onboard`, `/credential-sync`, `/trinity-sync` |
| [playbook-builder](plugins/playbook-builder/) | Create structured playbooks with state management | `/create-playbook`, `/save-playbook` |

## Installation

### From Marketplace

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install trinity-onboard@abilityai
/plugin install playbook-builder@abilityai
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/abilityai/abilities.git

# Install a plugin directly
/plugin add ./abilities/plugins/trinity-onboard
```

## Plugin Details

### Trinity Onboard

Deploy any Claude Code agent to the [Trinity](https://github.com/abilityai/trinity) platform.

**What is Trinity?** Trinity is sovereign infrastructure for autonomous AI agents. It provides:

- **Autonomous operation** — Agents run 24/7 with cron-based scheduling
- **Multi-agent orchestration** — Coordinate teams of specialized agents
- **Human-in-the-loop** — Approval gates where decisions matter
- **Enterprise controls** — Complete audit trails, cost tracking, Docker isolation
- **Your infrastructure** — Self-hosted, data never leaves your perimeter

```bash
/onboard                   # Convert workspace to Trinity agent
/credential-sync           # Encrypt/decrypt credentials
```

The onboarding wizard analyzes your agent, creates required configuration files (`template.yaml`, `.mcp.json`), pushes to GitHub, and deploys to Trinity.

After deployment, your agent can:
- Run autonomously on schedules
- Collaborate with other agents via MCP
- Persist memory across sessions
- Be managed via web UI or API

### Playbook Builder

Create structured, transactional playbooks with state management for autonomous, gated, or manual execution.

```bash
/create-playbook           # Interactive playbook creation wizard
/save-playbook             # Capture workflow from conversation
```

- **Autonomous mode**: Full automation with checkpoints
- **Gated mode**: Human approval at critical steps
- **Manual mode**: Step-by-step guided execution

Supports state persistence, rollback capabilities, and Trinity integration.

## Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Adding a Plugin

1. Create a new directory in `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add your skills in `skills/[skill-name]/SKILL.md`
4. Add a `README.md` with usage documentation
5. Register in `.claude-plugin/marketplace.json`
6. Submit a pull request

## License

[MIT](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/abilityai/abilities/issues)
- **Email**: support@ability.ai
- **Website**: [ability.ai](https://ability.ai)
