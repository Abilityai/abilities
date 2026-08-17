---
name: onboard
description: Onboard this agent to Trinity platform. Creates required files, configures MCP connection, and optionally deploys to remote.
argument-hint: "[analyze | in-place]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__create_agent, mcp__trinity__deploy_local_agent, mcp__trinity__get_agent, mcp__trinity__inject_credentials, mcp__trinity__get_agent_github_pat_status, mcp__trinity__set_agent_github_pat, mcp__trinity__initialize_github_sync, mcp__trinity__git_pull, mcp__trinity__get_git_sync_state, mcp__trinity__list_agent_schedules, mcp__trinity__create_agent_schedule, mcp__trinity__update_agent_schedule, mcp__trinity__toggle_agent_schedule, mcp__trinity__get_agent_compatibility_report, mcp__trinity__git_sync
metadata:
  version: "6.0"
  created: 2025-02-05
  author: Ability.ai
  changelog:
    - "6.0: In-place onboarding + the plugins: block (trinity#1704, ent#411). NEW goal in Step 1b, auto-recommended when the skill detects it is running INSIDE a deployed Trinity agent (AGENT_NAME env, /home/developer, ~/.trinity/): make the agent Trinity-compatible in place — write the files, install/declare its plugins, commit + push back (source mode is pull-only, so an in-place result that is not pushed is lost on reset — the skill pushes with the agent's write credentials, or hands back a patch and says so), reconcile schedules live, and VERIFY via mcp__trinity__get_agent_compatibility_report (0 HARD) instead of its own checklist (trinity#2137 alignment). Step 3a teaches the plugins: block (marketplaces + installed → committed ~/.trinity/plugins.yaml, re-installed headlessly on every container boot; the interactive /plugin install was never the mechanism, the CLI is); every scaffold now declares trinity@abilityai. Deployment paths gains Path C — deploy the bare repo as-is, then onboard in place — with the one-line headless bootstrap for agents that predate the block. Path A/B completions also end with the compat-report verification"
    - "5.3: Conform to the playbook-call grammar (`protocols/playbook-call.md`, abilities#15): the documented `schedules:` example now shows the message as a bare playbook call (`/weekly-report`) rather than a prose sentence wrapping one — the example is what every reader copies. A prose message is a second copy of the playbook's procedure living in an unversioned scheduler field, free to drift from the SKILL.md that owns it; it also names no playbook, so the /audit-wizards autonomy-mode gate cannot see a gated skill scheduled that way"
    - "5.2: Platform-truth refresh (Trinity dev 88a4e2f7) — TWO gates decide whether a schedule fires, and the second was undocumented: agent autonomy defaults OFF on every new agent, the scheduler skips all cron triggers while it is off and writes NO execution row, and there is no MCP tool for it (turn it on in the UI after deploy). Schedule reconcile now matches on the literal `name` (ent#89 materializes it verbatim and dedups on it) — the old `[id]`-prefixed name could never collide, so Path A agents got DUPLICATE double-firing schedules. Declared schedules honour six keys only (timeout_seconds/max_retries/model/allowed_tools are dropped on the github: path), bounded at 20 entries, armed only by a literal YAML true, never re-applied on recreate. New Step 3b teaches credentials:/credential_setup: (ent#128/#127, gate T-015). Step 4 now teaches .mcp.json.template (trinity#2007): ${VAR} in env blocks ONLY — a placeholder in command/url/args withholds the whole server — and the command allowlist. .gitignore scaffold gains .claude/settings.json + the negation escape hatch (trinity#2036)"
    - "5.1: Teach the event layer's emit side — agents can publish custom domain events via emit_event(event_type, payload) and any agent that should react subscribes ITSELF via subscribe_to_event ({{payload.field}} interpolates into the task it receives; self-service, no on-behalf wiring), with the two safety caveats: no recursion guard outside agent.task.* (keep custom event graphs acyclic — a cycle runs forever at real spend) and wakes reach only running subscribers (at-most-once, no replay)"
    - "5.0: Repository-first deployment — Path A (default) creates the agent from its GitHub repo via create_agent(template: github:owner/repo@branch), which Trinity clones and tracks in source mode; Path B (local tar.gz via deploy_local_agent) stays as the fallback for repos that don't exist yet, and now offers initialize_github_sync to promote the agent onto the repo path. New Step 4b gates deploy on GitHub readiness (token tier + pushed remote) before any deploy runs, new 'Deployment paths' section states the doctrine, Step 5f is path-aware (github: templates materialize template.yaml schedules at creation, ent#89), Step 6 teaches push→git_pull as the update loop, and the PAT troubleshooting section is rewritten against the real resolver (per-agent → per-user → global, ent#162) incl. the tokenless public-repo path (ent#123) and create-time access validation (#218)"
    - "4.15: Platform-truth refresh (Trinity dev 62ae49f9) — prerequisites point at /trinity:connect (trinity_mcp_ keys, no manual copy), stall-watchdog claim corrected (1800s, mcp__* tools only, #1369), schedule timeout inherits the agent's 60-min cap (not 15), chat_with_agent queued_timeout receipt at ~25s + agent.task.* event report-back (#1578), reports pruned past agent_reports_retention_days (90d), display-label-vs-slug note"
    - "4.14: Next Steps now includes 'Publish structured reports' — deployed agents end result-producing/scheduled skills with a guarded mcp__trinity__report call so output lands on the Reports tab (append-only history complementing the live dashboard.yaml snapshot), guarded to skip silently off-Trinity"
    - "4.13: New 'Long-running jobs inside a run' subsection — a headless/scheduled execution is a single agent turn and CANNOT host a job longer than the ~10-min synchronous Bash window (a hard platform ceiling): the harness auto-backgrounds it, active waiting is blocked, and ending the turn reaps every background task/monitor (fires `killed`, not `completed`). >~10-min work must decouple to an OS-level cron/systemd/sidecar + done-marker; the run only triggers/verifies. Annotated the Async Task row and added a timeout_seconds Rule accordingly. Always verify the artifact moved, never trust exit code/business_status"
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
| **MCP Key** | Provisioned automatically by `/trinity:connect` | `trinity_mcp_...` |

Run `/trinity:connect` first — it authenticates and provisions the MCP key (`trinity_mcp_...`) automatically; no manual key copying from the dashboard.

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

### Deployment paths — the repository is the default

There are two ways to get an agent onto Trinity, and they are **not equal**. The repository path is the one the platform is built around; the local-archive path exists for the cases the repository path can't cover.

