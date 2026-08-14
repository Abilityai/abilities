---
name: create-agent
description: Scaffold a new Trinity-compatible Claude Code agent from scratch on any topic. Creates directory, CLAUDE.md, skills, and Trinity files — ready for development.
argument-hint: "[topic or purpose]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill, mcp__trinity__list_agents
metadata:
  version: "1.8"
  created: 2026-04-01
  updated: 2026-07-29
  author: Ability.ai
  changelog:
    - "1.8: Platform-truth refresh (Trinity dev 88a4e2f7) — report payload cap corrected 256 KB → 5 MiB (object only), display_hint gains `json` and now drives the customer-facing Workspace Reports tab, and list_reports/get_report are taught as read-before-write. template.yaml scaffold gains credentials: + credential_setup: (ent#128/#127; gate T-015). schedules: block documents the ent#89 contract — materialized at creation, max 20, deduped by name, armed only by a literal YAML true, never re-applied on recreate, and gated again by agent autonomy (OFF on new agents); dropped the non-schema id: key and moved timezone off America/New_York to UTC (#1795, and legacy IANA aliases now 500, #1823). .gitignore gains .claude/settings.json + .trinity/* (trinity#2036/#1936) Its .mcp.json.template no longer ships a hand-written `trinity` entry (the platform injects and overwrites its own) and TRINITY_URL/TRINITY_API_KEY are gone from .env.example (read only by the retired CLI); report_type documents the ^[a-z0-9_]+(\.[a-z0-9_]+)+$ rule — a hyphenated agent name 422s."
    - "1.7: Repository-first deployment — the GitHub-repo step is framed as the deploy path (Trinity clones the repo and tracks the branch; skipping means an upload-only deploy with no reproducible source), and the deploy offer now states what /trinity:onboard actually does: create_agent(template: github:owner/repo@branch) when a remote exists — schedules materialized at creation, updates via git push + git_pull — falling back to a local-file deploy that offers promotion onto the repo path"
    - "1.6: Generated CLAUDE.md gains a Request Dispatch section — an SOP table routing incoming requests (user, other agents, operator queue) to skills; task requests with no matching skill are handled if safe and flagged as playbook gaps (told to the user interactively, filed as a playbook-gap-<slug> operator-queue item when headless on Trinity) with a pointer to /agent-dev:create-playbook"
    - "1.5: Trinity-connected deploy is the default next action — new Step 14 offers deploying the freshly created agent from its repository via /trinity:onboard when Trinity MCP is connected, gated by explicit AskUserQuestion confirmation; skipped silently when not connected"
    - "1.4: Generated agents publish structured reports via the mcp__trinity__report tool — CLAUDE.md gains a Reporting-to-Trinity section, result-producing skills get a guarded report step, and /update-dashboard also emits a kpi_snapshot report (history alongside the live snapshot)"
    - "1.3: Scaffold ships README.md + ARCHITECTURE.md + TARGET-ARCHITECTURE.md (current→target development model) and a /reconcile-docs default skill that keeps them coherent with CLAUDE.md, skills, and subagents"
    - "1.2: Wizards emit a template.yaml schedules: block for declarative Trinity scheduling"
    - "1.1: Removed Trinity CLI references — deployment guidance is now MCP/onboard-based"
    - "1.0: Backfilled the /agent-dev:add-git-sync follow-up prompt into the scaffold"
---

# Create Agent

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-agent vX.Y — recent: <summary>`. Then proceed.

Scaffold a complete Claude Code agent from scratch. The agent will be Trinity-compatible and ready for development with playbook-based skill creation.

---

## STEP 1: Gather Agent Requirements

If the user provided a topic as an argument, use it as context. Otherwise, ask.

Use AskUserQuestion to gather the following (can be a single open-ended question if user already provided detail, or multiple focused questions):

### 1a. Agent Purpose

**Question:** "What should this agent do? Describe its purpose, who it serves, and what problems it solves."

**Header:** "Agent Purpose"

Get enough detail to write a meaningful CLAUDE.md. Push for specifics — not "a coding agent" but "an agent that reviews Python PRs for a data engineering team and checks for SQL injection, missing tests, and schema migration issues."

### 1b. Agent Name

**Question:** "What should the agent be called?"

**Header:** "Agent Name"

- Suggest a name based on the purpose (lowercase-with-hyphens, short, memorable)
- Let the user override
- This becomes the directory name and the agent identity

### 1c. Destination

**Question:** "Where should I create the agent?"

**Header:** "Location"

**Options:**
1. `~/[agent-name]` — Home directory (recommended)
2. `./[agent-name]` — Current directory
3. Custom path — Let me specify

Expand `~` to actual home directory:
```bash
echo "$HOME"
```

### 1d. Initial Skills

**Question:** "What should this agent be able to do from day one? List 2-4 key capabilities."

**Header:** "Starting Skills"

Examples based on the purpose — if it's a content agent, suggest: "generate blog posts, review drafts, manage editorial calendar." If it's an ops agent: "check service health, deploy updates, investigate incidents."

These will become the agent's first skills.

### 1e. Starter Plugin Selection

Present the available plugins from the Ability.ai marketplace that are relevant to this agent's purpose. Let the user choose which to include in the agent's setup instructions.

**Always recommend:**
- **agent-dev** — For creating and managing skills (the agent's primary way to grow)
- **trinity** — For deploying to Trinity when ready

**Recommend based on purpose:**
- **utilities** — If the agent manages infrastructure or ops tasks

Use AskUserQuestion:
- **Question:** "Which plugins should this agent use? I'll include setup instructions in the agent's CLAUDE.md."
- **Header:** "Plugins"
- Show each recommendation with a one-line explanation of why it fits this agent
- Let user select multiple or add others

---

## STEP 2: Validate Destination

Check the destination doesn't already exist:

```bash
ls -la [destination] 2>/dev/null
```

If it exists and is non-empty, warn the user and ask whether to:
1. Use the existing directory (merge into it)
2. Pick a different name
3. Cancel

---

## STEP 3: Create Directory Structure

```bash
mkdir -p [destination]/.claude/skills
mkdir -p [destination]/.claude/skills/onboarding
mkdir -p [destination]/.claude/skills/update-dashboard
mkdir -p [destination]/.claude/skills/reconcile-docs
```

Create subdirectories for each skill from Step 1d as well.

---

## STEP 4: Generate CLAUDE.md

This is the most important file — it defines the agent's identity and behavior. Generate it tailored to the agent's specific purpose.

Write `[destination]/CLAUDE.md` with this structure:

```markdown
# CLAUDE.md

