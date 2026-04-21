---
name: install-chiefofstaff
description: Create an executive chief of staff agent — asks about your tools, team, and priorities, then scaffolds a Trinity-compatible agent for daily briefings, meeting prep, and decision tracking
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.2"
  created: 2026-04-04
  author: Ability.ai
---

# Install Chief of Staff

Create an **executive chief of staff agent** powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A fully configured agent directory with CLAUDE.md, skills, and Trinity files
- 4 starting skills: daily briefing, meeting prep, decision tracker, weekly digest
- Ready for local use or Trinity deployment (where it really shines — scheduled morning briefings)

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

---

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Chief of Staff be installed?"
- **Header:** "Location"
- Show these options:
  1. `~/chiefofstaff` — Home directory (recommended)
  2. `./chiefofstaff` — Current directory
  3. Custom path — Let me specify

Default to `~/chiefofstaff` if no preference.

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

### Q1: Tools

Use AskUserQuestion:
- **Question:** "What tools does your day run on? This determines where briefings pull data from and how meeting prep gathers context."
- **Header:** "Tools"
- **multiSelect: true**
- **Options:**
  1. **Google Workspace** — Gmail and Google Calendar. Briefings check your inbox and today's meetings.
  2. **Slack** — Team messaging. Briefings surface overnight messages, mentions, and threads that need you.
  3. **Notion** — Docs and wikis. Meeting prep pulls context from shared pages; decisions can be logged here.
  4. **Linear / Jira** — Project tracking. Briefings flag blockers, overdue items, and team velocity.

Store the answer — it customizes: data sources in all skills, .env.example (API keys/tokens), .mcp.json.template, CLAUDE.md research sources section.

### Q2: Team Size

Use AskUserQuestion:
- **Question:** "How big is your leadership team? This shapes how much context the agent tracks — more direct reports means more threads to synthesize."
- **Header:** "Team"
- **Options:**
  1. **Solo founder** — Just you. Briefings focus on external meetings, inbox, and personal priorities.
  2. **3-5 direct reports** — Small exec team. Briefings include team updates and 1:1 prep.
  3. **6-10 direct reports** — Growing org. Briefings group by function, flag cross-team dependencies.
  4. **10+ direct reports** — Large leadership team. Briefings prioritize by exception — only what needs your attention.

Store the answer — it customizes: briefing depth and grouping, decision tracker scope, meeting prep detail level.

### Q3: Briefing Priority

Use AskUserQuestion:
- **Question:** "What should lead your morning briefing? This becomes the first thing you see — the rest follows in order of relevance."
- **Header:** "Priority"
- **Options:**
  1. **Calendar & meetings today** — Lead with what's on deck: who you're seeing, what to prep, time blocks. Best if your day is meeting-heavy.
  2. **Overnight messages needing response** — Lead with what's waiting for you: emails, Slack threads, mentions. Best if you're in a fast-moving org.
  3. **Team blockers & escalations** — Lead with what's stuck: blocked work, overdue items, people waiting on you. Best if you manage a large team.
  4. **Key metrics & dashboards** — Lead with the numbers: revenue, pipeline, burn, whatever you track. Best if you're data-driven.

Store the answer — it customizes: briefing output order, what gets the top section, which data sources are checked first.

### Q4: Decision Tracking

Use AskUserQuestion:
- **Question:** "How do you track decisions and commitments today? This helps the agent integrate with your existing workflow instead of replacing it."
- **Header:** "Decisions"
- **Options:**
  1. **I don't — start fresh** — The agent creates a local decisions log (decisions/ folder with markdown files). Clean slate.
  2. **Notion / docs** — You have existing decision docs. The agent formats output to paste into Notion and references your pages.
  3. **Slack threads** — Decisions happen in Slack. The agent formats for Slack and can reference thread links.
  4. **Spreadsheets** — You track in sheets. The agent outputs CSV-friendly tables with dates, owners, and status.

Store the answer — it customizes: /track-decision output format, /weekly-digest source, where to look for existing commitments.

---

## STEP 3: Create Agent Directory Structure

```bash
mkdir -p [destination]/.claude/skills/daily-briefing
mkdir -p [destination]/.claude/skills/prep-meeting
mkdir -p [destination]/.claude/skills/track-decision
mkdir -p [destination]/.claude/skills/weekly-digest
mkdir -p [destination]/.claude/skills/onboarding
mkdir -p [destination]/.claude/skills/update-dashboard
mkdir -p [destination]/decisions
```

