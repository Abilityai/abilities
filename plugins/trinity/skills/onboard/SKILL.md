---
name: onboard
description: Onboard this agent to Trinity platform. Creates required files, configures MCP connection, and optionally deploys to remote.
argument-hint: "[analyze]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__deploy_local_agent, mcp__trinity__get_agent, mcp__trinity__inject_credentials, mcp__trinity__list_agent_schedules, mcp__trinity__create_agent_schedule, mcp__trinity__update_agent_schedule, mcp__trinity__toggle_agent_schedule
metadata:
  version: "4.12"
  created: 2025-02-05
  author: Ability.ai
  changelog:
    - "4.12: Delegate connection to /trinity:connect (Composition Rule) — Step 2 is now a connect handoff (no inline credential resolution), Step 4 just verifies the connection (deleted the stale `npx mcp-remote` .mcp.json writer + .mcp.json.template; connect is the single writer). .env is now for the agent's own secrets only (Trinity creds live in connect's ~/.trinity/config.json + .mcp.json). Updated Step 1b/Step 6/error table accordingly"
    - "4.11: Deploy robustness — Step 5 preamble: use Trinity MCP tools (not the CLI/curl) for every remote op and confirm the target instance when multiple Trinity servers are connected; new Step 5e injects gitignored credentials (e.g. .env) after deploy via inject_credentials, since the archive excludes them; schedule reconcile renumbered 5e→5f; fixed Step 6 Next-Steps numbering (5,6 were 6,7)"
    - "4.10: Unified remote registry — `.trinity-remote.yaml` is now the shared multi-remote file (default + remotes:) read by /trinity:sync and /trinity:loop, not a single-remote tracking file. Step 5c records the deploy as a named remote without clobbering sync's config; Step 5b parses the multi-remote shape and migrates legacy single-remote files"
    - "4.9: Declarative schedules — define a schedules: block in template.yaml (Step 3a); deploy reconciles them onto the instance via create_agent_schedule (Step 5e). Fixed wrong MCP tool names (create_schedule → create_agent_schedule, list_schedules → list_agent_schedules)"
    - "4.8: Document Trinity resource constraints (integer cpu, g-suffix memory) in Step 3a + error table — fractional cpu/Mi memory are rejected at deploy time"
    - "4.7: Add /agent-dev:add-git-sync follow-up prompt in both completion paths"
    - "4.6: Add GitHub PAT troubleshooting guide for private repo deployment"
    - "4.5: Prefer GitHub repository deployment over local files when remote exists"
    - "4.4: Credential resolution (~/.trinity/config.json), .trinity-remote.yaml tracking, mcp_api_key from profile"
    - "4.3: Added setup.sh, voice chat, channel adapters, fan-out, per-user memory, execution query tools"
    - "4.2: Added avatar_prompt field to template.yaml generation"
    - "4.1: Added choice between full deployment and adaptation-only mode"
    - "4.0: Complete onboarding flow - files, MCP config, and remote sync"
    - "3.0: Focused scope - adoption only"
    - "2.0: Added remote execution features"
    - "1.0: Initial version"
---

# Trinity Onboarding

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `onboard vX.Y — recent: <summary>`. Then proceed.

Onboard any Claude Code agent to the Trinity Deep Agent Orchestration Platform. This skill guides you through the complete setup process.

## Prerequisites: Getting a Trinity Instance

**You need access to a Trinity instance before proceeding.**

### Option 1: Self-Host (Open Source)

Trinity is open source. Deploy your own instance:

1. Visit the Trinity repository: **https://github.com/abilityai/trinity**
2. Follow the installation instructions in the README
3. Once deployed, you'll have your own Trinity URL and can generate API keys

### Option 2: Managed by Ability AI

If you want Ability AI to provision and manage a Trinity instance for you:

**Contact us at: trinity@ability.ai**

We'll set you up with:
- A managed Trinity instance
- Your instance URL
- API credentials

---

## What You'll Need

Once you have a Trinity instance, gather these before starting:

| Item | Description | Example |
|------|-------------|---------|
| **Trinity URL** | Your Trinity instance URL | `https://trinity.example.com` |
| **API Key** | Your Trinity API key | `tr_abc123...` |

Get your API key from your Trinity dashboard under **Settings > API Keys**.

---

