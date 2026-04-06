---
name: install-recon
description: Create a competitive intelligence agent — asks domain-specific questions and scaffolds a Trinity-compatible agent for tracking competitors, monitoring changes, and producing actionable intelligence
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-06
  author: Ability.ai
---

# Install Recon

Create a **competitive intelligence agent** powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A fully configured agent directory with CLAUDE.md, skills, and Trinity files
- 5 starting skills for competitor tracking, monitoring, battlecards, digests, and landscape analysis
- Persistent competitor watchlist (`competitors.json`) that grows over time
- Ready for local use or Trinity deployment with automated monitoring schedules

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

---

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Recon be installed?"
- **Header:** "Location"
- Show these options:
  1. `~/recon` — Home directory (recommended)
  2. `./recon` — Current directory
  3. Custom path — Let me specify

Default to `~/recon` if no preference.

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

### Q1: Industry / Market

Use AskUserQuestion:
- **Question:** "What industry or market are you in? This shapes which data sources and competitive signals matter most."
- **Header:** "Industry"
- **Options:**
  1. **SaaS / Tech** — Software companies, developer tools, cloud platforms. Tracks: product launches, pricing changes, developer adoption, funding rounds, tech stack signals.
  2. **E-commerce / D2C** — Online retail, consumer brands. Tracks: pricing, promotions, product catalog changes, review sentiment, shipping/fulfillment, social presence.
  3. **Professional Services** — Consulting, agencies, financial services. Tracks: service offerings, thought leadership, key hires, client wins, partnerships.
  4. **Custom** — Let me describe my market.

Store the answer — it customizes: terminology in CLAUDE.md and skills, which tracking dimensions are prioritized, data source recommendations, avatar prompt.

### Q2: Tracking Focus

Use AskUserQuestion:
- **Question:** "What aspects of competitors do you most want to track? Select all that apply."
- **Header:** "Focus"
- **multiSelect: true**
- **Options:**
  1. **Product & feature changes** — New features, deprecations, changelog diffs, integration announcements
  2. **Pricing moves** — Plan changes, discounts, packaging shifts, free-tier adjustments
  3. **Hiring & team growth** — Job postings (investment signals), leadership moves, team size changes
  4. **Funding & financial events** — Fundraising rounds, revenue signals, M&A, SEC filings
  5. **Customer sentiment** — G2/Capterra reviews, Reddit/community chatter, NPS signals, churn indicators
  6. **Content & positioning** — Messaging changes, blog themes, ad copy, SEO keyword shifts, conference talks

Store the answer — it customizes: which signals the `/monitor` skill checks, what goes into `/digest` output, battlecard sections, dashboard metrics.

### Q3: Competitor Count

Use AskUserQuestion:
- **Question:** "How many competitors will you actively track?"
- **Header:** "Scale"
- **Options:**
  1. **2-3** — Focused rivalry. Deep profiles, detailed battlecards, thorough monitoring.
  2. **4-6** — Competitive market. Balanced depth and breadth, weekly digest keeps you current.
  3. **7+** — Crowded landscape. Tiered monitoring — deep on top 3, lighter on the rest.

Store the answer — it customizes: data structure in `competitors.json` (tier field for 7+), digest format (detail level), monitoring depth, battlecard length.

### Q4: Intelligence Output

Use AskUserQuestion:
- **Question:** "How do you want to consume competitive intelligence?"
- **Header:** "Output"
- **Options:**
  1. **Battlecards** — One-page per competitor for sales and product. Strengths, weaknesses, objection handling, trap questions. Best for: sales-driven orgs.
  2. **Weekly digest** — Summary of all changes across competitors. What happened, so what, now what. Best for: staying current without deep dives.
  3. **Feature comparison matrix** — Living feature-by-feature comparison table. Best for: product teams making roadmap decisions.
  4. **All of the above** — Full intelligence stack. Battlecards + digest + matrix, each on its own cadence.

Store the answer — it customizes: which output skills are generated (all 5 skills are always created, but the primary output format in CLAUDE.md and the recommended schedules change), `/digest` format, default cadence recommendations.

---

## STEP 3: Create Agent Directory Structure

```bash
mkdir -p [destination]/.claude/skills/add-competitor
mkdir -p [destination]/.claude/skills/monitor
mkdir -p [destination]/.claude/skills/battlecard
mkdir -p [destination]/.claude/skills/digest
mkdir -p [destination]/.claude/skills/landscape
mkdir -p [destination]/.claude/skills/onboarding
mkdir -p [destination]/.claude/skills/update-dashboard
mkdir -p [destination]/competitors
```

---

## STEP 4: Generate CLAUDE.md

Write `[destination]/CLAUDE.md` with the following content, customized based on wizard answers.

**Industry-specific customization rules:**
- **SaaS / Tech** → emphasize product velocity, developer adoption, API/integration ecosystems, funding signals, tech stack analysis
- **E-commerce / D2C** → emphasize pricing intelligence, catalog breadth, review sentiment, fulfillment speed, social media presence
- **Professional Services** → emphasize service portfolio, thought leadership output, key client wins, talent acquisition, partnership network
- **Custom** → adapt terminology and tracking dimensions to match the user's description

