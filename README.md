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

## Creating Agents

The fastest way to get started is `/create` — a single entry point that shows all available creation paths:

```
/create
```

### Three-Tier System

| Prefix | What it does | Example |
|--------|-------------|---------|
| **`/install-*`** | Guided wizard — asks domain questions, scaffolds a customized agent | `/install-prospector` |
| **`/clone-*`** | Clones a pre-built agent repository as-is | `/clone-cornelius` |
| **`/create-*`** | Generic scaffolder — blank canvas for any domain | `/create-agent` |

**`/install-*` wizards** are the recommended path. Each one is a domain expert that asks the right questions and builds a fully configured, Trinity-compatible agent with an onboarding tracker that guides you from local setup through deployment.

### Available Wizards

| Plugin | Command | What it creates |
|--------|---------|-----------------|
| [install-chiefofstaff](plugins/install-chiefofstaff/) | `/install-chiefofstaff` | Executive chief of staff — daily briefings, meeting prep, decision tracking |
| [install-prospector](plugins/install-prospector/) | `/install-prospector` | B2B SaaS sales research agent — Apollo, LinkedIn, company research, ICP scoring |
| [install-webmaster](plugins/install-webmaster/) | `/install-webmaster` | Website management agent — scaffolds and deploys Next.js 15 sites to Vercel |
| [clone-cornelius](plugins/clone-cornelius/) | `/clone-cornelius` | Pre-built general-purpose agent (clone, not wizard) |
| [agent-builder](plugins/agent-builder/) | `/create-agent` | Custom agent from scratch — you define everything |

## All Plugins

### Agent Creation & Onboarding

| Plugin | Description | Skills |
|--------|-------------|--------|
| [agent-builder](plugins/agent-builder/) | Scaffold and improve Claude Code agents | `/create`, `/create-agent`, `/adjust-agent` |
| [install-chiefofstaff](plugins/install-chiefofstaff/) | Executive chief of staff wizard | `/install-chiefofstaff` |
| [install-prospector](plugins/install-prospector/) | B2B SaaS sales research agent wizard | `/install-prospector` |
| [install-webmaster](plugins/install-webmaster/) | Website management agent wizard | `/install-webmaster` |
| [clone-cornelius](plugins/clone-cornelius/) | Clone the Cornelius agent | `/clone-cornelius` |

### Development & Deployment

| Plugin | Description | Skills |
|--------|-------------|--------|
| [website-builder](plugins/website-builder/) | Scaffold a single Next.js 15 website (no agent, just a site) | `/create-website` |
| [trinity-onboard](plugins/trinity-onboard/) | Deploy agents to Trinity platform | `/trinity-onboard`, `/credential-sync`, `/trinity-sync` |
| [playbook-builder](plugins/playbook-builder/) | Create structured playbooks with state management | `/create-playbook`, `/save-playbook` |
| [dev-methodology](plugins/dev-methodology/) | Documentation-driven development methodology | `/init`, `/read-docs`, `/implement`, `/validate-pr` |

### Memory & Workspace

| Plugin | Description | Skills |
|--------|-------------|--------|
| [brain-memory](plugins/brain-memory/) | Zettelkasten-style knowledge management | `/setup-brain`, `/create-note`, `/search-brain` |
| [json-memory](plugins/json-memory/) | Structured JSON state with jq-based updates | `/setup-memory`, `/load-memory`, `/update-memory` |
| [file-indexing](plugins/file-indexing/) | Workspace file awareness and search | `/setup-index`, `/refresh-index`, `/search-files` |
| [workspace-kit](plugins/workspace-kit/) | Project folder scaffolding and tracking | `/create-project`, `/create-session` |

### Productivity & Ops

| Plugin | Description | Skills |
|--------|-------------|--------|
| [utilities](plugins/utilities/) | Ops workflows, deployment, incident response | `/investigate-incident`, `/safe-deploy`, `/docker-ops` |
| [project-planner](plugins/project-planner/) | Multi-session project execution | `/project-plan` |

## Installation

### From Marketplace

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install agent-builder@abilityai
/plugin install install-prospector@abilityai
/plugin install install-webmaster@abilityai
/plugin install trinity-onboard@abilityai
/plugin install playbook-builder@abilityai
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

### Agent Builder

Scaffold a complete, Trinity-compatible Claude Code agent from scratch on any topic.