## Understanding the Local-Remote Model

Trinity uses a **paired agent architecture** where the same agent runs both locally (on your machine) and remotely (on Trinity). This enables powerful workflows that combine the best of both worlds.

### The Pairing Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub                                  │
│              (Source of Truth for Agent State)                  │
│                                                                 │
│   Skills, CLAUDE.md, template.yaml, memory/, scripts/           │
└─────────────────────┬───────────────────────┬───────────────────┘
                      │                       │
                 git push                 git pull
                      │                       │
                      ▼                       ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│      LOCAL AGENT            │   │      REMOTE AGENT           │
│    (Your Machine)           │   │      (Trinity)              │
│                             │   │                             │
│  • Interactive development  │   │  • Always-on execution      │
│  • Direct file access       │   │  • Scheduled tasks          │
│  • Quick iteration          │   │  • Background processing    │
│  • Orchestration            │   │  • API accessible           │
│                             │   │                             │
└─────────────┬───────────────┘   └───────────────┬─────────────┘
              │                                   │
              │         MCP Connection            │
              └───────────────────────────────────┘
                    (chat, execute, monitor)
```

**Key insight:** Both agents share the same identity—same skills, same instructions, same capabilities. They're synchronized through Git.

### GitHub as State Management

Your agent's **identity** lives in Git:

| What's Stored | Purpose | Synced? |
|---------------|---------|---------|
| `CLAUDE.md` | Agent's core instructions | ✓ Yes |
| `.claude/skills/` | Agent capabilities | ✓ Yes |
| `template.yaml` | Agent metadata | ✓ Yes |
| `memory/` | Persistent state, schedules | ✓ Yes |
| `scripts/` | Automation code | ✓ Yes |
| `.env`, `.mcp.json` | Credentials | ✗ No (gitignored) |
| `content/`, `session-files/` | Runtime data | ✗ No (gitignored) |

When you modify skills locally and push to GitHub, the remote agent pulls those changes and immediately has the new capabilities.

### Local Orchestrator Pattern

Your local Claude Code session acts as an **orchestrator** that controls remote execution:

```
Local (Orchestrator)                    Remote (Worker)
┌─────────────────┐                    ┌─────────────────┐
│                 │                    │                 │
│  You: "Process  │───── trigger ─────▶│  Executes task  │
│   100 videos"   │                    │  autonomously   │
│                 │                    │                 │
│  Monitor...     │◀──── status ──────│  Working...     │
│                 │                    │                 │
│  "Check status" │───── query ───────▶│  "75% done"     │
│                 │                    │                 │
│  Continue work  │                    │  Continues...   │
│  locally...     │                    │                 │
│                 │◀─── completion ────│  Done!          │
└─────────────────┘                    └─────────────────┘
```

**Benefits:**
- Start long-running tasks on remote, continue other work locally
- Remote agent runs 24/7 even when your laptop is closed
- Local agent can orchestrate multiple remote agents
- Pay for remote compute only when needed

### Heartbeat Pattern

For long-running tasks, use the **heartbeat pattern**—your local agent periodically checks on and manages remote execution:

```
Local Session                           Remote Agent
     │                                       │
     │──── "Start batch job" ───────────────▶│
     │                                       │ Working...
     │         (sleep 20 min)                │
     │                                       │
     │──── "Status check" ──────────────────▶│
     │◀─── "50% complete" ──────────────────│
     │                                       │
     │         (sleep 20 min)                │
     │                                       │
     │──── "Status check" ──────────────────▶│
     │◀─── "Done! Results at..." ───────────│
     │                                       │
