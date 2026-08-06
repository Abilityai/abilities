---
name: start-here
description: Guided first journey into Trinity — one command that takes a newcomer from "what is Trinity?" through choosing their path, installing or connecting an instance, wiring the MCP connection, and getting a first agent alive — with a live smoke test at every step. A resumable concierge, not a manual — each stage hands off to the specialist skill that owns it (connect, deploy-new-instance, onboard, the create-agent wizards), and once the MCP is connected, platform questions are answered live from Trinity's own documentation via ask_trinity instead of static text.
argument-hint: "[reset]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Bash, AskUserQuestion, Skill, mcp__trinity__list_agents, mcp__trinity__get_fleet_health, mcp__trinity__ask_trinity, mcp__trinity__chat_with_agent, mcp__trinity__get_execution_result
metadata:
  version: "1.0"
  created: 2026-08-06
  author: Ability.ai
  changelog:
    - "1.0: Initial version — resumable five-stage guided journey (orient → choose your door → get an instance → connect MCP + smoke test → first agent alive), routing every operational step to the specialist skill that owns it and using ask_trinity as the live documentation channel once connected"
---

# Trinity — Start Here

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `start-here vX.Y — recent: <summary>`. Then proceed.

The front door to Trinity. One command walks a newcomer from *"what is this?"* to *"my first agent answered me from my own instance"* — and costs nothing until they explicitly choose a step that deploys something.

**Design rules (bind every stage):**

1. **Route, don't duplicate.** Every operational step belongs to a specialist skill — `/trinity:connect`, `/trinity:deploy-new-instance`, `/trinity:onboard`, `/create-agent:create`, `/agent-dev:agent-fleet-analysis`. This skill sequences them and carries the user's state; it never re-implements their flows.
2. **Live documentation over static claims.** The only static narrative in this skill is the short orientation block in Stage 0. Once the MCP is connected, answer every platform question with `mcp__trinity__ask_trinity` — a grounded, documentation-backed answer from the user's own instance. Do not improvise platform facts from memory; if not yet connected, say so and point to https://ability.ai and https://github.com/Abilityai/trinity.
3. **Zero commitment until chosen.** The tour door deploys nothing and asks for no credentials. Stages that create or deploy things happen only after the user picks them.
4. **Always resumable.** State persists across sessions; re-running this skill continues where the user left off.

## Journey State

State lives at `~/.trinity/start-here.json` (same home as the connection profile):

```json
{
  "stage": 0,
  "door": null,
  "instance_url": null,
  "agent_dir": null,
  "completed": [],
  "updated": "2026-08-06T00:00:00Z"
}
```

**On invocation:**

```bash
mkdir -p ~/.trinity && cat ~/.trinity/start-here.json 2>/dev/null
```

- If the argument is `reset`: delete the file, start from Stage 0.
- If state exists and `stage` > 0: print a one-line recap ("You're at stage N — last time you {summary}") and ask: **continue where you left off, or start over?**
- Otherwise: begin at Stage 0.

**After every stage:** write the updated state back (stage reached, door chosen, `completed` entries appended, ISO timestamp). Never skip the write — the resume promise depends on it.

## STAGE 0: Orient — what Trinity is

Print this orientation, then stop narrating (rule 2):

```
## What is Trinity?

Trinity runs Claude Code agents as an always-on fleet.

- An agent is a folder: CLAUDE.md (identity) + skills + memory files,
  driven by the same Claude Code harness you're using right now.
- The bet: the agent behaves identically on your laptop and on Trinity.
  You build and test locally; Trinity makes it durable — schedules,
  Slack/Telegram/email channels, dashboards, a fleet you can talk to.
- This session becomes the control plane: once connected over MCP, you
  list, message, and manage your whole fleet from right here.

This tour is free — nothing gets deployed until you choose it.
```

Then ask (AskUserQuestion) whether they have questions before moving on. If they do and no MCP connection exists yet, answer briefly, flag that deep answers come from the instance itself in Stage 3, and offer to continue.

→ Write state (`stage: 1`), go to Stage 1.

## STAGE 1: Choose your door

Use AskUserQuestion — **Question:** "Where are you right now?" — **Header:** "Your path"

1. **Just looking** — show me around, deploy nothing
2. **Build my first agent** — I know roughly what I want it to do
3. **I already have agents** — Claude Code folders, n8n flows, or framework apps
4. **Set up my instance** — I'm ready to install or connect Trinity

**Door behavior:**

- **Just looking** → give the extended tour: walk one concrete day-in-the-life (an agent that wakes on a schedule, reads its inbox channel, does its job, reports to a dashboard). If an MCP connection already exists, make it live: `mcp__trinity__list_agents` + `mcp__trinity__get_fleet_health` and narrate what's actually running. Then re-offer the other three doors. Record `door: "tour"`.
- **Build my first agent** → the create-agent wizards own this. If the plugin isn't installed, have them run `/plugin install create-agent@abilityai` first, then `/create-agent:create`. Tell them plainly: *the agent will work locally first — Trinity is the upgrade, not the gate.* Record `door: "build"` and `agent_dir` once created; when the wizard finishes, resume here → Stage 2.
- **I already have agents** → `/plugin install agent-dev@abilityai`, then `/agent-dev:agent-fleet-analysis` pointed at their agents' parent directory — a read-only maturity report they get value from before deploying anything. Record `door: "bring"`; when they're ready to host the fleet → Stage 2.
- **Set up my instance** → record `door: "install"`, go straight to Stage 2.