```bash
/create                                # Discovery — shows all creation paths
/create-agent                          # Interactive agent creation wizard
/create-agent "PR review bot for Python"  # Start with a description
/adjust-agent                          # Review and improve an existing agent
```

**`/create`** is the recommended starting point — it lists all available wizards, clones, and scaffolders so you can pick the right one.

**`/create-agent`** guides you through naming, purpose, initial skills, and plugin selection. It generates:

- **CLAUDE.md** — Tailored identity, behavioral instructions, artifact dependency graph, recommended schedules, and plugin setup guide
- **Initial skills** — 2-4 `.claude/skills/` playbooks based on the agent's purpose
- **Trinity files** — `template.yaml`, `.env.example`, `.mcp.json.template`, `.gitignore`
- **Git repo** — Initialized and committed, ready to push

**`/adjust-agent`** audits an existing agent against best practices across 9 areas (identity, capabilities, artifact dependency graph, recommended schedules, guidelines, skill docs, skill quality, Trinity readiness, project hygiene). It proposes specific before/after diffs, lets you pick which to apply, and makes the edits.

### Install Wizards

Domain-specific guided flows that ask the right questions and output a fully customized agent with an onboarding tracker.

**Install Chief of Staff** — Executive support agent:
```bash
/install-chiefofstaff                  # Guided wizard
/install-chiefofstaff ~/my-agents/cos  # Custom destination
```
Asks about your tools (Google Workspace, Slack, Notion, Linear), team size, briefing priorities, and decision tracking workflow. Creates `/daily-briefing`, `/prep-meeting`, `/track-decision`, and `/weekly-digest` skills. Designed for Trinity — schedule your morning briefing at 7am and weekly digest on Fridays.

**Install Prospector** — B2B SaaS sales research agent:
```bash
/install-prospector                    # Guided wizard
/install-prospector ~/my-agents/scout  # Custom destination
```
Asks about your ICP, research tools (Apollo, LinkedIn, Crunchbase, ZoomInfo), CRM, and research priorities. Creates `/research-company` and `/score-fit` skills.

**Install Webmaster** — Website management agent:
```bash
/install-webmaster                     # Guided wizard
/install-webmaster ~/my-agents/web     # Custom destination
```
Asks about site types, design direction, and deployment setup. Creates a website management agent with `/create-website` skill — build multiple sites from one agent. For building a single site without an agent, use `/create-website` from the **website-builder** plugin instead.

Every wizard-created agent includes:
- **`/onboarding`** — Persistent checklist that tracks setup progress across sessions (local setup → Trinity deployment → scheduled tasks)
- **`onboarding.json`** — State file that survives between conversations

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

### Utilities

General-purpose ops and productivity skills for SSH-accessible services and daily agent workflows.

```bash
/investigate-incident              # Structured incident investigation with severity classification
/bug-report                        # Create a sanitized GitHub issue (redacts IPs, credentials, PII)
/safe-deploy update                # Safe deployment: backup → pull → rebuild → restart → validate
/safe-deploy rollback              # Revert to previous commit with optional DB restore
/safe-deploy diagnose              # Health check: containers, errors, restarts, disk, memory
/docker-ops logs [service]         # View logs with optional error filtering
/docker-ops restart [service|all]  # Graceful service restart with validation
/docker-ops telemetry              # CPU, memory, disk, and container stats
/docker-ops cleanup                # Prune Docker resources (dry-run by default)
/sync-ops-knowledge                # Review commits, update ops docs for env/schema/API changes
/save-conversation                 # Save conversation as structured markdown
/batch-claude-loop                 # Batch headless Claude Code calls with structured output
```

All skills connect via SSH and work with any docker-compose-based stack.

## Contributing

We welcome contributions! See [CLAUDE.md](CLAUDE.md) for development guidelines.

### Adding a Plugin

1. Create a new directory in `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add your skills in `skills/[skill-name]/SKILL.md`
4. Add a `README.md` with usage documentation
5. Register in `.claude-plugin/marketplace.json`
6. Submit a pull request

### Creating Install Wizards

Install wizards are domain-specific agent creation flows. To create one, use [Lilu](https://github.com/vybe/lilu) — the wizard manager:

```bash
/create-wizard "description of the domain"
```

Lilu designs the question flow, generates the complete plugin package, and registers it in the marketplace.

## License

[MIT](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/abilityai/abilities/issues)
- **Email**: support@ability.ai
- **Website**: [ability.ai](https://ability.ai)