## Identity

You are **[Agent Display Name]** — [one-sentence purpose].

[2-3 paragraph description of what the agent does, who it serves, how it approaches work. Written in second person ("you are...", "you help..."). Be specific about the domain, the user's expectations, and the agent's personality/approach.]

## Core Capabilities

[Bulleted list of what this agent can do, mapped to its skills]

- **[Capability 1]**: [What it does and when to use it] — `/[skill-name]`
- **[Capability 2]**: [What it does and when to use it] — `/[skill-name]`
- ...

## Request Dispatch

Standard operating procedure for incoming requests — from your user, from other agents, or from the operator queue. Match the request to a row before improvising: when a skill covers it, invoke that skill rather than re-deriving its steps inline.

| Request type | Route |
|--------------|-------|
| [One row per skill — phrase it as the incoming request, not the skill name] | `/[skill-name]` |
| Question about this agent, its data, or its domain | Answer directly — no skill needed |
| Any other task request | **Playbook gap** — see below |

**Playbook gap** — a task request no skill covers. Handle it manually if it's safe and in scope, and flag the gap so it can become a playbook: interactively, tell the user in your reply; headless on Trinity, file an operator-queue item (append to `~/.trinity/operator-queue.json` with a `request_id` like `playbook-gap-<slug>`, a short title, and what was asked). Suggest `/agent-dev:create-playbook` for request types that recur. When a new skill lands, add its row here and to Core Capabilities.

## How to Work With This Agent

### Quick Start

1. Describe what you need in plain language
2. The agent will ask clarifying questions if needed
3. Review and approve any proposed actions

### Available Skills

Run these slash commands for structured workflows:

| Skill | Purpose |
|-------|---------|
| `/[skill-1]` | [description] |
| `/[skill-2]` | [description] |

### Development Workflow

Build this agent iteratively:

1. **Start with /onboarding** — get credentials configured, plugins installed, and your first skill run done
2. **Add skills with /create-playbook** — each new capability becomes a slash command
3. **Refine skills with /adjust-playbook** — improve based on real usage
4. **Deploy when ready** — run `/trinity:onboard` to go live on Trinity

### Deploying to Trinity

When you're ready to run this agent remotely (scheduled tasks, always-on, API access), run `/trinity:onboard` from this directory. It configures Trinity compatibility and deploys the agent to your instance.

**Deploy from the repository.** Push this agent to GitHub and add a GitHub token to your Trinity instance (Settings → GitHub token, fine-grained PAT with *Contents: Read*) before onboarding. Trinity then clones the repo and tracks the branch, so the deployed agent is always a named commit and updates ship with `git push` — no re-uploading. Deploying from local files still works and stays the fallback for an agent with no repo yet.

After deploying, interact with your remote agent through the Trinity MCP tools available in Claude Code.

