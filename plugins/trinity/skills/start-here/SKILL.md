---
name: start-here
description: Guided first journey into Trinity — one command that takes a newcomer from "what is Trinity?" through choosing their path, installing or connecting an instance, wiring the MCP connection, and getting a first agent alive — with a live smoke test at every step. A resumable concierge, not a manual — each stage hands off to the specialist skill that owns it (connect, deploy-new-instance, onboard, the create-agent wizards), and platform questions are always answered from live documentation, never static text — before any instance exists via the public Trinity Docs Q&A endpoint (Vertex AI Search over docs/user-docs, resynced on every release) and the user-docs index on GitHub, after connecting via the instance's own ask_trinity MCP tool.
argument-hint: "[reset]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Bash, AskUserQuestion, Skill, mcp__trinity__list_agents, mcp__trinity__get_fleet_health, mcp__trinity__ask_trinity, mcp__trinity__chat_with_agent, mcp__trinity__get_execution_result
metadata:
  version: "1.3"
  created: 2026-08-06
  author: Ability.ai
  changelog:
    - "1.3: Smoke test no longer treats an empty agent list as the fresh-install signature — ent#124 seeds the acme trio plus Cornelius, so a fresh instance boots ~4 agents (Stage 4 already assumed seeded agents existed)"
    - "1.2: Stage 4 teaches the repository-first deploy sequence — push the agent to GitHub and add the instance's GitHub token (Settings → GitHub token) before /trinity:onboard, which then deploys by cloning the repo; the local-file deploy is named as the fallback that offers promotion afterwards"
    - "1.1: Ground the whole journey in live docs — pre-connect questions now go to the public Trinity Docs Q&A endpoint (Vertex AI Search over docs/user-docs, no auth, no instance needed) and Stage 0 orients against the live user-docs index on GitHub; the static narrative is demoted to a fallback for when the network is down"
    - "1.0: Initial version — resumable five-stage guided journey (orient → choose your door → get an instance → connect MCP + smoke test → first agent alive), routing every operational step to the specialist skill that owns it and using ask_trinity as the live documentation channel once connected"
---

# Trinity — Start Here

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `start-here vX.Y — recent: <summary>`. Then proceed.

The front door to Trinity. One command walks a newcomer from *"what is this?"* to *"my first agent answered me from my own instance"* — and costs nothing until they explicitly choose a step that deploys something.

**Design rules (bind every stage):**

1. **Route, don't duplicate.** Every operational step belongs to a specialist skill — `/trinity:connect`, `/trinity:deploy-new-instance`, `/trinity:onboard`, `/create-agent:create`, `/agent-dev:agent-fleet-analysis`. This skill sequences them and carries the user's state; it never re-implements their flows.
2. **Live documentation over static claims — at every stage.** Never improvise platform facts from memory. Two grounded channels cover the whole journey (see **Live documentation channels** below): before any instance exists, the public Trinity Docs Q&A endpoint and the live `docs/user-docs` index on GitHub; after connecting, the instance's own `mcp__trinity__ask_trinity`. The short Stage 0 block is a network-down fallback, not the source of truth.
3. **Zero commitment until chosen.** The tour door deploys nothing and asks for no credentials. Stages that create or deploy things happen only after the user picks them.
4. **Always resumable.** State persists across sessions; re-running this skill continues where the user left off.

## Live documentation channels

**Pre-connect (no instance, no auth, works from any laptop):**

1. **Trinity Docs Q&A** — a public endpoint backed by Vertex AI Search over the platform's `docs/user-docs/**`, onboarding docs, and the Trinity Compatible Agent Guide, re-indexed automatically on every push to the platform's main branch — always current:

   ```bash
   curl -sS -m 30 -X POST -H "Content-Type: application/json" \
     "https://us-central1-mcp-server-project-455215.cloudfunctions.net/ask-trinity" \
     -d '{"question": "<the user'\''s question>"}'
   ```

   Response: `{"answer": "...", "state": "SUCCEEDED", "session_id": "..."}`. Contract notes: pass `session_id` back for multi-turn follow-ups, but treat it as an **opaque string** (it exceeds 2^53 — numeric handling corrupts it); sessions expire silently (~30 min) — if the returned `session_id` differs from the one you sent, context was lost, mention nothing and carry on; errors come back as `{"error": "..."}` or, from Google's frontend, as HTML.

