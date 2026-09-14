---
name: create
description: Discover and launch agent creation wizards — your single entry point for creating a custom agent, a website, or reviewing/adjusting/cloning an existing agent
argument-hint: "[what to create]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "3.0"
  created: 2026-04-16
  updated: 2026-09-14
  author: Ability.ai
  changelog:
    - "3.0: Retire the eight pre-built domain wizards (prospector, chief-of-staff, webmaster, recon, receptionist, ghostwriter, kb-agent, doctor) per operator ruling 2026-09-14 — the menu is now custom + website + clone/review/adjust; any domain goes through /create-agent:custom"
    - "2.2: Cross-link /trinity:start-here — newcomers to Trinity itself get pointed at the guided journey before picking a wizard"
    - "2.1: List the read-only /review-agent wizard alongside /adjust-agent in the menu"
    - "2.0: Add the doctor wizard (personal medical records) to the menu"
---

# Create

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create vX.Y — recent: <summary>`. Then proceed.

Your single entry point for creating agents, websites, and projects. Lists all available creation paths and launches the right one.

> 🧭 **New to Trinity itself?** Run `/trinity:start-here` first — a guided, resumable journey from "what is Trinity" to a connected instance with your first agent alive. (Install with `/plugin install trinity@abilityai`.) This menu is one of its stops.

## Available Wizards

All wizards are skills within this plugin. Use `/create-agent:[wizard-name]` to launch directly.

| Wizard | Description | Command |
|--------|-------------|---------|
| **custom** | Interview-driven agent for any domain — you define the role, skills, schedules, and Trinity wiring | `/create-agent:custom` |
| **website** | Single website scaffold (no agent, just a site) | `/create-agent:website` |
| **clone** | Clone an existing agent repository as starting point | `/create-agent:clone` |
| **review** | Audit an existing agent against best practices (read-only report) | `/create-agent:review` |
| **adjust** | Apply best-practice fixes to an existing agent | `/create-agent:adjust` |

> The pre-built domain wizards (sales research, executive assistant, website manager, competitive intelligence, email gateway, content writer, knowledge base, medical records) were retired in create-agent 2.0.0 (2026-09-14). Every one of those shapes is reachable through `/create-agent:custom` — describe the domain and the interview builds it.

## Process

### Step 1: Check Argument

If the user provided an argument (e.g., `/create-agent:create sales` or `/create-agent:create website`), try to match it to an available wizard and skip to Step 3.

### Step 2: Show Available Options

Use AskUserQuestion:
- **Question:** "What kind of agent would you like to create?"
- **Header:** "Create Agent"
- **Options:**

  1. **Custom agent** — Interview-driven, any domain: you define the role, skills, schedules, and Trinity wiring
  2. **Website** — Scaffold a Next.js site (no agent, just a site)
  3. **Clone existing agent** — Start from a working agent as template
  4. **Review or adjust an existing agent** — Read-only audit, or apply best-practice fixes

### Step 3: Launch

Based on the user's selection, tell them the command to run:

```
## Ready to go

Run this command to start the wizard:

/create-agent:[wizard-name]
```

For example, if they chose "Custom agent", output:

```
## Ready to go

Run this command to start the wizard:

/create-agent:custom
```

### Step 4: Optional Direct Launch

If you have high confidence about which wizard the user wants based on their argument, you can tell them the command and offer to describe the wizard:

```
## Custom Agent

This wizard builds an agent for your domain from an interview. It will ask about:
- The agent's role, audience, and the outcomes it owns
- The skills it needs and which run on a schedule
- Credentials, MCP servers, and Trinity deployment wiring

Ready to start? Run: `/create-agent:custom`
```

## Notes

- This skill routes to other skills in the same plugin — all use `/create-agent:` prefix
- For the generic `/create` alias without the plugin prefix, this same skill is used
- Every domain goes through `/create-agent:custom` — there are no domain-specific wizards any more; describe the domain and the interview shapes the agent