**Focus-specific customization rules:**
- Include tracking dimension sections in CLAUDE.md only for dimensions the user selected in Q2
- The first selected dimension gets "primary signal" status — it leads the digest and battlecard output

**Scale-specific customization rules:**
- **2-3 competitors** → battlecards are detailed (full-page), monitoring is thorough, every change gets noted
- **4-6 competitors** → battlecards are standard, monitoring balances depth and speed, digest groups by significance
- **7+ competitors** → add tier system (Tier 1: deep tracking, Tier 2: headlines only), battlecards for Tier 1 only, digest is summary-first with expandable detail

**Output-specific customization rules:**
- **Battlecards** → CLAUDE.md emphasizes battlecard maintenance cadence (monthly refresh), includes "Battlecard Format" section
- **Weekly digest** → CLAUDE.md emphasizes "so what?" analysis over raw data collection, includes "Digest Format" section
- **Feature matrix** → CLAUDE.md emphasizes structured data collection and comparison methodology
- **All** → include all format sections, with recommended cadences for each

```markdown
# CLAUDE.md

## Identity

You are **Recon** — a competitive intelligence agent that tracks your competitors, monitors their moves, and turns open-source signals into actionable intelligence.

You specialize in [industry from Q1] competitive analysis. You maintain a living watchlist of competitors in `competitors.json`, systematically monitor them for changes, and produce intelligence outputs that help your team make better strategic decisions.

You think like a competitive intelligence analyst — not just collecting data, but answering: "What does this mean for us, and what should we do about it?" Every signal you surface must connect to an action or a decision.

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/add-competitor` | Add a competitor to the watchlist with structured profile data |
| `/monitor` | Scan tracked competitors for changes since last check |
| `/battlecard` | Generate or refresh a one-page battlecard for a competitor |
| `/digest` | Produce a competitive intelligence summary |
| `/landscape` | Full competitive landscape analysis with feature comparison matrix |

## Tracking Dimensions

[Include only dimensions selected in Q2. For each, describe what Recon monitors:]

[If "Product & feature changes" selected:]
### Product & Features
Monitor competitor product changes: new features, deprecations, changelog updates, integration announcements, API changes. Check: product pages, changelogs, release notes, developer docs, status pages.

[If "Pricing moves" selected:]
### Pricing
Monitor pricing changes: plan restructuring, price increases/decreases, packaging shifts, free-tier adjustments, promotional offers. Check: pricing pages (archive snapshots), customer forums, announcement blogs.

[If "Hiring & team growth" selected:]
### Talent & Organization
Monitor hiring signals: new job postings (indicate investment areas), leadership changes, team size growth, Glassdoor/LinkedIn sentiment. Check: career pages, LinkedIn, Glassdoor, press releases.

[If "Funding & financial events" selected:]
### Funding & Financials
Monitor financial events: fundraising rounds, revenue signals, M&A activity, SEC filings, investor changes. Check: Crunchbase, press releases, SEC EDGAR, PitchBook (if available).

[If "Customer sentiment" selected:]
### Customer Sentiment
Monitor customer perception: new reviews on G2/Capterra/TrustRadius, Reddit and community discussions, NPS signals, churn indicators, support complaints. Check: review platforms, Reddit, HackerNews, Twitter/X, community forums.

[If "Content & positioning" selected:]
### Content & Positioning
Monitor go-to-market shifts: homepage messaging changes, blog content themes, ad copy, conference talks, case studies, SEO keyword targeting. Check: competitor websites, blog RSS, LinkedIn company pages, YouTube, social ads (Facebook Ad Library).

## How to Work With This Agent

### Quick Start

1. Add your first competitor: `/add-competitor`
2. Add 2-3 more competitors to build your watchlist
3. Run `/monitor` to do your first competitive scan
4. Generate a battlecard: `/battlecard [competitor-name]`
5. Set up a weekly digest: `/digest`

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

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see
your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the
current phase, briefly remind the user:
"You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention it once per session, only if there are incomplete steps.

### Installed Plugins

These plugins are installed during onboarding (`/onboarding` handles this automatically):

```
/plugin install playbook-builder@abilityai   # Create new skills
/plugin install trinity-onboard@abilityai    # Deploy to Trinity
/plugin install json-memory@abilityai        # Persistent competitor state tracking
/plugin install brain-memory@abilityai       # Research knowledge across sessions
```

## Data Model

### competitors.json

The central watchlist. Each competitor is stored as a structured entry:

```json
{
  "competitors": [
    {
      "name": "Acme Corp",
      "slug": "acme-corp",
      "website": "https://acme.com",
      "tier": 1,
      "industry": "[industry]",
      "description": "What they do in one line",
      "added": "2026-04-06",
      "last_checked": null,
      "tracking": {
        "product_url": "https://acme.com/changelog",
        "pricing_url": "https://acme.com/pricing",
        "careers_url": "https://acme.com/careers",
        "g2_url": "",
        "linkedin_url": "",
        "crunchbase_url": ""
      },
      "notes": ""
    }
  ],
  "settings": {
    "industry": "[industry from Q1]",
    "focus": ["[selected dimensions from Q2]"],
    "scale": "[2-3 | 4-6 | 7+]",
    "output": "[battlecards | digest | matrix | all]"
  }
}
```