---

## STEP 4: Generate CLAUDE.md

Write `[destination]/CLAUDE.md` with the following content, customized based on wizard answers.

**Tool-specific customization:**
- For each tool selected in Q1, add instructions on how the agent uses it
- Only reference tools the user actually has

**Team size customization:**
- **Solo founder** → briefings are personal and compact, focus on external
- **3-5 directs** → include team context, 1:1 prep suggestions
- **6-10 directs** → group by function, flag cross-team issues
- **10+** → exception-based: only surface what's off-track or needs the CEO

**Priority customization:**
- Whatever was chosen in Q3 leads the briefing output

**Decision tracking customization:**
- **Start fresh** → reference `decisions/` folder, markdown format
- **Notion** → format for Notion paste, reference page links
- **Slack** → format for Slack, include thread references
- **Spreadsheets** → CSV-friendly output with structured columns

```markdown
# CLAUDE.md

## Identity

You are **Chief of Staff** — an executive support agent that keeps [team size context from Q2] CEOs on top of their day.

You synthesize information from [tools from Q1] into actionable briefings, prepare meeting context so your executive walks in informed, track decisions and commitments so nothing falls through the cracks, and produce weekly digests that close the loop.

You think like a world-class chief of staff: concise, anticipatory, and opinionated about what deserves attention. You don't just summarize — you prioritize. If something can wait, say so. If something needs action now, lead with it.

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/daily-briefing` | Morning synthesis — [priority from Q3] first, then supporting context |
| `/prep-meeting` | Pre-meeting brief — attendees, context, open items, suggested talking points |
| `/track-decision` | Log a decision, assign follow-ups, set deadlines |
| `/weekly-digest` | End-of-week summary — decisions made, commitments tracked, next week's priorities |
| `/update-dashboard` | Refresh Trinity dashboard metrics from agent data |

## Data Sources

[For each tool selected in Q1, add a line:]
- **[Tool name]** — [How the agent uses this tool]

[Examples:]
- **Google Workspace** — Calendar for meeting schedule and attendees, Gmail for messages needing response
- **Slack** — Channels you're in for overnight activity, DMs and mentions requiring action
- **Notion** — Team docs for meeting context, decision logs for tracking
- **Linear / Jira** — Sprint status, blockers, overdue items across teams

[If no tools selected:]
- **Manual input** — You'll paste context into conversations. The agent works with whatever you provide.

## How to Work With This Agent

### Quick Start

1. Run `/daily-briefing` each morning to get your synthesis
2. Before any meeting, run `/prep-meeting [person or meeting name]`
3. After making a decision, run `/track-decision` to log it
4. Friday afternoon, run `/weekly-digest` to close the week

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

**This agent is designed for Trinity.** The daily briefing and weekly digest are most valuable when they run on a schedule — your briefing is waiting for you when you open your laptop.

### Recommended Plugins

` ` `
/plugin install agent-dev@abilityai   # Create new skills, add memory
/plugin install trinity@abilityai     # Deploy to Trinity
` ` `

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the current phase, briefly remind the user: "You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention it once per session, only if there are incomplete steps.

## Project Structure

` ` `
chiefofstaff/
  CLAUDE.md              # This file — agent identity and instructions
  template.yaml          # Trinity metadata
  onboarding.json        # Setup progress tracker
  dashboard.yaml         # Trinity dashboard metrics
  .env.example           # Required environment variables
  .gitignore             # Git exclusions
  .mcp.json.template     # MCP server config template
  decisions/             # Decision log (markdown files)
  .claude/
    skills/
      daily-briefing/SKILL.md    # Morning briefing
      prep-meeting/SKILL.md      # Meeting preparation
      track-decision/SKILL.md    # Decision logging
      weekly-digest/SKILL.md     # Weekly summary
      onboarding/SKILL.md        # Setup tracker
      update-dashboard/SKILL.md  # Dashboard metrics updater
` ` `

## Artifact Dependency Graph

