<div align="center">
  <h1>Abilities</h1>
  <p><strong>The agent development toolkit for Claude Code</strong></p>
  <p>Curated plugins covering the full agent lifecycle — from scaffolding and onboarding to deployment, scheduling, and ongoing operations. Build agents that appreciate over time.</p>

  <p>
    <a href="https://github.com/abilityai/abilities/stargazers"><img src="https://img.shields.io/github/stars/abilityai/abilities?style=social" alt="Stars"></a>
    <a href="https://github.com/abilityai/abilities/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
    <a href="https://ability.ai"><img src="https://img.shields.io/badge/platform-Trinity-purple.svg" alt="Trinity"></a>
  </p>

  <p>
    <a href="#quick-start">Quick Start</a> &bull;
    <a href="#creating-agents">Creating Agents</a> &bull;
    <a href="#all-plugins">All Plugins</a> &bull;
    <a href="#plugin-details">Plugin Details</a> &bull;
    <a href="#contributing">Contributing</a>
  </p>
</div>

---

## Quick Start

```bash
# Add the abilities marketplace (one-time)
/plugin marketplace add abilityai/abilities

# List available plugins
/plugin list abilityai

# Install the core plugins
/plugin install create-agent@abilityai
/plugin install agent-dev@abilityai
/plugin install trinity@abilityai
```

Or from the terminal:

```bash
claude plugin add abilityai/abilities
claude plugin install create-agent@abilityai
```

---

## Creating Agents

The fastest way to get started is `/create-agent:create` — a single entry point that shows all available creation paths:

```
/create-agent:create
```

### Available Wizards

All agent creation wizards are consolidated into the **create-agent** plugin. Use `/create-agent:[wizard]` syntax:

| Wizard | Command | What it creates |
|--------|---------|-----------------|
| **prospector** | `/create-agent:prospector` | B2B SaaS sales research — company research, ICP scoring, CRM integration |
| **chief-of-staff** | `/create-agent:chief-of-staff` | Executive assistant — daily briefings, meeting prep, decision tracking |
| **webmaster** | `/create-agent:webmaster` | Website management — scaffolds and deploys Next.js 15 sites to Vercel |
| **recon** | `/create-agent:recon` | Competitive intelligence — competitor tracking, market research, battlecards |
| **receptionist** | `/create-agent:receptionist` | Email gateway — public-facing email communication and request routing |
| **ghostwriter** | `/create-agent:ghostwriter` | Content writer — brand voice profiles, platform-specific writing |
| **kb-agent** | `/create-agent:kb-agent` | Knowledge-base agent — Cornelius-shaped KB with local vector search |
| **website** | `/create-agent:website` | Single website scaffold (no agent, just a site) |
| **custom** | `/create-agent:custom` | Custom agent from scratch — you define everything |
| **clone** | `/create-agent:clone` | Clone an existing agent repository as starting point |
| **adjust** | `/create-agent:adjust` | Review and improve an existing agent |

