---
name: add-deutero
description: Give an existing Trinity agent the ability to run user research on Deutero (AI-conducted interviews). Adds the agent's own Deutero API key and the Deutero MCP server (about 100 tools) without touching its other credentials, assigns the Deutero skills from the Trinity skills library, and checks the agent can reach Deutero. Use when someone wants an agent to design studies, recruit participants, read interview results, or says "add Deutero to <agent>".
disable-model-invocation: false
user-invocable: true
argument-hint: "[agent-name] [researcher|recruiter|analyst|full]"
allowed-tools: Read, Bash, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__list_skill_sources, mcp__trinity__register_skill_source, mcp__trinity__sync_skill_source, mcp__trinity__assign_skill_to_agent, mcp__trinity__get_agent_skills, mcp__trinity__chat_with_agent
metadata:
  version: "1.0"
  created: 2026-11-08
  updated: 2026-11-08
  author: Ability.ai
  changelog:
    - "1.0: Initial version — merge-safe key + MCP server injection (scripts/add_deutero.py), Deutero skills from the library by role preset, live credit-balance check"
---

# Add Deutero to a Trinity agent

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-deutero vX.Y — recent: <summary>`. Then proceed.

[Deutero](https://deutero.ai) runs AI-conducted user interviews. It exposes about 100 tools (projects, studies, questions, screening, recruitment, simulations, transcripts, quotes, clustering) through a remote MCP server at `https://dashboard.deutero.ai/mcp`, and ships agent skills in the public repo [`deutero-ai/agent-skill`](https://github.com/deutero-ai/agent-skill).

This skill wires one running Trinity agent to Deutero:

| Piece | Where it lands | How |
|---|---|---|
| `DEUTERO_API_KEY` | the agent's `~/.env` | `scripts/add_deutero.py` — reads the current file, merges, re-injects |
| `deutero` MCP server | the agent's `~/.mcp.json` | same script; the header is `X-API-Key: ${DEUTERO_API_KEY}`, so the key never sits in `.mcp.json` |
| Deutero skills | the agent's `~/.claude/skills/` | Trinity skills library: register the repo once, then `assign_skill_to_agent` |

**Why a script, not `inject_credentials` directly:** Trinity's inject call replaces whole files. Calling it with a `.env` holding only the Deutero key would delete every other credential the agent has. The script downloads the agent's current `.env` and `.mcp.json` (owner access), changes only the Deutero lines, and writes both back.

**Why not Deutero's own Claude Code plugin:** its `deutero` MCP entry uses OAuth, which needs a person at a browser. A headless Trinity agent cannot complete it, so the agent would get a second, unusable `deutero` server. Use an API key and the skills library instead.

---

## Requirements

- **Trinity connection** — `/trinity:connect` has been run on this machine (the script reads `~/.trinity/config.json`). You must **own** the agent (or be an admin), signed in as a person: agent keys cannot change credentials.
- **The agent is running.**
- **A Deutero account.** None yet? The free Hobby plan gives 15 credits a month; sign up at `https://dashboard.deutero.ai`. If the Deutero plugin is installed, `/deutero-setup` walks through it.
- **Registering the skills repo needs a Trinity admin** (once per instance). A non-admin can still do everything else.

---

## STEP 1: Pick the agent and the role

If the argument names an agent, use it. Otherwise call `mcp__trinity__list_agents` and ask which one with `AskUserQuestion`. Confirm it is running (`mcp__trinity__get_agent`).

Then pick a role preset — the second argument, or ask:

| Preset | Skills assigned | Use for |
|---|---|---|
| `researcher` (default) | `deutero-setup`, `plan-interview-research`, `user-research`, `simulate-users` | designing and running studies end to end |
| `recruiter` | `researcher` + `recruit-participants` | participant links, embeds, rewards on completion |
| `analyst` | `deutero-setup`, `plan-interview-research` | reading transcripts, quotes and clusters, writing reports |
| `full` | all eight: the above + `deutero-interview-flow`, `idea-validation`, `improve-agent` | one agent that does everything |

Plan limits to mention when relevant: simulations need **Solo** or above, branching interview flows need **Pro** or above. The agent can check its plan with the `get_credit_balance` tool.

---

## STEP 2: Get the agent's own Deutero key

Each agent gets **its own** key, so one agent can be revoked without touching the others. Keys are organisation-scoped and shown once.

1. In Deutero: **Settings → Generate API Key**. Name it after the agent (for example `trinity-<agent-name>`).
2. Save it to a file on this machine — **not in this chat**. Tell the user to copy the key, then run (macOS):
   ```
   ! mkdir -p ~/.config/deutero && pbpaste > ~/.config/deutero/<agent-name>.key && chmod 600 ~/.config/deutero/<agent-name>.key
   ```
   On Linux, create the file with an editor and `chmod 600` it.
3. If the user pastes the key into the chat anyway, write it to that file yourself and do not repeat it back.

Never print the key, put it in a command line, or write it into the agent's repo.

---

## STEP 3: Add the key and the MCP server

Run the bundled script from this skill's directory. Dry run first, and show the user its one-line summary:

