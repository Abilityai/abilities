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
| [dev-methodology](plugins/dev-methodology/) | Documentation-driven development methodology | `/init`, `/read-docs`, `/implement`, `/validate-pr` |
| [website-builder](plugins/website-builder/) | Scaffold Next.js 15 websites and deploy to Vercel via GitHub | `/create-website` |
| [utilities](plugins/utilities/) | Ops workflows, deployment, incident response, and conversation management | `/investigate-incident`, `/bug-report`, `/safe-deploy`, `/docker-ops`, `/sync-ops-knowledge`, `/save-conversation`, `/batch-claude-loop` |

## Installation

### From Marketplace

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install trinity-onboard@abilityai
/plugin install playbook-builder@abilityai
/plugin install website-builder@abilityai
/plugin install utilities@abilityai
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

### Dev Methodology

Documentation-driven development methodology for Claude Code projects. Enforces a 5-phase cycle: context loading, development, testing, documentation, and PR validation.

```bash
/dev-methodology:init              # Scaffold methodology into your project
/read-docs                         # Load project context at session start
/implement #42                     # End-to-end feature implementation
/validate-pr 123                   # Validate PR against methodology
```

Includes 14 skills, 3 sub-agents (test-runner, feature-flow-analyzer, security-analyzer), and templates for project memory files (requirements, architecture, changelog, feature flows).

### Website Builder

Scaffold complete, production-ready Next.js 15 websites and deploy to Vercel in minutes. Creates a GitHub repo, pushes, and deploys via Vercel MCP — all from a single skill.

```bash
/create-website my-landing-page    # Scaffold, push to GitHub, deploy to Vercel
```

- **Full stack**: Next.js 15 App Router, TypeScript, Tailwind CSS, CSS variable design system
- **Design presets**: Minimal Clean, Bold Dark, Warm Professional, or Custom
- **GitHub + Vercel**: Creates repo via `gh`, deploys via Vercel MCP with auto-deploy on push
- **Production-ready**: SEO (sitemap, robots, OpenGraph), image optimization, cache headers

Requires [GitHub CLI](https://cli.github.com) and optionally the [Vercel MCP server](https://vercel.com/docs/agent-resources/vercel-mcp) for one-command deployment.

### Utilities

General-purpose ops and productivity skills for SSH-accessible services and daily agent workflows.

```bash
/investigate-incident              # Structured incident investigation with severity classification and root cause report
/bug-report                        # Create a sanitized GitHub issue (redacts IPs, credentials, PII)
/safe-deploy update                # Safe deployment: backup → pull → rebuild → restart → validate
/safe-deploy rollback              # Revert to previous commit with optional DB restore
/safe-deploy diagnose              # Health check: containers, errors, restarts, disk, memory
/docker-ops logs [service]         # View logs from any service with optional error filtering
/docker-ops restart [service|all]  # Graceful service restart with post-restart validation
/docker-ops telemetry              # CPU, memory, disk, and container resource stats
/docker-ops cleanup                # Prune Docker resources (dry-run by default)
/sync-ops-knowledge                # Review recent commits and update ops docs for new env vars, schema changes, API changes
/save-conversation                 # Save the current conversation as a structured markdown file
/batch-claude-loop                 # Orchestrate batch headless Claude Code calls with structured output
```

All skills connect via SSH and work with any docker-compose-based stack. Configure with a local `.env` file:

```bash
SSH_HOST=your-server-ip
SSH_USER=ubuntu
SSH_KEY=~/.ssh/id_rsa
APP_PATH=~/app
COMPOSE_FILE=docker-compose.yml
```

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
