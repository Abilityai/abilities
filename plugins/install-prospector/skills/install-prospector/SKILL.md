---
name: install-prospector
description: Create a B2B SaaS sales research agent — asks domain-specific questions and scaffolds a Trinity-compatible prospector agent customized to your sales stack
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-04
  author: Ability.ai
---

# Install Prospector

Create a **B2B SaaS sales research agent** powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A fully configured agent directory with CLAUDE.md, skills, and Trinity files
- 2 starting skills tailored to B2B SaaS company research
- Ready for local use or Trinity deployment

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

---

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Prospector be installed?"
- **Header:** "Location"
- Show these options:
  1. `~/prospector` — Home directory (recommended)
  2. `./prospector` — Current directory
  3. Custom path — Let me specify

Default to `~/prospector` if no preference.

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

Ask these 4 questions to customize the agent. Each answer directly shapes the generated files.

### Q1: ICP Segment

Use AskUserQuestion:
- **Question:** "What's your ideal customer profile (ICP) segment?"
- **Header:** "ICP"
- **Options:**
  1. **SMB SaaS** — Early-stage, <100 employees, seed to Series A. Research focuses on founders, product-market fit signals, tech stack.
  2. **Mid-Market SaaS** — 100-1000 employees, Series B-D. Research focuses on department heads, growth trajectory, competitive landscape.
  3. **Enterprise SaaS** — 1000+ employees, public or late-stage. Research focuses on org structure, procurement signals, strategic initiatives.
  4. **Custom** — Let me define my own ICP criteria.

Store the answer — it customizes: research depth, data points prioritized, scoring criteria in CLAUDE.md and `/score-fit`.

### Q2: Research Tools

Use AskUserQuestion:
- **Question:** "Which research tools do you have access to? Select all that apply."
- **Header:** "Tools"
- **multiSelect: true**
- **Options:**
  1. **Apollo.io** — Contact and company data, email sequences
  2. **LinkedIn Sales Navigator** — Advanced search, lead lists, InMail
  3. **Crunchbase** — Funding rounds, investors, company financials
  4. **ZoomInfo** — Org charts, intent data, technographics

Store the answer — it customizes: `.env.example` (API keys), `.mcp.json.template` (tool configs), research instructions in skills.

### Q3: CRM

Use AskUserQuestion:
- **Question:** "What CRM does your team use?"
- **Header:** "CRM"
- **Options:**
  1. **Salesforce** — Enterprise CRM with robust API
  2. **HubSpot** — Marketing-first CRM, free tier available
  3. **Pipedrive** — Pipeline-focused, popular with SMB sales teams
  4. **None / Other** — No CRM or something else

Store the answer — it customizes: output format guidance in CLAUDE.md, field mapping notes in research skill.

### Q4: Research Priority

Use AskUserQuestion:
- **Question:** "When researching a company, what matters most to your team?"
- **Header:** "Priority"
- **Options:**
  1. **Funding & financials** — Runway, burn rate, recent raises, investor quality
  2. **Tech stack & tools** — What they use, what they might replace, integration opportunities
  3. **Org structure & key people** — Decision-makers, reporting lines, new hires
  4. **Recent news & triggers** — Product launches, expansions, leadership changes, pain signals

Store the answer — it customizes: which data points get top billing in research output, scoring weight in `/score-fit`.

---

## STEP 3: Create Agent Directory Structure

```bash
mkdir -p [destination]/.claude/skills/research-company
mkdir -p [destination]/.claude/skills/score-fit
```

---

## STEP 4: Generate CLAUDE.md

Write `[destination]/CLAUDE.md` with the following content, customized based on wizard answers.

**ICP-specific customization rules:**
- **SMB SaaS** → emphasize founder backgrounds, product-market fit signals, hiring velocity, tech stack modernity
- **Mid-Market SaaS** → emphasize growth metrics, department structure, competitive positioning, expansion signals
- **Enterprise SaaS** → emphasize org hierarchy, procurement cycles, strategic initiatives, vendor consolidation trends

