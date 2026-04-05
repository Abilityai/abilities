# install-prospector

Create a **B2B SaaS sales research** agent — a guided wizard that scaffolds a Trinity-compatible prospector agent customized to your sales stack and ICP.

## Usage

```
/install-prospector
/install-prospector ~/my-agents/prospector
```

## What It Does

1. Asks 4 domain-specific questions to understand your sales workflow
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Customizes research priorities, tools, and output format based on your answers
4. Initializes a git repository
5. Guides you to open Claude Code inside the new agent

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/research-company` | Deep-dive company research — funding, tech stack, news, org structure |
| `/score-fit` | Score a company against your ICP criteria |

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-prospector@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-prospector@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-prospector@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