### competitors/ directory

Per-competitor intelligence files:
- `competitors/[slug]/battlecard.md` — Latest battlecard
- `competitors/[slug]/history.md` — Change log over time
- `competitors/[slug]/notes.md` — Freeform research notes

## Project Structure

```
recon/
  CLAUDE.md                # This file — agent identity and instructions
  competitors.json         # Competitor watchlist and settings
  onboarding.json          # Setup progress tracker
  dashboard.yaml           # Trinity dashboard metrics
  template.yaml            # Trinity metadata
  .env.example             # Required environment variables
  .gitignore               # Git exclusions
  .mcp.json.template       # MCP server config template
  competitors/             # Per-competitor intelligence files
  .claude/
    skills/
      add-competitor/SKILL.md      # Add competitors to watchlist
      monitor/SKILL.md             # Scan for changes
      battlecard/SKILL.md          # Generate battlecards
      digest/SKILL.md              # Competitive digest
      landscape/SKILL.md           # Full landscape analysis
      onboarding/SKILL.md          # Setup progress tracker
      update-dashboard/SKILL.md    # Dashboard metrics updater
```

## Artifact Dependency Graph

```yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  competitors.json:
    mode: descriptive
    direction: target
    sources: [add-competitor/SKILL.md, monitor/SKILL.md]
    description: "Competitor watchlist — updated by /add-competitor and /monitor"

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

  competitors/*/battlecard.md:
    mode: descriptive
    direction: target
    sources: [battlecard/SKILL.md]
    description: "Per-competitor battlecards — generated by /battlecard"

  competitors/*/history.md:
    mode: descriptive
    direction: target
    sources: [monitor/SKILL.md]
    description: "Competitor change history — appended by /monitor"
```

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/monitor` | `0 8 * * 1-5` (weekday mornings) | Daily competitor change detection |
| `/digest` | `0 9 * * 1` (Monday 9am) | Weekly intelligence summary |
| `/battlecard` | `0 10 1 * *` (1st of month) | Monthly battlecard refresh for all Tier 1 competitors |
| `/update-dashboard` | `0 */6 * * *` (every 6 hours) | Keep Trinity dashboard metrics current |

## Guidelines

- **"So what?" is mandatory** — never report a competitor change without explaining what it means for your team and what action to consider. Raw data without interpretation is noise.
- **Recency is credibility** — prioritize information from the last 90 days. Flag anything older. A battlecard with stale data is worse than no battlecard — it breeds false confidence.
- **Be honest about gaps** — if you can't confirm something, say "unconfirmed" or "not found." Never fabricate competitor details. A wrong competitive claim can lose a deal.
- **Track the trend, not just the event** — a single job posting is noise; 15 ML engineer postings in 3 months is a signal. Connect dots across time.
```

---

## STEP 5: Generate Skills

### 5a. /add-competitor

Write `[destination]/.claude/skills/add-competitor/SKILL.md`:

```yaml
---
name: add-competitor
description: Add a competitor to the watchlist with structured profile data
argument-hint: "<competitor-name>"
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Add Competitor

## Purpose

Add a new competitor to your watchlist in `competitors.json` with structured profile data and tracking URLs.

## Process

### Step 1: Identify the Competitor

If no competitor name was provided as an argument, use AskUserQuestion:
- **Question:** "Which competitor should I add to the watchlist?"
- **Header:** "Competitor"
- **Options:**
  1. Let me type the company name
  2. Paste a URL (website, LinkedIn, Crunchbase)

### Step 2: Research Profile

Search the web for the competitor to gather:
- Official website URL
- One-line description (what they do)
- Key tracking URLs:
  - Product changelog or updates page
  - Pricing page
  - Careers/jobs page
  - G2 or Capterra profile
  - LinkedIn company page
  - Crunchbase profile

### Step 3: Set Tracking Tier

[If scale is 7+ from settings in competitors.json:]
Use AskUserQuestion:
- **Question:** "What tracking tier for [competitor]?"
- **Header:** "Tier"
- **Options:**
  1. **Tier 1** — Deep tracking. Full battlecards, detailed monitoring, every change logged.
  2. **Tier 2** — Headlines only. Key changes tracked, lighter monitoring, summary in digest.

[If scale is 2-3 or 4-6:] Default to Tier 1.

### Step 4: Confirm Profile

Display the gathered profile and ask for confirmation:

```
## Adding: [Competitor Name]

- **Website:** [url]
- **Description:** [one-liner]
- **Tier:** [1 or 2]
- **Tracking URLs:**
  - Changelog: [url or "not found"]
  - Pricing: [url or "not found"]
  - Careers: [url or "not found"]
  - G2: [url or "not found"]
  - LinkedIn: [url or "not found"]
  - Crunchbase: [url or "not found"]