**Tool-specific customization rules:**
- For each tool selected in Q2, add a bullet under "Research Sources" describing how the agent should use it
- Only reference tools the user actually has access to

**CRM-specific customization rules:**
- **Salesforce** → structure output to map to Account/Contact/Opportunity fields
- **HubSpot** → structure output to map to Company/Contact/Deal properties
- **Pipedrive** → structure output to map to Organization/Person/Deal fields
- **None** → output as clean markdown briefs

**Priority-specific customization rules:**
- The research priority from Q4 determines what appears first in research output and carries the most weight in scoring

```markdown
# CLAUDE.md

## Identity

You are **Prospector** — a B2B SaaS sales research agent that helps SDRs and BDRs deeply understand target companies before outreach.

You specialize in researching [ICP segment from Q1] companies. You pull data from [tools from Q2], synthesize it into actionable intelligence, and format it so your team can use it immediately.

You think like a top-performing SDR who does their homework. Every piece of research you surface should answer: "Why should we reach out to this company, and what should we say?"

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/research-company` | Deep-dive company research — [priority from Q4], plus supporting data |
| `/score-fit` | Score a company against your [ICP from Q1] criteria |

## Research Sources

[For each tool selected in Q2, add a line:]
- **[Tool name]** — [How the agent uses this tool for research]

[If no tools selected, add:]
- **Web research** — Public sources, company websites, press releases, job boards

## How to Work With This Agent

### Quick Start

1. Run `/research-company Acme Corp` to get a full company brief
2. Run `/score-fit Acme Corp` to see how well they match your ICP
3. Use the research to personalize your outreach

### Creating New Skills

This agent uses **playbooks** — structured skill definitions that live in `.claude/skills/`. To create new capabilities:

1. Install the playbook builder: `/plugin install playbook-builder@abilityai`
2. Run `/create-playbook` and follow the guided flow
3. The new skill becomes available as a slash command immediately

### Deploying to Trinity

To run this agent remotely (scheduled tasks, always-on, API access):

1. Install Trinity tools: `/plugin install trinity-onboard@abilityai`
2. Run `/trinity-onboard` to deploy
3. Use `/trinity-remote` to interact with the remote instance

