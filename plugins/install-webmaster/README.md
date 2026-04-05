# install-webmaster

Create a **website management** agent — a guided wizard that scaffolds a Trinity-compatible webmaster agent for building and deploying Next.js sites to Vercel.

## Usage

```
/install-webmaster
/install-webmaster ~/my-agents/webmaster
```

## What It Does

1. Asks 3 domain-specific questions to understand your web development workflow
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Customizes the agent for your preferred site types, design direction, and deployment setup
4. Creates an onboarding tracker with `/onboarding` skill
5. Initializes a git repository
6. Guides you through setup with a persistent checklist (local → Trinity → schedules)

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/create-website` | Scaffold a production-ready Next.js 15 site with design system, components, SEO, and Vercel deployment |
| `/onboarding` | Track your setup progress from local configuration through Trinity deployment |

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-webmaster@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-webmaster@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-webmaster@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
