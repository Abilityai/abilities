---
name: install-ghostwriter
description: Create a content writer agent — asks about your brand voice, platforms, and topics, then scaffolds a Trinity-compatible ghostwriter agent that writes in your voice
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-09
  author: Ability.ai
---

# Install Ghostwriter

Create a **content writer agent** that knows your brand voice and writes platform-specific content. Powered by Claude Code and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**
- A fully configured agent directory with CLAUDE.md, skills, and Trinity files
- 5 starting skills: write, set-voice, repurpose, hooks, library
- A voice profile customized to your writing style
- Zero API keys required — Claude does all the writing natively
- Ready for local use or Trinity deployment

> Built by [Ability.ai](https://ability.ai) — the agent orchestration platform.

---

## STEP 1: Determine Destination

If the user provided a destination path as an argument, use it. Otherwise, ask:

Use AskUserQuestion:
- **Question:** "Where should Ghostwriter be installed?"
- **Header:** "Location"
- Show these options:
  1. `~/ghostwriter` — Home directory (recommended)
  2. `./ghostwriter` — Current directory
  3. Custom path — Let me specify

Default to `~/ghostwriter` if no preference.

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

### Q1: Platforms

Use AskUserQuestion:
- **Question:** "What platforms do you write for? Select all that apply."
- **Header:** "Platforms"
- **multiSelect: true**
- **Options:**
  1. **Twitter/X** — Short-form, threads, punchy takes
  2. **LinkedIn** — Professional long-form, thought leadership
  3. **Newsletter** — Email-based, editorial voice, subscriber relationship
  4. **Blog** — Long-form articles, SEO-friendly, evergreen content

Store the answer — it customizes:
- Platform-specific voice guidelines in `voice-profile.md`
- Output formats in `/write` and `/repurpose` skills
- Platform list in CLAUDE.md identity section

### Q2: Writing Style

Use AskUserQuestion:
- **Question:** "How would you describe your writing style? Pick the closest match or describe your own."
- **Header:** "Style"
- **Options:**
  1. **Direct & Opinionated** — Strong takes, no hedging, first-person authority. Think: founder sharing hard-won lessons.
  2. **Warm & Educational** — Approachable teacher tone, uses analogies and examples. Think: explaining to a smart friend.
  3. **Technical & Precise** — Data-driven, specific, minimal fluff. Think: senior engineer writing for peers.
  4. **Conversational & Witty** — Casual, humor-laced, relatable. Think: popular podcast host writing posts.

Store the answer — it customizes:
- Core tone characteristics in `voice-profile.md`
- Writing instructions in every skill
- Hook style preferences in `/hooks`

### Q3: Topics

Use AskUserQuestion:
- **Question:** "What are your 3-5 main topics or content pillars? (e.g., 'AI agents, developer productivity, startup lessons, open source')"
- **Header:** "Topics"
- **Options:**
  1. **Tech & AI** — AI, developer tools, software engineering, emerging tech
  2. **Business & Startups** — Entrepreneurship, growth, leadership, fundraising
  3. **Marketing & Growth** — Content strategy, audience building, brand, SEO
  4. **Custom** — I'll type my own topics

Store the answer — it customizes:
- Content pillars in `voice-profile.md`
- Topic suggestions in `/hooks` skill
- Categorization in `/library` skill
- Pillar tagging across all content

### Q4: Anti-Patterns

Use AskUserQuestion:
- **Question:** "What should your ghostwriter NEVER do? Pick all that apply, or add your own."
- **Header:** "Never Do"
- **multiSelect: true**
- **Options:**
  1. **Use emojis excessively** — Max 1-2 per post, or none
  2. **Be salesy or promotional** — No "check out my course", no hard CTAs
  3. **Use corporate jargon** — No "leverage", "synergize", "circle back"
  4. **Start with greetings** — No "Hey everyone!", "Happy Monday!", "Good morning"

Store the answer — it customizes:
- Anti-pattern rules in `voice-profile.md`
- Style guardrails in every skill
- Explicit "DON'T" lists in writing instructions

---

## STEP 3: Create Agent Directory Structure

```bash
mkdir -p [destination]/.claude/skills/write
mkdir -p [destination]/.claude/skills/set-voice
mkdir -p [destination]/.claude/skills/repurpose
mkdir -p [destination]/.claude/skills/hooks
mkdir -p [destination]/.claude/skills/library
mkdir -p [destination]/.claude/skills/onboarding
mkdir -p [destination]/.claude/skills/update-dashboard
```

---

## STEP 4: Generate voice-profile.md

Write `[destination]/voice-profile.md`. This is the core artifact — the agent reads this before writing anything.

Customize entirely based on Q1-Q4 answers:

```markdown
# Voice Profile

## Tone

[Based on Q2 — expand the selected style into 4-5 specific characteristics]
[Example for "Direct & Opinionated":]
- **Direct** — No hedging, no "I think maybe", no qualifiers
- **Opinionated** — Strong takes backed by experience, not afraid to disagree
- **First-person** — "I built..." not "We built...", personal authority
- **Concise** — Every sentence earns its place, cut the fluff
- **Confident** — State things as fact when you know them, acknowledge uncertainty when you don't

## Content Pillars

[Based on Q3 — list each topic with a one-line description and example keywords]

1. **[Pillar 1]** — [description]
   Keywords: [relevant terms]
2. **[Pillar 2]** — [description]
   Keywords: [relevant terms]
[etc.]

## Platform Guidelines

[Based on Q1 — only include selected platforms]

### [Platform Name]
- **Format:** [character limits, structure notes]
- **Tone adjustment:** [how the base tone adapts for this platform]
- **Best practices:** [2-3 platform-specific tips]

[Repeat for each selected platform]

## Style Rules

### DO:
- [3-5 positive rules derived from Q2 style choice]
- Lead with insight, not promotion
- Use specific examples and numbers
- Write like you talk (contractions OK)

### DON'T:
[Based on Q4 — list each selected anti-pattern as a concrete rule]
- [Anti-pattern 1 expanded into a clear rule]
- [Anti-pattern 2 expanded into a clear rule]
[etc.]

## Hook Framework (3S+2F)

Use these hook types to open content:

- **Scary** — Trigger loss aversion ("You're losing readers because...")
- **Strange** — Counterintuitive take ("I stopped writing headlines")
- **Sexy** — Aspirational outcome ("How I 5x'd my engagement with one change")
- **Free Value** — Actionable insight given freely ("The 3-part hook formula I use")
- **Familiar** — Shared experience ("Every writer hits this wall at 1000 followers")
```

---

## STEP 5: Generate CLAUDE.md

Write `[destination]/CLAUDE.md`. Customize based on all wizard answers.

The CLAUDE.md must include these sections:

```markdown
# CLAUDE.md

## Identity

You are **Ghostwriter** — a content writer agent that writes in [user's name]'s voice across [list platforms from Q1].

You know [their] brand voice intimately. Before writing anything, you read `voice-profile.md` and follow it precisely. You write [style from Q2 — e.g., "direct, opinionated content"] about [topics from Q3].

You are NOT a generic AI writer. You have a specific voice, specific topics, and specific rules. When asked to write, you produce content that sounds like it came from the person, not from a language model.

**Repository:** [will be set after git init]

## Core Capabilities

| Skill | Purpose |
|-------|---------|
| `/write` | Write a post for any platform in your voice |
| `/set-voice` | Update your brand voice profile |
| `/repurpose` | Turn one idea into posts for multiple platforms |
| `/hooks` | Generate scroll-stopping hooks for a topic |
| `/library` | Track content pipeline (draft → review → posted) |

## How to Work With This Agent

### Quick Start

1. Run `/onboarding` to complete setup
2. Try `/write` to create your first post
3. Use `/repurpose` to turn one idea into content for all your platforms
4. Track everything with `/library`

### Available Skills

| Skill | Purpose |
|-------|---------|
| `/write` | Write a post for any platform in your voice |
| `/set-voice` | Define or update your brand voice profile |
| `/repurpose` | Turn one idea into posts for multiple platforms |
| `/hooks` | Generate scroll-stopping hooks for a topic |
| `/library` | Track content pipeline (draft → review → posted) |
| `/onboarding` | Setup progress tracker |
| `/update-dashboard` | Refresh dashboard metrics |

## Voice Profile

Your voice is defined in `voice-profile.md`. **Always read it before writing content.** This file is the source of truth for tone, style, platform guidelines, and anti-patterns.

To update the voice: run `/set-voice` or edit `voice-profile.md` directly.

## Development Workflow

Build this agent iteratively:

1. **Start with /onboarding** — get plugins installed and your first post written
2. **Refine your voice** — run `/set-voice` after seeing initial output, adjust until it sounds right
3. **Add skills with /create-playbook** — each new capability becomes a slash command
4. **Deploy when ready** — run `trinity deploy .` from your terminal to go live on Trinity

### Deploying to Trinity

When you're ready to run this agent remotely (scheduled tasks, always-on, API access):

```bash
pip install trinity-cli    # one-time install
trinity init               # connect to your Trinity instance
trinity deploy .           # deploy this agent
```

After deploying, manage from your terminal:
- `trinity chat ghostwriter "message"` — talk to the remote agent
- `trinity logs ghostwriter` — view logs
- `trinity schedules list ghostwriter` — check scheduled tasks

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
/plugin install agent-dev@abilityai   # Create new skills
/plugin install trinity@abilityai     # Deploy to Trinity
```

## Project Structure

```
ghostwriter/
  CLAUDE.md              # Agent identity and instructions
  voice-profile.md       # Brand voice definition (the core artifact)
  content-library.yaml   # Content tracking (created by /library)
  onboarding.json        # Setup progress tracker
  dashboard.yaml         # Trinity dashboard metrics
  template.yaml          # Trinity metadata
  .env.example           # Environment variable template (empty — no keys needed)
  .gitignore             # Git exclusions
  .mcp.json.template     # MCP config template
  .claude/
    skills/
      write/SKILL.md          # Write platform-specific content
      set-voice/SKILL.md      # Update voice profile
      repurpose/SKILL.md      # One idea → multiple platforms
      hooks/SKILL.md          # Generate scroll-stopping hooks
      library/SKILL.md        # Content pipeline tracker
      onboarding/SKILL.md     # Setup progress tracker
      update-dashboard/SKILL.md  # Dashboard metrics updater
```

## Artifact Dependency Graph

```yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior — single source of truth"

  voice-profile.md:
    mode: prescriptive
    direction: source
    description: "Brand voice definition — read before all writing tasks"

  content-library.yaml:
    mode: descriptive
    direction: target
    sources: [library/SKILL.md, write/SKILL.md, repurpose/SKILL.md]
    description: "Content tracking — updated when content is created or status changes"

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
```

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/update-dashboard` | `0 */6 * * *` (every 6 hours) | Refresh content metrics on Trinity dashboard |

## Guidelines

- **Always read voice-profile.md before writing** — never generate content without checking the voice profile first. The voice is the product.
- **Every piece of content gets a pillar tag** — classify content by topic pillar for tracking and balance.
- **Platform-specific, not generic** — a Twitter post and a LinkedIn post about the same idea should read completely differently.
- **Anti-patterns are hard rules** — if the voice profile says "never use emojis", that means never. No exceptions.
```

[End of CLAUDE.md — customize the Identity section based on the user's actual Q1-Q4 answers. Replace bracketed placeholders with real values.]

---

## STEP 6: Generate template.yaml

Write `[destination]/template.yaml`:

```yaml
name: ghostwriter
display_name: Ghostwriter
description: |
  Content writer agent that knows your brand voice and writes platform-specific content.
  Writes for [platforms from Q1]. Style: [style from Q2]. Topics: [topics from Q3].
  Zero API keys — powered entirely by Claude's native writing ability.
avatar_prompt: A creative writer in their element — sitting at a vintage wooden desk with a modern laptop, surrounded by notebooks and sticky notes with content ideas. Warm ambient lighting from a desk lamp. They wear a comfortable sweater and have an expressive, thoughtful face mid-composition. A corkboard behind them shows platform icons (Twitter, LinkedIn) and content pillars. The mood is focused creativity — someone who deeply understands their voice and audience. Digital art, warm tones, slight film grain.
resources:
  cpu: "2"
  memory: "4g"
```

[Customize description based on actual Q1-Q3 answers.]

---

## STEP 7: Generate Skills

### 7a. /write skill

Write `[destination]/.claude/skills/write/SKILL.md`:

```yaml
---
name: write
description: Write a post for any platform in your brand voice. Reads your voice profile and produces platform-specific content.
allowed-tools: Read, Write, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Write

Create a single piece of content for a specific platform, written in your brand voice.

## Process

### Step 1: Load Voice Profile

Read `voice-profile.md` from the agent root directory. This is mandatory — never write content without reading the voice profile first.

### Step 2: Get Parameters

If the user didn't specify, ask with AskUserQuestion:

**Platform** (if not specified):
- **Question:** "Which platform is this for?"
- **Header:** "Platform"
- **Options:** [list only the platforms from the user's Q1 selection]

**Topic** (if not specified):
- **Question:** "What's the topic or idea for this post?"
- **Header:** "Topic"
- **Options:** [list content pillars from voice profile, plus "Custom topic"]

### Step 3: Write Content

Write the content following these rules:
1. Match the tone characteristics from the voice profile exactly
2. Follow the platform-specific guidelines for the selected platform
3. Respect all anti-patterns (the DON'T list)
4. Tag with the appropriate content pillar
5. Use the hook framework (3S+2F) for the opening

**Output format:**

```
## [Platform] Post

**Pillar:** [content pillar]
**Hook type:** [scary/strange/sexy/free_value/familiar]

---

[The content itself]

---

**Word count:** [count]
**Character count:** [count] [note if near platform limit]
```

### Step 4: Offer Next Steps

After showing the content, ask:
- **Question:** "What would you like to do with this?"
- **Header:** "Next"
- **Options:**
  1. **Looks good** — Save to content library as "draft"
  2. **Revise** — Adjust tone, length, or angle
  3. **Repurpose** — Turn this into posts for other platforms too
  4. **Discard** — Start over

If saving, update `content-library.yaml` with the new entry.

## Outputs

- Platform-specific content in the user's brand voice
- Optional: entry added to `content-library.yaml`
```

### 7b. /set-voice skill

Write `[destination]/.claude/skills/set-voice/SKILL.md`:

```yaml
---
name: set-voice
description: Define or update your brand voice profile — tone, style rules, platform guidelines, and anti-patterns
allowed-tools: Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Set Voice

Define or refine your brand voice profile. This updates `voice-profile.md`, which every writing skill reads before creating content.

## Process

### Step 1: Load Current Profile

Read `voice-profile.md`. If it exists, show a summary:
```
Current voice profile:
- Tone: [summary]
- Platforms: [list]
- Pillars: [list]
- Anti-patterns: [count] rules
```

### Step 2: Determine What to Change

Use AskUserQuestion:
- **Question:** "What would you like to update?"
- **Header:** "Update"
- **Options:**
  1. **Tone** — Adjust how you sound (more casual, more authoritative, etc.)
  2. **Platforms** — Add or remove platforms
  3. **Topics/Pillars** — Change your content focus areas
  4. **Anti-patterns** — Update what the agent should never do
  5. **Full rewrite** — Start the voice profile from scratch

### Step 3: Gather Changes

Based on selection, ask targeted questions:

**For Tone:** "Describe how you want to sound differently. What's not working about the current tone?"
**For Platforms:** "Which platforms to add or remove?"
**For Pillars:** "What topics should be added, removed, or renamed?"
**For Anti-patterns:** "What new rules should be added, or which existing ones removed?"
**For Full rewrite:** Run through all 4 questions again (same as wizard Q1-Q4).

### Step 4: Update Profile

Edit `voice-profile.md` with the changes. Show a before/after diff summary.

### Step 5: Test

Offer to generate a short sample post using the updated voice:
- **Question:** "Want to test the new voice with a quick sample post?"
- **Header:** "Test"
- **Options:**
  1. **Yes** — Generate a short sample
  2. **No** — I'm done

## Outputs

- Updated `voice-profile.md`
- Optional: sample post demonstrating the new voice
```

### 7c. /repurpose skill

Write `[destination]/.claude/skills/repurpose/SKILL.md`:

```yaml
---
name: repurpose
description: Turn one idea or piece of content into posts for multiple platforms — each adapted to the platform's format and audience
allowed-tools: Read, Write, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Repurpose

Take one idea, article, or piece of content and turn it into platform-specific posts for all your platforms.

## Process

### Step 1: Load Voice Profile

Read `voice-profile.md`. Extract the list of platforms and their guidelines.

### Step 2: Get Source Content

If the user didn't provide content, ask:

Use AskUserQuestion:
- **Question:** "What's the source content to repurpose?"
- **Header:** "Source"
- **Options:**
  1. **An idea** — I'll describe a topic or angle
  2. **Existing content** — I'll paste or point to something I've already written
  3. **From library** — Pick from my content library

If "From library": read `content-library.yaml` and show recent entries for selection.

### Step 3: Select Platforms

Use AskUserQuestion:
- **Question:** "Which platforms should I create content for?"
- **Header:** "Platforms"
- **multiSelect: true**
- **Options:** [list only platforms from voice profile]
- Default: all platforms selected

### Step 4: Generate Content

For each selected platform, generate a platform-specific version:

1. Read the platform guidelines from the voice profile
2. Adapt the core idea to the platform's format, length, and tone
3. Use a different hook type (from the 3S+2F framework) for each platform where possible — variety prevents repetition
4. Tag each with content pillar

**Output format:**

```
## Repurposed Content: [topic summary]

Source: [idea/content description]
Pillar: [content pillar]

---

### Twitter/X
**Hook type:** [type]
[content]
(X characters)

---

### LinkedIn
**Hook type:** [type]
[content]
(X words)

---

[etc. for each platform]
```

### Step 5: Save to Library

Ask if the user wants to save all generated content to the library:
- **Question:** "Save all to content library?"
- **Header:** "Save"
- **Options:**
  1. **Save all as drafts** — Add all posts to content-library.yaml
  2. **Save some** — Let me pick which ones
  3. **Don't save** — Just showing me options

Update `content-library.yaml` for saved entries.

## Outputs

- Platform-specific content for each selected platform
- Optional: entries added to `content-library.yaml`
```

### 7d. /hooks skill

Write `[destination]/.claude/skills/hooks/SKILL.md`:

```yaml
---
name: hooks
description: Generate scroll-stopping hooks for a topic using the 3S+2F framework — scary, strange, sexy, free value, familiar
allowed-tools: Read, Write, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Hooks

Generate scroll-stopping opening lines for a topic using the 3S+2F hook framework.

## Process

### Step 1: Load Voice Profile

Read `voice-profile.md`. Extract tone characteristics and content pillars.

### Step 2: Get Topic

If the user didn't specify, ask:

Use AskUserQuestion:
- **Question:** "What topic do you need hooks for?"
- **Header:** "Topic"
- **Options:** [list content pillars from voice profile, plus "Custom topic"]

### Step 3: Select Platform

Use AskUserQuestion:
- **Question:** "Which platform are these hooks for? (affects length and style)"
- **Header:** "Platform"
- **Options:** [list platforms from voice profile, plus "General / all platforms"]

### Step 4: Generate Hooks

Generate 2 hooks for each of the 5 hook types (10 total), tailored to the topic and platform:

```
## Hooks: [topic]

Platform: [platform]
Voice: [tone summary]

### Scary (loss aversion, urgency)
1. [hook]
2. [hook]

### Strange (counterintuitive, unexpected)
1. [hook]
2. [hook]

### Sexy (aspirational, desirable outcomes)
1. [hook]
2. [hook]

### Free Value (actionable insight given freely)
1. [hook]
2. [hook]

### Familiar (shared experience, relatability)
1. [hook]
2. [hook]
```

### Step 5: Develop a Hook

Ask if the user wants to develop any hook into a full post:
- **Question:** "Want to turn any of these into a full post?"
- **Header:** "Develop"
- **Options:**
  1. **Yes, pick one** — I'll select a hook to develop
  2. **No, just the hooks** — I'm done

If yes, ask which hook number, then invoke the `/write` skill flow with that hook as the opening.

## Outputs

- 10 hooks (2 per hook type) tailored to topic and platform
- Optional: full post developed from a selected hook
```

### 7e. /library skill

Write `[destination]/.claude/skills/library/SKILL.md`:

```yaml
---
name: library
description: Track your content pipeline — view, add, update, and filter content pieces by status, platform, and pillar
allowed-tools: Read, Write, Edit, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Library

Manage your content pipeline. Track pieces from idea through draft, review, and posted status.

## Process

### Step 1: Load Library

Read `content-library.yaml`. If it doesn't exist, create an empty one:

```yaml
# Content Library
# Managed by /library skill
entries: []
```

### Step 2: Determine Action

Use AskUserQuestion:
- **Question:** "What would you like to do?"
- **Header:** "Action"
- **Options:**
  1. **View pipeline** — See all content by status
  2. **Add entry** — Track a new piece of content
  3. **Update status** — Move a piece to the next stage
  4. **Filter** — Find content by platform, pillar, or status

### Step 3: Execute Action

**View pipeline:**
Display content grouped by status:

```
## Content Pipeline

### Ideas (X)
- [title] — [pillar] — [platform]

### Drafts (X)
- [title] — [pillar] — [platform] — created [date]

### In Review (X)
- [title] — [pillar] — [platform] — created [date]

### Posted (X)
- [title] — [pillar] — [platform] — posted [date]

**Total: X pieces | X drafts ready for review**
```

**Add entry:**
Ask for title, platform, pillar, and optional notes. Add to library with status "idea" and today's date.

**Update status:**
Show entries in current status, let user pick one, advance to next status:
- idea → draft → review → posted

**Filter:**
Ask by what dimension (platform, pillar, status, date range), then show matching entries.

### Step 4: Save

Write updated `content-library.yaml` after any changes.

## Outputs

- Content pipeline view
- Updated `content-library.yaml`
```

---

## STEP 8: Generate Onboarding

### 8a. Generate onboarding.json

Write `[destination]/onboarding.json`:

```json
{
  "phase": "local",
  "started": "[today's date]",
  "steps": {
    "local": {
      "voice_reviewed": { "done": false, "label": "Review and refine your voice profile (/set-voice)" },
      "first_post": { "done": false, "label": "Write your first post (/write)" },
      "plugins_installed": { "done": false, "label": "Install plugins (agent-dev, trinity)" }
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

[Use today's actual date for the `started` field.]

Note: there is no `env_configured` step because Ghostwriter requires zero API keys. The first step is reviewing the voice profile — this gets the user to a meaningful "aha moment" quickly.

### 8b. Generate /onboarding skill

Write `[destination]/.claude/skills/onboarding/SKILL.md`:

```yaml
---
name: onboarding
description: Track your setup progress — shows what's done, what's next, and walks you through each step
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Onboarding

Track and continue your setup progress. This skill reads `onboarding.json`, shows your current status, and walks you through the next incomplete step.

## Process

### Step 1: Load State

Read `onboarding.json` from the agent root directory. If it doesn't exist, inform the user that onboarding is complete or the file was removed.

### Step 2: Show Progress

Display a checklist grouped by phase:

```
## Ghostwriter — Setup Progress

### Phase 1: Local Setup  ← current
- [ ] Review and refine your voice profile (/set-voice)
- [ ] Write your first post (/write)
- [ ] Install plugins (agent-dev, trinity)

### Phase 2: Trinity Deployment
- [ ] Deploy to Trinity
- [ ] Sync credentials to remote
- [ ] Run a skill remotely

### Phase 3: Schedules
- [ ] Set up scheduled tasks
- [ ] Verify first scheduled execution

**Progress: 0/8 complete**
```

### Step 3: Guide Next Step

Identify the first incomplete step in the current phase. Provide specific guidance:

**For `voice_reviewed`:**
- Show a summary of the current voice profile (read `voice-profile.md`)
- Ask: "Does this sound like you? Run `/set-voice` to adjust, or confirm it's good."
- After user confirms or adjusts, mark done.

**For `first_post`:**
- Tell the user: "Let's write your first post! Run `/write` and pick a platform and topic."
- After they complete a post, mark done.

**For `plugins_installed`:**
- Run the install commands:
  ```
  /plugin install agent-dev@abilityai
  /plugin install trinity@abilityai
  ```
- Run each via Bash. Note successes and failures.
- After all attempted, mark done.

**For `onboarded` (Trinity phase):**
- Tell user to run `/trinity:onboard` or `trinity deploy .` from terminal.
- After completion, mark done and advance phase.

**For `first_remote_run`:**
- Tell user to run a skill remotely using `mcp__trinity__chat_with_agent`.
- After completion, mark done and advance phase.

**For `schedules_configured`:**
- Tell user to use MCP schedule tools (`mcp__trinity__create_schedule`).
- Suggest scheduling `/update-dashboard` every 6 hours.
- After completion, mark done.

**For `first_scheduled_run`:**
- Tell user to check scheduled executions via MCP (`mcp__trinity__list_schedules`).
- After verified, mark done.

### Step 4: Update State

After each step is completed, update `onboarding.json`:
- Set the step's `done` to `true`
- If all steps in current phase are done, advance `phase` to the next phase
- If all phases complete, congratulate the user

### Step 5: Phase Transitions

**Local → Trinity:**
```
## Local Setup Complete!

Your ghostwriter agent is fully configured and writing in your voice.

Ready for the next level? Trinity gives you:
- Remote execution (run skills from anywhere)
- Scheduling (automate recurring content generation)
- Multi-agent coordination

Run /onboarding again when you're ready to set up Trinity.
```

**Trinity → Schedules:**
```
## Trinity Deployment Complete!

Your ghostwriter is live on Trinity. Now let's set up automation.

Run /onboarding to configure scheduled tasks.
```

**All Complete:**
```
## Onboarding Complete!

Your ghostwriter agent is fully set up:
- ✓ Voice profile configured
- ✓ First content written
- ✓ Deployed to Trinity
- ✓ Schedules running

You're all set. The onboarding.json file can be kept as a record or deleted.
```

## Outputs

- Updated `onboarding.json` with progress
- Step-by-step guidance for the current task
- Phase transition messages at milestones
```

---

## STEP 9: Generate Dashboard

### 9a. Generate dashboard.yaml

Write `[destination]/dashboard.yaml`:

```yaml
title: "Ghostwriter"
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
        label: "Voice Profile"
        value: "Configured"
        color: green

  - title: "Content Pipeline"
    layout: grid
    columns: 2
    widgets:
      - type: metric
        label: "Total Pieces"
        value: "0"
      - type: metric
        label: "Drafts Ready"
        value: "0"
      - type: list
        title: "Recent Content"
        items: []
        max_items: 5
      - type: metric
        label: "Posts This Week"
        value: "0"

  - title: "Quick Links"
    layout: list
    widgets:
      - type: link
        label: "Trinity Dashboard"
        url: "https://ability.ai"
        external: true
```

[Use today's actual date for the `updated` field.]

### 9b. Generate /update-dashboard skill

Write `[destination]/.claude/skills/update-dashboard/SKILL.md`:

```yaml
---
name: update-dashboard
description: Refresh dashboard.yaml with current metrics from content library and agent state
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-09
  author: ghostwriter
---
```

```markdown
# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from the content library and agent state.

## Process

### Step 1: Gather Metrics

Read the agent's data sources:
- Read `content-library.yaml` — count entries by status (idea, draft, review, posted)
- Read `voice-profile.md` — check it exists and has content
- Check recent git activity: `git log --oneline -10`
- Count posts from the current week

### Step 2: Update Dashboard

Read `dashboard.yaml`, update widget values:

- Update `updated` timestamp to now
- Update "Total Pieces" with total content count
- Update "Drafts Ready" with draft + review count
- Update "Posts This Week" with this week's posted count
- Update "Recent Content" list with last 5 entries from library
- Update "Voice Profile" status (Configured/Not Set)
- Update "Last Activity" with most recent git commit date

Write the updated `dashboard.yaml`.

### Step 3: Confirm

Report what was updated:
```
Dashboard refreshed:
- Total pieces: [count]
- Drafts ready: [count]
- Posts this week: [count]
- Last updated: [timestamp]
```

Note: On Trinity remote, the dashboard path is `/home/developer/dashboard.yaml`.

## Outputs

- Updated `dashboard.yaml` with current metrics
```

---

## STEP 10: Generate Supporting Files

### .env.example

Write `[destination]/.env.example`:

```bash
# Ghostwriter — Environment Variables
# This agent requires NO API keys for core functionality.
# Claude's native writing ability powers all content generation.
#
# Add keys below only if you extend the agent with additional integrations:
# OPENAI_API_KEY=          # If adding AI image generation
# BLOTATO_API_KEY=         # If adding direct social media posting
```

### .gitignore

Write `[destination]/.gitignore`:

```
# Credentials (never commit)
.env
.mcp.json

# Runtime
node_modules/
__pycache__/
*.pyc
.DS_Store

# Claude Code internals
.claude/settings.local.json
```

### .mcp.json.template

Write `[destination]/.mcp.json.template`:

```json
{
  "mcpServers": {}
}
```

Note: Ghostwriter starts with no MCP servers since it needs zero API keys. MCP servers get added as the user extends the agent with integrations.

---

## STEP 11: Initialize Git

```bash
cd [destination] && git init && git add -A && git commit -m "Initial agent scaffold: ghostwriter"
```

---

## STEP 12: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Create a GitHub repository for this agent?"
- **Header:** "GitHub"
- **Options:**
  1. **Public repo** — `ghostwriter` on GitHub (visible to everyone)
  2. **Private repo** — `ghostwriter` on GitHub (only you)
  3. **Skip** — I'll set up GitHub later

If creating a repo:
```bash
gh repo create ghostwriter --[public|private] --source=[destination] --remote=origin --push
```

If `gh` is not available, show manual instructions.

---

## STEP 13: Completion

Display:

```
## Ghostwriter Installed

### What Was Created

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent identity and instructions |
| `voice-profile.md` | Your brand voice definition |
| `.claude/skills/write/SKILL.md` | Write platform-specific content |
| `.claude/skills/set-voice/SKILL.md` | Update voice profile |
| `.claude/skills/repurpose/SKILL.md` | One idea → multiple platforms |
| `.claude/skills/hooks/SKILL.md` | Generate scroll-stopping hooks |
| `.claude/skills/library/SKILL.md` | Content pipeline tracker |
| `.claude/skills/onboarding/SKILL.md` | Setup progress tracker |
| `.claude/skills/update-dashboard/SKILL.md` | Dashboard metrics updater |
| `onboarding.json` | Persistent onboarding checklist |
| `dashboard.yaml` | Trinity dashboard with content metrics |
| `template.yaml` | Trinity metadata |
| `.env.example` | Environment variable template |
| `.gitignore` | Git exclusions |
| `.mcp.json.template` | MCP config template |

### Zero API Keys Required

Ghostwriter is ready to use immediately — no environment variables to configure.
Your voice profile has been created from your wizard answers.

### Get Started

1. Open your new agent:
   ```
   cd [destination] && claude
   ```

2. Run the setup wizard:
   ```
   /onboarding
   ```

   This will walk you through reviewing your voice, writing your first post,
   and (when you're ready) deploying to Trinity.
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn, offer alternatives |
| Git not installed | Skip git init, advise install |
| User unsure about questions | Provide sensible defaults, allow skipping |
| gh CLI not available | Show manual GitHub instructions |
| voice-profile.md missing at runtime | Skills should warn and offer to run /set-voice |
