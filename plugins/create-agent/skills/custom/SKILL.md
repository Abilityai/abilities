---
name: create-agent
description: Scaffold a new Trinity-compatible Claude Code agent from scratch on any topic. Creates directory, CLAUDE.md, skills, and Trinity files — ready for development.
argument-hint: "[topic or purpose]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.2"
  created: 2026-04-01
  updated: 2026-04-21
  author: Ability.ai
---

# Create Agent

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
4. **Deploy when ready** — run `trinity deploy .` from your terminal to go live on Trinity

### Deploying to Trinity

When you're ready to run this agent remotely (scheduled tasks, always-on, API access):

```bash
pip install trinity-cli    # one-time install
trinity init               # connect to your Trinity instance
trinity deploy .           # deploy this agent
```

After deploying, manage from your terminal:
- `trinity chat [agent-name] "message"` — talk to the remote agent
- `trinity logs [agent-name]` — view logs
- `trinity schedules list [agent-name]` — check scheduled tasks

Learn more at [ability.ai](https://ability.ai)

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
      onboarding/SKILL.md     # Setup progress tracker
      update-dashboard/SKILL.md  # Dashboard metrics updater
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

*To activate schedules after deploying to Trinity, use `mcp__trinity__create_schedule`.*

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
```

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
      "schedules_configured": { "done": false, "label": "Set up scheduled tasks (mcp__trinity__create_schedule)" },
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
- Tell user to use `mcp__trinity__create_schedule` and suggest which skills benefit from scheduling.
- Reference the recommended schedules from CLAUDE.md.
- After completion, mark done.

**For `first_scheduled_run`:**
- Tell user to check `mcp__trinity__list_schedules` for execution confirmation.
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

### Step 3: Confirm

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

## STEP 9: Generate Supporting Files

### 7a. Create .env.example

Write `[destination]/.env.example`:

```
# [Agent Display Name] Configuration
# Copy this to .env and fill in your values

# Trinity Platform Connection (optional — for remote deployment)
# Get your API key from your Trinity dashboard > Settings > API Keys
TRINITY_URL=https://your-trinity-instance.example.com
TRINITY_API_KEY=your-api-key-here

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
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/

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

```json
{
  "mcpServers": {
    "trinity": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "${TRINITY_URL}/mcp"],
      "env": {
        "API_KEY": "${TRINITY_API_KEY}"
      }
    }
  }
}
```

---

## STEP 10: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: [agent-name]"
```

---

## STEP 11: Create GitHub Repository

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

Move on silently. The agent works fine without a remote.

---

## STEP 12: Completion

Display this to the user:

```
## Agent Created: [Agent Display Name]

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity and instructions |
| `.claude/skills/[skill-1]/SKILL.md` | [skill description] |
| `.claude/skills/[skill-2]/SKILL.md` | [skill description] |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
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
