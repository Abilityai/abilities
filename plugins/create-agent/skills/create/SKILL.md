---
name: create
description: Discover and launch agent creation wizards — your single entry point for creating agents, websites, and projects
argument-hint: "[what to create]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "2.0"
  created: 2026-04-16
  author: Ability.ai
---

# Create

Your single entry point for creating agents, websites, and projects. Lists all available creation paths and launches the right one.

## Available Wizards

All wizards are skills within this plugin. Use `/create-agent:[wizard-name]` to launch directly.

| Wizard | Description | Command |
|--------|-------------|---------|
| **prospector** | B2B SaaS sales research agent with Apollo, LinkedIn, ICP scoring | `/create-agent:prospector` |
| **chief-of-staff** | Executive assistant with daily briefings, meeting prep, decision tracking | `/create-agent:chief-of-staff` |
| **webmaster** | Website management agent for Next.js + Vercel deployments | `/create-agent:webmaster` |
| **website** | Single website scaffold (no agent, just a site) | `/create-agent:website` |
| **recon** | Competitive intelligence agent for tracking competitors | `/create-agent:recon` |
| **receptionist** | Email gateway agent for public-facing communication | `/create-agent:receptionist` |
| **ghostwriter** | Content writer agent that knows your brand voice | `/create-agent:ghostwriter` |
| **kb-agent** | Knowledge-base agent (community manager, CS researcher, clinical, legal, personal) | `/create-agent:kb-agent` |
| **custom** | Blank canvas agent — you define everything | `/create-agent:custom` |
| **clone** | Clone an existing agent repository as starting point | `/create-agent:clone` |
| **adjust** | Modify an existing agent's identity and focus | `/create-agent:adjust` |

## Process

### Step 1: Check Argument

If the user provided an argument (e.g., `/create-agent:create sales` or `/create-agent:create website`), try to match it to an available wizard and skip to Step 3.

### Step 2: Show Available Options

Use AskUserQuestion:
- **Question:** "What kind of agent would you like to create?"
- **Header:** "Create Agent"
- **Options:**

  1. **Sales research (prospector)** — B2B SaaS prospecting with Apollo, LinkedIn, company research, ICP scoring
  2. **Executive assistant (chief-of-staff)** — Daily briefings, meeting prep, decision tracking, weekly digests
  3. **Website manager (webmaster)** — Build and deploy Next.js sites to Vercel
  4. **Competitive intelligence (recon)** — Track competitors, monitor changes, produce battlecards
  5. **Email gateway (receptionist)** — Public-facing email communication and request routing
  6. **Content writer (ghostwriter)** — Brand-aware writing for multiple platforms
  7. **Knowledge base (kb-agent)** — Domain knowledge management with Zettelkasten structure
  8. **Custom from scratch** — Blank canvas, you define everything
  9. **Clone existing agent** — Start from a working agent as template

### Step 3: Launch

Based on the user's selection, tell them the command to run:

```
## Ready to go

Run this command to start the wizard:

/create-agent:[wizard-name]
```

For example, if they chose "Sales research", output:

```
## Ready to go

Run this command to start the wizard:

/create-agent:prospector
```

### Step 4: Optional Direct Launch

If you have high confidence about which wizard the user wants based on their argument, you can tell them the command and offer to describe the wizard:

```
## Sales Research Agent

This wizard creates a prospector agent for B2B SaaS sales research. It will ask about:
- Your CRM and sales tools (Apollo, LinkedIn, etc.)
- Ideal Customer Profile (ICP) criteria
- Research depth and automation preferences

Ready to start? Run: `/create-agent:prospector`
```

## Notes

- This skill routes to other skills in the same plugin — all use `/create-agent:` prefix
- For the generic `/create` alias without the plugin prefix, this same skill is used
- If a user describes a domain that doesn't have a wizard yet, suggest `/create-agent:custom` for a blank canvas approach