2. **The user-docs index** — fetch `https://raw.githubusercontent.com/abilityai/trinity/main/docs/user-docs/README.md` to see the current documentation map, and deep-link the user to specific pages as `https://github.com/abilityai/trinity/blob/main/docs/user-docs/<path>`.

**Post-connect:** prefer `mcp__trinity__ask_trinity` (the instance's own docs tool — same grounded corpus, plus it lives where the user's fleet lives). The public endpoint remains the fallback whenever the instance is unreachable.

**Channel routine:** any time the user asks anything about Trinity — at any stage — answer through whichever channel is available, quote the grounded answer, and offer the relevant user-docs deep link when one exists.

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

Then **orient against the live docs** (rule 2): fetch the user-docs index (channel 2 above) and add one live line under the block — the newest release from its *What's New* section with the deep link, e.g. *"Current release: v<A.B> — what's new: <link>"* (always the version the fetch returned — never a remembered one). If the fetch fails, skip this line silently; the static block stands alone.

Then ask (AskUserQuestion) whether they have questions before moving on. Answer every question through the public Docs Q&A endpoint (multi-turn — keep the `session_id`), quoting the grounded answer with a deep link where one fits. There is no "wait until you're connected" — the docs are live from the first minute.

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
   | Fleet visible | `mcp__trinity__list_agents` | A list returns. A fresh install is **not** empty — it seeds the `acme` system (`scout`, `sage`, `scribe`) plus Cornelius, so expect ~4 agents (ent#124). An empty list is still a pass; it just means the seed was disabled or this instance isn't fresh |
   | Instance healthy | `mcp__trinity__get_fleet_health` | Health summary returns, no critical agents |
   | Live docs online | `mcp__trinity__ask_trinity` | Grounded answer returns |

   For the `ask_trinity` check, ask something the user actually wants to know (or default to *"What can agents do on a schedule?"*), show the answer, and tell them explicitly: **this is the documentation channel from now on — any question about how Trinity works gets a live, doc-backed answer from your own instance.**

4. Print the checklist with PASS/FAIL per row. On any FAIL, fix before proceeding: unreachable instance → verify it's up (their ops agent's `/status` if they deployed one); auth issues → `/trinity:connect --force`.

→ Write state (`stage: 4`, `completed` += "mcp-connected").

## STAGE 4: A first agent, alive

Goal — the user exchanges a real message with an agent running on *their* instance. Branch on their situation:

- **They built an agent locally** (door "build"): deployment is **repository-first**, so set that up before deploying — it's two small steps and it's how every later update reaches the agent:
  1. **Push the agent to GitHub** (`gh repo create <name> --private --source=. --push` from its directory) — Trinity deploys by cloning the repo, so the repo is the deliverable.
  2. **Add a GitHub token** in the instance UI under **Settings → GitHub token** (a fine-grained PAT, *Contents: Read*) — required for private repos, recommended for public ones.

  Then, from the agent's directory, `/trinity:onboard` deploys it from that repo and reports which commit landed. (No repo, or GitHub unreachable? onboard falls back to a local-file deploy — fine to get moving, and it offers to put the agent on the repo path afterwards.) Then, from here, `mcp__trinity__chat_with_agent` — send a short real task, show the reply.
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
- Docs assistant anywhere  → claude mcp add trinity-docs -- npx -y @abilityai/trinity-docs-mcp
                             (the same grounded Q&A in any session, no
                             instance required)
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

- **Never grow the Stage 0 narrative.** It is deliberately a network-down fallback; every other platform fact must come from the live channels at run time. The drift surface to review when the platform changes is exactly three things: the Stage 0 block, the Docs Q&A endpoint URL, and the user-docs raw/deep-link URLs — the docs *content* behind them keeps itself current (resynced to Vertex on every push to main).
- This skill's hand-off targets are contracts: `connect` (single `.mcp.json` writer), `deploy-new-instance`, `onboard`, `create-agent:create`, `agent-dev:agent-fleet-analysis`. If any of those are renamed or resharded, update the routes here in the same change.
