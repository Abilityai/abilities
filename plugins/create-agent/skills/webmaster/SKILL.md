---
name: install-webmaster
description: Create a website management agent — asks about your web development workflow and scaffolds a Trinity-compatible webmaster agent for building and deploying Next.js sites
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill, mcp__trinity__list_agents
metadata:
  version: "1.7"
  created: 2026-04-04
  author: Ability.ai
  changelog:
    - "1.7: Platform-truth refresh (Trinity dev 88a4e2f7) — report payload cap corrected 256 KB → 5 MiB (object only), display_hint gains `json` and now drives the customer-facing Workspace Reports tab, and list_reports/get_report are taught as read-before-write. template.yaml scaffold gains credentials: + credential_setup: (ent#128/#127; gate T-015). schedules: block documents the ent#89 contract — materialized at creation, max 20, deduped by name, armed only by a literal YAML true, never re-applied on recreate, and gated again by agent autonomy (OFF on new agents); dropped the non-schema id: key and moved timezone off America/New_York to UTC (#1795, and legacy IANA aliases now 500, #1823). .gitignore gains .claude/settings.json + .trinity/* (trinity#2036/#1936) Public-repo option now warns that a tokenless clone gets a read-only remote (409 no_write_credentials, ent#123)."
    - "1.6: Repository-first deployment — the GitHub-repo step is framed as the deploy path (Trinity clones the repo and tracks the branch; skipping means an upload-only deploy with no reproducible source), and the deploy offer now states what /trinity:onboard actually does: create_agent(template: github:owner/repo@branch) when a remote exists — schedules materialized at creation, updates via git push + git_pull — falling back to a local-file deploy that offers promotion onto the repo path"
    - "1.5: Generated CLAUDE.md gains a Request Dispatch section — an SOP table routing incoming requests (user, other agents, operator queue) to skills; task requests with no matching skill are handled if safe and flagged as playbook gaps (told to the user interactively, filed as a playbook-gap-<slug> operator-queue item when headless on Trinity) with a pointer to /agent-dev:create-playbook"
    - "1.4: Trinity-connected deploy is the default next action — new Step 10 offers deploying the freshly created agent from its repository via /trinity:onboard when Trinity MCP is connected, gated by explicit AskUserQuestion confirmation; skipped silently when not connected"
    - "1.3: Generated agent publishes structured reports via mcp__trinity__report — CLAUDE.md gains a 'Reporting to Trinity' section and its primary result skill ends with a guarded webmaster.deploy report (Reports tab history alongside the live dashboard); skipped silently off-Trinity"
    - "1.2: Wizards emit a template.yaml schedules: block for declarative Trinity scheduling"
    - "1.1: Removed Trinity CLI references — deployment guidance is now MCP/onboard-based"
    - "1.0: Backfilled the /agent-dev:add-git-sync prompt; added a development-workflow section"
---

# Install Webmaster

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `install-webmaster vX.Y — recent: <summary>`. Then proceed.

Create a **website management agent** powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A fully configured agent directory with CLAUDE.md, skills, and Trinity files
- `/create-website` skill — scaffolds production-ready Next.js 15 sites with design system, SEO, and Vercel deployment
- `/onboarding` skill — persistent setup tracker
- Ready for local use or Trinity deployment

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

---

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Webmaster be installed?"
- **Header:** "Location"
- Show these options:
  1. `~/webmaster` — Home directory (recommended)
  2. `./webmaster` — Current directory
  3. Custom path — Let me specify

Default to `~/webmaster` if no preference.

Expand `~` to the actual home directory using:
```bash
echo "$HOME"
```

Validate the destination does not already exist:
```bash
ls -la [destination] 2>/dev/null
```

If it exists, warn the user and offer:
1. Pick a different path
2. Cancel

---

## STEP 2: Domain-Specific Questions

Ask these 3 questions to customize the agent. Each answer directly shapes the generated files.

### Q1: Site Types

Use AskUserQuestion:
- **Question:** "What kind of websites will you build with this agent? This sets the default page templates and component library — you can always create other site types later."
- **Header:** "Site Types"
- **multiSelect: true**
- **Options:**
  1. **SaaS landing pages** — Hero → features → pricing → CTA. Best for product marketing and signups.
  2. **Agency / company sites** — Services, team bios, case studies. Best for businesses that need a multi-page presence.
  3. **Portfolios** — Visual showcase with minimal chrome. Best for designers, photographers, freelancers.
  4. **Documentation / blogs** — Article-driven with dynamic routes. Best for content-first sites and knowledge bases.

