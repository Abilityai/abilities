# install-ghostwriter

Create a **content writer** agent — a guided wizard that scaffolds a Trinity-compatible ghostwriter agent that knows your brand voice and writes platform-specific content.

## Usage

```
/install-ghostwriter
/install-ghostwriter ~/my-agents/ghostwriter
```

## What It Does

1. Asks 4 domain-specific questions to understand your voice, platforms, and topics
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Creates a voice profile tailored to your writing style
4. Sets up an onboarding tracker with `/onboarding` skill
5. Initializes a git repository
6. Guides you through setup with a persistent checklist (local → Trinity → schedules)

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/write` | Write a post for any platform in your brand voice |
| `/set-voice` | Define or update your brand voice profile |
| `/repurpose` | Turn one idea into posts for multiple platforms |
| `/hooks` | Generate scroll-stopping hooks for a topic |
| `/library` | Track your content pipeline (draft → review → posted) |

## Zero API Keys Required

Ghostwriter uses Claude's native writing ability — no external API keys needed. Your voice profile and content library are stored as local files.

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-ghostwriter@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-ghostwriter@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-ghostwriter@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