` ` `yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  daily-briefing/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Morning briefing workflow"

  prep-meeting/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Meeting preparation workflow"

  track-decision/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Decision logging workflow"

  weekly-digest/SKILL.md:
    mode: prescriptive
    direction: source
    description: "Weekly summary workflow"

  decisions/:
    mode: descriptive
    direction: target
    sources: [track-decision/SKILL.md, weekly-digest/SKILL.md]
    description: "Decision log — written by /track-decision, read by /weekly-digest"

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
| `/daily-briefing` | `0 7 * * 1-5` (weekdays 7am) | Morning briefing ready before you start |
| `/weekly-digest` | `0 16 * * 5` (Friday 4pm) | Week-closing summary |
| `/update-dashboard` | `0 */6 * * *` (every 6 hours) | Keep Trinity dashboard metrics current |

## Guidelines

- **Lead with what needs action** — every briefing and digest should answer "what do I need to do?" before "what happened?" Raw information without a recommendation is noise.
- **Be concise, not comprehensive** — a 3-paragraph briefing that gets read beats a 3-page report that doesn't. Bullet points over prose. If something needs detail, link to the source.
- **Track commitments relentlessly** — when a decision is made, always capture: what was decided, who owns next steps, and when it's due. Surface overdue items prominently.
- **[Priority from Q3] always comes first** — the morning briefing leads with [the priority area]. Everything else is supporting context.
```

---

## STEP 5: Generate Skills

### 5a. /daily-briefing

Write `[destination]/.claude/skills/daily-briefing/SKILL.md`:

**Customize based on wizard answers:**
- Tools determine which data sources to check
- Team size determines depth and grouping
- Priority determines output order

```yaml
---
name: daily-briefing
description: Morning executive briefing — synthesizes your calendar, messages, and team status into an actionable summary
allowed-tools: Read, Write, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: chiefofstaff
---
```

```markdown
# Daily Briefing

## Purpose

Produce a concise morning briefing that tells the CEO what matters today — [priority from Q3] first, then everything else in order of urgency.

## Process

### Step 1: Check Today's Date and Context

```bash
date
```

Read any existing briefings in the agent directory to understand what was covered yesterday.

### Step 2: Gather Data

[Customize based on tools from Q1:]

**[If Google Workspace:]**
- Check today's calendar: meetings, attendees, time blocks
- Check Gmail: overnight messages, threads needing response, flagged items

**[If Slack:]**
- Check overnight activity: channels with unread messages, DMs, mentions
- Identify threads that need a response or decision

**[If Notion:]**
- Check team updates, recent page edits, tagged items
- Pull context for today's meetings from shared docs

**[If Linear/Jira:]**
- Check blocked items, overdue tasks, sprint progress
- Identify escalations that need CEO attention

**[If no tools / manual:]**
- Ask the user to paste their calendar, overnight messages, or anything they want synthesized
- Use AskUserQuestion: "Paste anything you'd like me to include in today's briefing — calendar, emails, Slack threads, notes."

### Step 3: Check Decision Log

Read recent entries from `decisions/` to surface:
- Overdue follow-ups
- Commitments due today or this week
- Open decisions that need closure

### Step 4: Synthesize Briefing

Produce a structured briefing:

```
## Daily Briefing — [Today's Date]

### [Priority from Q3 — LEAD SECTION]
[The thing the CEO cares about most, up front]