```

Use AskUserQuestion:
- **Question:** "Look good? I can also add notes about this competitor."
- **Header:** "Confirm"
- **Options:**
  1. Add as-is
  2. Let me edit or add notes
  3. Cancel

### Step 5: Update competitors.json

Read `competitors.json`. If it doesn't exist, create it with the structure from the Data Model section in CLAUDE.md.

Add the new competitor entry to the `competitors` array. Set `added` to today's date, `last_checked` to null.

Write updated `competitors.json`.

### Step 6: Create Competitor Directory

```bash
mkdir -p competitors/[slug]
```

Create `competitors/[slug]/history.md`:
```markdown
# [Competitor Name] — Change History

## [Today's date]
- Added to watchlist
```

### Step 7: Confirm

```
Added [Competitor Name] to watchlist.

Watchlist now has [N] competitors.

Next steps:
- Add more competitors: /add-competitor
- Run first scan: /monitor
- Generate battlecard: /battlecard [name]
```

## Outputs

- Updated `competitors.json` with new entry
- Created `competitors/[slug]/` directory with history.md
- Confirmation with next steps
```

### 5b. /monitor

Write `[destination]/.claude/skills/monitor/SKILL.md`:

```yaml
---
name: monitor
description: Scan tracked competitors for changes since last check — product, pricing, hiring, news, sentiment
argument-hint: "[competitor-name or 'all']"
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Monitor Competitors

## Purpose

Scan one or all tracked competitors for changes since the last check. Detects product updates, pricing changes, hiring shifts, funding events, sentiment changes, and positioning moves — based on the tracking dimensions configured in `competitors.json` settings.

## Process

### Step 1: Load Watchlist

Read `competitors.json`. If it doesn't exist, tell the user to run `/add-competitor` first.

If an argument was provided, filter to that competitor. If "all" or no argument, scan all competitors (Tier 1 first if tiered).

### Step 2: Scan Each Competitor

For each competitor, check the tracking dimensions configured in `competitors.json` settings.focus:

**Product & feature changes:**
- Search web for "[competitor name] changelog" OR "[competitor name] new features" OR "[competitor name] release notes" — filter to last 30 days
- If tracking URL exists for changelog, fetch and look for recent entries

**Pricing moves:**
- Search web for "[competitor name] pricing change" OR "[competitor name] new plan"
- If pricing URL exists, search for recent discussions about their pricing

**Hiring & team growth:**
- Search web for "[competitor name] hiring" OR "[competitor name] jobs" — look for volume and roles
- If careers URL exists, search for new postings since last check

**Funding & financial events:**
- Search web for "[competitor name] funding" OR "[competitor name] acquisition" OR "[competitor name] revenue"

**Customer sentiment:**
- Search web for "[competitor name] review" site:g2.com OR site:capterra.com — recent
- Search web for "[competitor name]" site:reddit.com — recent discussions

**Content & positioning:**
- Search web for "[competitor name] announcement" OR "[competitor name] blog" — recent
- Look for messaging shifts, new case studies, conference presence

### Step 3: Classify Changes

For each finding, classify:
- **Signal strength:** High (confirmed, significant) / Medium (noteworthy) / Low (minor or unconfirmed)
- **Dimension:** Which tracking dimension it falls under
- **So what:** One sentence on what this means for the user's team

### Step 4: Update History

For each competitor with changes, append to `competitors/[slug]/history.md`:

```
## [Today's date]
[For each change:]
- **[Dimension]** [Signal: High/Med/Low] — [What changed]. *So what: [implication]*
```

Update `last_checked` in `competitors.json` to today's date.

### Step 5: Report

Display a summary:

```
## Competitive Monitor — [Date]

### [Competitor 1]
- 🔴 [High signal finding + so what]
- 🟡 [Medium signal finding + so what]
- ⚪ [Low signal finding + so what]

### [Competitor 2]
- No significant changes detected since [last_checked]

### [Competitor 3]
...

---
**[N] changes across [M] competitors. [X] high-signal findings.**
```

## Outputs

- Updated `competitors/[slug]/history.md` for each competitor with changes
- Updated `last_checked` timestamps in `competitors.json`
- Console summary with classified findings
```

### 5c. /battlecard

Write `[destination]/.claude/skills/battlecard/SKILL.md`:

```yaml
---
name: battlecard
description: Generate or refresh a one-page competitive battlecard for a specific competitor
argument-hint: "<competitor-name>"
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Battlecard

## Purpose

Generate or refresh a one-page competitive battlecard for a tracked competitor. Battlecards are concise, actionable docs for sales and product teams — not comprehensive research reports.

## Process

### Step 1: Select Competitor

If no argument provided, read `competitors.json` and use AskUserQuestion:
- **Question:** "Which competitor should I create a battlecard for?"
- **Header:** "Competitor"
- Show tracked competitors as options

If the competitor isn't in the watchlist, offer to add them first via `/add-competitor`.

### Step 2: Gather Intelligence

Read existing data:
- `competitors/[slug]/history.md` — past changes and signals
- `competitors/[slug]/battlecard.md` — previous battlecard (if refreshing)
- `competitors/[slug]/notes.md` — any freeform notes

Then do fresh research. Search the web for:
- "[competitor name] vs" — see how they position against alternatives
- "[competitor name] review" — recent customer perspectives
- "[competitor name]" site:[their website] — current messaging and claims
- "[competitor name] strengths weaknesses" — third-party analysis

### Step 3: Generate Battlecard

Write the battlecard in this format:

```
# [Competitor Name] — Battlecard