Learn more at [ability.ai](https://ability.ai)

### Recommended Plugins

```
/plugin install playbook-builder@abilityai   # Create new skills
/plugin install trinity-onboard@abilityai    # Deploy to Trinity
/plugin install brain-memory@abilityai       # Remember research across sessions
```

## Project Structure

```
prospector/
  CLAUDE.md              # This file — agent identity and instructions
  template.yaml          # Trinity metadata
  .env.example           # Required environment variables
  .gitignore             # Git exclusions
  .mcp.json.template     # MCP server config template
  .claude/
    skills/
      research-company/SKILL.md  # Company research skill
      score-fit/SKILL.md         # ICP fit scoring skill
```

## Artifact Dependency Graph

```yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  research-company/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Company research workflow — core capability"

  score-fit/SKILL.md:
    mode: prescriptive
    direction: source
    description: "ICP scoring criteria and methodology"

  template.yaml:
    mode: prescriptive
    direction: source
    description: "Trinity deployment metadata"
```

## Output Format

[Customize based on CRM from Q3:]

[If Salesforce:] Structure research output to align with Salesforce Account fields — Industry, Annual Revenue, Number of Employees, Description, and custom fields your team uses.

[If HubSpot:] Structure research output to align with HubSpot Company properties — industry, revenue, employee count, description, and lifecycle stage signals.

[If Pipedrive:] Structure research output to align with Pipedrive Organization fields — keep it concise and pipeline-focused.

[If None:] Output clean markdown briefs with clear sections. Prioritize scannability — SDRs read fast.

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/research-company` | On-demand | Run before calls, demos, or outreach sequences |
| `/score-fit` | On-demand | Score new inbound leads or prospect lists |

## Guidelines

- **Lead with the "so what"** — every research finding should connect to a reason to reach out or a talk track. Raw data without insight is noise.
- **Recency matters** — prioritize information from the last 6 months. Stale data kills credibility.
- **Be honest about gaps** — if you can't find data, say so. Don't hallucinate company details. A confident wrong fact is worse than admitting "I couldn't confirm this."
- **[Priority from Q4] comes first** — always lead your research output with [the priority area], then fill in supporting context.
```

---

## STEP 5: Generate Skills

### 5a. /research-company

Write `[destination]/.claude/skills/research-company/SKILL.md`:

**Customize based on wizard answers:**
- ICP segment determines research depth and focus areas
- Tools determine where to look for data
- Priority determines what gets top billing in the output
- CRM determines output structure

```yaml
---
name: research-company
description: Deep-dive research on a B2B SaaS company — pulls data from available sources and synthesizes an actionable brief
argument-hint: "<company-name>"
allowed-tools: Read, Write, Bash, WebSearch, WebFetch, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: prospector
---
```

```markdown
# Research Company

## Purpose

Research a B2B SaaS company and produce an actionable brief for SDR/BDR outreach preparation.

## Process

### Step 1: Identify the Company

If no company name was provided as an argument, use AskUserQuestion:
- **Question:** "Which company should I research?"
- **Header:** "Company"
- **Options:**
  1. Let me type the company name
  2. Paste a URL (company website, LinkedIn, Crunchbase)

### Step 2: Gather Data

Research the company using available sources. Search the web for:

[Customize this list based on ICP and priority from wizard answers]

**[If priority is Funding & financials:]**
1. **Funding history** — rounds, amounts, investors, valuation signals
2. **Revenue indicators** — employee count trends, job postings, pricing page analysis
3. **Burn rate signals** — recent layoffs, office downsizing, aggressive hiring
4. **Financial health** — profitability signals, runway estimates

**[If priority is Tech stack & tools:]**
1. **Known tech stack** — from job postings, BuiltWith, GitHub, case studies
2. **Tools they use** — integrations page, partner listings, review sites
3. **What they might replace** — complaints on G2/Capterra, outdated tech mentions
4. **Integration opportunities** — where your product fits in their stack

**[If priority is Org structure & key people:]**
1. **Leadership team** — C-suite, VPs, directors with LinkedIn profiles
2. **Org structure** — department sizes, reporting lines, recent reorgs
3. **New hires** — recent executive hires signal strategic shifts
4. **Decision-makers** — who owns budget for your product category

**[If priority is Recent news & triggers:]**
1. **Product launches** — new features, pivots, market expansion
2. **Press coverage** — media mentions, awards, analyst reports
3. **Leadership changes** — new CEO/CRO/CTO = new priorities
4. **Pain signals** — negative reviews, outage reports, regulatory issues

Then gather supporting data across all other categories.

### Step 3: Synthesize Brief

Produce a structured research brief:

```
## [Company Name] — Research Brief

**One-liner:** [What they do in ≤15 words]
**ICP Fit:** [High / Medium / Low] — [one sentence why]

### [Priority area from Q4 — LEAD SECTION]
[Detailed findings for the user's top priority]

### Company Overview
- **Founded:** [year]
- **HQ:** [location]
- **Employees:** [count + trend]
- **Industry:** [specific niche]
- **Website:** [url]

### Funding & Financials
[If available — rounds, investors, estimated revenue]

### Tech Stack & Tools
[If available — known technologies, integrations]

### Key People
[Relevant contacts — name, title, LinkedIn URL, notable background]

### Recent Activity
[Last 6 months — news, launches, hires, changes]

### Outreach Angles
1. [Specific angle based on research — why they'd care about your product]
2. [Second angle — different entry point or pain signal]
3. [Third angle — timely trigger or connection point]

### Sources
[List URLs used for this research]
```

### Step 4: Save Brief

Write the brief to `[agent-directory]/research/[company-name-slugified].md`.

```bash
mkdir -p research
```

Report the file location to the user.

## Outputs

- Markdown research brief saved to `research/[company].md`
- Console summary with ICP fit assessment and top outreach angles
```

### 5b. /score-fit

Write `[destination]/.claude/skills/score-fit/SKILL.md`:

**Customize scoring criteria based on ICP segment from Q1:**
- **SMB SaaS** → weight: team size <100, recent funding, founder-led, modern tech stack
- **Mid-Market SaaS** → weight: 100-1000 employees, Series B+, departmentalized, growth signals
- **Enterprise SaaS** → weight: 1000+ employees, established procurement, multi-year contracts, global presence

```yaml
---
name: score-fit
description: Score a company against your ICP criteria to prioritize outreach
argument-hint: "<company-name>"
allowed-tools: Read, Write, Bash, WebSearch, WebFetch, Glob, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: prospector
---
```

```markdown
# Score Fit

## Purpose

Score a B2B SaaS company against your ICP criteria to help prioritize outreach.

## Process

### Step 1: Get Company

If no company name was provided as an argument, use AskUserQuestion:
- **Question:** "Which company should I score?"
- **Header:** "Company"
- **Options:**
  1. Let me type the company name
  2. Score from existing research (check `research/` directory)

If scoring from existing research, read the most recent brief from `research/`.

### Step 2: Gather or Load Data

If a research brief exists in `research/[company].md`, load it. Otherwise, do a lightweight research pass (company website, LinkedIn, Crunchbase) to gather enough data to score.

### Step 3: Score Against ICP

[Customize criteria based on ICP segment from Q1]

**[If SMB SaaS:]**
Score on a 1-5 scale for each criterion:

| Criterion | Weight | What to look for |
|-----------|--------|-------------------|
| Team size | 20% | <100 employees, ideally 10-50 |
| Funding stage | 20% | Seed to Series A, recently funded = bonus |
| Tech stack fit | 20% | Modern stack, likely to adopt new tools |
| Growth signals | 20% | Hiring, product launches, expanding |
| Founder accessibility | 20% | Founder-led sales, active on LinkedIn/Twitter |

**[If Mid-Market SaaS:]**
| Criterion | Weight | What to look for |
|-----------|--------|-------------------|
| Company size | 20% | 100-1000 employees |
| Funding/revenue stage | 20% | Series B-D, $10M-$100M ARR signals |
| Department structure | 20% | Clear department owning your product area |
| Growth trajectory | 20% | Revenue growth, hiring in relevant teams |
| Competitive landscape | 20% | Using a competitor or underserved in your category |

**[If Enterprise SaaS:]**
| Criterion | Weight | What to look for |
|-----------|--------|-------------------|
| Company size | 15% | 1000+ employees |
| Budget signals | 20% | Known tech spend, procurement team exists |
| Strategic alignment | 25% | Your product fits their stated initiatives |
| Champion access | 20% | Can you reach a decision-maker or influencer? |
| Timing signals | 20% | Contract renewals, fiscal year, reorg, new leadership |

### Step 4: Generate Scorecard

```
## [Company Name] — ICP Fit Scorecard

**Overall Score: [X]/5 — [Excellent / Good / Moderate / Weak / Poor] Fit**

| Criterion | Score | Evidence |
|-----------|-------|----------|
| [criterion] | [1-5] | [one-line evidence] |
| ... | ... | ... |

### Verdict
[2-3 sentences: should the SDR prioritize this company? Why or why not?]

### Recommended Next Step
[Specific action: research deeper, reach out to [person], skip, revisit in Q[X]]
```

### Step 5: Save Scorecard

Append or write the scorecard to `research/[company-name-slugified]-score.md`.

## Outputs

- ICP fit scorecard with 1-5 scoring per criterion
- Overall recommendation (prioritize / deprioritize / revisit)
- Saved to `research/[company]-score.md`
```

---

## STEP 6: Generate Supporting Files

### 6a. template.yaml

Write `[destination]/template.yaml`:

```yaml
name: prospector
display_name: Prospector
description: |
  B2B SaaS sales research agent for [ICP from Q1] companies.
  Pulls data from [tools from Q2], synthesizes actionable briefs,
  and scores companies against your ICP criteria.
avatar_prompt: A sharp-eyed young professional in smart business casual — navy blazer over a crisp white shirt, no tie. Short styled hair, confident half-smile. Sitting at a modern desk with dual monitors showing company dashboards and org charts. Warm office lighting with a city skyline visible through floor-to-ceiling windows. The scene conveys intelligence, preparation, and quiet ambition. Digital art, clean lines, professional color palette.
resources:
  cpu: "2"
  memory: "4g"
```

### 6b. .env.example

Write `[destination]/.env.example`:

```bash
# Prospector — Environment Variables
# Copy this to .env and fill in your values

[If Apollo selected:]
# Apollo.io API key — get from https://app.apollo.io/#/settings/integrations/api
APOLLO_API_KEY=

[If LinkedIn Sales Navigator selected:]
# LinkedIn credentials (for Sales Navigator access)
# Note: LinkedIn doesn't offer a public API — Prospector uses web research as a supplement
LINKEDIN_EMAIL=
LINKEDIN_PASSWORD=

[If Crunchbase selected:]
# Crunchbase API key — get from https://data.crunchbase.com/docs/using-the-api
CRUNCHBASE_API_KEY=

[If ZoomInfo selected:]
# ZoomInfo API credentials — get from your ZoomInfo admin
ZOOMINFO_USERNAME=
ZOOMINFO_PASSWORD=

[If no tools selected:]
# No API keys required — Prospector uses web research
# Add API keys here as you integrate more tools
```

### 6c. .gitignore

Write `[destination]/.gitignore`:

```
# Credentials — never commit
.env
.mcp.json

# Research output (optional — uncomment to track research in git)
# research/

# OS files
.DS_Store
Thumbs.db

# Claude Code
.claude/settings.local.json
```

### 6d. .mcp.json.template

Write `[destination]/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

Note: MCP server entries should be added here as the user integrates specific tools. The base template starts empty since Prospector primarily uses web research and CLI tools.

---

## STEP 7: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: prospector"
```

---

## STEP 8: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Want to create a GitHub repository for Prospector?"
- **Header:** "GitHub"
- **Options:**
  1. **Create private repo** — `gh repo create prospector --private --source=. --push` (recommended)
  2. **Create public repo** — `gh repo create prospector --public --source=. --push`
  3. **Skip** — I'll set up GitHub later

If option 1 or 2, run the command. If `gh` is not available, show manual instructions.

---

## STEP 9: Completion

Display this summary:

```
## Prospector Installed

Your B2B SaaS sales research agent is ready.

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity — customized for [ICP] research |
| `.claude/skills/research-company/SKILL.md` | Deep-dive company research |
| `.claude/skills/score-fit/SKILL.md` | ICP fit scoring |
| `template.yaml` | Trinity deployment metadata |
| `.env.example` | API key template for [tools] |
| `.gitignore` | Excludes credentials and OS files |
| `.mcp.json.template` | MCP server config template |

### Next Steps

1. **Open Prospector:**
   ```
   cd [destination] && claude
   ```

2. **Try your first research:**
   ```
   /research-company [a company you're prospecting]
   ```

3. **Score a lead:**
   ```
   /score-fit [company name]
   ```

4. **Install recommended plugins:**
   ```
   /plugin install playbook-builder@abilityai
   /plugin install trinity-onboard@abilityai
   /plugin install brain-memory@abilityai
   ```

5. **Deploy to Trinity** (when ready):
   ```
   /trinity-onboard
   ```

Happy prospecting!
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn, offer to pick a different path |
| Git not installed | Skip git init, advise `brew install git` |
| User unsure about questions | Provide sensible defaults, allow skipping |
| gh CLI not available | Show manual GitHub repo creation instructions |
| No research tools selected | Default to web-only research — still fully functional |