```

Use scheduled skills or CronCreate to automate this polling.

### Collaboration Modes

| Mode | Tool/Command | Use Case |
|------|--------------|----------|
| **Execute** | `mcp__trinity__chat_with_agent` | Run task on remote, get response |
| **Deploy-Run** | `/trinity:sync` then `chat_with_agent` | Sync changes first, then execute |
| **Async Task** | `chat_with_agent(..., async=true)` | Fire-and-forget, poll with `get_execution_result` |
| **Scheduled** | `mcp__trinity__create_agent_schedule` | Cron-based autonomous execution (declared in `template.yaml`, see Step 3a) |

### When to Use Local vs Remote

| Scenario | Use Local | Use Remote |
|----------|-----------|------------|
| Quick edits and testing | ✓ | |
| Interactive development | ✓ | |
| File browsing and exploration | ✓ | |
| Long-running batch jobs | | ✓ |
| Scheduled daily tasks | | ✓ |
| Always-on availability | | ✓ |
| Processing while laptop closed | | ✓ |
| Orchestrating multiple agents | ✓ | |

---

## Platform Capabilities (Post-Onboarding)

Once deployed to Trinity, agents gain access to these platform features. These don't require configuration during onboarding but are important to understand for full platform utilization.

### Persistent Setup Script

Agents can persist system-level packages (apt-get, npm -g, pip) across container restarts by placing a script at `~/.trinity/setup.sh`. This file runs automatically on every container start.

```bash
# Example: ~/.trinity/setup.sh (on the remote agent)
#!/bin/bash
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg imagemagick
npm install -g typescript ts-node
pip install --user opencv-python moviepy
```

**How to set up:** Install packages on the remote agent, then append each install command to `~/.trinity/setup.sh`. The `/home/developer/` volume persists across container recreations, so the script survives image updates.

**Best practices:** Keep the script idempotent, use `-y` flags, minimize `apt-get` calls (each adds startup time).

### Voice Chat

Agents can accept real-time voice conversations via the Gemini Live API. Users click a microphone button in the Chat tab to speak naturally with the agent.

**To enable:**
1. Set `GEMINI_API_KEY` in platform environment variables
2. Set `VOICE_ENABLED=true` in platform settings
3. Create a voice system prompt file on the agent: `/home/developer/voice-agent-system-prompt.md`
   - Keep it concise (< 500 tokens), personality-focused
   - Example: "You are a helpful assistant. Keep responses under 2 sentences. Use casual, friendly language."

Transcripts are automatically saved to the chat session history.

### Channel Adapters (Slack & Telegram)

Agents can receive and respond to messages from Slack channels and Telegram groups. Each agent gets its own dedicated channel with identity customization (name + avatar).

**Slack setup** (from Trinity Settings):
1. Configure Slack OAuth credentials (Client ID, Secret, Signing Secret)
2. Install to workspace via OAuth flow
3. Per-agent: Agent Detail > Sharing > "Create Slack Channel"

**Telegram setup** (via agent .env):
- Set `ANNOUNCE_TELEGRAM_TOKEN` (from BotFather)
- Set `ANNOUNCE_TELEGRAM_UPDATES_CHANNEL` (chat ID, negative for groups)

Messages from Slack/Telegram users go through the same execution pipeline as web chat, with automatic rate limiting and audit trails.

### Per-User Persistent Memory

Public-facing agents (shared via public link) automatically maintain per-user memory for email-verified visitors. Memory is scoped to `(agent_name, user_email)` and injected into every conversation.

**No configuration needed** — this is automatic when:
- The public link has "Require email verification" enabled
- Users verify their email before chatting

Memory is summarized every 5 messages using Claude Haiku and persists across sessions.

### Execution Query Tools

Three MCP tools enable programmatic monitoring and async result polling:

| Tool | Purpose |
|------|---------|
| `list_recent_executions` | List recent executions with optional status filter |
| `get_execution_result` | Get full result of a specific execution (including transcript) |
| `get_agent_activity_summary` | High-level activity summary (by trigger type, agent) |

These are especially useful for orchestrator agents monitoring worker fleets, and for polling async task results that exceed the 60-second MCP timeout.

---

## Onboarding Workflow

```
STEP 1        STEP 1b
Check    →    Ask Goal  → ─┬─────────────────────────────────────────────┐
State                      │                                             │
                           ▼ (Deploy to Trinity)                         ▼ (Adapt only)
                    STEP 2         STEP 3        STEP 4         STEP 5   │
                    Get       →    Create   →    Configure →    Deploy   │
                    Credentials     Files         MCP            Remote   │
                                                                         │
                                   STEP 3 (partial)                      │
                                   Create Files ──────────────────────────┘
                                   (templates only)
```

**Two paths available:**
- **Deploy to Trinity**: Full setup with credentials, MCP connection, and remote deployment
- **Adapt only**: Create Trinity-compatible files without connecting to any Trinity instance

---

## STEP 1: Analyze Current State

Check what exists in this agent directory:

```bash
ls -la
ls .claude/ 2>/dev/null
ls .claude/skills/ 2>/dev/null
cat template.yaml 2>/dev/null
cat .env 2>/dev/null | head -5
```

Present findings:

```
## Current State

