# Abilities

High-quality Claude Code plugins from [Ability.ai](https://ability.ai).

## Quick Start

```bash
# Add the abilities marketplace
/plugin marketplace add abilityai/abilities

# List available plugins
/plugin list abilityai

# Install a plugin
/plugin install process-miner@abilityai
```

## Available Plugins

| Plugin | Description | Use Case |
|--------|-------------|----------|
| [process-miner](plugins/process-miner/) | Analyze Claude Code logs to discover workflow patterns | Extract repeatable processes from agent behavior |
| [repo-tidy](plugins/repo-tidy/) | Audit and clean up repository structure | Find orphan files, outdated docs, misplaced configs |
| [validate-pr](plugins/validate-pr/) | Validate PRs against security standards | Pre-merge security and quality checks |
| [trinity-onboard](plugins/trinity-onboard/) | Onboard agents to Trinity platform | Deploy Claude Code agents to the cloud |

## Installation

### Install from Marketplace

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install individual plugins
/plugin install process-miner@abilityai
/plugin install repo-tidy@abilityai
/plugin install validate-pr@abilityai
/plugin install trinity-onboard@abilityai
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/abilityai/abilities.git

# Install a plugin directly
/plugin add ./abilities/plugins/process-miner
```

## Plugin Details

### Process Miner

Analyze Claude Code execution logs to discover workflow patterns and generate process definitions.

```bash
/process-miner
```

**Features:**
- Parse JSONL transcripts from `~/.claude/projects/`
- Discover frequent tool sequences
- Classify user intents
- Generate workflow YAML definitions

### Repo Tidy

Audit and clean up repository structure safely.

```bash
/tidy              # Full audit
/tidy docs         # Audit docs folder only
/tidy --report-only # Report without changes
```

**Features:**
- Auto-clean safe artifacts (`__pycache__`, `.pyc`, etc.)
- Find orphan documentation
- Detect misplaced files
- Archive outdated content

### Validate PR

Validate pull requests against security and documentation standards.

```bash
/validate-pr 123
/validate-pr https://github.com/org/repo/pull/123
```

**Features:**
- Security scanning (API keys, tokens, secrets)
- Documentation update checks
- Code quality assessment
- Merge recommendation

### Trinity Onboard

Onboard any Claude Code agent to the Trinity Deep Agent Orchestration Platform.

```bash
/onboard
```

**Features:**
- Create required Trinity config files
- Set up git repository
- Deploy agent to cloud
- Zero-friction onboarding flow

## Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md).

### Adding a Plugin

1. Create a new directory in `plugins/`
2. Add `.claude-plugin/plugin.json` with plugin metadata
3. Add your skills, commands, or agents
4. Update `marketplace.json` with the new plugin
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/abilityai/abilities/issues)
- **Email**: support@ability.ai
- **Website**: [ability.ai](https://ability.ai)