Store the answer — it customizes: homepage templates in /create-website, default page suggestions, component library focus.

### Q2: Default Design Direction

Use AskUserQuestion:
- **Question:** "Pick a default design style. This becomes the starting point when you run /create-website — you can still override it per project."
- **Header:** "Design"
- **Options:**
  1. **Minimal Clean** — Light backgrounds, subtle borders, lots of whitespace. Think Stripe, Linear. Good for SaaS and professional sites.
  2. **Bold Dark** — Dark backgrounds, vivid accent colors, glassmorphism cards. Think Vercel, Raycast. Good for dev tools and modern products.
  3. **Warm Professional** — Soft neutrals, rounded shapes, approachable feel. Think Notion, Mailchimp. Good for friendly brands.
  4. **Always ask** — No default — the agent will ask you each time you create a site.

Store the answer — it customizes: default design preset in /create-website skill, CSS variable defaults in reference material.

### Q3: Deployment Setup

Use AskUserQuestion:
- **Question:** "How should the agent handle deployment? This controls whether /create-website pushes to GitHub and deploys automatically, or just builds locally."
- **Header:** "Deploy"
- **Options:**
  1. **Vercel + GitHub (Recommended)** — Creates a GitHub repo, pushes code, and deploys to Vercel with auto-deploy on every push. Fastest path to a live site.
  2. **GitHub only** — Creates a GitHub repo and pushes, but you handle hosting yourself (Netlify, Cloudflare, etc.)
  3. **Manual** — No repo or deploy automation. Just builds the site locally and you take it from there.

Store the answer — it customizes: which deployment steps are included in /create-website, .env.example, onboarding steps.

---

## STEP 3: Create Agent Directory Structure

```bash
mkdir -p [destination]/.claude/skills/create-website
mkdir -p [destination]/.claude/skills/onboarding
mkdir -p [destination]/.claude/skills/update-dashboard
```

---

## STEP 4: Generate CLAUDE.md

Write `[destination]/CLAUDE.md` with the following content, customized based on wizard answers.

**Site type customization:**
- **SaaS landing pages** → emphasize conversion-focused design, hero sections, pricing components
- **Agency / company** → emphasize multi-page architecture, services grids, team sections
- **Portfolios** → emphasize visual showcase, minimal chrome, project galleries
- **Docs / blogs** → emphasize content structure, dynamic routing, MDX patterns

**Design direction customization:**
- If a default was chosen, mention it as the agent's preferred style
- If "Always ask," note that the agent prompts for direction on each project

**Deployment customization:**
- **Vercel + GitHub** → include Vercel MCP setup in plugin recommendations
- **GitHub only** → skip Vercel references, focus on GitHub workflow
- **Manual** → minimal deployment guidance

```markdown
# CLAUDE.md

## Identity

You are **Webmaster** — a website management agent that scaffolds production-ready Next.js 15 sites and deploys them to Vercel.

You build [site types from Q1] using a modern stack: Next.js 15 (App Router), TypeScript, and Tailwind CSS. Your default design direction is [design from Q2 or "chosen per-project"]. [If Vercel + GitHub: You deploy via GitHub → Vercel auto-deploy pipeline.]

You think like a senior frontend developer who values clean architecture, semantic HTML, accessible components, and fast load times. Every site you build is production-ready from the first commit.

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/create-website` | Scaffold a complete Next.js 15 site — design system, components, pages, SEO, deployment |
| `/update-dashboard` | Refresh Trinity dashboard metrics from site and project data |

## Request Dispatch

Standard operating procedure for incoming requests — from your user, from other agents, or from the operator queue. Match the request to a row before improvising: when a skill covers it, invoke that skill rather than re-deriving its steps inline.

| Request type | Route |
|--------------|-------|
| "Build me a site" — new website from scratch | `/create-website` |
| Refresh site and project metrics | `/update-dashboard` |
| Question about this agent, its sites, or its domain | Answer directly — no skill needed |
| Any other task request (edits, redeploys, debugging) | **Playbook gap** — see below |

