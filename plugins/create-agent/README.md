# create-agent

Create new Claude Code agents with domain-specific wizards or from scratch.

## Installation

```
/plugin install create-agent@abilityai
```

## Usage

```
/create-agent:create              # Show all available wizards
/create-agent:prospector          # B2B SaaS sales research agent
/create-agent:chief-of-staff      # Executive assistant agent
/create-agent:webmaster           # Website management agent
/create-agent:website             # Single website (no agent)
/create-agent:recon               # Competitive intelligence agent
/create-agent:receptionist        # Email gateway agent
/create-agent:ghostwriter         # Content writer agent
/create-agent:kb-agent            # Knowledge-base agent
/create-agent:doctor              # Personal medical-records agent
/create-agent:custom              # Blank canvas agent
/create-agent:clone               # Clone existing agent
/create-agent:review              # Audit existing agent (read-only report)
/create-agent:adjust              # Apply best-practice fixes to existing agent
```

## Available Wizards

### Domain-Specific Wizards

| Wizard | Description |
|--------|-------------|
| **prospector** | B2B SaaS sales research agent with Apollo, LinkedIn, ICP scoring, company research |
| **chief-of-staff** | Executive assistant with daily briefings, meeting prep, decision tracking, weekly digests |
| **webmaster** | Website management agent for Next.js + Vercel deployments |
| **recon** | Competitive intelligence agent for tracking competitors and producing battlecards |
| **receptionist** | Email gateway agent for public-facing communication and request routing |
| **ghostwriter** | Content writer agent that learns your brand voice and writes for multiple platforms |
| **kb-agent** | Knowledge-base agent for community management, CS research, clinical, legal, or personal KB |
| **doctor** | Personal medical-records agent — ingests health documents, tracks lab trends, prepares doctor visits, flags drug-supplement interactions |

### Generic Tools

| Tool | Description |
|------|-------------|
| **website** | Scaffold a single Next.js website (no agent, just a site) |
| **custom** | Create any agent from scratch — blank canvas, you define everything |
| **clone** | Clone an existing agent repository as a starting point |
| **review** | Audit an existing agent against best practices — read-only findings report (composition integrity, identity, schedules, Trinity readiness) |
| **adjust** | Apply best-practice fixes to an existing agent — runs review, then applies approved edits |

## How Wizards Work

Each wizard is a guided conversation that:

1. Asks domain-specific questions to understand your needs
2. Scaffolds a Trinity-compatible agent directory
3. Generates customized CLAUDE.md, skills, docs (README + ARCHITECTURE + TARGET-ARCHITECTURE), and configuration
4. Declares recommended `schedules:` in `template.yaml` (disabled by default — the operator chooses what runs)
5. Optionally deploys to Trinity for remote execution

Generated agents ship with a `schedules:` block in `template.yaml` describing the recurring tasks the agent is designed to run. They're declared `enabled: false` — `/trinity:onboard` and `/trinity:sync` reconcile them onto your Trinity instance, and you turn on the ones you want.

**Best practice: each scheduled entry calls one playbook and nothing else** — no inline instructions or arguments in the cron prompt. Business logic belongs in the playbook the schedule triggers, so changing a scheduled task means editing that playbook, not the schedule.

### Current → target development model

Every generated agent carries a clear picture of *what it is*, *how it runs today*, and *where it's going*:

- **`README.md`** — human-facing capabilities overview (descriptive)
- **`ARCHITECTURE.md`** — current state, how the agent runs today (descriptive)
- **`TARGET-ARCHITECTURE.md`** — target state, where it's deliberately headed (prescriptive)

The model is **A → B**: build toward the target, and when something ships, move it out of `TARGET-ARCHITECTURE.md` and into `ARCHITECTURE.md`. A bundled **`/reconcile-docs`** skill walks the agent's Artifact Dependency Graph and keeps these docs consistent with CLAUDE.md, the skills, and any subagents — run it after shipping a capability or on a weekly schedule. `/review` audits this coherence; `/adjust` retrofits the docs into agents created before this convention.

All generated agents work locally first — Trinity deployment is the natural upgrade path, not a requirement.

## Next Steps After Creating an Agent

1. **Add capabilities**: `/agent-dev:create-playbook` — add new skills/playbooks
2. **Add memory**: `/agent-dev:add-memory` — choose appropriate memory system
3. **Deploy to Trinity**: `/trinity:onboard` — deploy for remote execution
4. **Orchestrate a fleet**: `/agent-dev:add-orchestrator` — make this agent system-aware, able to discover and drive other agents

**Compose, don't copy.** When one of an agent's skills needs work another skill already does, it should *invoke that skill by name* (``Invoke `/child-skill` ``, `Skill` in `allowed-tools`) rather than inline its steps or call its internal scripts — so the child stays the single source of truth and its fixes propagate automatically. See [Composing skills (hierarchical playbooks)](../agent-dev/README.md#composing-skills-hierarchical-playbooks).

## Source

This plugin consolidates the following original plugins:
- install-prospector, install-chiefofstaff, install-webmaster
- install-recon, install-receptionist, install-ghostwriter
- install-kb-agent, agent-builder, clone-cornelius, website-builder
