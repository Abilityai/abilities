# install-recon

Create a **competitive intelligence** agent — a guided wizard that scaffolds a Trinity-compatible agent for tracking competitors, monitoring changes, and producing actionable intelligence from open sources.

## Usage

```
/install-recon
/install-recon ~/my-agents/recon
```

## What It Does

1. Asks 4 domain-specific questions to understand your competitive landscape
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Customizes tracking dimensions, output formats, and monitoring cadence
4. Creates an onboarding tracker with `/onboarding` skill
5. Initializes a git repository
6. Guides you through setup with a persistent checklist (local → Trinity → schedules)

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/add-competitor` | Add a competitor to your watchlist with structured profile data |
| `/monitor` | Scan tracked competitors for changes since last check |
| `/battlecard` | Generate or refresh a one-page sales battlecard for a competitor |
| `/digest` | Produce a competitive intelligence summary of recent changes |
| `/landscape` | Full competitive landscape analysis with feature comparison matrix |

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-recon@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-recon@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-recon@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
