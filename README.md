# Abilities

A curated collection of Claude Code plugins from [Ability.ai](https://ability.ai).

## Quick Start

```bash
# Add the abilities marketplace (one-time)
/plugin marketplace add abilityai/abilities

# List available plugins
/plugin list abilityai

# Install a plugin
/plugin install git-workflow@abilityai
```

## Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| [git-workflow](plugins/git-workflow/) | Streamlined git with safety checks | `/commit`, `/sync`, `/publish` |
| [skill-builder](plugins/skill-builder/) | Create Claude Code skills | `/skill-builder`, `/agentic-best-practices` |
| [process-miner](plugins/process-miner/) | Discover workflow patterns from logs | `/process-miner` |
| [repo-tidy](plugins/repo-tidy/) | Audit and clean up repositories | `/tidy` |
| [validate-pr](plugins/validate-pr/) | PR validation and security checks | `/validate-pr` |
| [workspace-tools](plugins/workspace-tools/) | File indexing and organization | `/file-indexer`, `/workspace-discipline` |
| [trinity-onboard](plugins/trinity-onboard/) | Deploy agents to Trinity platform | `/onboard`, `/credential-sync` |

## Installation

### From Marketplace

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install git-workflow@abilityai
/plugin install skill-builder@abilityai
/plugin install process-miner@abilityai
/plugin install repo-tidy@abilityai
/plugin install validate-pr@abilityai
/plugin install workspace-tools@abilityai
/plugin install trinity-onboard@abilityai
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/abilityai/abilities.git

# Install a plugin directly
/plugin add ./abilities/plugins/git-workflow
```

## Plugin Details

### Git Workflow

Safe git operations with built-in guardrails.

```bash
/commit                    # Create commit with auto-generated message
/commit fix login bug      # Create commit with custom message
/sync                      # Pull-rebase-push workflow
/publish                   # Push changes to remote
```

Never commits `.env`, `.mcp.json`, or credential files.

### Skill Builder

Expert guidance for creating Claude Code skills.

```bash
/skill-builder             # Interactive skill creation wizard
/agentic-best-practices    # Apply best practices to complex tasks
```

Covers YAML frontmatter, skill structure, testing, and validation.

### Process Miner

Analyze Claude Code execution logs to discover workflow patterns.

```bash
/process-miner
```

- Parse JSONL transcripts from `~/.claude/projects/`
- Discover frequent tool sequences
- Classify user intents
- Generate workflow YAML definitions

### Repo Tidy

Audit and clean up repository structure safely.

```bash
/tidy                      # Full audit
/tidy docs                 # Audit docs folder only
/tidy --report-only        # Report without changes
```

- Auto-clean safe artifacts (`__pycache__`, `.pyc`, `.DS_Store`)
- Find orphan documentation
- Archive outdated content (preserves history)

### Validate PR

Validate pull requests against security and documentation standards.

```bash
/validate-pr 123
/validate-pr https://github.com/org/repo/pull/123
```

- Security scanning (API keys, tokens, secrets)
- Documentation update checks
- Code quality assessment

### Workspace Tools

Keep projects organized and navigable.

```bash
/file-indexer              # Generate file indexes
/workspace-discipline      # Enforce workspace conventions
```

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