```bash
python3 "<this skill's dir>/scripts/add_deutero.py" --agent <agent-name> \
  --key-file ~/.config/deutero/<agent-name>.key --dry-run
```

Then the real run (same command without `--dry-run`). The script:

1. checks the key against Deutero (`401`/`403` → a clear "regenerate the key" error),
2. checks the agent exists, you own it, and it is running,
3. reads the agent's `.env` and `.mcp.json`, sets `DEUTERO_API_KEY` and the `deutero` server, keeps everything else,
4. writes back only the files that changed (Trinity validates `.mcp.json` before writing it).

It prints JSON such as `{"ok": true, "env": "added", "mcp": "added", "key_check": "valid", "written": [".env", ".mcp.json"]}`. Re-running is safe: unchanged files report `"unchanged"` and are not rewritten. A new key for the same agent reports `"env": "updated"`.

| Result | Meaning |
|---|---|
| `already has a different 'deutero' MCP server` | someone configured Deutero by hand. Show it to the user; rerun with `--force` to replace it. |
| `Agent ... not found, or you do not own it` | wrong name, or not your agent. Ask its owner, or an admin. |
| `Trinity refused the write (HTTP 400) ...` | Trinity's MCP config validator rejected the file — the message says why. Usually another server in `.mcp.json` is invalid; fix that first. |
| `Deutero key check returned HTTP 5xx` | Deutero is unreachable right now. Retry, or `--no-verify` to skip the check. |

The new server is used from the agent's **next** run; nothing needs restarting. To undo: `add_deutero.py --agent <agent-name> --remove`, then revoke the key in Deutero.

---

## STEP 4: Assign the Deutero skills

1. Find the Deutero source: `mcp__trinity__list_skill_sources` → look for url `https://github.com/deutero-ai/agent-skill`.
2. **Not registered yet** (admin only):
   ```
   mcp__trinity__register_skill_source(url: "https://github.com/deutero-ai/agent-skill", ref: "main", ref_type: "branch", name: "Deutero")
   mcp__trinity__sync_skill_source(source_id: "<id from the result>")
   ```
   The repo keeps its skills in a top-level `skills/` folder, which Trinity finds on its own. `refused_busy` on sync means another sync is running — retry in a minute.
   **Not an admin** (`list_skill_sources` / `register_skill_source` refused): give the user those two calls to pass to their Trinity admin, finish Step 5, and come back to this step later.
3. Assign each skill in the preset:
   ```
   mcp__trinity__assign_skill_to_agent(agent_name: "<agent-name>", skill_name: "<skill>")
   ```
   Report each skill's `delivery` result. `injected` = available now. `conflict` = the agent already has its own skill of that name, and its own copy is kept. `pending_start` or `not_delivered` = it lands on the next start or `sync_agent_skills`.

---

## STEP 5: Check it works

Ask the agent to make one read-only Deutero call:

```
mcp__trinity__chat_with_agent(agent_name: "<agent-name>",
  message: "Call the Deutero MCP tool get_credit_balance and reply with only the plan name and credits remaining. Do not create or change anything in Deutero.")
```

- **Plan and credits come back** → done.
- **The agent says it has no Deutero tools** → its `.mcp.json` was not picked up. Run the script again: `"mcp": "unchanged"` means it is in place. Then ask the agent to run `claude mcp list` and report the `deutero` line.
- **401 from Deutero** → the key in `.env` is wrong or was revoked. Generate a new one, save it to the key file, and rerun Step 3.

---

## STEP 6: Report and recommend guardrails

Summarise in a few lines: agent, preset, key added, MCP server added, skills delivered, plan and credits.

Then suggest, without writing anything unless asked:

- **Spending guardrails in the agent's `CLAUDE.md`** — check `get_credit_balance` before anything that costs credits; never `publish_study`, `run_simulation` or send recruitment emails without a person's approval (`ask_operator` on Trinity); treat transcripts and participant contacts as personal data that stays out of git and shared folders.
- **Survive a rebuild** — for an agent deployed from its own GitHub repo, also add the server to the repo, so a fresh deploy gets it too: put the same `deutero` entry in `.mcp.json.template`, and declare `credentials.mcp_servers.deutero.env_vars: [DEUTERO_API_KEY]` in `template.yaml` plus `DEUTERO_API_KEY=` in `.env.example`. The key itself still goes in through Step 3.
- **Interview results** — Deutero can send an `interview.completed` webhook, but Trinity's schedule webhooks only verify Trinity's own signature and do not pass the webhook body to the agent. Until they do, have the agent poll instead: a schedule running daily that calls `list_interviews` for its open studies and processes new completions.

---

## Notes

- **Permissions.** Reading `.env`/`.mcp.json` and writing credentials are owner-tier, person-only on Trinity. An agent cannot run this skill on itself or a sibling with its own key — by design.
- **Key handling.** The script never prints the key and sends it only to `dashboard.deutero.ai` (the check) and to your Trinity instance (the write). It never lands in `.mcp.json`: Claude Code fills in `${DEUTERO_API_KEY}` from the agent's environment, which Trinity loads from `.env` on every run.
- **One organisation.** Deutero keys are organisation-wide, so per-agent keys let you revoke one agent; they do not separate data between agents.