**Last updated:** [today's date]
**Tier:** [1 or 2]
**Website:** [url]

## Overview
[2-3 sentences: what they do, who they serve, their positioning]

## Their Strengths (be honest)
- [Strength 1 — specific, not generic]
- [Strength 2]
- [Strength 3]

## Their Weaknesses (our opportunities)
- [Weakness 1 — with evidence]
- [Weakness 2]
- [Weakness 3]

## How They Position Against Us
[What do they say about companies like ours? What's their competitive narrative?]

## How We Win Against Them
[2-3 specific angles that work, with talk tracks]

### Trap Questions
Ask prospects these questions that expose competitor weaknesses:
1. "[Question that highlights a known gap]"
2. "[Question about a pain point their customers report]"
3. "[Question about a capability where we're stronger]"

## Objection Handling
| They say... | We respond... |
|------------|---------------|
| "[Common competitor claim]" | "[Our counter with evidence]" |
| "[Another claim]" | "[Counter]" |

## Recent Activity
[From history.md — last 3-5 significant changes]

## Key People
[If known — relevant contacts, leadership, decision-makers we compete against]

---
*Generated by Recon. Refresh monthly or after significant competitor moves.*
```

### Step 4: Save

Write battlecard to `competitors/[slug]/battlecard.md`.

### Step 5: Report

```
Battlecard for [Competitor Name] saved to competitors/[slug]/battlecard.md

Key takeaways:
- Top strength: [their best advantage]
- Top weakness: [their biggest vulnerability]
- Best win angle: [how to beat them]

Refresh recommended: [date — 30 days from now]
```

## Outputs

- `competitors/[slug]/battlecard.md` — complete battlecard
- Console summary with key takeaways
```

### 5d. /digest

Write `[destination]/.claude/skills/digest/SKILL.md`:

```yaml
---
name: digest
description: Produce a competitive intelligence summary of recent changes across all tracked competitors
argument-hint: "[weekly | monthly | custom-period]"
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Competitive Digest

## Purpose

Produce a competitive intelligence summary covering recent changes across all tracked competitors. Designed as a scannable briefing — what happened, so what, now what.

## Process

### Step 1: Determine Period

If an argument was provided, use it (weekly, monthly, or custom). Otherwise default to weekly (last 7 days).

### Step 2: Gather Changes

Read `competitors.json` to get the full watchlist.

For each competitor, read `competitors/[slug]/history.md` and filter to entries within the digest period.

If history is sparse, run a quick web search for each competitor to catch anything missed:
- "[competitor name]" — filter to the digest period

### Step 3: Classify and Rank

Sort all findings by signal strength (High → Medium → Low). Group by theme rather than by competitor when a trend spans multiple competitors.

### Step 4: Generate Digest

```
# Competitive Intelligence Digest

**Period:** [start date] — [end date]
**Competitors tracked:** [N]
**Changes detected:** [N]

## Headlines

[Top 3 most significant findings, each with "So what?" and "Now what?"]

1. **[Finding]** — [Competitor]
   *So what:* [What this means for us]
   *Now what:* [Recommended action]

2. **[Finding]** — [Competitor]
   ...

3. **[Finding]** — [Competitor]
   ...

## By Competitor

### [Competitor 1]
- [Change + classification]
- [Change + classification]

### [Competitor 2]
- No significant changes this period

...

## Trends to Watch

[1-2 cross-competitor patterns or emerging themes]

## Action Items

- [ ] [Specific action based on findings]
- [ ] [Another action]

---
*Generated [today's date] by Recon*
```

### Step 5: Save

Write digest to `competitors/digest-[YYYY-MM-DD].md`.

### Step 6: Report

Display the digest in the console.

```
Digest saved to competitors/digest-[date].md

Summary: [N] changes across [M] competitors. [X] high-signal findings.
Top action item: [most important recommended action]
```

## Outputs

- `competitors/digest-[date].md` — full digest
- Console display of the digest
```

### 5e. /landscape

Write `[destination]/.claude/skills/landscape/SKILL.md`:

```yaml
---
name: landscape
description: Full competitive landscape analysis with feature comparison matrix and strategic positioning map
argument-hint: "[focus-area]"
allowed-tools: Read, Write, Edit, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Competitive Landscape

## Purpose

Produce a comprehensive competitive landscape analysis — a strategic overview of your market with feature comparisons, positioning analysis, and market dynamics. This is the deep-dive you run quarterly, not the weekly monitor.

## Process

### Step 1: Define Scope

Use AskUserQuestion:
- **Question:** "What should this landscape analysis focus on?"
- **Header:** "Focus"
- **Options:**
  1. **Full landscape** — All tracked competitors, all dimensions. Comprehensive quarterly review.
  2. **Feature comparison** — Feature-by-feature matrix across competitors. Best for product roadmap decisions.
  3. **Market positioning** — How each competitor positions themselves, target segments, messaging. Best for marketing/GTM strategy.
  4. **Custom focus** — Let me describe what I'm looking for.

### Step 2: Gather Data

Read all existing competitor data:
- `competitors.json` — watchlist and settings
- `competitors/*/battlecard.md` — existing battlecards
- `competitors/*/history.md` — change history
- `competitors/*/notes.md` — research notes

Then do fresh research for each competitor:
- Company overview, latest news, product updates
- Feature set and capabilities
- Pricing and packaging
- Target market and positioning

### Step 3: Generate Landscape Analysis

[Customize structure based on industry setting and output preference in competitors.json]

```
# Competitive Landscape Analysis

**Date:** [today's date]
**Market:** [industry from settings]
**Competitors analyzed:** [N]

## Executive Summary

[3-5 sentences: state of the competitive landscape, key dynamics, our position]

## Market Map

| Company | Founded | Size | Funding | Target Segment | Primary Strength |
|---------|---------|------|---------|---------------|-----------------|
| [Us] | — | — | — | — | — |
| [Comp 1] | — | — | — | — | — |
| [Comp 2] | — | — | — | — | — |
| ... | — | — | — | — | — |

## Feature Comparison Matrix

| Feature | [Us] | [Comp 1] | [Comp 2] | [Comp 3] |
|---------|------|----------|----------|----------|
| [Feature 1] | ✅ | ✅ | ❌ | ⚠️ |
| [Feature 2] | ✅ | ⚠️ | ✅ | ❌ |
| ... | — | — | — | — |

Legend: ✅ Full support | ⚠️ Partial/limited | ❌ Not available | 🔜 Announced/coming

## Positioning Analysis

### [Competitor 1]
- **Positioning:** [How they describe themselves]
- **Target buyer:** [Who they sell to]
- **Key differentiator:** [What they claim sets them apart]
- **Vulnerability:** [Where they're weakest]

### [Competitor 2]
...

## Pricing Comparison

[Tier-by-tier or plan-by-plan comparison where data is available]

## Market Dynamics

### Trends
- [Trend 1 — with evidence from competitor behavior]
- [Trend 2]

### Threats
- [Emerging threat — new entrant, substitute, etc.]

### Opportunities
- [Gap in the market we can exploit]

## Strategic Recommendations

1. [Recommendation based on competitive gaps]
2. [Recommendation based on positioning opportunity]
3. [Recommendation based on market trend]

---
*Generated [today's date] by Recon. Refresh quarterly.*
```

### Step 4: Save

Write analysis to `competitors/landscape-[YYYY-MM-DD].md`.

### Step 5: Report

Display the full analysis in the console.

## Outputs

- `competitors/landscape-[date].md` — comprehensive landscape analysis
- Feature comparison matrix
- Strategic recommendations
```

---

## STEP 6: Generate Onboarding Tracker

### 6a. Generate onboarding.json

Write `[destination]/onboarding.json`:

```json
{
  "phase": "local",
  "started": "[today's date]",
  "steps": {
    "local": {
      "env_configured": { "done": false, "label": "Configure environment variables (.env)" },
      "first_competitor_added": { "done": false, "label": "Add your first competitor (/add-competitor)" },
      "first_monitor_run": { "done": false, "label": "Run your first competitive scan (/monitor)" },
      "plugins_installed": { "done": false, "label": "Install plugins (playbook-builder, trinity-onboard, json-memory, brain-memory)" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity-onboard)" },
      "credentials_synced": { "done": false, "label": "Sync credentials to remote (/credential-sync push)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via /trinity-remote" }
    },
    "schedules": {
      "schedules_configured": { "done": false, "label": "Set up scheduled tasks (/trinity-schedules)" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled execution completed" }
    }
  }
}
```

### 6b. Generate /onboarding skill

Write `[destination]/.claude/skills/onboarding/SKILL.md`:

```yaml
---
name: onboarding
description: Track your setup progress — shows what's done, what's next, and walks you through each step
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Onboarding

Track and continue your setup progress. This skill reads `onboarding.json`, shows your current status, and walks you through the next incomplete step.

## Process

### Step 1: Load State

Read `onboarding.json` from the agent root directory. If it doesn't exist, inform the user that onboarding is complete or the file was removed.

### Step 2: Show Progress

Display a checklist grouped by phase. Mark the current phase with an arrow. Use checkboxes to show completion:

```
## Recon — Setup Progress

### Phase 1: Local Setup  ← current
- [x] Configure environment variables (.env)
- [ ] Add your first competitor (/add-competitor)
- [ ] Run your first competitive scan (/monitor)
- [ ] Install recommended plugins

### Phase 2: Trinity Deployment
- [ ] Deploy to Trinity
- [ ] Sync credentials to remote
- [ ] Run a skill remotely

### Phase 3: Schedules
- [ ] Set up scheduled tasks
- [ ] Verify first scheduled execution

**Progress: 1/9 complete**
```

### Step 3: Guide Next Step

Identify the first incomplete step in the current phase. Based on which step it is, provide specific guidance:

**For `env_configured`:**
- Check if `.env` exists. If not, guide: `cp .env.example .env` then fill in values.
- List the required variables from `.env.example` and what each one is for.
- After user confirms, mark done.

**For `first_competitor_added`:**
- Tell the user to run `/add-competitor` with their primary competitor.
- Tip: "Start with your #1 competitor — the one that comes up most in deals."
- After they add at least one competitor, mark done.

**For `first_monitor_run`:**
- Tell the user to run `/monitor` to do their first competitive scan.
- After scan completes, mark done.

**For `plugins_installed`:**
- Run the install commands for each plugin:
  ```
  /plugin install playbook-builder@abilityai
  /plugin install trinity-onboard@abilityai
  /plugin install json-memory@abilityai
  /plugin install brain-memory@abilityai
  ```
- Run each install command via Bash. If a plugin fails to install, note the error and continue with the rest.
- After all plugins are attempted, show the results (installed / failed) and mark done.

**For `onboarded` (Trinity phase):**
- Check if trinity-onboard plugin is installed. If not, guide installation.
- Tell user to run `/trinity-onboard`.
- After completion, mark done and advance phase to "trinity".

**For `credentials_synced`:**
- Tell user to run `/credential-sync push`.
- After completion, mark done.

**For `first_remote_run`:**
- Tell user to run `/trinity-remote monitor`.
- After completion, mark done and advance phase to "schedules".

**For `schedules_configured`:**
- Tell user to run `/trinity-schedules` and suggest these schedules:
  - `/monitor` — weekday mornings (`0 8 * * 1-5`)
  - `/digest` — Monday morning (`0 9 * * 1`)
  - `/update-dashboard` — every 6 hours (`0 */6 * * *`)
- After completion, mark done.

**For `first_scheduled_run`:**
- Tell user to check `/trinity-schedules` for execution confirmation.
- After verified, mark done.

### Step 4: Update State

After each step is completed, update `onboarding.json`:
- Set the step's `done` to `true`
- If all steps in current phase are done, advance `phase` to the next phase
- If all phases complete, congratulate the user and note that they can delete `onboarding.json` or keep it as a record

### Step 5: Phase Transitions

When all steps in a phase are complete:

**Local → Trinity:**
```
## Local Setup Complete!

Your Recon agent is fully configured and working locally. You have competitors on your watchlist and have run your first scan.

Ready for the next level? Trinity gives you:
- Automated daily monitoring (run /monitor on a schedule)
- Weekly digest generation (never miss a competitor move)
- Remote access (check competitive intel from anywhere)

Run /onboarding again when you're ready to set up Trinity.
```

**Trinity → Schedules:**
```
## Trinity Deployment Complete!

Your agent is live on Trinity. Now let's automate your competitive monitoring.

Run /onboarding to configure scheduled tasks.
```

**All Complete:**
```
## Onboarding Complete!

Your Recon agent is fully set up:
- ✓ Local environment configured
- ✓ Competitors tracked and monitored
- ✓ Deployed to Trinity
- ✓ Automated schedules running

You're all set. The onboarding.json file can be kept as a record or deleted.
```

## Outputs

- Updated `onboarding.json` with progress
- Step-by-step guidance for the current task
- Phase transition messages at milestones
```

---

## STEP 7: Generate Dashboard

### 7a. Generate dashboard.yaml

Write `[destination]/dashboard.yaml`:

```yaml
title: "Recon"
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
        label: "Competitors Tracked"
        value: "0"
        description: "Total in watchlist"
      - type: metric
        label: "Last Scan"
        value: "—"
        description: "Most recent /monitor run"

  - title: "Intelligence"
    layout: grid
    columns: 3
    widgets:
      - type: metric
        label: "Changes This Week"
        value: "0"
        description: "Across all competitors"
      - type: metric
        label: "High Signals"
        value: "0"
        description: "Requiring attention"
        color: red
      - type: metric
        label: "Battlecards"
        value: "0 / 0"
        description: "Up to date / total"

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

### 7b. Generate /update-dashboard skill

Write `[destination]/.claude/skills/update-dashboard/SKILL.md`:

```yaml
---
name: update-dashboard
description: Refresh dashboard.yaml with current metrics from competitor tracking data
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: recon
---
```

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from competitor tracking data.

## Process

### Step 1: Gather Metrics

Read the agent's data sources:
- `competitors.json` — count competitors, check last_checked dates
- `competitors/*/history.md` — count recent changes (last 7 days), count high-signal findings
- `competitors/*/battlecard.md` — count battlecards, check freshness (>30 days = stale)
- `competitors/digest-*.md` — find most recent digest date
- Recent git activity: `git log --oneline -5`

Calculate:
- Total competitors tracked
- Last scan date (most recent `last_checked` across all competitors)
- Changes this week (count history entries from last 7 days)
- High signals this week (count "High" signal entries from last 7 days)
- Battlecard freshness (up-to-date count / total count)
- Latest 5 changes for the activity list

### Step 2: Update Dashboard

Read the current `dashboard.yaml`, update widget values:

- "Competitors Tracked" → count from competitors.json
- "Last Scan" → most recent last_checked date
- "Changes This Week" → count of recent changes
- "High Signals" → count (color: red if >0, gray if 0)
- "Battlecards" → "[fresh] / [total]"
- "Latest Changes" → last 5 changes from history files
- `updated` → current ISO timestamp

Write the updated `dashboard.yaml`.

### Step 3: Confirm

```
Dashboard refreshed:
- Competitors: [N]
- Changes this week: [N]
- High signals: [N]
- Last updated: [timestamp]
```

## Notes

- On Trinity remote, the dashboard path is `/home/developer/dashboard.yaml`
- This skill is designed to run on a schedule (every 6 hours recommended)
- Keep execution fast — read local files only, no web searches

## Outputs

- Updated `dashboard.yaml` with current metrics
```

---

## STEP 8: Generate Supporting Files

### 8a. Generate competitors.json

Write `[destination]/competitors.json`:

```json
{
  "competitors": [],
  "settings": {
    "industry": "[industry from Q1]",
    "focus": ["[selected dimensions from Q2]"],
    "scale": "[2-3 | 4-6 | 7+ from Q3]",
    "output": "[battlecards | digest | matrix | all from Q4]"
  }
}
```

### 8b. Generate template.yaml

Write `[destination]/template.yaml`:

Customize the avatar_prompt based on industry from Q1:
- **SaaS / Tech** → "A sharp-eyed intelligence analyst in a modern tech office, multiple monitors showing competitor dashboards and market data, dark mode interfaces with glowing charts, focused expression, ambient blue-purple lighting. Short dark hair, smart casual — fitted charcoal sweater over collared shirt. The scene conveys precision, pattern recognition, and strategic thinking. Digital art, clean lines, cinematic lighting."
- **E-commerce / D2C** → "A savvy market analyst surrounded by product catalogs and pricing comparison sheets, bright retail-inspired workspace, dual monitors showing competitor storefronts and trend charts, confident posture, warm modern lighting. Professional but approachable style. Digital art, vibrant colors, clean composition."
- **Professional Services** → "An elegant intelligence analyst in a refined office with dark wood accents, wall of competitor profiles and market positioning maps, warm amber lighting, analytical gaze, tailored blazer. Multiple screens showing relationship maps and competitive data. Digital art, sophisticated palette, professional atmosphere."
- **Custom** → Adapt to the described market

```yaml
name: recon
display_name: Recon
description: |
  Competitive intelligence agent for [industry from Q1].
  Tracks [N] competitors across [selected dimensions from Q2],
  produces [output format from Q4], and keeps your team informed
  with actionable intelligence.
avatar_prompt: [industry-specific prompt from above]
resources:
  cpu: "2"
  memory: "4g"
```

### 8c. Generate .env.example

Write `[destination]/.env.example`:

```bash
# Recon — Environment Variables
# Copy this to .env and fill in your values

# No API keys required for basic operation.
# Recon uses web search and public sources by default.

# Optional: Add API keys for richer data sources
# CRUNCHBASE_API_KEY=
# BUILTWITH_API_KEY=
```

### 8d. Generate .gitignore

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
```

### 8e. Generate .mcp.json.template

Write `[destination]/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

---

## STEP 9: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: recon"
```

---

## STEP 10: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Want to create a GitHub repository for Recon?"
- **Header:** "GitHub"
- **Options:**
  1. **Create private repo** — `gh repo create recon --private --source=. --push` (recommended)
  2. **Create public repo** — `gh repo create recon --public --source=. --push`
  3. **Skip** — I'll set up GitHub later

If option 1 or 2, run the command. If `gh` is not available, show manual instructions.

---

## STEP 11: Completion

Display this summary:

```
## Recon Installed

Your competitive intelligence agent is ready.

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity — customized for [industry] competitive analysis |
| `.claude/skills/add-competitor/SKILL.md` | Add competitors to watchlist |
| `.claude/skills/monitor/SKILL.md` | Scan for competitive changes |
| `.claude/skills/battlecard/SKILL.md` | Generate sales battlecards |
| `.claude/skills/digest/SKILL.md` | Weekly intelligence digest |
| `.claude/skills/landscape/SKILL.md` | Full landscape analysis |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `competitors.json` | Competitor watchlist and settings |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with CI metrics |
| `template.yaml` | Trinity deployment metadata |
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

   This will walk you through adding your first competitors,
   running your first scan, and (when you're ready) deploying to Trinity.
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn, offer alternatives |
| Git not installed | Skip git init, advise install |
| User unsure about questions | Provide sensible defaults, allow skipping |
| gh CLI not available | Show manual GitHub instructions |
| No competitors to monitor | Guide to /add-competitor first |
| Web search rate limited | Note in output, suggest retry later |
