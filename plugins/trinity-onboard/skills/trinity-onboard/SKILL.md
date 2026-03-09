---
name: trinity-onboard
description: Onboard this agent to Trinity platform. Creates required files, configures MCP connection, and optionally deploys to remote.
argument-hint: "[analyze]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__deploy_local_agent, mcp__trinity__get_agent
metadata:
  version: "4.2"
  created: 2025-02-05
  author: Ability.ai
  changelog:
    - "4.2: Added avatar_prompt field to template.yaml generation"
    - "4.1: Added choice between full deployment and adaptation-only mode"
    - "4.0: Complete onboarding flow - files, MCP config, and remote sync"
    - "3.0: Focused scope - adoption only"
    - "2.0: Added remote execution features"
    - "1.0: Initial version"
---

# Trinity Onboarding

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

Create heartbeat skills with `/create-heartbeat` to automate this polling.

### Collaboration Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **Execute** | `/trinity-remote exec <task>` | Run task on remote, get response |
| **Deploy-Run** | `/trinity-remote run <task>` | Sync changes first, then execute |
| **Async Task** | `chat_with_agent(..., async=true)` | Fire-and-forget, check later |
| **Scheduled** | `/trinity-schedules` | Cron-based autonomous execution |
| **Heartbeat** | `/create-heartbeat` | Local-controlled polling loop |

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
  - Skip creating `.env` with credentials (Step 3b)
  - Skip creating `.mcp.json` with credentials (Step 4a)
  - Skip Step 5 (Deploy) entirely
  - Show "Adaptation Complete" instead of "Onboarding Complete"

---

## STEP 2: Get Trinity Credentials

**SKIP THIS STEP if user chose "Adapt only".**

Ask the user for their Trinity instance details using AskUserQuestion:

```
## Trinity Instance Configuration

To connect this agent to Trinity, I need your instance details.

**Don't have a Trinity instance yet?**
- Self-host: https://github.com/abilityai/trinity
- Managed service: Contact trinity@ability.ai

Please provide:

1. **Trinity Instance URL**
   The full URL to your Trinity instance (e.g., https://trinity.example.com)

2. **Trinity API Key**
   Your API key from Trinity dashboard > Settings > API Keys
```

**IMPORTANT:** Do not proceed until the user provides both values.

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
  cpu: "2"
  memory: "4g"
```

**avatar_prompt guidance:** This field is used by Trinity to generate a portrait avatar for the agent using AI image generation. Write a vivid, specific character description that captures the agent's personality and role. The prompt should describe a person or character as a portrait subject — appearance, attire, expression, setting, and lighting.

Examples:
- `A wise elder advisor in a tailored charcoal suit, silver-haired with knowing eyes, seated in a mahogany-paneled study surrounded by strategic frameworks and books, warm authoritative presence`
- `A sharp-eyed explorer with binoculars and a weathered field journal, wearing a safari vest over a crisp shirt, confident and alert expression, warm golden-hour lighting`
- `A thoughtful analyst surrounded by floating data visualizations and charts, wearing smart-casual attire with reading glasses, warm studio lighting, contemplative expression`

Ask the user to describe what character or persona fits their agent, or propose one based on the agent's purpose from CLAUDE.md.

### 3b. Create .env

**SKIP THIS STEP if user chose "Adapt only".**

Create `.env` with the user's credentials:
```
# Trinity Platform Connection
TRINITY_URL=[user-provided-url]
TRINITY_API_KEY=[user-provided-key]
```

### 3c. Create .env.example

Create `.env.example` (safe to commit):
```
# Trinity Platform Connection
# Get your API key from your Trinity dashboard > Settings > API Keys
TRINITY_URL=https://your-trinity-instance.example.com
TRINITY_API_KEY=your-api-key-here
```

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

## STEP 4: Configure MCP Connection

**SKIP THIS ENTIRE STEP if user chose "Adapt only".**

### 4a. Create .mcp.json

Create `.mcp.json` with the actual Trinity URL and API key:

```json
{
  "mcpServers": {
    "trinity": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "[TRINITY_URL]/mcp"],
      "env": {
        "API_KEY": "[TRINITY_API_KEY]"
      }
    }
  }
}
```

Replace `[TRINITY_URL]` and `[TRINITY_API_KEY]` with the actual values from the user.

### 4b. Create .mcp.json.template

Create `.mcp.json.template` with placeholders (safe to commit):

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

### 4c. Verify MCP Connection

Tell the user:

```
## MCP Configuration Created

I've created .mcp.json with your Trinity credentials.

**To activate the connection, you need to restart Claude Code.**

Please:
1. Exit this Claude Code session
2. Start Claude Code again in this directory
3. Run `/trinity-onboard` again to continue

The Trinity MCP tools will then be available.
```

**If Trinity MCP tools are already available** (check if `mcp__trinity__list_agents` works), skip to Step 5.

---

## STEP 5: Deploy to Trinity

**SKIP THIS ENTIRE STEP if user chose "Adapt only" — go directly to Step 6.**

### 5a. Initialize Git (if needed)

```bash
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "Initial commit for Trinity onboarding"
fi
```

### 5b. Deploy Agent

Use the Trinity MCP tool to deploy:

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

### 5c. Verify Deployment

```
mcp__trinity__get_agent(name: "[agent-name]")
```

Confirm the agent is running.

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
- [x] .env (with your credentials)
- [x] .env.example (template)
- [x] .gitignore
- [x] .mcp.json (with your credentials)
- [x] .mcp.json.template (template)

### Next Steps

1. **Interact with your remote agent:**
   ```
   /trinity-remote exec "Hello, what can you do?"
   ```

2. **Sync local changes to remote:**
   ```
   /trinity-sync push
   ```

3. **Push credentials after changes:**
   ```
   /credential-sync push
   ```

4. **Set up scheduled tasks:**
   ```
   /trinity-schedules
   ```
```

---

## STEP 6 (Alternative): Adaptation Complete

**Show this instead of the above if user chose "Adapt only":**

```
## Trinity Adaptation Complete!

Your agent is now Trinity-compatible and ready for deployment when you're ready.

### Files Created
- [x] template.yaml (agent metadata)
- [x] .env.example (credential template)
- [x] .gitignore (with Trinity patterns)
- [x] .mcp.json.template (MCP config template)

### What's NOT configured (by your choice)
- [ ] .env (no credentials stored)
- [ ] .mcp.json (no MCP connection)
- [ ] Remote deployment (agent not on Trinity)

### When You're Ready to Deploy

Run `/trinity-onboard` again and choose "Deploy to Trinity" to:
1. Connect to your Trinity instance
2. Configure MCP tools
3. Deploy this agent to the platform

### Files Ready for Git

You can now commit these Trinity-compatible files:
```bash
git add template.yaml .env.example .gitignore .mcp.json.template
git commit -m "Add Trinity compatibility files"
```
```

---

## Mode: Analyze Only

If user runs `/trinity-onboard analyze`:

Only perform Steps 1-2 (check state and gather info), then present a report without making any changes.

---

## Error Handling

| Error | Resolution |
|-------|------------|
| No CLAUDE.md | Create minimal CLAUDE.md first |
| MCP tools not available | Restart Claude Code after creating .mcp.json |
| Deployment failed | Check Trinity URL and API key are correct |
| Agent already exists | Will update existing agent |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity-compatibility` | Read-only audit of current state |
| `/trinity-sync` | Git-based synchronization with remote |
| `/trinity-remote` | Remote agent operations |
| `/trinity-schedules` | Scheduled task management |
| `/credential-sync` | Sync credentials to remote |