| Item | Status |
|------|--------|
| CLAUDE.md | [EXISTS/MISSING] |
| template.yaml | [EXISTS/MISSING] |
| .gitignore | [EXISTS/MISSING/INCOMPLETE] |
| .env | [EXISTS/MISSING] |
| .mcp.json | [EXISTS/MISSING] |
| Git repository | [YES/NO] |
```

---

## STEP 1b: Ask About Onboarding Goal

After analyzing the current state, use AskUserQuestion to determine what the user wants:

**Question:** "What would you like to do with this agent?"

**Header:** "Goal"

**Options:**

1. **Deploy to Trinity** (Recommended)
   - Description: "Make this agent Trinity-compatible AND deploy it to your Trinity instance for remote execution, scheduling, and orchestration"

2. **Adapt only (no deployment)**
   - Description: "Create Trinity-compatible files (template.yaml, .gitignore, etc.) without connecting to or deploying to a Trinity instance"

**Based on the answer:**

- **If "Deploy to Trinity"**: Continue with Steps 2-6 (full flow)
- **If "Adapt only"**: Skip to Step 3, but:
  - Skip Step 2 (Trinity connection) and Step 4 (MCP verification) — both depend on `/trinity:connect`
  - Skip Step 5 (Deploy) entirely
  - Show "Adaptation Complete" instead of "Onboarding Complete"

---

## STEP 2: Ensure Trinity Connection

**SKIP THIS STEP if user chose "Adapt only".**

Authentication and MCP configuration are owned by **`/trinity:connect`** — the single source of truth. onboard does **not** resolve credentials or write `.mcp.json` itself (duplicating that is what drifted before).

- **If the `mcp__trinity__*` tools are already available** this session, you're connected — continue to Step 3.
- **Otherwise, hand off:** tell the user to run **`/trinity:connect`** (it authenticates via email and writes `.mcp.json`, or refreshes it from a stored profile — no Trinity CLI, no manual URL/key entry), then reconnect with `/mcp` and re-run `/trinity:onboard`. Do **not** prompt for a URL/API key or write `.mcp.json` here.

When onboard later needs the instance URL (for the deploy tracking file in Step 5), read it from the active profile in `~/.trinity/config.json` (written by connect). Reading that shared artifact is fine; reimplementing connect's auth or MCP config is not.

---

## STEP 3: Create Required Files

### 3a. Create template.yaml (if missing)

Detect agent name from directory:
```bash
basename "$(pwd)"
```

Create `template.yaml`:
```yaml
name: [agent-name-lowercase]
display_name: [Agent Display Name]
description: |
  [Description - ask user or extract from CLAUDE.md]