Every wizard-created agent includes:
- **`/onboarding`** — Persistent checklist that tracks setup progress across sessions
- **`dashboard.yaml`** — Domain-specific metrics dashboard for [Trinity](https://github.com/abilityai/trinity)
- **`/update-dashboard`** — Schedulable skill that keeps dashboard metrics current

---

## All Plugins

The abilities marketplace contains 5 focused plugins:

### create-agent

Create new Claude Code agents with domain-specific wizards or from scratch.

```bash
/plugin install create-agent@abilityai
```

| Skill | Description |
|-------|-------------|
| `/create-agent:create` | Entry point — shows all available wizards |
| `/create-agent:prospector` | B2B SaaS sales research agent |
| `/create-agent:chief-of-staff` | Executive assistant agent |
| `/create-agent:webmaster` | Website management agent |
| `/create-agent:recon` | Competitive intelligence agent |
| `/create-agent:receptionist` | Email gateway agent |
| `/create-agent:ghostwriter` | Content writer agent |
| `/create-agent:kb-agent` | Knowledge-base agent |
| `/create-agent:website` | Single website (no agent) |
| `/create-agent:custom` | Blank canvas agent |
| `/create-agent:clone` | Clone existing agent |
| `/create-agent:adjust` | Modify existing agent |

### agent-dev

Develop and extend existing agents with skills, memory systems, and workflows.

```bash
/plugin install agent-dev@abilityai
```

| Skill | Description |
|-------|-------------|
| `/agent-dev:create-playbook` | Create a new skill/playbook for the agent |
| `/agent-dev:adjust-playbook` | Modify an existing skill/playbook |
| `/agent-dev:add-memory` | Add memory system (file-index, brain, json-state, workspace) |
| `/agent-dev:add-backlog` | Add GitHub Issues backlog workflow |
| `/agent-dev:backlog` | View GitHub Issues backlog |
| `/agent-dev:pick-work` | Pick next issue to work on |
| `/agent-dev:close-work` | Close current issue |
| `/agent-dev:work-loop` | Run autonomous work loop |
| `/agent-dev:plan` | Plan multi-session work |

**Memory systems** (installed via `/agent-dev:add-memory`):
- **file-index** — Workspace file awareness and search
- **brain** — Zettelkasten-style knowledge graph
- **json-state** — Structured JSON state with jq updates
- **workspace** — Multi-session project tracking

### trinity

Connect, deploy, and sync agents to the [Trinity](https://github.com/abilityai/trinity) platform.

```bash
/plugin install trinity@abilityai
```

| Skill | Description |
|-------|-------------|
| `/trinity:connect` | One-time: authenticate and configure MCP connection |
| `/trinity:onboard` | Per-agent: compatibility check, file creation, deploy |
| `/trinity:sync` | Ongoing: sync changes between local and remote |

After connection, Trinity MCP tools are available directly:
- `mcp__trinity__list_agents` — List all remote agents
- `mcp__trinity__chat_with_agent` — Send messages to remote agents
- `mcp__trinity__deploy_local_agent` — Deploy agent to Trinity

### dev-methodology

Documentation-driven development methodology for any codebase.

```bash
/plugin install dev-methodology@abilityai
```

| Skill | Description |
|-------|-------------|
| `/dev-methodology:init` | Scaffold methodology into your project |
| `/dev-methodology:read-docs` | Load project context at session start |
| `/dev-methodology:implement` | End-to-end feature implementation |
| `/dev-methodology:validate-pr` | Validate PR against methodology |
| `/dev-methodology:commit` | Create well-formatted commits |
| `/dev-methodology:security-check` | Quick security scan |
| `/dev-methodology:security-analysis` | Deep security analysis |
| `/dev-methodology:add-testing` | Add tests to existing code |
| `/dev-methodology:tidy` | Clean up code |
| `/dev-methodology:roadmap` | Generate project roadmap |

### utilities

General-purpose ops and productivity skills.

```bash
/plugin install utilities@abilityai
```

| Skill | Description |
|-------|-------------|
| `/utilities:save-conversation` | Save conversation as structured markdown |
| `/utilities:investigate-incident` | Structured incident investigation |
| `/utilities:bug-report` | Create sanitized GitHub issue |
| `/utilities:safe-deploy` | Safe deployment with backup/rollback |
| `/utilities:docker-ops` | Docker container management |
| `/utilities:sync-ops-knowledge` | Update ops docs from commits |
| `/utilities:batch-claude-loop` | Batch headless Claude Code calls |

---

## The Agent Development Workflow

Abilities supports a four-step workflow for building agents that appreciate over time:

```
1. Scaffold              2. Develop                    3. Deploy              4. Iterate
/create-agent:*          /agent-dev:create-playbook    /trinity:onboard       /trinity:sync
                         /agent-dev:add-memory         trinity deploy .       git push
                         /agent-dev:add-backlog                               /create-agent:adjust
```

**Scaffold** — Use a wizard like `/create-agent:prospector` or `/create-agent:custom` to get a fully configured agent with CLAUDE.md, skills, Trinity files, and an onboarding tracker.

**Develop** — Use `/agent-dev:create-playbook` to add capabilities, `/agent-dev:add-memory` to add persistence, and `/agent-dev:add-backlog` for task management.

**Deploy** — Run `/trinity:connect` once to authenticate, then `/trinity:onboard` for each agent. Or use the [Trinity CLI](https://pypi.org/project/trinity-cli/): `trinity deploy .`

**Iterate** — Push changes with `git push` or `/trinity:sync`. Use `/create-agent:adjust` to audit and improve.

---

## Plugin Details

### create-agent

Consolidated plugin containing all agent creation wizards. Each wizard is a domain expert that asks the right questions and builds a fully configured, Trinity-compatible agent.

```bash
/create-agent:create                    # Discovery — shows all wizards
/create-agent:prospector                # B2B sales research wizard
/create-agent:chief-of-staff            # Executive assistant wizard
/create-agent:custom                    # Blank canvas wizard
/create-agent:adjust                    # Improve existing agent
```

**Generated agents include:**
- **CLAUDE.md** — Identity, behavioral instructions, artifact dependency graph
- **Initial skills** — 2-4 `.claude/skills/` playbooks based on purpose
- **Onboarding system** — `onboarding.json` + `/onboarding` skill
- **Dashboard** — `dashboard.yaml` + `/update-dashboard` skill
- **Trinity files** — `template.yaml`, `.env.example`, `.mcp.json.template`
- **Git repo** — Initialized and committed

### agent-dev

Development tools for extending existing agents. Memory systems are copied directly into agents — no plugin dependency at runtime.

```bash
/agent-dev:create-playbook              # Create new skill/playbook
/agent-dev:adjust-playbook              # Modify existing skill/playbook
/agent-dev:add-memory                   # Add memory system
/agent-dev:add-backlog                  # Add GitHub Issues workflow
/agent-dev:work-loop                    # Autonomous work loop
```

**Memory options:**
- **file-index** — Agent needs awareness of workspace files
- **brain** — Connected notes, knowledge graph (Zettelkasten)
- **json-state** — Structured state, counters, config
- **workspace** — Multi-session project tracking

### trinity

Simplified deployment to the [Trinity](https://github.com/abilityai/trinity) platform — 3 skills covering the complete workflow.

```bash
/trinity:connect                        # One-time authentication
/trinity:onboard                        # Deploy agent to Trinity
/trinity:sync                           # Sync local/remote changes
```

**What is Trinity?** Sovereign infrastructure for autonomous AI agents:
- **Autonomous operation** — Agents run 24/7 with cron-based scheduling
- **Multi-agent orchestration** — Coordinate teams of specialized agents
- **Human-in-the-loop** — Approval gates where decisions matter
- **Enterprise controls** — Audit trails, cost tracking, Docker isolation
- **Your infrastructure** — Self-hosted, data never leaves your perimeter

### dev-methodology

Documentation-driven development for any codebase. Enforces a 5-phase cycle: context loading, development, testing, documentation, and PR validation.

```bash
/dev-methodology:init                   # Scaffold methodology
/dev-methodology:read-docs              # Load context at session start
/dev-methodology:implement #42          # End-to-end feature implementation
/dev-methodology:validate-pr 123        # Validate PR
```

### utilities

General-purpose ops and productivity skills for SSH-accessible services and daily workflows.

```bash
/utilities:investigate-incident         # Structured incident investigation
/utilities:safe-deploy update           # Safe deployment with backup
/utilities:safe-deploy rollback         # Revert to previous commit
/utilities:docker-ops logs [service]    # View container logs
/utilities:save-conversation            # Save conversation as markdown
```

---

## Installation

### From Marketplace (Recommended)

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install create-agent@abilityai
/plugin install agent-dev@abilityai
/plugin install trinity@abilityai
/plugin install dev-methodology@abilityai
/plugin install utilities@abilityai
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/abilityai/abilities.git

# Install a plugin directly
/plugin add ./abilities/plugins/create-agent
```

---

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

To add a new agent creation wizard:

1. Create a skill directory in `plugins/create-agent/skills/[wizard-name]/`
2. Add a `SKILL.md` with the guided question flow
3. Update the `/create` entry point skill to include the new wizard
4. Update `marketplace.json` to register the new skill

---

## License

[MIT](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/abilityai/abilities/issues)
- **Trinity Platform**: [ability.ai](https://ability.ai)
- **Trinity Repository**: [github.com/abilityai/trinity](https://github.com/abilityai/trinity)
- **Email**: support@ability.ai

---

<div align="center">
  <sub>Built by <a href="https://ability.ai">Ability.ai</a> — Sovereign AI infrastructure for the autonomous enterprise</sub>
</div>