Learn more at [ability.ai](https://ability.ai)

### Reporting to Trinity

Once deployed, publish **structured reports** so an operator can see what you produced without reading chat. At the end of any skill that yields a meaningful result — a summary, a batch of items, a metrics snapshot — call the `mcp__trinity__report` MCP tool. The report appears on this agent's **Reports** tab and the fleet-wide **Operations → Reports** view.

- **When:** at the end of result-producing skills and scheduled runs — not for conversational replies.
- **`report_type`:** namespaced `lower_snake` segments joined by `.` — `^[a-z0-9_]+(\.[a-z0-9_]+)+$`. **Hyphens are rejected (422)**, so an agent named `pr-reviewer` reports as `pr_reviewer.weekly_summary`, not `pr-reviewer.weekly_summary`.
- **`title`:** one short line (≤300 chars). **`payload`:** a JSON **object** (≤5 MiB serialized — a top-level array or scalar is rejected).
- **`display_hint`:** `table` (`{columns, rows}`), `kpi` (`{tiles:[{label,value,unit?}]}`), `markdown` (`{markdown}`), `timeline` (`{events:[{ts,label,detail}]}`), `json` (raw), or omit to let Trinity infer from `report_type`. Pick deliberately — the customer-facing Workspace Reports tab renders through these same renderers, so a mismatched hint is visible to users.
- **Read before you write:** call `mcp__trinity__list_reports` first (metadata only — filters `report_type`, `hours` ∈ {0,1,6,24,168,720}, `search`) to avoid duplicating or contradicting a report you already filed, then `mcp__trinity__get_report` with an id to diff this period against the last.
- **Guard the call:** the tool exists only when running on Trinity (it publishes under this agent's own key). If `mcp__trinity__report` isn't available — e.g. running locally — skip it silently. **Trinity is an upgrade, not a requirement.**

Reports complement `dashboard.yaml`: the dashboard is the *current* snapshot (overwritten each refresh); reports are an *append-only* history of what the agent accomplished.

## Architecture & Direction

This agent is developed deliberately, from where it is to where it's going:

- **`ARCHITECTURE.md`** — the *current state*: how the agent actually runs today (skills, subagents, data, schedules). Descriptive — it tracks reality.
- **`TARGET-ARCHITECTURE.md`** — the *target state*: where the agent is deliberately headed and why. Prescriptive — it defines intent.
- **`README.md`** — the human-facing capabilities overview, derived from this file and the skills.

Both architecture docs are living documents. The development model is **A → B**: build toward the target, and **when something ships, move it out of `TARGET-ARCHITECTURE.md` and into `ARCHITECTURE.md`.** Keep the descriptive docs (`ARCHITECTURE.md`, `README.md`) honest about what exists; keep the prescriptive doc (`TARGET-ARCHITECTURE.md`) honest about what's next. Run `/reconcile-docs` to check they — and CLAUDE.md, the skills, and any subagents — stay consistent.

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see
your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the
current phase, briefly remind the user:
"You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention it once per session, only if there are incomplete steps.

### Installed Plugins

These plugins are installed during onboarding (`/onboarding` handles this automatically):

[PLUGIN_INSTALL_COMMANDS]

[ADDITIONAL_PLUGIN_INSTRUCTIONS]

## Project Structure

```
[agent-name]/
  CLAUDE.md              # This file — agent identity and instructions
  README.md              # Human-facing capabilities overview
  ARCHITECTURE.md        # Current state — how the agent runs today
  TARGET-ARCHITECTURE.md # Target state — where the agent is headed
  onboarding.json        # Setup progress tracker
  dashboard.yaml         # Trinity dashboard metrics
  template.yaml          # Trinity metadata
  .env.example           # Required environment variables
  .gitignore             # Git exclusions
  .mcp.json.template     # MCP server config template
  .claude/
    skills/              # Agent capabilities (playbooks)
      [skill-1]/SKILL.md
      [skill-2]/SKILL.md
      onboarding/SKILL.md       # Setup progress tracker
      update-dashboard/SKILL.md # Dashboard metrics updater
      reconcile-docs/SKILL.md   # Doc/skill/architecture coherence check
  memory/                # Persistent state (if using memory plugin)
```

## Artifact Dependency Graph

This agent's workspace contains artifacts that depend on each other. When one changes, others may need updating. The **source** is authoritative — when source and target disagree, update the target.

```yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  TARGET-ARCHITECTURE.md:
    mode: prescriptive
    direction: source
    description: "Target state — where the agent is deliberately headed. Defines intent; humans own it."

  ARCHITECTURE.md:
    mode: descriptive
    direction: target
    sources: [CLAUDE.md, TARGET-ARCHITECTURE.md, .claude/skills, .claude/agents]
    description: "Current state — how the agent runs today. Tracks reality; shipped target items move here."

  README.md:
    mode: descriptive
    direction: target
    sources: [CLAUDE.md, .claude/skills]
    description: "Human-facing capabilities overview — derived from CLAUDE.md and the skills."

  onboarding.json:
    mode: descriptive
    direction: target
    sources: [onboarding/SKILL.md]
    description: "Persistent onboarding state — updated by /onboarding skill"

  dashboard.yaml:
    mode: descriptive
    direction: target
    sources: [update-dashboard/SKILL.md]
    description: "Trinity dashboard layout and metrics — updated by /update-dashboard skill"

  [artifact-1]:
    mode: [prescriptive|descriptive]
    direction: [source|target]
    sources: [list of artifacts this derives from]
    description: "[what this artifact represents]"

  [artifact-2]:
    mode: [prescriptive|descriptive]
    direction: [source|target]
    sources: [list of artifacts this derives from]
    description: "[what this artifact represents]"

sync_skills:
  - skill: /reconcile-docs
    source: [CLAUDE.md, TARGET-ARCHITECTURE.md, .claude/skills, .claude/agents]
    target: [README.md, ARCHITECTURE.md]
    trigger: after shipping a capability, changing skills/subagents, or on a weekly schedule

  - skill: /[skill-name]
    source: [source artifacts]
    target: [target artifacts]
    trigger: [when to run]
```

**Direction rules:**
- **Source wins**: When two artifacts conflict, the source is correct, the target is stale
- **Prescriptive** artifacts define intent (what *should* be true) — implementation conforms to them
- **Descriptive** artifacts reflect reality (what *is* true) — they conform to implementation
- Artifacts can transition: a new spec starts prescriptive, then becomes descriptive after implementation

## Recommended Schedules

Skills that should run on a recurring basis once the agent is deployed to Trinity:

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/[skill-name]` | [cron expression or human interval] | [why it runs on this cadence] |
| `/[skill-name]` | [cron expression or human interval] | [why it runs on this cadence] |

*Source of truth: the `schedules:` block in `template.yaml`. Deploying with `/trinity:onboard` reconciles it onto Trinity; turn individual schedules on/off on the live agent with `mcp__trinity__toggle_agent_schedule`.*

## Guidelines

[2-4 domain-specific guidelines for how this agent should behave. Examples:]

[- For a code review agent: "Always check for security issues before style issues. Never auto-approve — present findings and let the user decide."]
[- For a content agent: "Match the user's brand voice. Ask for tone/style preferences on first interaction and remember them."]
[- For an ops agent: "Never run destructive commands without explicit approval. Always show a dry-run first."]
```

**IMPORTANT:** The `[PLUGIN_INSTALL_COMMANDS]` placeholder should be replaced with install commands for **each plugin selected in Step 1e**. Always include agent-dev and trinity. Format as:

```markdown
```
/plugin install agent-dev@abilityai   # Create new skills
/plugin install trinity@abilityai     # Deploy to Trinity
/plugin install [plugin]@abilityai    # [domain-specific reason]
```
```

The `[ADDITIONAL_PLUGIN_INSTRUCTIONS]` placeholder should be replaced with setup instructions for any extra plugins the user selected in Step 1e. Format as:

```markdown
### [Plugin Name]

[One-line description of what this plugin adds]

Install: `/plugin install [plugin-name]@abilityai`
Setup: `/[setup-skill-name]`
```

If the user selected utilities, include relevant skills for the agent's domain.

If no additional plugins were selected, remove the placeholder entirely.

**Artifact Dependency Graph guidance:** Populate the graph based on the agent's actual artifacts and skills. Every agent has at minimum:
- `CLAUDE.md` as a prescriptive source (defines the agent)
- Each skill's `SKILL.md` as a prescriptive source (defines behavior)
- Any generated outputs (reports, docs, configs) as descriptive targets

Map the agent's skills as `sync_skills` entries — each skill that produces or updates an artifact should be listed with its source, target, and trigger. This gives the agent structured reasoning about its workspace instead of ad-hoc update rules.

**Recommended Schedules guidance:** Based on the agent's skills and purpose, suggest which skills benefit from running on a schedule. Consider:
- **Monitoring/health** skills → frequent (every 15m–1h)
- **Sync/update** skills → moderate (every 1–6h or daily)
- **Report/summary** skills → daily or weekly
- **Cleanup/maintenance** skills → weekly

Only include skills that make sense as automated recurring tasks. Interactive or on-demand skills should not be scheduled. Use human-readable intervals (e.g., "every 6 hours", "daily at 9am UTC") alongside cron expressions.

**Always include `/update-dashboard`** with a schedule appropriate to how frequently the agent's metrics change (e.g., `*/15 * * * *` for active agents, `0 */6 * * *` for less active ones).

**Always include `/reconcile-docs`** on a light cadence (e.g., weekly `0 9 * * 1`) so doc/skill/architecture drift gets surfaced regularly. Scheduled runs are report-only; the operator applies fixes interactively.

---

## STEP 5: Generate template.yaml

Write `[destination]/template.yaml`:

```yaml
name: [agent-name]
display_name: [Agent Display Name]
description: |
  [2-3 sentence description from Step 1]
avatar_prompt: [Generate a vivid character portrait prompt that fits the agent's purpose — see guidance below]
resources:
  cpu: "2"
  memory: "4g"

# What this agent needs, BY NAME ONLY — names-only is the frozen contract; never values.
# Every ${VAR} used in .mcp.json.template must appear here or the agent HARD-fails
# compatibility check T-015. An agent with no secrets declares an explicit `credentials: {}`.
credentials:
  env_file: [EXAMPLE_API_KEY]

# Per-variable setup guidance (ent#128). DECORATES credentials: — it cannot declare a
# name that isn't above (undeclared entries are dropped). Drives the platform's guided
# checklist: GET /api/agents/{name}/credential-requirements (ent#127).
credential_setup:
  - name: EXAMPLE_API_KEY
    title: Example service API key
    description: What the agent uses it for, in one line.
    required: true
    secret: true
    format: secret
    setup_url: https://example.com/settings/api-keys

# Optional: recommended schedules (design source of truth). Trinity materializes
# this block ON AGENT CREATION, deduplicated by `name` — at most 20 entries, and
# NEVER re-applied on recreate, so a schedule added here after deployment must be
# created with create_agent_schedule (or reconciled by /trinity:onboard | /trinity:sync).
# `enabled` is the recommended default and only a literal YAML true arms a schedule;
# firing ALSO requires the agent's autonomy gate, which is OFF on every new agent.
# timezone: canonical IANA zones only — legacy aliases (Europe/Kiev, Asia/Calcutta,
# US/Eastern) no longer resolve and 500 on schedule create. The container clock is UTC.
# Propose 1–2 from the agent's purpose, or omit this block if it has no scheduled tasks.
# schedules:
#   - name: Daily summary
#     cron: "0 9 * * *"
#     timezone: UTC
#     message: "Summarize yesterday's activity and surface anything needing attention."
#     purpose: Daily status digest
#     enabled: false
```

**schedules guidance:** If the agent has recurring tasks, uncomment the `schedules:` block above and add 1–2 entries derived from its purpose (fields map one-to-one onto `create_agent_schedule`; see `/trinity:onboard` Step 3a). Leave them `enabled: false` so the operator chooses what runs after deploy. Omit the block entirely for purely on-demand agents.

**avatar_prompt guidance:** Write a vivid, specific character description for generating the agent's portrait. Describe a person or character — appearance, attire, expression, setting, and lighting — that embodies the agent's role and personality.

Ask the user if they'd like to customize the avatar prompt, or accept the generated one.

---

## STEP 6: Generate Initial Skills

For each skill identified in Step 1d, create a SKILL.md in `.claude/skills/[skill-name]/`.

Use the **simple skill template** for initial skills (Tier 1) unless the skill clearly requires state:

```yaml
---
name: [skill-name]
description: [What it does]
allowed-tools: [appropriate tools — Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion]
user-invocable: true
metadata:
  version: "1.0"
  created: [today's date]
  author: [user or agent name]
---

# [Skill Title]

## Purpose

[One sentence — what this skill accomplishes]

## Process

### Step 1: [First Action]

[Instructions for what to do]

### Step 2: [Second Action]

[Instructions for what to do]

[... more steps as needed]

## Outputs

- [What the skill produces or changes]
```

**Skill design guidelines:**
- Keep initial skills focused and simple — they can be upgraded later with `/adjust-playbook`
- Use `AskUserQuestion` for any step that needs user input
- Include specific, actionable instructions — not vague descriptions
- Match the tools to what the skill actually needs (don't grant Write if it only reads)
- **Publish a report on result-producing skills:** if a skill yields a surfaceable result (a summary, a batch, metrics), end it with a step that calls `mcp__trinity__report` (`report_type: <agent>.<result>`, a fitting `display_hint`) — guarded so it only fires when the tool is available on Trinity (see CLAUDE.md → *Reporting to Trinity*)

**Present each skill outline to the user before creating it.** Show the name, purpose, steps, and tools. Let them adjust before you write the files.

---

## STEP 7: Generate Onboarding System

Every agent includes a persistent onboarding tracker — a checklist that guides the user from local setup through Trinity deployment and scheduling.

### 7a. Generate onboarding.json

Write `[destination]/onboarding.json`. Customize the `local` phase based on the agent's domain and skills.

```json
{
  "phase": "local",
  "started": "[today's date]",
  "steps": {
    "local": {
      "env_configured": { "done": false, "label": "Configure environment variables (.env)" },
      "first_skill_run": { "done": false, "label": "[Run /primary-skill — customized to this agent's first skill]" },
      "plugins_installed": { "done": false, "label": "Install plugins ([list plugin names from Step 1e])" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity:onboard)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via mcp__trinity__chat_with_agent" }
    },
    "schedules": {
      "schedules_configured": { "done": false, "label": "Declare scheduled tasks in template.yaml (schedules:)" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled execution completed" }
    }
  }
}
```

**Customization rules for `local` steps:**
- If the agent needs no API keys, remove `env_configured` and make the first step domain-specific (e.g., reviewing a config, running the primary skill)
- Add 1-2 domain-specific steps between `env_configured` and `plugins_installed` that reflect the most important first actions for this agent
- The `first_skill_run` label should reference the agent's primary skill by name

### 7b. Generate /onboarding skill

Write `[destination]/.claude/skills/onboarding/SKILL.md`:

```yaml
---
name: onboarding
description: Track your setup progress — shows what's done, what's next, and walks you through each step
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: [today's date]
  author: [agent-name]
---
```

```markdown
# Onboarding

Track and continue your setup progress. This skill reads `onboarding.json`, shows your current status, and walks you through the next incomplete step.

## Process

### Step 1: Load State

Read `onboarding.json` from the agent root directory. If it doesn't exist, inform the user that onboarding is complete or the file was removed.

### Step 2: Show Progress

Display a checklist grouped by phase. Mark the current phase with an arrow. Use checkboxes:

```
## [Agent Name] — Setup Progress

### Phase 1: Local Setup  ← current
- [x] Configure environment variables (.env)
- [ ] [Domain-specific step]
- [ ] Install recommended plugins

### Phase 2: Trinity Deployment
- [ ] Deploy to Trinity
- [ ] Sync credentials to remote
- [ ] Run a skill remotely

### Phase 3: Schedules
- [ ] Set up scheduled tasks
- [ ] Verify first scheduled execution

**Progress: 1/8 complete**
```

### Step 3: Guide Next Step

Identify the first incomplete step in the current phase. Based on which step it is, provide specific guidance:

**For `env_configured`:**
- Check if `.env` exists. If not, guide: `cp .env.example .env` then fill in values.
- List the required variables from `.env.example` and what each one is for.
- After user confirms, mark done.

**For domain-specific steps (e.g., `first_skill_run`):**
- Tell the user exactly which command to run.
- After they run it successfully, mark done.

**For `plugins_installed`:**
- Run the install commands for each plugin selected in Step 1e:
  ```
  /plugin install [plugin-name]@abilityai
  ```
- Run each install command via Bash. Note successes and failures.
- After all attempted, mark done.

**For `onboarded` (Trinity phase):**
- Guide the user to run `/trinity:onboard`.
- After completion, mark done and advance phase.

**For `first_remote_run`:**
- Tell user to run `mcp__trinity__chat_with_agent` with the agent name and skill.
- After completion, mark done and advance phase.

**For `schedules_configured`:**
- Tell user the recommended schedules live in `template.yaml` (`schedules:`); deploying with `/trinity:onboard` reconciles them onto the instance. Suggest which skills benefit from scheduling and add them to the block.
- To turn one on/off on the live agent, use `mcp__trinity__toggle_agent_schedule`.
- After completion, mark done.

**For `first_scheduled_run`:**
- Tell user to check `mcp__trinity__get_schedule_executions` for execution confirmation.
- After verified, mark done.

### Step 4: Update State

After each step is completed, update `onboarding.json`:
- Set the step's `done` to `true`
- If all steps in current phase are done, advance `phase` to the next phase
- If all phases complete, congratulate the user

### Step 5: Phase Transitions

When all steps in a phase are complete:

**Local → Trinity:**
```
## Local Setup Complete!

Your [agent-name] agent is fully configured and working locally.

Ready for the next level? Trinity gives you:
- Remote execution (run skills from anywhere)
- Scheduling (automate recurring tasks)
- Multi-agent coordination

Run /onboarding again when you're ready to set up Trinity.
```

**Trinity → Schedules:**
```
## Trinity Deployment Complete!

Your agent is live on Trinity. Now let's set up automation.

Run /onboarding to configure scheduled tasks.
```

**All Complete:**
```
## Onboarding Complete!

Your [agent-name] agent is fully set up:
- ✓ Local environment configured
- ✓ Deployed to Trinity
- ✓ Schedules running

You're all set. The onboarding.json file can be kept as a record or deleted.
```

## Outputs

- Updated `onboarding.json` with progress
- Step-by-step guidance for the current task
- Phase transition messages at milestones
```

**Customize the onboarding skill** based on the agent's actual skills and plugins:
- Replace `[agent-name]` with the real agent name
- Replace `[primary-skill]` references with the agent's first skill
- Adjust the `env_configured` guidance to list the actual env vars from `.env.example`
- Adjust `plugins_installed` to list the actual plugins from Step 1e

---

## STEP 8: Generate Dashboard

Every agent includes a starter `dashboard.yaml` and an `/update-dashboard` skill for Trinity.

### 8a. Generate dashboard.yaml

Write `[destination]/dashboard.yaml`. Customize sections and widgets based on the agent's purpose and skills.

```yaml
title: "[Agent Display Name]"
refresh: 300
updated: "[today's date ISO]"

sections:
  - title: "Status"
    layout: grid
    columns: 3
    widgets:
      - type: status
        label: "Agent Status"
        value: "Active"
        color: green
      - type: metric
        label: "Last Activity"
        value: "—"
        description: "Updated by /update-dashboard"
      - type: metric
        label: "[Domain-Specific Metric]"
        value: "0"

  - title: "[Domain Section]"
    layout: grid
    columns: 2
    widgets:
      - type: metric
        label: "[Metric from primary skill]"
        value: "—"
      - type: list
        title: "Recent Activity"
        items: []
        max_items: 5

  - title: "Quick Links"
    layout: list
    widgets:
      - type: link
        label: "Trinity Dashboard"
        url: "https://ability.ai"
        external: true
```

**Widget types:** metric (label/value/trend/unit), status (label/value/color), progress (label/value 0-100), text (content), markdown (content), table (columns/rows), list (items/max_items), link (label/url), chart (chart_type/series), divider, spacer.

**Colors:** green, yellow, red, gray, blue, orange, purple.

**Customization:** Choose 2-3 sections with 3-6 widgets that reflect the agent's actual domain and skills. Keep it focused — `/update-dashboard` fills in real values later.

### 8b. Generate /update-dashboard skill

Write `[destination]/.claude/skills/update-dashboard/SKILL.md`:

```yaml
---
name: update-dashboard
description: Refresh dashboard.yaml with current metrics from agent data sources
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: [today's date]
  author: [agent-name]
---
```

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from this agent's data sources and state files.

## Process

### Step 1: Gather Metrics

Read the agent's data sources to collect current values:
- Read state/tracking files (*.json, *.yaml in agent root)
- Check recent git activity: `git log --oneline -10`
- Count items in data directories
- Check skill execution artifacts

[Customize this list based on the agent's actual data sources and skills]

### Step 2: Update Dashboard

Read `dashboard.yaml`, update widget values with fresh data:
- Update the `updated` timestamp to now
- Update metric values from gathered data
- Update status colors based on health thresholds
- Update activity lists with recent items

Write the updated `dashboard.yaml`.

### Step 3: Publish a KPI snapshot report (Trinity)

If the `mcp__trinity__report` tool is available (i.e. running on Trinity), also publish the same headline numbers as a report so they accumulate as history alongside the live snapshot:

- `report_type`: `[agent-name].kpi_snapshot`
- `display_hint`: `kpi`
- `payload`: `{ "tiles": [ {"label": "...", "value": "...", "unit": "..."} ] }`, built from the same values you just wrote to the dashboard.

Skip this step silently if the tool isn't available — the dashboard refresh above still succeeds.

### Step 4: Confirm

Report what was updated:
```
Dashboard refreshed:
- [metric]: [old] → [new]
- Last updated: [timestamp]
```

Note: On Trinity remote, the dashboard path is `/home/developer/dashboard.yaml`.

## Outputs

- Updated `dashboard.yaml` with current metrics
```

**Customize** the "Gather Metrics" step to reference the specific data sources this agent uses.

---

## STEP 9: Generate Architecture & Capability Docs

Every agent ships three living documents that, together with CLAUDE.md, give it a clear picture of *what it is*, *how it runs today*, and *where it's going*. They make the **A → B development model** explicit: `TARGET-ARCHITECTURE.md` is B, `ARCHITECTURE.md` is A, and shipping moves an item from B into A.

### 9a. Generate README.md

Human-facing capabilities overview — what someone sees first when they open the repo. **Descriptive** (derived from CLAUDE.md + skills). Write `[destination]/README.md`:

```markdown
# [Agent Display Name]

**Role:** [one-line purpose from Step 1]

[1-2 paragraph plain-language description of what the agent does and who it serves.]

## Capabilities

[One subsection or bullet per capability, mirroring CLAUDE.md's Core Capabilities — each pointing at the skill that delivers it.]

- **[Capability 1]** — [what it does] (`/[skill-1]`)
- **[Capability 2]** — [what it does] (`/[skill-2]`)

## Getting Started

```
cd [agent-name] && claude
/onboarding
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for how the agent is built today and **[TARGET-ARCHITECTURE.md](TARGET-ARCHITECTURE.md)** for where it's headed.

## Skills

| Skill | Purpose |
|-------|---------|
| `/[skill-1]` | [description] |
| `/[skill-2]` | [description] |
| `/reconcile-docs` | Keep docs, skills, and architecture consistent |
```

### 9b. Generate ARCHITECTURE.md

The *current state* — how the agent actually runs today. **Descriptive** (tracks reality). Keep it honest: only describe what exists. Write `[destination]/ARCHITECTURE.md`:

```markdown
# [Agent Display Name] Architecture (Current State)

**What this is:** the agent as it actually runs today. For where it's deliberately headed, see the companion **`TARGET-ARCHITECTURE.md`**. When a target ships, it moves *out* of that doc and *into* this one.

**Last updated:** [today's date]

## Overview

[2-3 sentences on the agent's shape — its main components and how they fit together.]

## Components

### Skills
[List each skill and what it does — mirrors `.claude/skills/`.]

### Subagents
[List each subagent in `.claude/agents/`, or "None yet."]

### Data & State
[State files, memory, data directories the agent reads/writes — or "None yet."]

### Schedules
[Recurring tasks declared in template.yaml `schedules:`, or "None yet."]

## Trinity Integration

[How the agent deploys — template.yaml resources, MCP config — or "Local only so far."]
```

### 9c. Generate TARGET-ARCHITECTURE.md

The *target state* — where the agent is deliberately going. **Prescriptive** (defines intent). Write `[destination]/TARGET-ARCHITECTURE.md`:

```markdown
# [Agent Display Name] Target Architecture

**What this is:** where the agent is deliberately headed. The companion to **`ARCHITECTURE.md`** (what runs today). When something here ships, it moves *out* of this doc and *into* `ARCHITECTURE.md`.

**Last updated:** [today's date]

## Direction

[The guiding principle(s) for this agent's evolution — what it should become and what it should never do.]

## Planned Capabilities

[Capabilities the agent is built toward but doesn't have yet. Derive 1-3 from Step 1d's "planned" items, the user's stated goals, or obvious next skills. Each: what it is, why it matters, and roughly what it depends on. If the agent is fully built for now, say so and leave a single "Next ideas" bullet list.]

- **[Planned capability]** — [what it enables; what it depends on]
```

**Guidance:** Populate all three from the actual agent — its real skills, subagents, and the purpose from Step 1. Don't invent components that don't exist in `ARCHITECTURE.md`. If the user named capabilities beyond the 4 initial skills (Step 1d "planned capabilities"), put those in `TARGET-ARCHITECTURE.md`. Keep each doc short — they grow with the agent.

---

## STEP 10: Generate /reconcile-docs Skill

Every agent ships a `/reconcile-docs` skill that walks the **Artifact Dependency Graph** and keeps the agent's docs honest — so CLAUDE.md, README, the architecture docs, the skills, and any subagents never silently drift apart.

Write `[destination]/.claude/skills/reconcile-docs/SKILL.md`:

```yaml
---
name: reconcile-docs
description: Check that CLAUDE.md, README, ARCHITECTURE/TARGET-ARCHITECTURE, skills, and subagents are mutually consistent — reports drift and applies approved fixes. Run after shipping a capability or on a schedule.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: [today's date]
  author: [agent-name]
  changelog:
    - "1.0: Initial version — dependency-graph-driven coherence check across docs, skills, and subagents"
---
```

```markdown
# Reconcile Docs

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `reconcile-docs vX.Y — recent: <summary>`. Then proceed.

Keep this agent's documentation honest. This skill reads the **Artifact Dependency Graph** in `CLAUDE.md` and checks that every artifact agrees with its sources — then reports drift and, interactively, applies approved fixes.

**Direction rule (from the graph):** the *source* wins.
- **Descriptive targets** (`README.md`, `ARCHITECTURE.md`) must match reality — when they disagree with their sources (CLAUDE.md, the skills, the subagents, the code), **fix the target.**
- **Prescriptive sources** (`CLAUDE.md`, `TARGET-ARCHITECTURE.md`) define intent — when they're out of date, **flag for a human.** Never silently rewrite intent to match a possibly-buggy implementation.

## Process

### Step 1: Load the graph

Read `CLAUDE.md` and parse the `## Artifact Dependency Graph` (the `artifacts:` and `sync_skills:` blocks). This is the spec for what depends on what.

### Step 2: Gather reality

```bash
find .claude/skills -name SKILL.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
ls README.md ARCHITECTURE.md TARGET-ARCHITECTURE.md template.yaml 2>/dev/null
```

Read `README.md`, `ARCHITECTURE.md`, `TARGET-ARCHITECTURE.md`, and the `schedules:` block in `template.yaml`. Note each skill's name/description from its frontmatter and each subagent's purpose.

### Step 3: Check coherence

Evaluate each, recording CONSISTENT / DRIFT / MISSING:

1. **CLAUDE.md ↔ skills** — every skill in `.claude/skills/` is listed in Core Capabilities; every listed skill exists; descriptions agree.
2. **README ↔ reality** — README capabilities/skills table matches the actual skills and subagents.
3. **ARCHITECTURE ↔ reality** — components described (skills, subagents, data, schedules) all exist on disk; nothing real is undocumented.
4. **TARGET-ARCHITECTURE ↔ ARCHITECTURE** — no item described as shipped/live in ARCHITECTURE is still sitting in TARGET as "planned." Anything now implemented → propose moving it from target into current.
5. **Subagents ↔ docs** — every `.claude/agents/*` is referenced in CLAUDE.md/ARCHITECTURE; nothing referenced is missing.
6. **Schedules ↔ template.yaml** — the Recommended Schedules table in CLAUDE.md matches the `schedules:` block.
7. **Guidelines ↔ behavior** — guidelines don't contradict what the skills actually do.

### Step 4: Report

Produce a drift report — **this mode is read-only and safe to run on a schedule.**

```
## Doc Reconciliation: [agent name]

| # | Check | Status | Drift | Fix side |
|---|-------|--------|-------|----------|
| 1 | CLAUDE.md ↔ skills | DRIFT | /foo exists but isn't in Core Capabilities | target (CLAUDE.md*) |
| 2 | ARCHITECTURE ↔ reality | DRIFT | subagent `bar` not documented | target (ARCHITECTURE.md) |

\* CLAUDE.md is prescriptive — flag, don't auto-edit.
```

If everything is CONSISTENT, say so and stop.

### Step 5: Apply (interactive only)

**Skip this step when running on a schedule** — scheduled runs report only (no approval gate). When run interactively and drift exists, propose exact edits and confirm:

Use AskUserQuestion:
- **Question:** "Which fixes should I apply?"
- **Header:** "Apply Fixes"
- **Options:** Apply all (descriptive targets only) / Let me pick / Just the report

Apply approved edits to **descriptive targets** (`README.md`, `ARCHITECTURE.md`) — and, when a target item has shipped, move it from `TARGET-ARCHITECTURE.md` into `ARCHITECTURE.md`. For drift that implicates a **prescriptive source** (CLAUDE.md, TARGET-ARCHITECTURE.md), present it as a recommendation for the user to decide — do not auto-edit.

## Outputs

- A coherence report (always)
- Updated `README.md` / `ARCHITECTURE.md` when fixes are approved
- Flagged recommendations for any CLAUDE.md / TARGET-ARCHITECTURE.md drift
```

**Recommend a weekly schedule** for `/reconcile-docs` in the agent's `template.yaml` (report-only cadence, e.g. `0 9 * * 1`), and add it to the Recommended Schedules table. Scheduled runs surface drift; the operator applies fixes interactively.

---

## STEP 11: Generate Supporting Files

### 7a. Create .env.example

Write `[destination]/.env.example`:

```
# [Agent Display Name] Configuration
# Copy this to .env and fill in your values

# Trinity connection is NOT configured here — the platform injects it.
# (/trinity:connect keeps local credentials in ~/.trinity/config.json + .mcp.json;
#  a deployed agent gets its `trinity` MCP entry written by the container at startup.)

[AGENT_SPECIFIC_VARS]
```

Add agent-specific environment variables based on the purpose. Examples:
- API keys for services the agent interacts with
- Configuration values mentioned in the skills
- Leave them as descriptive placeholders

### 7b. Create .gitignore

Write `[destination]/.gitignore`:

```gitignore
# Credentials - never commit
.mcp.json
.env
*.pem
*.key

# Claude Code internals
.claude.json
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/
.claude/sessions/
.claude/shell-snapshots/
.claude/plugins/
.claude/backups/
.claude/settings.local.json
# Container-only config: the Trinity base image bakes ~/.claude/settings.json with
# hook paths that exist only inside the container, and HOME is the repo root. A
# committed copy bricks any clone made outside it (the missing hook exits 2, which
# Claude Code reads as "block this tool call"). Trinity enforces this fleet-wide and
# untracks an already-committed copy on the next Push (trinity#2036).
.claude/settings.json
# Trinity runtime state — star form so authored hooks stay tracked
.trinity/*
!.trinity/pre-check
!.trinity/post-check
!.trinity/setup.sh
credentials.json
*.pem
*.key

# Runtime
content/
session-files/
node_modules/
__pycache__/
*.pyc
.DS_Store
```

### 7c. Create .mcp.json.template

Write `[destination]/.mcp.json.template`:

Declare the agent's **own** MCP servers here — never a `trinity` entry. Trinity injects its own `trinity` server into `~/.mcp.json` on every container start (from the `TRINITY_MCP_URL` / `TRINITY_MCP_API_KEY` env vars it sets at creation) and **overwrites** any `trinity` entry you ship, so a hand-written one is dead weight.

If the agent has no MCP servers of its own, write exactly:

```json
{
  "mcpServers": {}
}
```

Otherwise declare them like this — note that `${VAR}` is substituted **inside `env` blocks only**. A placeholder in `command`, `url`, or `args` makes Trinity **withhold the whole server** at startup with a named reason in the log, and `command` must be an allowlisted literal (`npx`, `uvx`, `python`, `python3`, `node`, `bun`, `deno`, `docker`):

```json
{
  "mcpServers": {
    "some_service": {
      "command": "npx",
      "args": ["-y", "some-service-mcp"],
      "env": {
        "SOME_SERVICE_API_KEY": "${SOME_SERVICE_API_KEY}"
      }
    }
  }
}
```

Every `${VAR}` used here must also appear in the `credentials:` block of `template.yaml`, or the agent HARD-fails compatibility check T-015.

---

## STEP 12: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: [agent-name]"
```

---

## STEP 13: Create GitHub Repository

Ask the user if they want to create a GitHub repository for this agent.

Use AskUserQuestion:
- **Question:** "Would you like me to create a GitHub repo for this agent?"
- **Header:** "GitHub Repository"
- **Options:**
  1. **Yes, public** — Create a public repo
  2. **Yes, private** — Create a private repo (recommended)
  3. **No, I'll do it later** — Skip this step

### If the user chooses to create a repo:

First, verify `gh` CLI is available and authenticated:

```bash
gh auth status 2>&1
```

If not authenticated, tell the user to run `! gh auth login` and retry.

Then create the repo and push:

```bash
cd [destination] && gh repo create [agent-name] --[public|private] --source=. --push --description "[Agent Display Name] — [one-line description]"
```

Report the repo URL to the user on success.

**After creating the repo**, update `CLAUDE.md` to include the repository URL. Add it to the Identity section, right after the agent name line:

```markdown
## Identity

You are **[Agent Display Name]** — [one-sentence purpose].

**Repository:** [repo-url]
```

Then amend the initial commit to include the updated CLAUDE.md:

```bash
cd [destination] && git add CLAUDE.md && git commit --amend --no-edit && git push --force-with-lease
```

### If `gh` is not installed:

Tell the user:
> GitHub CLI (`gh`) is not installed. You can create a repo manually:
> 1. Go to github.com/new
> 2. Name it `[agent-name]`
> 3. Then run:
>    ```bash
>    cd [destination]
>    git remote add origin git@github.com:[username]/[agent-name].git
>    git push -u origin main
>    ```

### If the user skips:

Move on silently — the agent works fine without a remote. Note once, without pushing: Trinity deploys agents by cloning their GitHub repo, so without one, deployment falls back to uploading local files and this agent has no reproducible source until a repo exists.

---

## STEP 14: Offer Trinity Deployment (if connected)

**Default approach:** when this session is already connected to Trinity, deploying the new agent from its repository is the default next action — but it **never happens without explicit confirmation**.

**Detect the connection:** Trinity is connected when the `mcp__trinity__*` MCP tools are available in this session (probe with `mcp__trinity__list_agents`). If more than one Trinity server is connected, confirm which instance the tools reach before offering.

**If Trinity is NOT connected:** skip this step silently — the Completion summary keeps `/trinity:onboard` as the deploy-later path. Trinity is the upgrade, not the gate.

**If Trinity IS connected:** ask for confirmation — never deploy unprompted. Use AskUserQuestion:
- **Question:** "Trinity is connected in this session. Deploy [Agent Display Name] to Trinity now from [destination]?"
- **Header:** "Deploy"
- **Options:**
  1. **Yes, deploy now (Recommended)** — deploy from the repository via `/trinity:onboard`
  2. **Not now** — keep it local; deploy later with `/trinity:onboard` from the agent directory

**If confirmed:** set the working directory to `[destination]`, then invoke `/trinity:onboard` (Skill tool). It owns the deployment end-to-end, and it is **repository-first**: with a pushed GitHub remote (Step 13) it deploys via `create_agent(template: "github:owner/repo@branch")` — Trinity clones the repo, tracks the branch, and materializes the `template.yaml` schedules at creation, after which every change ships by `git push` + `git_pull` instead of re-uploading the agent. Without a remote it falls back to a local-file deploy and offers to promote the agent onto the repo path afterwards. Either way it injects credentials and reconciles schedules. Do **not** inline raw `mcp__trinity__create_agent` / `mcp__trinity__deploy_local_agent` calls here — `/trinity:onboard` is the single source of truth for deployment. If `/trinity:onboard` isn't available (trinity plugin not installed), tell the user to run `/plugin install trinity@abilityai` and then `/trinity:onboard` from the agent directory — don't attempt a manual deploy.

**If declined:** move on silently.

**Carry the outcome forward:** if the deploy ran, reflect it in the Completion summary — a `✓ Deployed to Trinity — [instance URL]` line replacing any "deploy later" guidance; otherwise leave the summary as is.

---

## STEP 15: Completion

Display this to the user:

```
## Agent Created: [Agent Display Name]

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity and instructions |
| `README.md` | Human-facing capabilities overview |
| `ARCHITECTURE.md` | Current state — how the agent runs today |
| `TARGET-ARCHITECTURE.md` | Target state — where the agent is headed |
| `.claude/skills/[skill-1]/SKILL.md` | [skill description] |
| `.claude/skills/[skill-2]/SKILL.md` | [skill description] |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `.claude/skills/reconcile-docs/SKILL.md` | Doc/skill/architecture coherence check |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with domain metrics |
| `template.yaml` | Trinity metadata |
| `.env.example` | Environment variable template |
| `.gitignore` | Git exclusions |
| `.mcp.json.template` | MCP config template |

### Get Started

1. Open your new agent:
   ```
   cd [destination] && claude
   ```

2. Run the setup wizard:
   ```
   /onboarding
   ```

   This will walk you through configuring your environment,
   running your first skill, and (when you're ready) deploying to Trinity.

3. **Add cross-session durability** (recommended):
   ```
   /agent-dev:add-git-sync
   ```
```

**Do not list manual steps like "install plugins" or "try /skill-name" here.** The `/onboarding` skill handles all of that in a tracked, resumable flow.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists and is non-empty | Warn user, offer alternatives |
| Git not installed | Skip git init, tell user to install git |
| User can't decide on skills | Suggest 2 starter skills based on the purpose and offer to add more later |
| User wants many skills (>4) | Create the top 4, note the rest in CLAUDE.md as "planned capabilities" |