avatar_prompt: [A vivid character description for generating the agent's avatar portrait - see below]
resources:
  cpu: "2"      # integer only: "1" | "2" | "4" | "8" | "16"
  memory: "4g"  # g-suffix only: "1g" | "2g" | "4g" | "8g" | "16g" | "32g"
```

**Resource constraints — Trinity rejects invalid values at deploy time, not before.** Trinity validates `resources` server-side and only accepts a fixed set:

| Field | Accepted values | Rejected (examples) |
|-------|-----------------|---------------------|
| `cpu` | `"1"`, `"2"`, `"4"`, `"8"`, `"16"` (whole-number string) | `"0.5"` — Trinity parses cpu with `int()`, which raises on a fractional string and is the first thing to blow up |
| `memory` | `"1g"`, `"2g"`, `"4g"`, `"8g"`, `"16g"`, `"32g"` | `"512Mi"`, `"4Gi"`, `"4096m"` — only the lowercase `g` suffix is accepted |

Keep the defaults (`cpu: "2"`, `memory: "4g"`) unless the user explicitly needs a heavier tier — and when they do, snap their request to the nearest **allowed** value rather than passing through an arbitrary number. Never write a fractional cpu or a `Mi`/`Gi`/`m` memory suffix into `template.yaml`; the deploy in Step 5 will fail validation if you do.

#### Optional: `schedules:` block — declarative scheduled tasks

`template.yaml` is the agent's design manifest, so it is also where the agent's **recommended schedules** are declared. This is the single source of truth for "what this agent is built to run on a cadence" — no separate schedules file. The split is:

- **Design (this block):** the agent declares the schedules it's built to run. Travels with the agent through git; identical on every instance.
- **Operator decision (the instance):** which of those actually fire is the live state on Trinity. The per-schedule `enabled` flag is the *recommended default*; the operator can toggle any schedule on/off post-deploy without editing `template.yaml`.

Append a `schedules:` list to `template.yaml`. Each entry's fields map one-to-one onto `create_agent_schedule`, so deploy-time setup (Step 5f) is a direct mapping:

```yaml
schedules:
  - id: weekly-report          # REQUIRED, stable — round-trips to the live schedule (stamped into its name)
    name: Weekly report        # REQUIRED — human-readable schedule name
    cron: "0 9 * * 1"          # REQUIRED — 5-field cron (min hour dom mon dow)
    timezone: America/New_York # default UTC — set it, or 9am means 9am UTC
    message: "Run /weekly-report and post the summary"  # REQUIRED — task sent to the agent on trigger
    purpose: Weekly status digest                       # human note; rendered into CLAUDE.md
    enabled: true              # the RECOMMENDED default state (operator can override on the instance)
    timeout_seconds: 900       # optional — default 15 min
    max_retries: 1             # optional — 0–5
    model: claude-opus-4-8     # optional — model override for this schedule's runs
    allowed_tools: []          # optional — least-privilege tool scoping for the run
```

**Rules:**
- `id` must be unique within the agent and stable across edits — it's how a declared schedule is matched to its live counterpart during reconcile. Use kebab-case.
- Omit the whole block if the agent has no scheduled tasks. An empty/absent block is valid.
- The `## Recommended Schedules` table in `CLAUDE.md` is a human-readable rendering of this block, not a second source of truth.

**avatar_prompt guidance:** This field is used by Trinity to generate a portrait avatar for the agent using AI image generation. Write a vivid, specific character description that captures the agent's personality and role. The prompt should describe a person or character as a portrait subject — appearance, attire, expression, setting, and lighting.

Examples:
- `A wise elder advisor in a tailored charcoal suit, silver-haired with knowing eyes, seated in a mahogany-paneled study surrounded by strategic frameworks and books, warm authoritative presence`
- `A sharp-eyed explorer with binoculars and a weathered field journal, wearing a safari vest over a crisp shirt, confident and alert expression, warm golden-hour lighting`
- `A thoughtful analyst surrounded by floating data visualizations and charts, wearing smart-casual attire with reading glasses, warm studio lighting, contemplative expression`

Ask the user to describe what character or persona fits their agent, or propose one based on the agent's purpose from CLAUDE.md.

### 3b. Create .env (agent's own secrets only)

Trinity connection credentials are **not** stored here — `/trinity:connect` keeps them in `~/.trinity/config.json` and `.mcp.json`. Create `.env` only if the agent has its **own** integration secrets (API keys for the services it calls):

```
# Agent integration secrets (example — fill with what the agent actually uses)
# SOME_SERVICE_API_KEY=...
```

After deploy, these are injected into the remote agent (Step 5e). If the agent has no secrets of its own, skip 3b and 3c.

### 3c. Create .env.example

If you created `.env`, mirror its keys with empty/placeholder values in `.env.example` (safe to commit) so a fresh clone knows what to provide.

### 3d. Create/Update .gitignore

Ensure these exclusions exist:
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
```

---

## STEP 4: Verify MCP Connection

**SKIP THIS ENTIRE STEP if user chose "Adapt only".**

`.mcp.json` is written by `/trinity:connect` (Step 2) — onboard writes **no** MCP config of its own, so there is nothing to create here. Just confirm the connection is live before deploying:

- Check that `mcp__trinity__list_agents` works. If it does, the connection is live — continue to Step 5.
- If it errors with "no connection," `.mcp.json` was just written or changed and Claude Code hasn't loaded it yet: have the user reconnect with `/mcp` (full restart only as a fallback), then re-run `/trinity:onboard`. Do **not** write `.mcp.json` here or fall back to the Trinity CLI.

---

## STEP 5: Deploy to Trinity

**SKIP THIS ENTIRE STEP if user chose "Adapt only" — go directly to Step 6.**

**Before deploying — two guardrails:**

1. **Use Trinity MCP tools for every remote operation** (deploy, credential injection, schedules) — they are the sanctioned path. If the `mcp__trinity__*` tools aren't available in this session, the MCP connection isn't live: configure it (Step 4 / `/trinity:connect`), have the user reconnect, then resume here. **Do not** fall back to the Trinity CLI or raw `curl` to deploy or configure the agent.
2. **Confirm the target instance.** The `mcp__trinity__*` tools act on whichever instance is connected as the `trinity` server. If more than one Trinity server is connected this session (e.g. `trinity` and `trinity-dgx`), a deploy can silently land on the wrong instance. Before deploying, verify `mcp__trinity__list_agents` reaches the instance from Step 2 (its URL / the tracking-file remote) and shows the agents you expect. If the intended instance is connected under a different server name, have the user reconnect it as `trinity` (`/trinity:connect`) first.

### 5a. Initialize Git (if needed)

```bash
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "Initial commit for Trinity onboarding"
fi
```

### 5b. Check for existing tracking file

Check if `.trinity-remote.yaml` exists:

```bash
cat .trinity-remote.yaml 2>/dev/null
```

If it exists, parse it as the unified remote registry (a `remotes:` map keyed by name, with a `default:`). For a **legacy single-remote file** (top-level `agent:`/`instance:`, no `remotes:`), read it as if it were the lone `default` remote.

- Identify the **target remote** — the entry whose `instance` matches the current Trinity URL, else the `default` remote.
- Read its `agent` name and `instance` URL.
- If no remote matches the current Trinity URL, warn the user:
  ```
  ⚠ The tracking file (.trinity-remote.yaml) has no remote for this instance:
    Tracking file remotes: [name → instance, ...]
    Current credentials: [current instance URL]
  
  Do you want to deploy to the current instance (adds/updates a remote in the tracking file)?
  ```
- Use the target remote's `agent` name for redeployment unless the user overrides. Leave the other remotes in the file untouched.

### 5c. Deploy Agent

Deploy using the MCP tool:

```
mcp__trinity__deploy_local_agent(
  archive: [base64-encoded tar.gz of agent directory],
  name: [agent-name from template.yaml]
)
```

To create the archive:
```bash
tar -czf /tmp/agent.tar.gz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='.venv' --exclude='.env' -C "$(pwd)" .
base64 -i /tmp/agent.tar.gz
```

After deploy succeeds, write the tracking file. This is the shared **remote registry** — the same `.trinity-remote.yaml` that `/trinity:sync` uses for multi-remote config and `/trinity:loop` reads to find this agent's remote counterpart. Record the deployed instance as a named remote (default `prod`) under a `remotes:` block:

```yaml
# .trinity-remote.yaml — remote Trinity instances of this agent.
# Shared with /trinity:sync and /trinity:loop. The instance/profile/deployed_at
# fields are maintained by onboard; sync owns branch and any extra remotes.
default: prod

remotes:
  prod:
    agent: [agent-name]
    branch: main
    instance: [TRINITY_URL]
    profile: [CLI profile name if used, or "default"]
    deployed_at: [ISO 8601 timestamp]
    description: Deployed via /trinity:onboard
```

Save this as `.trinity-remote.yaml` in the agent directory.

**If the file already exists:** don't clobber sync's config. Update only the entry whose `instance` matches `TRINITY_URL` (refresh its `agent`/`profile`/`deployed_at`), or add a new named remote for this instance if none matches. Preserve every other remote and the `default`. If you find a **legacy single-remote file** (top-level `agent:`/`instance:`, no `remotes:`), migrate it into the unified form above as the `default` remote before writing.

### 5d. Verify Deployment

```
mcp__trinity__get_agent(name: "[agent-name]")
```

Confirm the agent is running.

### 5e. Inject Credentials

The deploy archive **excludes `.env`** (the `--exclude='.env'` flag in 5c), so the freshly-deployed agent starts without the secrets stored there. Inject the credentials it needs to function — the agent's *own* integration secrets, not the Trinity connection:

```
mcp__trinity__inject_credentials(
  name: "[agent-name]",
  files: { ".env": "[contents of the local .env, minus anything Trinity-only]" }
)
```

Notes:
- The agent must be running (it is, immediately after a successful deploy).
- `inject_credentials` writes files directly into the agent workspace; the current tool accepts `.env`, `.mcp.json`, and other files. If this agent reads credentials from a **non-standard path** (e.g. `config/*.yaml`), inject `.env` and have the agent transform it on startup, or inject the actual file if the instance permits — verify against the instance rather than assuming a fixed allowlist.
- Inject only what the remote agent needs for its own work. It does **not** need the local `.mcp.json` that points back at Trinity.

If the agent has no credentials of its own, skip this step.

### 5f. Reconcile Schedules

If `template.yaml` has a `schedules:` block (see Step 3a), materialize it onto the freshly-deployed agent so the design catalog and the live instance agree.

1. **Read declared schedules** from `template.yaml`.
2. **List what's already live:** `mcp__trinity__list_agent_schedules(agent_name: "[agent-name]")`.
3. **Match by `id`** — each live schedule carries its catalog `id` as a `[id]` prefix in its `name` (e.g. `"[weekly-report] Weekly report"`). Diff declared vs live:

   | Case | Condition | Action |
   |------|-----------|--------|
   | **Create** | Declared, no live match | `create_agent_schedule(...)` with `enabled` from the manifest. Prefix the live `name` with `[id]`. |
   | **Update** | Declared and live, but cron/message/timezone/etc. differ | `update_agent_schedule(schedule_id, ...)` to match the manifest. **Do not** touch `enabled` here. |
   | **In sync** | Declared and live, identical | Nothing to do |
   | **Drift** | Live `[id]` not in the manifest | **Report, never delete.** Flag it so the operator decides (it may be operator-added). |

4. **Respect the operator on `enabled`:** set `enabled` from the manifest only when *creating*. For schedules that already exist, never flip `enabled` during reconcile — toggling on/off is the operator's call (`toggle_agent_schedule`). The manifest's `enabled` is the recommended *default at birth*, not a continuous override.
5. **Report** what was created / updated / left / flagged.

```
## Schedules Reconciled

| id | Schedule | Cron | State | Action |
|----|----------|------|-------|--------|
| weekly-audit | Weekly wizard audit | 0 10 * * 1 | enabled | created |
| weekly-inventory | Weekly inventory | 0 9 * * 1 | disabled | created (operator can enable) |

⚠ Drift: 1 live schedule not in template.yaml — "[adhoc] manual cleanup" (left as-is; remove from instance or add to template.yaml)
```

If there is no `schedules:` block, skip this step.

---

## STEP 6: Completion

Only show this when the agent is successfully deployed:

```
## Trinity Onboarding Complete!

Your agent is now live on Trinity.

### Summary
- **Agent**: [agent-name]
- **Trinity URL**: [trinity-url]
- **Status**: Running

### Files Created
- [x] template.yaml
- [x] .gitignore
- [x] .env / .env.example (only if the agent has its own secrets)
- [x] .trinity-remote.yaml (deployment tracking)

(MCP config — `.mcp.json` — is written by `/trinity:connect`, not onboard.)

### Next Steps

1. **Interact with your remote agent:**
   Use `mcp__trinity__chat_with_agent` with your agent name and message.

2. **Sync local changes to remote:**
   ```
   /trinity:sync
   ```

3. **Set up scheduled tasks:**
   Declare them in `template.yaml` under `schedules:` (see Step 3a), then re-run onboard or `/trinity:sync` to reconcile them onto the instance. For one-off changes, `mcp__trinity__create_agent_schedule` / `toggle_agent_schedule` act directly on the live agent.

4. **Add cross-session durability** (recommended):
   ```
   /agent-dev:add-git-sync
   ```
   Installs three hooks that auto-commit on session end, rebase on session start, and snapshot before compaction — keeps local and remote state consistent without manual pushes. Ideal for Trinity-deployed agents running scheduled tasks.

5. **Enable voice chat** (optional):
   Create `voice-agent-system-prompt.md` on the remote agent

6. **Connect Slack** (optional):
   Agent Detail > Sharing > "Create Slack Channel"
```

---

## STEP 6 (Alternative): Adaptation Complete

**Show this instead of the above if user chose "Adapt only":**

```
## Trinity Adaptation Complete!

Your agent is now Trinity-compatible and ready for deployment when you're ready.

### Files Created
- [x] template.yaml (agent metadata)
- [x] .gitignore (with Trinity patterns)
- [x] .env.example (only if the agent has its own secrets)

### What's NOT configured (by your choice)
- [ ] Trinity connection (`/trinity:connect` authenticates and writes `.mcp.json`)
- [ ] Remote deployment (agent not on Trinity)

### When You're Ready to Deploy

1. Run `/trinity:connect` to authenticate and configure MCP, then reconnect with `/mcp`
2. Run `/trinity:onboard` and choose "Deploy to Trinity"

### Add Cross-Session Durability (Optional)

Run `/agent-dev:add-git-sync` to install git-sync hooks — auto-commits on session end, rebases on session start. Recommended before deploying to Trinity so local and remote stay in sync automatically.

### Files Ready for Git

You can now commit these Trinity-compatible files:
```bash
git add template.yaml .gitignore   # add .env.example too if you created one
git commit -m "Add Trinity compatibility files"
```
```

---

## Mode: Analyze Only

If user runs `/trinity:onboard analyze`:

Only perform Step 1 (check state), then present a report without making any changes — do not connect or deploy.

---

## Error Handling

| Error | Resolution |
|-------|------------|
| No CLAUDE.md | Create minimal CLAUDE.md first |
| MCP tools not available | Run `/trinity:connect` (writes `.mcp.json`), then reconnect with `/mcp` — full restart only as a fallback |
| Deployment failed | Confirm the connection is live (`mcp__trinity__list_agents`); re-run `/trinity:connect` if the profile expired |
| Deploy rejected on `resources` (e.g. `invalid literal for int() with base 10: '0.5'`) | `template.yaml` has an invalid cpu/memory. cpu must be integer (`"1"`/`"2"`/`"4"`/`"8"`/`"16"`), memory must use the `g` suffix (`"1g"`..`"32g"`). Fix `template.yaml` and redeploy — see Step 3a |
| Agent already exists | Will update existing agent |
| Git clone/pull fails on remote | Configure GitHub PAT in Trinity (see below) |

---

## Troubleshooting: GitHub PAT for Private Repos

If Trinity fails to clone or pull from your GitHub repository after deployment, the most common cause is a missing or incorrectly configured GitHub Personal Access Token (PAT).

### When is a PAT Required?

- **Private repositories** — Always required
- **Public repositories** — Not required, but recommended to avoid rate limits

### Creating a Fine-Grained PAT

1. Go to **GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens**
2. Click **Generate new token**
3. Configure the token:
   - **Token name**: `Trinity` (or similar)
   - **Expiration**: Choose based on your security policy
   - **Repository access**: Select "Only select repositories" and choose the repos Trinity needs
   - **Permissions**: Under "Repository permissions", set **Contents** to **Read-only**
4. Click **Generate token** and copy the token (starts with `github_pat_`)

### Configuring the PAT in Trinity

**Option 1: Via Trinity Settings UI (Recommended)**

1. Log in to your Trinity dashboard
2. Go to **Settings**
3. Find the **GitHub PAT** field
4. Paste your token and save

**Option 2: Via Environment Variable**

Add to your Trinity `.env` file:
```bash
GITHUB_PAT=github_pat_your_token_here
```

Then restart Trinity services.

### Verifying the PAT Works

After configuring, test by:
1. Creating a new agent from your GitHub template, or
2. Triggering a git sync on an existing agent

If the pull still fails, verify:
- The PAT has not expired
- The PAT has access to the specific repository
- The PAT has the **Contents: Read** permission

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity:connect` | First-time authentication and MCP setup |
| `/trinity:sync` | Git-based synchronization with remote |

For remote operations, schedules, and credentials, use MCP tools directly:
- `mcp__trinity__chat_with_agent` — Execute tasks on remote agent
- `mcp__trinity__list_agent_schedules` / `create_agent_schedule` / `update_agent_schedule` / `toggle_agent_schedule` / `delete_agent_schedule` / `trigger_agent_schedule` / `get_schedule_executions` — Manage scheduled tasks (prefer declaring them in `template.yaml`; see Step 3a)
- `mcp__trinity__list_agents` — View deployed agents
