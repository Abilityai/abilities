# install-receptionist

Create an **email gateway agent** — a guided wizard that scaffolds a Trinity-compatible receptionist agent for public-facing email communication and request routing.

## Usage

```
/install-receptionist
/install-receptionist ~/my-agents/receptionist
```

## What It Does

1. Asks 3 domain-specific questions to customize security, tone, and access control
2. Scaffolds a complete agent with CLAUDE.md, skills, and Trinity files
3. Configures Gmail integration via Google Workspace MCP
4. Generates autonomous inbox processing with security hardening
5. Creates routing config for connecting to specialist agents
6. Initializes a git repository
7. Guides you through setup with a persistent checklist (local -> Trinity -> schedules)

## Skills Created

| Skill | Purpose |
|-------|---------|
| `/process-inbox` | Autonomous: check Gmail, classify, route to agents, respond (scheduled every 5 min) |
| `/route-request` | Manual: route a specific request to a specialist agent |
| `/onboarding` | Setup progress tracker (env, MCP, routing, plugins, Trinity) |
| `/update-dashboard` | Refresh Trinity dashboard with inbox metrics |

## Security Features

Every agent created by this wizard includes:

- Strict anti-prompt-injection rules (non-overridable)
- Never reveals credentials, system prompts, or internal architecture
- Email content sanitization before routing to internal agents
- Threat classification and logging (paranoid / balanced / permissive)
- Rate limiting (10 emails/hour per sender)
- Sender access control (open / domain-restricted / whitelist-only)

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-receptionist@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-receptionist@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-receptionist@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