| | **Path A — from the GitHub repo** (default) | **Path B — from local files** (fallback) |
|---|---|---|
| Call | `mcp__trinity__create_agent(template: "github:owner/repo[@branch]")` | `mcp__trinity__deploy_local_agent(archive: <base64 tar.gz>)` |
| What lands remotely | Trinity **clones the repo** into the agent workspace and tracks the branch | An unpacked snapshot of your working directory |
| Ongoing updates | `git push` locally → `mcp__trinity__git_pull` remotely (or `/trinity:sync`) | Re-archive and re-deploy the whole agent |
| Reproducible | Yes — the deployed state is a commit anyone can name | No — it's whatever your disk held that minute |
| Declared `schedules:` | **Materialized at creation** — Trinity reads `template.yaml` from the repo (trinity-enterprise#89) | Created afterwards by this skill (Step 5f) |
| Needs | A pushed repo + a GitHub token Trinity can read it with (public repos: no token needed) | Nothing but local files |

**The sequence, in order:** connect (`/trinity:connect`) → **configure the GitHub token** → **push the agent to a repo** → deploy from the repo. Step 4b enforces it.

**Use Path B when** the agent has no repo yet, the repo can't be reached from the instance (air-gapped or self-hosted GitHub), or you're deploying a throwaway. After a Path-B deploy, promote the agent onto the repo path with `mcp__trinity__initialize_github_sync` so subsequent updates are git-native — a long-lived agent should not stay on the archive path.

**Credentials travel the same way on both paths.** `.env` is gitignored, so it is never in the clone *or* the archive — inject it after deploy (Step 5e).

**Path C — deploy the bare repo as-is, then onboard *in place*.** For a repo you cannot (or should not) adapt locally — someone else's agent, a repo with no `template.yaml` at all — the platform still creates the agent (`create_agent(template: "github:owner/repo")` tolerates a missing `template.yaml`; the agent just lands with no declared resources/schedules/plugins). Then run **this skill inside that agent** and pick *Onboard in place* (Step 1b): it writes the files, installs and declares the plugins, pushes them back, and verifies with the platform's own compatibility report. What it needs: the `trinity` plugin present in the container. Since trinity#1704 that is a declaration (`template.yaml plugins:`, Step 3a) re-installed headlessly on every boot — but an agent that predates the block has nothing declared yet, so bootstrap it once with the CLI the boot hook itself uses (a plain terminal call, not the interactive `/plugin` command):

```bash
claude plugin marketplace add abilityai/abilities && claude plugin install trinity@abilityai --yes
```

Then start a fresh session and run `/trinity:onboard`. (ent#411 asks the platform to pre-install the `trinity` plugin in the agent base image so this bootstrap disappears.)

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

### Long-running jobs inside a run

The heartbeat pattern above is *local orchestrating remote* — safe, because the local session persists. A harder trap bites when the **remote agent itself** kicks off a job inside one of its own **scheduled/headless** runs (a FAISS/index rebuild, full bootstrap, bulk embedding, a large migration). **A headless execution is a single agent turn, and it cannot host a job longer than the synchronous Bash window (~10 min max tool timeout). This is a hard platform ceiling, not a tuning problem** — do **not** try to "oversee it in-turn," and do not trust streaming output or a monitor to save it.

The failure chain, observed end-to-end with streaming working:

1. You run the job as one foreground streaming call (correct). Because it outruns the ~10-min synchronous Bash ceiling, **the harness auto-backgrounds it** — not your choice; it returns *"running in background, you'll be notified on completion."*
2. You **cannot actively wait**: `sleep`/poll loops are blocked (*"use monitor with an until-loop"*).
3. So you arm a **monitor** and, with no other work to do, **end the turn** to await the completion event.
4. **Ending the turn (= the execution finalizing) kills every background task and monitor spawned in it.** The job dies mid-run; the completion event fires as **`killed`, not `completed`**; the promised re-invoke never happens.

Streaming heartbeat output changes nothing — the no-output stall watchdog (`AGENT_TOOL_STALL_LIMIT_S`, default 1800s) watches `mcp__*` tools only since trinity#1369, and neither the ~10-min sync ceiling nor the turn-end reaping cares about output. The async background-task / monitor / re-invoke model works in an **interactive** session (which persists) but **NOT** in a **headless** execution (which ends the turn and reaps its tasks).

**The rule:**

- **Finishes within ~10 min:** run it as one **foreground, un-piped, streaming** Bash call, in-turn. Do **not** pipe through `tail`/`grep` — that buffers output and re-arms the stall watchdog.
- **Longer than ~10 min** (full FAISS rebuild, bulk embedding, big migrations): it **MUST run outside the agent turn**. Model the heavy work as an **OS-level job** in the container — a **cron/systemd unit** or a small **sidecar** — that builds the artifact and writes a **done-marker**. The scheduled execution then does only the **fast** parts: check the marker / artifact freshness, and if fresh, run the quick follow-ups (index verify, downstream bootstrap). Size the schedule's `timeout_seconds` for those fast parts, never for the heavy job.
- **Never** "fire a background task and end the turn to await a notification" in a headless execution — the task is reaped the instant the turn ends.

**Always verify the artifact.** Never report success off an exit code or `business_status`. Confirm the output *actually moved* — e.g. `brain.faiss` mtime advanced **and** `run_connections.sh --stats --json` returns count > 0 — before declaring done. A run that ends without the artifact changing is a **failure**, not a `skipped`.

### Collaboration Modes

| Mode | Tool/Command | Use Case |
|------|--------------|----------|
| **Execute** | `mcp__trinity__chat_with_agent` | Run task on remote, get response |
| **Deploy-Run** | `/trinity:sync` then `chat_with_agent` | Sync changes first, then execute |
| **Async Task** | `chat_with_agent(..., async=true)` | Fire-and-forget the *local→remote trigger*, poll with `get_execution_result`. This does **not** license the remote run to spawn a >~10-min child and end the turn — the turn-end reaps it. Decouple such work to an OS-level job (see *Long-running jobs inside a run*) |
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

These are especially useful for orchestrator agents monitoring worker fleets, and for polling async task results: a sync `chat_with_agent` call that outlives `MCP_CHAT_TIMEOUT_MS` (~25s) returns a `{status: "queued_timeout", execution_id}` receipt — poll `get_execution_result` with that id instead of re-sending. For push-style report-back, subscribe to the worker's backend-emitted `agent.task.completed` / `agent.task.failed` events (trinity#1578) instead of polling.

The same event layer carries **custom domain events** for agent-to-agent wiring: an agent publishes with `emit_event(event_type, payload)` in a namespace it owns (e.g. `research.done`), and any agent that should react subscribes **itself** with `subscribe_to_event(source_agent, event_type, target_message)` — subscriptions are self-service (the caller is always the subscriber; there is no wiring on another agent's behalf), and `{{payload.field}}` placeholders interpolate event data into the task the subscriber receives. Two caveats: only `agent.task.*` has a recursion guard, so keep custom event graphs **acyclic** (A→B→A on custom events runs forever, each hop at real spend), and a wake only reaches a *running* subscriber — delivery is at-most-once with no replay for stopped agents.

---

## Onboarding Workflow

```
STEP 1        STEP 1b
Check    →    Ask Goal  → ─┬─────────────────────────────────────────────────────┐
State                      │                                                     │
                           ▼ (Deploy to Trinity)                                 ▼ (Adapt only)
                    STEP 2       STEP 3      STEP 4     STEP 4b     STEP 5       │
                    Get      →   Create  →   Verify  →  GitHub  →   Deploy       │
                    Connected    Files       MCP        readiness   (repo first) │
                                                        (token+repo)             │
                                             STEP 3 (partial)                    │
                                             Create Files ────────────────────────┘
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

**Am I running inside a deployed Trinity agent?** Check the container markers before asking anything — they decide which goal Step 1b recommends:

```bash
[ -n "$AGENT_NAME" ] && echo "AGENT_NAME=$AGENT_NAME"      # set by the Trinity agent server
[ "$HOME" = "/home/developer" ] && [ -d "$HOME/.trinity" ] && echo "trinity workspace volume"
git remote get-url origin 2>/dev/null; git config --get branch.$(git branch --show-current 2>/dev/null).remote 2>/dev/null
[ -n "$GIT_SOURCE_MODE" ] && echo "GIT_SOURCE_MODE=$GIT_SOURCE_MODE (source mode = pull-only)"
```

Two or more markers ⇒ **in-place context**: the agent already exists on Trinity, the "deploy" half of this skill is moot, and the job is to make *this* workspace compatible and get the result back into its repo. Record `IN_PLACE=1` and the agent name (`$AGENT_NAME`).

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
| Running inside a deployed Trinity agent | [YES — `$AGENT_NAME` / NO] |
| Write credentials for push-back (in-place only) | [YES / NO — source mode, tokenless] |
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

3. **Onboard in place** *(list this FIRST and mark it Recommended when Step 1 detected the in-place context; otherwise omit it)*
   - Description: "This agent is already deployed on Trinity as `$AGENT_NAME`. Make this workspace Trinity-compatible in place — write template.yaml (with plugins:), .env.example, .gitignore, .mcp.json.template; install + declare plugins; push the result back to the repo; reconcile schedules; verify with the platform's compatibility report."

**Based on the answer:**

- **If "Onboard in place"**: run Step 3 (files) then jump to **Step 5-IP** — skip Step 2 (this agent *is* connected: its `mcp__trinity__*` tools come from the platform-injected MCP entry), Step 4b and Step 5 (nothing to deploy). Finish with Step 6-IP.

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
display_name: [Agent Display Name]   # note: the live UI's "rename" edits a display label (ent#181), not the deployed slug (`name`)
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
- **Operator decision (the instance):** which of those actually fire is the live state on Trinity — and it is **two gates, not one**:
  1. **The per-schedule `enabled` flag**, applied only at creation. An entry that omits `enabled`, or gives anything other than a literal YAML `true`, lands **disabled** (trinity-enterprise#89).
  2. **The agent's autonomy gate**, which is **OFF for every newly created agent** (`agent_ownership.autonomy_enabled` defaults to `0`). While it is off the scheduler refuses to fire any cron trigger — the schedule shows as enabled, nothing runs, and **no execution row is written**, so there is nothing in the run history to notice. There is no MCP tool for this; after deploying, tell the user to turn autonomy on for the agent in the Trinity UI (`PUT /api/agents/{name}/autonomy`), or their schedules are live and silently inert.

Append a `schedules:` list to `template.yaml`. **Trinity's creation-time reader honours exactly six keys** — `name`, `cron`, `message`, `enabled`, `timezone`, and `description` (`purpose` is accepted as an alias). `timeout_seconds`, `max_retries`, `model`, and `allowed_tools` are valid arguments to `create_agent_schedule` but are **dropped** when Trinity materializes the block from a `github:` repo — declare them here for the reconcile path (Step 5f), and expect a Path-A schedule to carry platform defaults instead. Hard bounds: **20 entries per template** (extras dropped), `name` ≤ 200 chars, `message` ≤ 10 000 chars (truncated), `description` ≤ 1000 chars (dropped); a malformed entry is dropped silently rather than failing the create.

```yaml
schedules:
  - id: weekly-report          # REQUIRED, stable — round-trips to the live schedule (stamped into its name)
    name: Weekly report        # REQUIRED — human-readable schedule name
    cron: "0 9 * * 1"          # REQUIRED — 5-field cron (min hour dom mon dow)
    timezone: America/New_York # default UTC — set it, or 9am means 9am UTC
    message: "/weekly-report"  # REQUIRED — the playbook call sent on trigger: one line, `/playbook [args]`, never prose (a prose message is a second copy of the playbook's procedure, free to drift from it)
    purpose: Weekly status digest                       # human note; rendered into CLAUDE.md
    enabled: true              # the RECOMMENDED default state (operator can override on the instance)
    timeout_seconds: 900       # optional — omit to inherit the agent's execution cap (default 60 min); must be ≤ that cap or schedule create 400s
    max_retries: 1             # optional — 0–5
    model: claude-opus-4-8     # optional — model override for this schedule's runs
    allowed_tools: []          # optional — least-privilege tool scoping for the run
```

**Rules:**
- `id` must be unique within the agent and stable across edits — it's how a declared schedule is matched to its live counterpart during reconcile. Use kebab-case.
- Omit the whole block if the agent has no scheduled tasks. An empty/absent block is valid.
- Size `timeout_seconds` for the work the run *actually does in-turn*. A run that only triggers-and-verifies a decoupled OS-level job stays fast, so a modest value like the example's 900s is plenty (omitted = the agent's 60-min cap). A run must **not** try to host a >~10-min job itself — the harness auto-backgrounds it past ~10 min and the turn-end reaps it, so a bigger timeout does not save it (see *Long-running jobs inside a run*).
- The `## Recommended Schedules` table in `CLAUDE.md` is a human-readable rendering of this block, not a second source of truth.

#### Required since trinity#1704: `plugins:` block — the agent's Claude Code plugins, declared

Trinity installs an agent's marketplace plugins from **this block**, not from anyone typing `/plugin install`. At creation the platform materializes it as a committed, secret-free `~/.trinity/plugins.yaml`; on **every container boot** `startup.sh` reconciles it headlessly (`claude plugin marketplace add <source>` / `claude plugin install <plugin>@<mkt> --yes`, no TTY, timeout-bounded, after credential injection — zero subprocesses when everything is already present). It is what makes the selection survive a fresh-volume rebuild or a move to another host, and it is the *only* way a headless agent gets a plugin without a human in a terminal. Always declare at least `trinity@abilityai` — it is what lets the deployed agent run `/trinity:sync` and, for a bare repo, `/trinity:onboard` in place (Path C).

```yaml
plugins:
  marketplaces:
    - name: abilityai
      source: abilityai/abilities        # owner/repo shorthand, or an https:// URL — never user:token@, never ../ or a leading -
  installed:
    - trinity@abilityai                  # plugin@marketplace; every marketplace referenced must be declared above
    # - agent-dev@abilityai              # add whatever this agent's skills actually depend on
  # enabledPlugins: { trinity@abilityai: true }   # alternative shape mirroring Claude's settings.json — false entries are dropped
```

Rules that bite:
- **Declare what the agent uses, nothing decorative** — each plugin is a boot-time fetch. Mirror the list in CLAUDE.md's "Installed Plugins" section so the two never disagree.
- **`plugin@marketplace` pins identity, not a commit** — a re-install fetches the marketplace's current content (a commit-pinned mode is a planned follow-up, trinity-enterprise#192).
- **Runtime installs are not captured back** — a plugin someone adds later with `/plugin install` (or the CLI) is lost on reconstitution unless it is added here too.
- **A private marketplace needs the agent's `GITHUB_PAT`** at boot (seeded as `GH_TOKEN` by the hook); a public one needs only network. Air-gapped instances see a named `withheld:<reason>` in the boot summary — never a fatal.
- **Materialization is creation-time; the boot hook is the runtime path.** Adding the block to an existing agent's `template.yaml` takes effect on the next restart via the hook's template fallback — or immediately if you run the same two CLI calls yourself (Step 5-IP does).

**avatar_prompt guidance:** This field is used by Trinity to generate a portrait avatar for the agent using AI image generation. Write a vivid, specific character description that captures the agent's personality and role. The prompt should describe a person or character as a portrait subject — appearance, attire, expression, setting, and lighting.

Examples:
- `A wise elder advisor in a tailored charcoal suit, silver-haired with knowing eyes, seated in a mahogany-paneled study surrounded by strategic frameworks and books, warm authoritative presence`
- `A sharp-eyed explorer with binoculars and a weathered field journal, wearing a safari vest over a crisp shirt, confident and alert expression, warm golden-hour lighting`
- `A thoughtful analyst surrounded by floating data visualizations and charts, wearing smart-casual attire with reading glasses, warm studio lighting, contemplative expression`

Ask the user to describe what character or persona fits their agent, or propose one based on the agent's purpose from CLAUDE.md.

### 3b. Declare the agent's credentials in `template.yaml`

Before writing `.env`, declare **what** the agent needs. `credentials:` is **names-only** — it lists variable names, never values. The optional `credential_setup:` block (trinity-enterprise#128) *decorates* each declared name with `title` / `description` / `required` / `secret` / `format` / `setup_url`; it cannot introduce a name that `credentials:` doesn't declare (undeclared entries are dropped).

```yaml
credentials:
  env_file: [SOME_SERVICE_API_KEY]
  mcp_servers:
    some_service:
      env_vars: [SOME_SERVICE_API_KEY]

credential_setup:
  - name: SOME_SERVICE_API_KEY
    title: Some Service API key
    description: Lets the agent read and write the user's Some Service workspace.
    required: true
    secret: true
    format: secret
    setup_url: https://someservice.example.com/settings/api-keys
```

This block is what drives the platform's guided checklist — after deploy, `GET /api/agents/{name}/credential-requirements` (trinity-enterprise#127) reports declared-vs-populated against a live container probe — and it is what the compatibility gates read: every `${VAR}` used in `.mcp.json.template` must appear here, or the agent HARD-fails check T-015. An agent with genuinely no secrets should declare an explicit `credentials: {}` rather than omitting the block.

### 3c. Create .env (agent's own secrets only)

Trinity connection credentials are **not** stored here — `/trinity:connect` keeps them in `~/.trinity/config.json` and `.mcp.json`. Create `.env` only if the agent has its **own** integration secrets (API keys for the services it calls):

```
# Agent integration secrets (example — fill with what the agent actually uses)
# SOME_SERVICE_API_KEY=...
```

After deploy, these are injected into the remote agent (Step 5e). If the agent has no secrets of its own, skip 3c and 3d (still declare `credentials: {}` in 3b).

### 3d. Create .env.example

If you created `.env`, mirror its keys with empty/placeholder values in `.env.example` (safe to commit) so a fresh clone knows what to provide.

### 3e. Create/Update .gitignore

Ensure these exclusions exist:
```gitignore
# Credentials - never commit
.mcp.json
.env
.env.*
*.pem
*.key
credentials.json

# Claude Code internals
.claude.json
.claude.json.backup
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/
.claude/sessions/
.claude/shell-snapshots/
.claude/plugins/
.claude/backups/
# Container-only config: the Trinity base image bakes ~/.claude/settings.json
# registering guardrail hooks by ABSOLUTE container path, and HOME is the repo
# root. A committed copy bricks any clone made outside the container — the
# missing hook script exits 2, which Claude Code reads as "block this tool
# call", so every Bash/Edit/Write fails there. Trinity enforces this fleet-wide
# and untracks an already-committed copy on the next Push (trinity#2036).
.claude/settings.json

# Runtime
content/
session-files/
```

**Keep this list in step with the platform's own.** Trinity applies `_GITIGNORE_PATTERNS` to every agent repo on each Push and `git rm --cached`s anything newly matched, so a scaffold that omits an entry doesn't win — it just churns. If a skill genuinely needs `.claude/settings.json` tracked (e.g. `/agent-dev:add-git-sync` registers its hooks there), the sanctioned escape hatch is to add the plain rule **and then** a negation, in that order:

```gitignore
.claude/settings.json
!.claude/settings.json
```

The plain line satisfies Trinity's exact-line `grep -qxF` check so it stops appending its own copy; the negation comes last so git's last-match-wins re-includes the file. Verify with `git check-ignore -v .claude/settings.json` before pushing.

---

## STEP 4: Verify MCP Connection

**SKIP THIS ENTIRE STEP if user chose "Adapt only".**

`.mcp.json` is written by `/trinity:connect` (Step 2) — onboard writes **no** *local* MCP config of its own, so there is nothing to create here. Just confirm the connection is live before deploying:

- Check that `mcp__trinity__list_agents` works. If it does, the connection is live — continue to Step 5.
- If it errors with "no connection," `.mcp.json` was just written or changed and Claude Code hasn't loaded it yet: have the user reconnect with `/mcp` (full restart only as a fallback), then re-run `/trinity:onboard`. Do **not** write `.mcp.json` here or fall back to the Trinity CLI.

**If the deployed agent needs MCP servers of its own**, commit a **`.mcp.json.template`** to the repo — it is the one MCP file that belongs in git (`.mcp.json` itself stays ignored). Since trinity#2007 the container renders it into `~/.mcp.json` at every startup, substituting `${VAR}` / `${VAR:-default}` from the agent's `.env` (inject it in Step 5e). Three rules the renderer enforces:

- **Substitution happens inside `env` blocks only.** A `${VAR}` in `command`, `url`, or `args` makes the renderer **withhold the whole server** with a named reason in the container log — it is not a warning, the server simply isn't there.
- **`command` must be an allowlisted literal**: `npx`, `uvx`, `python`, `python3`, `node`, `bun`, `deno`, `docker`. (`uv` is *not* on the list — use `uvx`.)
- **It refuses rather than blanks.** A placeholder with no value withholds that server instead of configuring it with `""`, and the merge never clobbers Trinity's own injected `trinity` entry.

This needs a rebuilt base image, so an agent created before the fix gains it on `/rebuild-agent` or recreate.

---

## STEP 4b: GitHub Readiness (gate for the default deploy path)

**SKIP if the user chose "Adapt only."**

Deployment is repository-first (see *Deployment paths* above), so establish the repo and the token **before** deploying — not as a recovery step after a local deploy. Two things must be true.

**1. The agent is a pushed GitHub repo.**

```bash
git remote get-url origin 2>/dev/null
git status --porcelain            # uncommitted work won't be in the clone
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null | head   # unpushed commits
```

| Finding | Action |
|---|---|
| No `origin` | Offer to create one: `gh repo create <agent-name> --private --source=. --push`. If `gh` is missing or the user declines, note that deploy falls back to Path B and continue. |
| Uncommitted changes | Commit them — Trinity clones the **remote**, so anything uncommitted simply won't exist on the deployed agent. |
| Unpushed commits | `git push` — same reason. Never deploy from a branch whose tip only exists locally. |
| Clean and pushed | Ready for Path A. Record `owner/repo` and the current branch. |

**2. Trinity can read that repo.** Resolution order at creation is **per-agent PAT → the creating user's personal token (Settings) → the platform/admin token** (ent#162).

- **Public repo:** no token needed — Trinity clones anonymously (ent#123). Still recommended to avoid GitHub's anonymous rate limits.
- **Private repo:** a token is **required**. Have the user add a fine-grained PAT with **Contents: Read** under **Settings → GitHub token** in the Trinity UI (that's the personal-token tier and it beats the shared admin token). Full instructions in *Troubleshooting: GitHub PAT* below.
- Don't guess: there is no MCP call that reports the user/global token tier before an agent exists. Ask the user to confirm a token is configured, and rely on the fact that `create_agent` **fails loudly** (400, naming the repo) if the resolved token can't read it — see the error table.

**Then choose the path** and carry it into Step 5:

- **Path A (default):** clean, pushed repo that Trinity can read.
- **Path B (fallback):** anything else — no repo, unreachable repo, or the user deliberately wants a snapshot deploy.

State the chosen path in one line before deploying (e.g. *"Deploying from `github:acme/my-agent@main`"*), so a wrong path is caught before it lands.

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

**Already deployed?** If Step 5b found a remote for this instance and `mcp__trinity__get_agent` confirms the agent exists, this is an *update*, not a create:

- **Repo-deployed agent (Path A):** do **not** call `create_agent` again — the name is taken and the workspace is a clone. Push locally, then `mcp__trinity__git_pull(agent_name)` (or run `/trinity:sync push`). Skip to 5e/5f.
- **Archive-deployed agent (Path B):** re-deploying with `deploy_local_agent` creates a new version (`my-agent-2`) and stops the old one. Prefer promoting it to Path A first (5c-B, final note).

Otherwise deploy via the path chosen in Step 4b.

#### 5c-A. Deploy from the GitHub repository (default)

```
mcp__trinity__create_agent(
  name: [agent-name from template.yaml],
  template: "github:[owner]/[repo]",     # add @branch for a non-default branch
  source_branch: [branch],               # e.g. "main"
  resources: { cpu: "[cpu]", memory: "[memory]" }   # from template.yaml — see the note below
)
```

Trinity clones the repo into the agent workspace, tracks that branch in **source mode (pull-only)**, materializes the repo's declared `schedules:` (Step 5f), and starts the agent.

Notes that bite if ignored:

- **`resources` must be passed explicitly.** For a dynamic `github:owner/repo` reference, Trinity does not read `resources:` out of your `template.yaml` — it uses what the call passes, and omitting it silently applies the platform default (`cpu: "2"`, `memory: "4g"`, unless the instance sets its own). Read the values from `template.yaml` and forward them (cpu integer strings `"1"`/`"2"`/…, memory lowercase-g `"4g"`). The repo's declared `schedules:` *are* read from `template.yaml`; `resources:` are not — don't generalize from one to the other.
- **The branch must exist on the remote** — a bad branch is rejected at creation, not silently.
- **`@branch` in the template string and `source_branch` mean the same thing;** pass either, and if you pass both keep them identical.
- **The deployed state is the remote's tip**, not your working tree. This is the point of the path — but it means Step 4b's "clean and pushed" check is load-bearing.

#### 5c-B. Deploy from local files (fallback)

Use when Step 4b landed on Path B.

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

**After a Path-B deploy, offer to promote the agent onto the repository path** — unless it's deliberately throwaway:

```
mcp__trinity__initialize_github_sync(
  agent_name: [agent-name],
  repo_owner: [owner],
  repo_name: [repo],
  private: true
)
```

This creates the repo (when asked), pushes the deployed workspace to it, and wires git sync — after which updates are `git push` + `git_pull` like any Path-A agent. Say plainly why: an archive-deployed agent has no reproducible source, and every future change means re-uploading the whole directory.

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
    source: github:[owner]/[repo]   # Path A — omit or use "local-archive" for Path B
    description: Deployed via /trinity:onboard
```

The `source` field records **how** this remote was deployed, so a later run (or `/trinity:sync`) knows whether updates flow through `git_pull` or a re-archive. A remote reading `local-archive` is a standing invitation to promote it (5c-B).

Save this as `.trinity-remote.yaml` in the agent directory.

**If the file already exists:** don't clobber sync's config. Update only the entry whose `instance` matches `TRINITY_URL` (refresh its `agent`/`profile`/`deployed_at`), or add a new named remote for this instance if none matches. Preserve every other remote and the `default`. If you find a **legacy single-remote file** (top-level `agent:`/`instance:`, no `remotes:`), migrate it into the unified form above as the `default` remote before writing.

### 5d. Verify Deployment

```
mcp__trinity__get_agent(name: "[agent-name]")
```

Confirm the agent is running. **On Path A, also confirm the clone actually landed on the commit you expect:**

```
mcp__trinity__get_git_sync_state(agent_name: "[agent-name]")
```

Check the tracked repo and branch match what you deployed. A running container whose workspace is empty or on the wrong branch is the failure mode this check exists to catch — verify the state, don't infer it from "running".

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

If `template.yaml` has a `schedules:` block (see Step 3a), make sure the design catalog and the live instance agree.

**Path A does most of this for you.** When an agent is created from a `github:` repo, Trinity reads `template.yaml` from that repo **at creation** and materializes the declared schedules itself (trinity-enterprise#89) — so this step is a *verification*, matched on the literal schedule `name`, and it usually reports "in sync" with nothing to create.

Two facts shape what you will see. A schedule arms only on a **literal YAML `enabled: true`** — an omitted key, or the string `"true"`, lands disabled. And materialization happens **at creation only**: it is deliberately never re-applied on container recreate, so a `schedules:` entry added to the repo *after* the agent existed will never appear on its own — only this reconcile creates it.

Two cases still need you:

- Trinity could not read `template.yaml` (token can't reach the repo, or an anonymous request hit GitHub's rate limit) — schedules come back empty. The reconcile below fills them in; also treat it as a signal that the token tier is weaker than you thought.
- The repo's `template.yaml` is behind your local one — the remote's copy is what was read. Push, then re-run the reconcile.

**Path B always needs the full reconcile** — an archive deploy materializes no schedules.

1. **Read declared schedules** from `template.yaml`.
2. **List what's already live:** `mcp__trinity__list_agent_schedules(agent_name: "[agent-name]")`.
3. **Match by `name`** — Trinity's creation-time materializer writes the declared `name` **verbatim** and de-duplicates on it, so the live schedule for `name: Weekly report` is called exactly `Weekly report`, with no prefix. Diff declared vs live on `name`, and never prefix a schedule you create — a `[id]`-prefixed name cannot collide with the platform's, so a Path-A agent would end up with both `Weekly report` and `[weekly-report] Weekly report` firing the same cron at real spend:

   | Case | Condition | Action |
   |------|-----------|--------|
   | **Create** | Declared, no live match | `create_agent_schedule(...)` with `enabled` from the manifest, and `name` **exactly** as declared. |
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

## STEP 5-IP: Onboard In Place (this workspace IS the deployed agent)

**Only when Step 1b chose "Onboard in place".** The agent exists; nothing is created. The job is: files → plugins → *get it back into the repo* → schedules → verify with the platform. Four facts shape it:

- **Source mode is pull-only.** `github:`-created agents track their branch read-only — a file written here is container-local until pushed. An in-place result that is not pushed **is lost on the next reset**. Never end this step silently in that state.
- **Materialization is creation-time.** Schedules (ent#89) and plugins (#1704) declared *now* are not re-read by the platform; schedules reconcile live over MCP (5f), plugins install via the CLI now and via the boot hook's template fallback on every later start.
- **The `mcp__trinity__*` tools are already here** — injected by the platform for this agent (agent-scoped key). `list_agents` proving they work is Step 4 for this path.
- **Nothing to inject.** `.env` already lives in this workspace; `.env.example` is what you write for the repo.

**5-IP-a. Files.** Step 3 already wrote/updated `template.yaml` (with `plugins:` — at least `trinity@abilityai`), `.env.example`, `.gitignore`, and `.mcp.json.template` if the agent needs MCP servers of its own. `name:` in `template.yaml` must equal `$AGENT_NAME` (the deployed slug), never the repo basename.

**5-IP-b. Plugins, now.** Make the declaration true immediately rather than waiting for the next boot — the same two calls the boot hook makes:

```bash
claude plugin marketplace list --json 2>/dev/null | grep -q '"abilityai"' || claude plugin marketplace add abilityai/abilities
for p in $(yq -r '.plugins.installed[]?' template.yaml 2>/dev/null); do
  claude plugin list --json 2>/dev/null | grep -q "\"${p%@*}\"" || claude plugin install "$p" --yes
done
```

Plugins load at session start — the new ones are available from the **next** execution, and the boot hook keeps them present from then on.

**5-IP-c. Push back — or say honestly that you couldn't.**

```bash
git add template.yaml .env.example .gitignore .mcp.json.template 2>/dev/null
git commit -m "Trinity compatibility (onboarded in place): template.yaml + plugins, .env.example, .gitignore"
git push 2>&1 | tail -3
```

| Result | Then |
|---|---|
| Push succeeded | The repo now carries the files; the next `git_pull` / recreate lands on them. Record the commit sha. |
| Push refused (no write credentials — tokenless source mode, or a read-only PAT) | Try the platform's push path: `mcp__trinity__git_sync(agent_name: "$AGENT_NAME")` (409 `no_write_credentials` means the same thing). If that fails too: **stop, do not pretend.** Print the patch (`git format-patch -1 --stdout`) and the message: *"Result is container-local only — it will not survive a reset. Give this agent write credentials (Settings → GitHub token / per-agent PAT) and re-run, or apply this patch to the repo yourself."* |
| Repo has no `origin` (archive-deployed agent) | Promote it onto the repo path first — `mcp__trinity__initialize_github_sync` (Step 5c-B) — then push. |

**5-IP-d. Reconcile schedules** — run Step 5f exactly as written (declared `schedules:` ↔ `list_agent_schedules`, match by literal `name`, create/update, never flip `enabled`).

**5-IP-e. Verify with the platform, not a checklist.**

```
mcp__trinity__get_agent_compatibility_report(name: "$AGENT_NAME")
```

Every **HARD** finding is yours to fix now (most are `.gitignore` lines — `S-001`… are auto-fixable, but you already own the file, so fix and re-run). SOFT and AI verdicts are advisory: list them, don't loop on them. The report — not this SKILL.md — is the definition of "compatible" (trinity#2137 keeps its catalog aligned with what this skill generates; if a HARD you cannot explain appears, that alignment slipped — say so rather than working around it).

## STEP 6-IP: In-Place Onboarding Complete

```
## Trinity Compatibility Established In Place

- **Agent**: $AGENT_NAME (already deployed — nothing created)
- **Files**: template.yaml (plugins: [list]), .env.example, .gitignore[, .mcp.json.template]
- **Pushed back**: [yes — <sha> on <branch> | NO — container-local; patch printed above; give the agent write credentials]
- **Plugins**: [installed now: …] — declared, re-installed on every boot
- **Schedules**: [created N · updated N · in sync N · drift N] (see 5f table)
- **Compatibility report**: [0 HARD · N SOFT · N AI-advisory]  ← the platform's verdict

### Next
1. Start a fresh session so the newly installed plugins load.
2. If not pushed: apply the patch / grant write credentials, then re-run `/trinity:onboard` (in place) — it is idempotent.
3. `/trinity:sync` reconciles schedules and plugins on demand from here on.
```

---

## STEP 6: Completion

Only show this when the agent is successfully deployed:

```
## Trinity Onboarding Complete!

Your agent is now live on Trinity.

### Summary
- **Agent**: [agent-name]
- **Trinity URL**: [trinity-url]
- **Deployed from**: [github:owner/repo@branch — or "local archive (no repo yet)"]
- **Status**: Running

### Files Created
- [x] template.yaml
- [x] .gitignore
- [x] .env / .env.example (only if the agent has its own secrets)
- [x] .trinity-remote.yaml (deployment tracking)
- [x] template.yaml `plugins:` — [list] (installed headlessly on every boot, trinity#1704)

(MCP config — `.mcp.json` — is written by `/trinity:connect`, not onboard.)

### Compatibility (the platform's verdict, not this skill's)
`mcp__trinity__get_agent_compatibility_report(name)` → [0 HARD · N SOFT · N AI-advisory]. Run it right after 5d; a HARD finding is a fix-now, not a note.

### Next Steps

1. **Interact with your remote agent:**
   Use `mcp__trinity__chat_with_agent` with your agent name and message.

2. **Ship changes the git-native way:**
   Commit locally → `git push` → the remote pulls. `/trinity:sync` runs that loop for you, or call `mcp__trinity__git_pull(agent_name)` directly. On a repo-deployed agent this is the *only* update mechanism you need — never re-archive, and never re-run `create_agent` for an agent that already exists.

   *(If this agent was deployed from a local archive, close that gap first — `mcp__trinity__initialize_github_sync` puts it on the repo path; see Step 5c-B.)*

3. **Set up scheduled tasks:**
   Declare them in `template.yaml` under `schedules:` (see Step 3a), then re-run onboard or `/trinity:sync` to reconcile them onto the instance. For one-off changes, `mcp__trinity__create_agent_schedule` / `toggle_agent_schedule` act directly on the live agent.

4. **Publish structured reports:**
   Once running remotely, have result-producing and scheduled skills end with a guarded `mcp__trinity__report` call so their output lands on the agent's **Reports** tab (and the fleet **Operations → Reports** view) instead of vanishing into a headless run's chat. Namespace `report_type` as `<agent>.<result>`, pick a `display_hint` (`table` / `kpi` / `markdown` / `timeline`), and skip silently when the tool isn't present (running locally). Reports are the append-only history that complements the live `dashboard.yaml` snapshot (pruned past `agent_reports_retention_days`, default 90 days — rolling history, not a permanent archive). Agents built with `/create-agent` already carry this pattern; add it to hand-built skills via `/agent-dev:create-playbook` (the Reporting Rule).

5. **Add cross-session durability** (recommended):
   ```
   /agent-dev:add-git-sync
   ```
   Installs three hooks that auto-commit on session end, rebase on session start, and snapshot before compaction — keeps local and remote state consistent without manual pushes. Ideal for Trinity-deployed agents running scheduled tasks.

6. **Enable voice chat** (optional):
   Create `voice-agent-system-prompt.md` on the remote agent

7. **Connect Slack** (optional):
   Agent Detail > Sharing > "Create Slack Channel"
```

---

## STEP 6 (Alternative): Adaptation Complete

**Show this instead of the above if user chose "Adapt only":**

```
## Trinity Adaptation Complete!

Your agent is now Trinity-compatible and ready for deployment when you're ready.

### Files Created
- [x] template.yaml (agent metadata + `plugins:` — installed on every boot once deployed)
- [x] .gitignore (with Trinity patterns)
- [x] .env.example (only if the agent has its own secrets)

### What's NOT configured (by your choice)
- [ ] Trinity connection (`/trinity:connect` authenticates and writes `.mcp.json`)
- [ ] Remote deployment (agent not on Trinity)

### When You're Ready to Deploy

1. Run `/trinity:connect` to authenticate and configure MCP, then reconnect with `/mcp`
2. Push this agent to a GitHub repo (`gh repo create <name> --private --source=. --push`) and add a fine-grained PAT with **Contents: Read** under **Settings → GitHub token** on your instance — deployment is repository-first
3. Run `/trinity:onboard` and choose "Deploy to Trinity"

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

## Mode: In Place (forced)

If user runs `/trinity:onboard in-place` — or a schedule/orchestrator dispatches that call to a deployed agent — skip the Step 1b question and take the *Onboard in place* path directly (Step 1 detection still runs; if the markers are absent, say so and fall back to the question rather than guessing). This is the playbook-call form an orchestrator uses after a Path C deploy: `/trinity:onboard in-place`.

---

## Error Handling

| Error | Resolution |
|-------|------------|
| No CLAUDE.md | Create minimal CLAUDE.md first |
| MCP tools not available | Run `/trinity:connect` (writes `.mcp.json`), then reconnect with `/mcp` — full restart only as a fallback |
| Deployment failed | Confirm the connection is live (`mcp__trinity__list_agents`); re-run `/trinity:connect` if the profile expired |
| Deploy rejected on `resources` (e.g. `invalid literal for int() with base 10: '0.5'`) | `template.yaml` has an invalid cpu/memory. cpu must be integer (`"1"`/`"2"`/`"4"`/`"8"`/`"16"`), memory must use the `g` suffix (`"1g"`..`"32g"`). Fix `template.yaml` and redeploy — see Step 3a |
| Agent already exists | Path A: don't re-create — push + `git_pull` (Step 5c). Path B: `deploy_local_agent` creates a new version (`my-agent-2`) and stops the old one |
| `Repository '<owner/repo>' was not found or is private` (400) | The repo is private and no token resolved. Add a personal GitHub token in **Settings → GitHub token**, or make the repo public. This fires *before* the container is created — nothing to clean up |
| `not found or PAT does not have access` (400) | A token resolved but can't read that repo — its repository scope doesn't include it, or it expired. Re-scope/replace it |
| `Branch '<x>' not found` (400) | The branch isn't on the remote. Push it, or pass the real one via `github:owner/repo@branch` |
| `Bidirectional git sync requires write credentials` (400) | A tokenless create asked for a write-mode workspace. Deploy in source mode (the default — just omit any bidirectional flag), or configure a token |
| `GitHub is unreachable` (502) | Transient — the anonymous access probe couldn't reach GitHub. Retry, or add a token (the token path tolerates transient errors that the tokenless path fails closed on) |
| Git clone/pull fails on remote | Configure the GitHub PAT (see below) — check the tier that actually resolved |
| In place: `git push` refused / `git_sync` 409 `no_write_credentials` | Source mode is pull-only and the agent has no write token. Print the patch, say the result is container-local, have the operator grant a write PAT (per-agent PAT or Settings → GitHub token) and re-run — never leave it silent |
| In place: `claude: command not found` or plugin install times out | The container predates the #1704 base image or has no network to the marketplace. Declare the block anyway (it applies on the next boot on a current image); report `withheld:` honestly |
| `get_agent_compatibility_report` shows a HARD you cannot map to a file you wrote | The platform's catalog and this skill drifted (trinity#2137). Fix the finding if it is legitimate; otherwise report the check id and stop rather than suppressing it |

---

## Troubleshooting: GitHub PAT for Private Repos

The GitHub token is the prerequisite of the default deploy path — configure it *before* deploying (Step 4b), not after a failure. If Trinity can't clone or pull your repository, a missing or wrongly-scoped token is almost always why.

### When is a PAT Required?

- **Private repositories** — Always required
- **Public repositories** — Not required (Trinity clones anonymously in source mode), but recommended: anonymous requests share GitHub's rate limit, and when they trip it Trinity can silently fail to read your `template.yaml` — costing you the auto-materialized schedules

### Which token gets used (resolution order)

Trinity resolves one token per agent **at creation time**, in this order:

| Tier | Source | Set with |
|------|--------|----------|
| 1. Per-agent | A token bound to this one agent | `mcp__trinity__set_agent_github_pat(agent_name, pat)` — validated on save, requires an agent restart |
| 2. Per-user | The creating user's **personal** token | Trinity UI → **Settings → GitHub token** |
| 3. Global | The platform/admin token | Admin settings, or `GITHUB_PAT` in Trinity's `.env` |

**Prefer tier 2 for your own agents.** The personal token wins over the shared admin one, so a non-admin isn't confined to whatever repos the admin token happens to see — and it's read live, so rotating it doesn't require touching each agent. Reach for tier 1 (`set_agent_github_pat`) only when one agent needs a *different* identity than the rest — for example, an agent that also needs `gh`/API access inside its container, since a per-agent token is exposed there as `GITHUB_PAT`/`GH_TOKEN`/`GITHUB_TOKEN`.

Check what an existing agent resolved with `mcp__trinity__get_agent_github_pat_status(agent_name)` — it reports whether the agent has its own token or falls back to the global one (it never returns the value).

### Creating a Fine-Grained PAT

1. Go to **GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens**
2. Click **Generate new token**
3. Configure the token:
   - **Token name**: `Trinity` (or similar)
   - **Expiration**: Choose based on your security policy
   - **Repository access**: Select "Only select repositories" and choose the repos Trinity needs
   - **Permissions**: Under "Repository permissions", set **Contents** to **Read-only**
4. Click **Generate token** and copy the token (starts with `github_pat_`)

Read-only is enough for the default (source-mode, pull-only) deploy. Only grant **Contents: Read and write** if the agent itself pushes back to the repo.

### Configuring the PAT in Trinity

**Option 1: Your personal token in the Trinity UI (Recommended — tier 2)**

1. Log in to your Trinity dashboard
2. Go to **Settings → GitHub token**
3. Paste your token, test it, and save

**Option 2: Bind it to a single agent (tier 1)**

```
mcp__trinity__set_agent_github_pat(agent_name: "[agent-name]", pat: "github_pat_...")
```

The token is validated against GitHub before saving and encrypted at rest; **restart the agent** for it to take effect. Pass an empty string to clear it and revert to the tiers below.

**Option 3: The platform-wide token (tier 3 — admin)**

Set it in admin settings, or add to Trinity's `.env`:
```bash
GITHUB_PAT=github_pat_your_token_here
```

Then restart Trinity services. This is the shared fallback for every agent whose owner has no personal token — prefer Option 1 for your own work.

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

Deployment and git surface:
- `mcp__trinity__create_agent` — **the default deploy** (`template: "github:owner/repo[@branch]"`)
- `mcp__trinity__deploy_local_agent` — fallback deploy from a local tar.gz
- `mcp__trinity__initialize_github_sync` — promote an archive-deployed agent onto the repo path
- `mcp__trinity__git_pull` / `get_git_sync_state` / `get_git_status` / `get_git_log` — the update loop for repo-deployed agents
- `mcp__trinity__set_agent_github_pat` / `get_agent_github_pat_status` — per-agent GitHub identity