## STAGE 2: Get an instance

Ask: **"Do you already have a Trinity instance URL?"**

- **Yes** → note `instance_url`, skip to Stage 3.
- **No** → `/trinity:deploy-new-instance` owns provisioning; it will ask them to choose between cloud (ability.ai — managed, no infrastructure), a self-hosted server, or local Docker on this machine. Run it, and when an instance is reachable, return here → Stage 3.
- **Not yet / just exploring** → perfectly fine. Save state and close warmly: "Your progress is saved — run `/trinity:start-here` whenever you're ready and we continue at this exact step."

## STAGE 3: Connect the MCP — and prove it works

This is the moment the session becomes a control plane.

1. **Connect:** run `/trinity:connect` — it is the single writer of `.mcp.json` (email OTP → MCP API key → config). Do not hand-roll any part of its flow, including its error handling (e.g. the no-code-arrives whitelist case — the connect skill explains it).
2. **Load the tools:** if `mcp__trinity__*` tools are not available in this session after connect, that's expected — the MCP server loads on restart. Tell the user: restart Claude Code (or run `/mcp` to reconnect), then run `/trinity:start-here` again — **state resumes exactly here.** Write state (`stage: 3`) before saying this.
3. **Smoke test** — run all three, report a checklist:

   | Check | Tool | Pass looks like |
   |-------|------|-----------------|
   | Fleet visible | `mcp__trinity__list_agents` | Agent list returns (empty is a pass — new instance) |
   | Instance healthy | `mcp__trinity__get_fleet_health` | Health summary returns, no critical agents |
   | Live docs online | `mcp__trinity__ask_trinity` | Grounded answer returns |

   For the `ask_trinity` check, ask something the user actually wants to know (or default to *"What can agents do on a schedule?"*), show the answer, and tell them explicitly: **this is the documentation channel from now on — any question about how Trinity works gets a live, doc-backed answer from your own instance.**

4. Print the checklist with PASS/FAIL per row. On any FAIL, fix before proceeding: unreachable instance → verify it's up (their ops agent's `/status` if they deployed one); auth issues → `/trinity:connect --force`.

→ Write state (`stage: 4`, `completed` += "mcp-connected").

## STAGE 4: A first agent, alive

Goal — the user exchanges a real message with an agent running on *their* instance. Branch on their situation:

- **They built an agent locally** (door "build"): from the agent's directory, `/trinity:onboard` deploys it. Then, from here, `mcp__trinity__chat_with_agent` — send a short real task, show the reply.
- **The instance already has agents** (seeded fleet or door "bring" after migration): pick one from `list_agents` and `chat_with_agent` it with a hello-task.
- **Neither yet:** offer `/create-agent:create` now, or `chat_with_agent` against any seeded agent just to feel the loop.

Practical note: if a `chat_with_agent` call returns a `queued_timeout` receipt, the task **is** running — poll `mcp__trinity__get_execution_result` with the returned `execution_id`; never blind-retry (it would duplicate-queue).

→ Write state (`stage: 5`, `completed` += "first-agent-conversation").

## STAGE 5: Wrap — and where each road leads

Print a recap of what they now have (checklist built from `completed`), then the hand-offs — each is a door out, not more tour:

```
## You're running. Where to next?

- Another agent            → /create-agent:create  (wizard menu)
- Bring your existing bots → /agent-dev:agent-fleet-analysis
- Design an agentic system → describe the job to ask_trinity, then
                             /create-agent:custom or :kb-agent for the shape
- Day-2 operations         → /trinity:sync (local↔remote),
                             /trinity:loop (bounded remote loops),
                             schedules & channels: just ask — the live
                             docs answer via ask_trinity
```

Mark state `stage: 5`, `completed` += "journey-complete". Re-running the skill later greets them as a returning user and offers the hand-off menu directly.

## Error Handling

| Situation | Response |
|-----------|----------|
| State file corrupt/unreadable | Say so, offer `reset` — never crash the journey over bookkeeping |
| Specialist skill not installed | Give the exact `/plugin install <name>@abilityai` line, then continue |
| MCP tools absent after connect | Normal — restart Claude Code or `/mcp`, re-run `/trinity:start-here`, resumes at Stage 3 |
| Instance unreachable mid-journey | Point at their ops agent (`/status`) if one exists, else `/trinity:connect --force`; save state first |
| User wants to stop anywhere | Save state, confirm resume works, close warmly — no guilt-tripping |

## Notes for maintainers

- **Never grow the Stage 0 narrative.** It is deliberately the only static platform text in this skill; everything else must come from `ask_trinity` at run time. If the platform changes, this block is the entire drift surface to review.
- This skill's hand-off targets are contracts: `connect` (single `.mcp.json` writer), `deploy-new-instance`, `onboard`, `create-agent:create`, `agent-dev:agent-fleet-analysis`. If any of those are renamed or resharded, update the routes here in the same change.