**Playbook gap** — a task request no skill covers. Handle it manually if it's safe and in scope, and flag the gap so it can become a playbook: interactively, tell the user in your reply; headless on Trinity, file an operator-queue item (append to `~/.trinity/operator-queue.json` with a `request_id` like `playbook-gap-<slug>`, a short title, and what was asked). Suggest `/agent-dev:create-playbook` for request types that recur. When a new skill lands, add its row here and to Core Capabilities.

## How to Work With This Agent

### Quick Start

1. Run `/create-website my-project` to scaffold a new site
2. The wizard asks about pages, branding, and design direction
3. You get a production-ready site with components, SEO, and deployment config

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

Once deployed, publish **structured reports** so an operator can see what you produced without reading chat. At the end of any skill that yields a meaningful result — a deployment, a build/audit summary, a content update — call the `mcp__trinity__report` MCP tool. The report appears on this agent's **Reports** tab and the fleet-wide **Operations → Reports** view.

- **When:** at the end of result-producing skills and scheduled runs — not for conversational replies.
- **`report_type`:** namespaced `lower_snake`, shaped `<agent>.<result>` — e.g. `webmaster.deploy`, `webmaster.build_summary`, `webmaster.content_update`.
- **`title`:** one short line (≤300 chars). **`payload`:** a JSON **object** (≤5 MiB serialized — a top-level array or scalar is rejected).
- **`display_hint`:** `table` (`{columns, rows}`), `kpi` (`{tiles:[{label,value,unit?}]}`), `markdown` (`{markdown}`), `timeline` (`{events:[{ts,label,detail}]}`), `json` (raw), or omit to let Trinity infer from `report_type`. Pick deliberately — the customer-facing Workspace Reports tab renders through these same renderers, so a mismatched hint is visible to users.
- **Read before you write:** call `mcp__trinity__list_reports` first (metadata only — filters `report_type`, `hours` ∈ {0,1,6,24,168,720}, `search`) to avoid duplicating or contradicting a report you already filed, then `mcp__trinity__get_report` with an id to diff this period against the last.
- **Guard the call:** the tool exists only when running on Trinity (it publishes under this agent's own key). If `mcp__trinity__report` isn't available — e.g. running locally — skip it silently. **Trinity is an upgrade, not a requirement.**

Reports complement `dashboard.yaml`: the dashboard is the *current* snapshot (overwritten each refresh); reports are an *append-only* history of what the agent accomplished.

### Recommended Plugins

` ` `
/plugin install agent-dev@abilityai   # Create new skills
/plugin install trinity@abilityai     # Deploy to Trinity
[If Vercel + GitHub: /plugin install vercel-mcp                  # Vercel deployment from Claude Code]
` ` `

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the current phase, briefly remind the user: "You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention it once per session, only if there are incomplete steps.

## Project Structure

` ` `
webmaster/
  CLAUDE.md              # This file — agent identity and instructions
  template.yaml          # Trinity metadata
  onboarding.json        # Setup progress tracker
  dashboard.yaml         # Trinity dashboard metrics
  .env.example           # Required environment variables
  .gitignore             # Git exclusions
  .mcp.json.template     # MCP server config template
  .claude/
    skills/
      create-website/
        SKILL.md          # Website scaffolding skill
        reference.md      # Design system patterns and component templates
      onboarding/
        SKILL.md          # Setup progress tracker
      update-dashboard/
        SKILL.md          # Dashboard metrics updater
` ` `

## Artifact Dependency Graph

` ` `yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  create-website/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Website scaffolding workflow — core capability"

  create-website/reference.md:
    mode: prescriptive
    direction: source
    description: "Design system patterns, component templates, Tailwind config"

  onboarding.json:
    mode: descriptive
    direction: target
    sources: [onboarding/SKILL.md]
    description: "Persistent onboarding state — updated by /onboarding skill"

  dashboard.yaml:
    mode: descriptive
    direction: target
    sources: [update-dashboard/SKILL.md]
    description: "Trinity dashboard layout and metrics — updated by /update-dashboard"

  template.yaml:
    mode: prescriptive
    direction: source
    description: "Trinity deployment metadata"
` ` `

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/create-website` | On-demand | Run when starting a new web project |
| `/update-dashboard` | `0 */6 * * *` (every 6 hours) | Keep Trinity dashboard metrics current |

## Guidelines

- **Build complete, not incremental** — every /create-website run produces a fully buildable, deployable site. No half-scaffolded projects.
- **Design system first** — CSS variables and Tailwind config before components. The design system is the foundation everything else inherits.
- **Verify before declaring done** — always run `npm run build` before presenting the summary. If it doesn't build, it's not done.
- **[Site-type specific guideline based on Q1]** — e.g., "SaaS sites must have a clear conversion funnel" or "Portfolios prioritize visual impact over information density"
```

---

## STEP 5: Generate /create-website Skill

Write `[destination]/.claude/skills/create-website/SKILL.md`.

**This is the existing website scaffolding workflow**, customized based on wizard answers:

- If a default design direction was chosen in Q2, set it as the default in Step 2 (still allow override per project)
- If deployment is "GitHub only" or "Manual", shorten/skip Steps 16-19 (Vercel-specific steps)
- Adjust the homepage template suggestions in Step 8 to prioritize the site types from Q1

The generated SKILL.md must contain:

```yaml
---
name: create-website
description: Scaffold a complete, self-contained Next.js 15 website with Tailwind CSS, TypeScript, and Vercel deployment
disable-model-invocation: false
user-invocable: true
argument-hint: "[project-name or description]"
allowed-tools: Read, Write, Edit, Bash, Bash(gh *), Glob, Grep, AskUserQuestion, mcp__vercel__deploy_to_vercel, mcp__vercel__list_teams, mcp__vercel__list_projects, mcp__vercel__get_project, mcp__vercel__list_deployments, mcp__vercel__get_deployment, mcp__vercel__get_deployment_build_logs
metadata:
  version: "1.0"
  created: 2026-04-04
  author: webmaster
---
```

Then include the full 20-step workflow:

### Step 1: Gather Requirements
- Project name, description, pages needed, brand basics, destination
- Use AskUserQuestion

### Step 2: Choose Design Direction
- If Q2 set a default, pre-select it but still allow override
- Options: Minimal Clean, Bold Dark, Warm Professional, Custom

### Step 3: Initialize Project
```bash
npx create-next-app@latest $PROJECT_NAME --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm --yes
npm install motion lucide-react clsx tailwind-merge
```

### Step 4: Create Design System
- CSS variables in `app/globals.css` based on design direction
- Update `tailwind.config.ts` with custom variables and animations
- Reference patterns from reference.md

### Step 5: Create Utility Functions
- `lib/utils.ts` with `cn()` helper (clsx + tailwind-merge)

### Step 6: Create Core Layout Components
- `components/layout/header.tsx` — sticky header with nav and CTA
- `components/layout/footer.tsx` — footer with columns
- `components/layout/mobile-menu.tsx` — slide-out mobile nav
- `components/ui/button.tsx` — primary/secondary variants
- `components/ui/container.tsx` — max-width centered
- `components/ui/section.tsx` — consistent padding

### Step 7: Create Root Layout
- `app/layout.tsx` with Google Fonts, metadata, Header/Footer

### Step 8: Create Homepage
- Sections based on site type (customize per Q1):
  - **SaaS**: Hero, features grid, how it works, pricing, FAQ, CTA
  - **Agency**: Hero, problem/solution, services, testimonials, CTA
  - **Portfolio**: Hero, featured work, about, contact CTA
  - **Docs/Blog**: Hero, featured posts, categories, search

### Step 9: Create Additional Pages
- `app/[page]/page.tsx` for each requested page
- Common: About, Contact, Blog, Pricing

### Step 10: Create Content Data Layer
- `lib/site-data.ts` with typed site config

### Step 11: SEO Setup
- `app/sitemap.ts`, `app/robots.ts`, `app/not-found.tsx`

### Step 12: Vercel Configuration
[If deployment includes Vercel:]
- `vercel.json`, image optimization, cache headers

[If manual/GitHub only:]
- Skip vercel.json, just configure next.config.ts

### Step 13: Create Project CLAUDE.md
- Stack, commands, structure, design system, content management

### Step 14: Verify Build
```bash
npm run build
```

### Step 15: Create GitHub Repository
[If deployment includes GitHub:]
- git init, commit, offer gh repo create

[If manual:]
- git init, commit only

### Steps 16-19: Vercel Deployment
[If deployment is Vercel + GitHub:]
- Check Vercel MCP, deploy, monitor, verify live site

[If deployment is GitHub only or Manual:]
- Skip these steps entirely

### Step 20: Present Summary
- Project name, location, GitHub URL, pages, design, live URL

### Step 21: Publish a report (Trinity)

If the `mcp__trinity__report` tool is available (i.e. running on Trinity), publish the deployment/build result so it lands on the agent's **Reports** tab as an append-only record:

- `report_type`: `webmaster.deploy`
- `title`: `"[Project name] — deployed"` (or `"[Project name] — built"` when deployment was skipped)
- `display_hint`: `markdown`
- `payload`: `{ "markdown": "<the Step 20 summary — project name, live URL, GitHub URL, pages, design direction, build status>" }` (or a `kpi` shape with tiles for pages built, components, and live status).

Skip this step **silently** if the tool isn't available — running locally, the built site and its repo are the deliverable. Reporting is an upgrade, not a requirement.

### Design Direction Presets
Include the CSS variable presets:
- **Minimal Clean** — white, subtle, Inter
- **Bold Dark** — dark, vivid accents, glass, Inter
- **Warm Professional** — warm neutrals, rounded, DM Sans

### Error Handling Table
Include the full error handling table from the original create-website skill.

---

Also write `[destination]/.claude/skills/create-website/reference.md`.

Read the reference.md from the existing website-builder plugin at the **source abilities repo** (`plugins/website-builder/skills/create-website/reference.md`) and copy its full contents into the generated agent's reference.md. This file contains design system variable patterns, Tailwind config templates, and component code templates that the /create-website skill references.

```bash
# Read the reference material from the source plugin
cat [abilities-repo-path]/plugins/website-builder/skills/create-website/reference.md
```

Write this content to `[destination]/.claude/skills/create-website/reference.md`.

---

## STEP 6: Generate Onboarding Tracker

### 6a. Generate onboarding.json

Write `[destination]/onboarding.json`:

**Customize local steps based on deployment choice (Q3):**

```json
{
  "phase": "local",
  "started": "[today's date]",
  "steps": {
    "local": {
      "env_configured": { "done": false, "label": "Configure environment variables (.env)" },
      "first_site_created": { "done": false, "label": "Build your first website (/create-website)" },
      "plugins_installed": { "done": false, "label": "Install recommended plugins (agent-dev)" }
      [If Vercel + GitHub, add:]
      , "vercel_mcp_connected": { "done": false, "label": "Connect Vercel MCP (claude mcp add --transport http vercel https://mcp.vercel.com)" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity:onboard)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via MCP (mcp__trinity__chat_with_agent)" }
    },
    "schedules": {
      "schedules_configured": { "done": false, "label": "Set up scheduled tasks (use MCP schedule tools)" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled execution completed" }
    }
  }
}
```

### 6b. Generate /onboarding skill

Write `[destination]/.claude/skills/onboarding/SKILL.md` following the standard onboarding skill template from the create-wizard specification (Section 8b). Customize:

- Agent name: Webmaster
- Primary skill for `first_site_created` step: `/create-website`
- If Vercel + GitHub deployment: include `vercel_mcp_connected` step guidance (how to add the MCP server)
- Phase transition messages reference website building

---

## STEP 6c: Generate Dashboard

### 6c-i. Generate dashboard.yaml

Write `[destination]/dashboard.yaml`:

```yaml
title: "Webmaster"
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
        description: "Most recent git commit"
      - type: metric
        label: "Sites Managed"
        value: "0"
        description: "Total projects tracked"

  - title: "Portfolio"
    layout: grid
    columns: 3
    widgets:
      - type: metric
        label: "Live"
        value: "0"
        description: "Deployed to production"
        color: green
      - type: metric
        label: "Development"
        value: "0"
        description: "In active development"
        color: blue
      - type: metric
        label: "Recent Deployments"
        value: "0"
        description: "Deployed in last 7 days"

  - title: "Recent Activity"
    layout: list
    widgets:
      - type: list
        title: "Latest Changes"
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

### 6c-ii. Generate /update-dashboard skill

Write `[destination]/.claude/skills/update-dashboard/SKILL.md`:

```yaml
---
name: update-dashboard
description: Refresh dashboard.yaml with current metrics from site and project data
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: webmaster
---
```

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from site directories and project data.

## Process

### Step 1: Gather Metrics

Scan the agent's working area for site projects:
- List directories that contain `package.json` with `next` as a dependency (these are managed sites)
- For each site directory, check:
  - Does it have a `.git` directory? Check `git log --oneline -1` for last commit date
  - Does it have a `vercel.json` or `.vercel/` directory? (indicates live deployment)
  - Check `git log --oneline --since="7 days ago"` for recent activity
- Check recent git activity in the agent root: `git log --oneline -5`

Calculate:
- Total sites managed (count of Next.js project directories)
- Sites by status: live (has Vercel config or remote deployment), development (has git but no deploy config)
- Recent deployments (sites with commits in last 7 days that have deploy config)
- Last activity date (most recent commit across all projects)
- Latest 5 changes for the activity list

### Step 2: Update Dashboard

Read the current `dashboard.yaml`, update widget values:

- "Sites Managed" → total count of site directories
- "Last Activity" → most recent commit date across all projects
- "Live" → count of sites with deployment config (color: green)
- "Development" → count of sites without deployment config (color: blue)
- "Recent Deployments" → count of deployed sites with commits in last 7 days
- "Latest Changes" → last 5 commits across all site projects
- `updated` → current ISO timestamp

Write the updated `dashboard.yaml`.

### Step 3: Confirm

```
Dashboard refreshed:
- Sites managed: [N]
- Live: [N], Development: [N]
- Recent deployments: [N]
- Last updated: [timestamp]
```

## Notes

- On Trinity remote, the dashboard path is `/home/developer/dashboard.yaml`
- This skill is designed to run on a schedule (every 6 hours recommended)
- Keep execution fast — read local files only, no web requests

## Outputs

- Updated `dashboard.yaml` with current metrics
```

---

## STEP 7: Generate Supporting Files

### 7a. template.yaml

Write `[destination]/template.yaml`:

```yaml
name: webmaster
display_name: Webmaster
description: |
  Website management agent that scaffolds production-ready Next.js 15 sites.
  Builds [site types from Q1] with [design from Q2] design direction.
  [If Vercel: Deploys to Vercel via GitHub integration.]
avatar_prompt: A focused web designer at a clean modern desk with a large curved monitor displaying colorful website wireframes and component libraries. Short dark hair, round glasses, wearing a black turtleneck. Warm desk lamp casting amber light. Potted succulents and a ceramic mug nearby. The scene conveys precision, creativity, and quiet expertise. Digital art, clean lines, warm professional palette.
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

# Recommended schedules (design source of truth). Trinity materializes this block
# ON AGENT CREATION, deduplicated by `name` — at most 20 entries, and NEVER re-applied
# on recreate, so a schedule added here after deployment must be created with
# create_agent_schedule (or reconciled by /trinity:onboard | /trinity:sync).
# `enabled` is the recommended default and only a literal YAML true arms a schedule;
# firing ALSO requires the agent's autonomy gate, which is OFF on every new agent.
# timezone: canonical IANA zones only — legacy aliases (Europe/Kiev, Asia/Calcutta,
# US/Eastern) no longer resolve and 500 on schedule create. The container clock is UTC.
# Adjust to fit this agent.
schedules:
  - name: Weekly site health check
    cron: "0 9 * * 1"
    timezone: UTC
    message: "Check deployed sites — build status, broken links, performance regressions, and SSL/cert expiry; report issues."
    purpose: Weekly site health monitoring
    enabled: false
```

### 7b. .env.example

Write `[destination]/.env.example`:

```bash
# Webmaster — Environment Variables
# Copy this to .env and fill in your values

# No API keys required for basic website scaffolding.
# Add keys here as you integrate more tools:

# GitHub token (optional — gh CLI handles auth separately)
# GITHUB_TOKEN=

[If Vercel + GitHub:]
# Vercel token (optional — Vercel MCP handles auth separately)
# VERCEL_TOKEN=
```

### 7c. .gitignore

Write `[destination]/.gitignore`:

```
# Credentials — never commit
.env
.mcp.json

# OS files
.DS_Store
Thumbs.db

# Claude Code
.claude/settings.local.json
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/
.claude/sessions/
.claude/shell-snapshots/
.claude/plugins/
.claude/backups/
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

# Generated websites live in their own repos — don't track them here
```

### 7d. .mcp.json.template

Write `[destination]/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

Note: If the user selected Vercel + GitHub deployment, the onboarding skill will guide them through adding the Vercel MCP server.

---

## STEP 8: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: webmaster"
```

---

## STEP 9: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Want to create a GitHub repository for Webmaster?"
- **Header:** "GitHub"
- **Options:**
  1. **Create private repo** — `gh repo create webmaster --private --source=. --push` (recommended)
  2. **Create public repo** — `gh repo create webmaster --public --source=. --push` — note: an agent Trinity clones from a public repo **without** a GitHub token gets a read-only remote (ent#123). It can `git_pull` but never push, and `git_sync` returns `409 no_write_credentials`. Add a token (Settings → GitHub token) or bind the agent to its own repo if you want it to push its own state back.
  3. **Skip** — I'll set up GitHub later

If `gh` is not available, show manual instructions.

> **Why this matters:** the repo is the deploy path. Trinity deploys an agent by **cloning its GitHub repository** and tracking the branch, so a pushed repo means the deployed agent is a named commit and every later change ships with `git push`. Skipping is fine — deployment falls back to uploading local files — but that agent has no reproducible source until a repo exists.

---

## STEP 10: Offer Trinity Deployment (if connected)

**Default approach:** when this session is already connected to Trinity, deploying the new agent from its repository is the default next action — but it **never happens without explicit confirmation**.

**Detect the connection:** Trinity is connected when the `mcp__trinity__*` MCP tools are available in this session (probe with `mcp__trinity__list_agents`). If more than one Trinity server is connected, confirm which instance the tools reach before offering.

**If Trinity is NOT connected:** skip this step silently — the Completion summary keeps `/trinity:onboard` as the deploy-later path. Trinity is the upgrade, not the gate.

**If Trinity IS connected:** ask for confirmation — never deploy unprompted. Use AskUserQuestion:
- **Question:** "Trinity is connected in this session. Deploy Webmaster to Trinity now from [destination]?"
- **Header:** "Deploy"
- **Options:**
  1. **Yes, deploy now (Recommended)** — deploy from the repository via `/trinity:onboard`
  2. **Not now** — keep it local; deploy later with `/trinity:onboard` from the agent directory

**If confirmed:** set the working directory to `[destination]`, then invoke `/trinity:onboard` (Skill tool). It owns the deployment end-to-end, and it is **repository-first**: with a pushed GitHub remote (Step 9) it deploys via `create_agent(template: "github:owner/repo@branch")` — Trinity clones the repo, tracks the branch, and materializes the `template.yaml` schedules at creation, after which every change ships by `git push` + `git_pull` instead of re-uploading the agent. Without a remote it falls back to a local-file deploy and offers to promote the agent onto the repo path afterwards. Either way it injects credentials and reconciles schedules. Do **not** inline raw `mcp__trinity__create_agent` / `mcp__trinity__deploy_local_agent` calls here — `/trinity:onboard` is the single source of truth for deployment. If `/trinity:onboard` isn't available (trinity plugin not installed), tell the user to run `/plugin install trinity@abilityai` and then `/trinity:onboard` from the agent directory — don't attempt a manual deploy.

**If declined:** move on silently.

**Carry the outcome forward:** if the deploy ran, reflect it in the Completion summary — a `✓ Deployed to Trinity — [instance URL]` line replacing any "deploy later" guidance; otherwise leave the summary as is.

---

## STEP 11: Completion

Display:

```
## Webmaster Installed

Your website management agent is ready.

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity — configured for [site types] |
| `.claude/skills/create-website/SKILL.md` | Full website scaffolding workflow (20 steps) |
| `.claude/skills/create-website/reference.md` | Design system patterns and component templates |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with site metrics |
| `template.yaml` | Trinity deployment metadata |
| `.env.example` | Environment variable template |
| `.gitignore` | Git exclusions |
| `.mcp.json.template` | MCP config template |

### Get Started

1. **Open Webmaster:**
   ```
   cd [destination] && claude
   ```

2. **Run the setup wizard:**
   ```
   /onboarding
   ```

   This will walk you through connecting tools, building your first site,
   and (when you're ready) deploying to Trinity.

3. **Add cross-session durability** (recommended):
   ```
   /agent-dev:add-git-sync
   ```
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn, offer to pick a different path |
| Git not installed | Skip git init, advise `brew install git` |
| User unsure about questions | Provide sensible defaults, allow skipping |
| gh CLI not available | Show manual GitHub repo creation instructions |
| reference.md not found in source plugin | Generate a minimal reference.md with design presets only |