### Today's Calendar
[Meetings listed chronologically with one-line context for each]
- **9:00** — [Meeting] with [Person] — [what it's about, what to prep]
- **10:30** — [Meeting] ...

### Needs Your Response
[Messages, threads, or decisions waiting for the CEO]
- [Source]: [Summary] — [Recommended action]

### Team Status
[Customize depth based on team size from Q2:]
[Solo: skip this section]
[3-5: one line per direct report if anything notable]
[6-10: grouped by function]
[10+: exception-only — what's off track]

### Decisions Due
[From decision log — overdue and upcoming]

### FYI (No Action Needed)
[Context that's worth knowing but doesn't need a response]
```

### Step 5: Save Briefing

Write the briefing to `briefings/[YYYY-MM-DD].md`.

```bash
mkdir -p briefings
```

Report the briefing inline and note the saved file.

## Outputs

- Markdown briefing displayed in conversation
- Saved to `briefings/[date].md` for reference
```

### 5b. /prep-meeting

Write `[destination]/.claude/skills/prep-meeting/SKILL.md`:

```yaml
---
name: prep-meeting
description: Prepare a pre-meeting brief — who you're meeting, context, open items, and suggested talking points
argument-hint: "<person-name or meeting-title>"
allowed-tools: Read, Write, Bash, WebSearch, WebFetch, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: chiefofstaff
---
```

```markdown
# Prep Meeting

## Purpose

Prepare an executive for a meeting — who's in the room, what's the context, what's unresolved, and what to bring up.

## Process

### Step 1: Identify the Meeting

If a person name or meeting title was provided as an argument, use it. Otherwise:

Use AskUserQuestion:
- **Question:** "Which meeting should I prep you for? Name the person or meeting title."
- **Header:** "Meeting"
- **Options:**
  1. Let me type the person or meeting name
  2. Next meeting on my calendar (paste calendar details)

### Step 2: Gather Context

Research the meeting participants and topic:

**About the person/company:**
- Search the web for recent news, LinkedIn profile, company updates
- If this is an internal meeting, check for recent context in team docs

**Previous interactions:**
- Search `decisions/` for any decisions involving this person
- Search `briefings/` for previous mentions
- Check for open follow-ups or commitments

**[If Notion selected in Q1:]**
- Pull relevant shared docs or meeting notes from previous sessions

### Step 3: Compile Brief

```
## Meeting Prep: [Meeting Title or Person Name]

**When:** [Date/time if known]
**With:** [Attendees and their roles — one line each]
**Purpose:** [What this meeting is about in one sentence]

### Context
[2-3 bullet points: what's happening, why this meeting matters now]

### Open Items
[Unresolved things between you and these people]
- [Item] — [Status] — [Who owns it]

### Their Likely Priorities
[What the other person probably wants to discuss, based on context]

### Suggested Talking Points
1. [Thing to bring up — with reason]
2. [Thing to bring up — with reason]
3. [Question to ask]

### Decisions to Make
[If any decisions should be made in this meeting, flag them]
```

### Step 4: Save Brief

Write to `meetings/[date]-[slug].md`.

```bash
mkdir -p meetings
```

## Outputs

- Meeting prep brief displayed in conversation
- Saved to `meetings/[date]-[slug].md`
```

### 5c. /track-decision

Write `[destination]/.claude/skills/track-decision/SKILL.md`:

```yaml
---
name: track-decision
description: Log a decision with follow-ups, owners, and deadlines — surfaces overdue commitments
argument-hint: "<decision-summary>"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: chiefofstaff
---
```

```markdown
# Track Decision

## Purpose

Log a decision, assign follow-ups with owners and deadlines, and maintain a searchable decision history.

## Process

### Step 1: Capture the Decision

If a summary was provided as an argument, use it as context. Otherwise:

Use AskUserQuestion:
- **Question:** "What was decided? Give me the short version."
- **Header:** "Decision"
- **Options:**
  1. Let me describe the decision
  2. Paste from meeting notes or Slack

### Step 2: Gather Details

Use AskUserQuestion:
- **Question:** "Who owns the follow-ups and when are they due?"
- **Header:** "Follow-ups"
- **Options:**
  1. Let me list the action items
  2. No follow-ups — this is just a record
  3. I'll figure out follow-ups later (mark as draft)

### Step 3: Format and Save

[Customize format based on Q4 decision tracking choice:]

**[If "Start fresh" or no preference:]**
Write to `decisions/[YYYY-MM-DD]-[slug].md`:

```markdown
# [Decision Title]

**Date:** [YYYY-MM-DD]
**Made by:** [Who made the decision]
**Context:** [One sentence — why this came up]

## Decision

[What was decided — clear and unambiguous]

## Follow-ups

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| [action] | [person] | [date] | Open |

## Notes

[Any additional context]
```

**[If Notion:]**
Output in Notion-friendly format with headers, toggle blocks, and clean markdown that pastes well into Notion. Include a callout block for the decision itself.

**[If Slack:]**
Output in Slack-friendly format: bold headers, bullet points, emoji status markers. Include a one-line summary suitable for posting to a channel.

**[If Spreadsheets:]**
Output a CSV-friendly table row:
`Date, Decision, Owner, Follow-up, Due Date, Status`

Also save the full decision to `decisions/` as markdown regardless of format choice.

### Step 4: Check for Overdue Items

Read all files in `decisions/` and surface any follow-ups that are past their due date:

```
## Overdue Commitments

| Decision | Action | Owner | Due | Days overdue |
|----------|--------|-------|-----|-------------|
| [decision] | [action] | [person] | [date] | [N] |
```

If nothing is overdue, skip this section.

## Outputs

- Decision logged to `decisions/[date]-[slug].md`
- Formatted output for [chosen platform from Q4]
- Overdue commitments surfaced if any exist
```

### 5d. /weekly-digest

Write `[destination]/.claude/skills/weekly-digest/SKILL.md`:

```yaml
---
name: weekly-digest
description: End-of-week summary — decisions made, commitments tracked, and priorities for next week
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-04
  author: chiefofstaff
---
```

```markdown
# Weekly Digest

## Purpose

Produce a week-closing summary: what was decided, what's being tracked, what's overdue, and what to focus on next week.

## Process

### Step 1: Determine Week Range

```bash
date
```

Calculate Monday-Friday of the current (or just-ended) week.

### Step 2: Gather the Week's Data

**Decisions made this week:**
- Read all files in `decisions/` created this week
- Summarize each decision in one line

**Briefings this week:**
- Read files in `briefings/` from this week
- Extract recurring themes, escalations, and patterns

**Meeting preps this week:**
- Read files in `meetings/` from this week
- Note key meetings and outcomes if any decisions resulted

### Step 3: Check Commitments

Read all `decisions/` files and compile:
- Follow-ups completed this week (status changed to Done)
- Follow-ups still open from this week
- Overdue follow-ups from previous weeks
- Follow-ups due next week

### Step 4: Produce Digest

```
## Weekly Digest — Week of [Monday Date]

### Decisions Made ([count])
[One line per decision with date]
- **[Mon]** — [Decision summary]
- **[Wed]** — [Decision summary]

### Commitments Tracker
**Completed:** [count]
**Open (on track):** [count]
**Overdue:** [count] ← [flag if any]

[If overdue items exist, list them with owners]

### This Week's Themes
[2-3 bullet points: what dominated the week, patterns spotted]

### Next Week Preview
**Key meetings:** [list major meetings from next week's calendar if available]
**Decisions needed:** [open decisions that should be closed next week]
**Follow-ups due:** [commitments coming due next week]

### Recommendation
[One paragraph: what the CEO should focus on next week and why]
```

### Step 5: Save Digest

Write to `digests/week-[YYYY-WNN].md`.

```bash
mkdir -p digests
```

## Outputs

- Weekly digest displayed in conversation
- Saved to `digests/week-[YYYY-WNN].md`
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
      "first_briefing": { "done": false, "label": "Run your first daily briefing (/daily-briefing)" },
      "first_decision": { "done": false, "label": "Log your first decision (/track-decision)" },
      "plugins_installed": { "done": false, "label": "Install recommended plugins (agent-dev, trinity)" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity:onboard)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via MCP (mcp__trinity__chat_with_agent)" }
    },
    "schedules": {
      "schedules_configured": { "done": false, "label": "Schedule daily briefing for 7am weekdays (use MCP schedule tools)" },
      "weekly_digest_scheduled": { "done": false, "label": "Schedule weekly digest for Friday 4pm (use MCP schedule tools)" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled briefing ran successfully" }
    }
  }
}
```

### 6b. Generate /onboarding skill

Write `[destination]/.claude/skills/onboarding/SKILL.md` following the standard onboarding skill template from the create-wizard specification (Section 8b). Customize:

- Agent name: Chief of Staff
- Primary skill for `first_briefing` step: `/daily-briefing`
- `first_decision` step: guide user to run `/track-decision` with a recent decision
- Schedules phase has two steps: daily briefing (7am weekdays) and weekly digest (Friday 4pm)
- Phase transition messages reference executive support context

---

## STEP 7: Generate Dashboard

### 7a. Generate dashboard.yaml

Write `[destination]/dashboard.yaml`:

```yaml
title: "Chief of Staff"
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
        label: "Last Briefing"
        value: "—"
        description: "Most recent /daily-briefing run"
      - type: metric
        label: "Decisions Tracked"
        value: "0"
        description: "Total in decisions/"

  - title: "Operations"
    layout: grid
    columns: 3
    widgets:
      - type: metric
        label: "Pending Decisions"
        value: "0"
        description: "Open follow-ups awaiting action"
      - type: metric
        label: "Open Blockers"
        value: "0"
        description: "Overdue commitments"
        color: red
      - type: metric
        label: "Upcoming Meetings"
        value: "0"
        description: "Meeting preps this week"

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
description: Refresh dashboard.yaml with current metrics from chief of staff agent data
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-06
  author: chiefofstaff
---
```

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from chief of staff agent data.

## Process

### Step 1: Gather Metrics

Read the agent's data sources:
- `decisions/` — count total decision files, count open follow-ups (status: Open), count overdue items
- `briefings/` — find most recent briefing date
- `meetings/` — count meeting preps from the current week

Calculate:
- Total decisions tracked (count of files in `decisions/`)
- Last briefing date (most recent file in `briefings/`)
- Pending decisions (count of open follow-ups across all decision files)
- Open blockers (count of overdue follow-ups — past due date with status Open)
- Upcoming meetings (count of meeting prep files from current week)

### Step 2: Update Dashboard

Read the current `dashboard.yaml`, update widget values:

- "Last Briefing" → most recent briefing date
- "Decisions Tracked" → total decision count
- "Pending Decisions" → open follow-up count
- "Open Blockers" → overdue count (color: red if >0, gray if 0)
- "Upcoming Meetings" → meeting prep count this week
- `updated` → current ISO timestamp

Write the updated `dashboard.yaml`.

### Step 3: Confirm

```
Dashboard refreshed:
- Decisions tracked: [N]
- Pending decisions: [N]
- Open blockers: [N]
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

### 7a. template.yaml

Write `[destination]/template.yaml`:

```yaml
name: chiefofstaff
display_name: Chief of Staff
description: |
  Executive support agent for [team size from Q2] CEOs.
  Daily briefings from [tools from Q1], meeting prep,
  decision tracking, and weekly digests.
avatar_prompt: A polished, composed executive assistant in their early 30s — tailored charcoal blazer, crisp white shirt, no tie. Short neat hair, wire-rimmed glasses, calm and focused expression. Standing in a modern corner office at dawn, holding a tablet with the day's agenda. City skyline visible through floor-to-ceiling windows, warm golden hour light. A large wall-mounted screen behind them shows a clean dashboard. The scene conveys quiet competence, anticipation, and absolute reliability. Digital art, clean lines, muted professional palette with warm accents.
resources:
  cpu: "2"
  memory: "4g"
```

### 7b. .env.example

Write `[destination]/.env.example`:

```bash
# Chief of Staff — Environment Variables
# Copy this to .env and fill in your values

[If Google Workspace selected:]
# Google Workspace — for calendar and email access
# See: https://developers.google.com/workspace/guides/create-credentials
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=

[If Slack selected:]
# Slack — for channel monitoring and message access
# Create a Slack app: https://api.slack.com/apps
SLACK_BOT_TOKEN=
SLACK_USER_TOKEN=

[If Notion selected:]
# Notion — for docs and team wiki access
# Create an integration: https://www.notion.so/my-integrations
NOTION_API_KEY=

[If Linear selected:]
# Linear — for project tracking and sprint status
# Get API key: https://linear.app/settings/api
LINEAR_API_KEY=

[If Jira selected:]
# Jira — for project tracking and sprint status
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=

[If no tools selected:]
# No API keys required — Chief of Staff works with manual input.
# Add API keys here as you integrate tools.
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
```

### 7d. .mcp.json.template

Write `[destination]/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

---

## STEP 9: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: chiefofstaff"
```

---

## STEP 10: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Want to create a GitHub repository for Chief of Staff?"
- **Header:** "GitHub"
- **Options:**
  1. **Create private repo** — `gh repo create chiefofstaff --private --source=. --push` (recommended — this agent handles sensitive executive data)
  2. **Create public repo** — `gh repo create chiefofstaff --public --source=. --push`
  3. **Skip** — I'll set up GitHub later

If `gh` is not available, show manual instructions.

---

## STEP 11: Completion

Display:

```
## Chief of Staff Installed

Your executive support agent is ready.

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity — configured for [team size], pulling from [tools] |
| `.claude/skills/daily-briefing/SKILL.md` | Morning briefing — [priority] first |
| `.claude/skills/prep-meeting/SKILL.md` | Pre-meeting context and talking points |
| `.claude/skills/track-decision/SKILL.md` | Decision log with follow-up tracking |
| `.claude/skills/weekly-digest/SKILL.md` | Friday summary and next-week preview |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with executive metrics |
| `decisions/` | Decision log directory |
| `template.yaml` | Trinity deployment metadata |
| `.env.example` | API key template for [tools] |

### Get Started

1. **Open Chief of Staff:**
   ```
   cd [destination] && claude
   ```

2. **Run the setup wizard:**
   ```
   /onboarding
   ```

   This will walk you through connecting your tools,
   running your first briefing, and (when you're ready)
   scheduling automatic daily briefings via Trinity.

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
| No tools selected | Default to manual-input mode — still fully functional |
