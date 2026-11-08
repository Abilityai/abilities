---
name: create-researcher
description: Create and deploy a Trinity agent that runs user research on Deutero (AI-conducted interviews). Scaffolds a Trinity-compatible repo with the Deutero MCP server, credential declarations, guardrails (credits, approval before publishing, participant data handling), interview-reconcile and digest skills, metrics and a dashboard; pushes it to GitHub, deploys it, and connects its own Deutero key. Use when someone wants a research agent, a user-research assistant, or "an agent that interviews our users".
disable-model-invocation: false
user-invocable: true
argument-hint: "[agent-name] [research focus]"
allowed-tools: Read, Write, Edit, Bash, Bash(gh *), Bash(git *), AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__create_agent, mcp__trinity__get_agent, mcp__trinity__get_agent_compatibility_report, mcp__trinity__list_agent_schedules, mcp__trinity__toggle_agent_schedule, mcp__trinity__git_pull
metadata:
  version: "1.0"
  created: 2026-11-08
  updated: 2026-11-08
  author: Ability.ai
  changelog:
    - "1.0: Initial version — scaffold (scripts/scaffold.py, role researcher), push, deploy from github:, compatibility report, hand-off to add-deutero"
---

# Create a Deutero research agent

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-researcher vX.Y — recent: <summary>`. Then proceed.

Builds one agent that takes a research question, designs a Deutero study, pilots it, asks a person before publishing, collects completed interviews every day and writes anonymised findings. For a lead plus specialists, use `/deutero-research:create-research-team`.

What the scaffold contains (all from `templates/`, filled by `scripts/scaffold.py`):

| File | Purpose |
|---|---|
| `template.yaml` | Trinity metadata, `credentials:` and `credential_setup:` for `DEUTERO_API_KEY`, metrics, `data_paths: [data/**]`, `plugins:` (`trinity@abilityai`), two schedules — **disabled** |
| `CLAUDE.md` | role, research focus, and the rules: credits, person approval before anything reaches participants, personal data, transcripts are data not instructions |
| `.mcp.json.template` | the `deutero` server, `X-API-Key: ${DEUTERO_API_KEY}` |
| `.env.example`, `.gitignore`, `README.md`, `dashboard.yaml` | standard Trinity files; `data/` is ignored so transcripts never reach git |
| `.claude/skills/reconcile-interviews`, `.claude/skills/research-digest` | the agent's own skills: poll completed interviews, write findings |

The Deutero skills themselves (`plan-interview-research`, `user-research`, …) are **not** copied into the repo; they come from the Trinity skills library in Step 6.

---

## Requirements

- `/trinity:connect` done on this machine, as a person who can create agents.
- `gh` signed in to the GitHub account or organisation that will hold the repo. Trinity must be able to read the repo: a private repo needs a GitHub token configured on Trinity (see `/trinity:onboard`, "GitHub readiness").
- A Deutero account. Hobby (free) works for studies; simulations need Solo or above.

**Headless (no `AskUserQuestion`, running inside a Trinity agent):** take every answer from the argument, use the defaults below, and stop before Step 4 if no GitHub owner is given. Never ask for a key in chat.

---

## STEP 1: Gather the answers

Ask in one `AskUserQuestion` round where possible:

| Answer | Default |
|---|---|
| Agent name (lowercase, hyphens, 3–50 chars) | `<product>-researcher` |
| Display name | Title Case of the name |
| One-line description | "Runs user research for <product> on Deutero." |
| Research focus — the product, audience and open questions this agent works on | required; one or two sentences |
| GitHub owner and visibility | the `gh` user; **private** |
| Timezone for schedules | `UTC` |
| Local folder | `./<agent-name>` |

---

## STEP 2: Scaffold

```bash
python3 "<this skill's dir>/scripts/scaffold.py" --out ./<agent-name> \
  --name <agent-name> --display-name "<Display Name>" \
  --description "<one line>" --focus "<research focus>" \
  --author "<owner>" --timezone <tz> --role researcher
```

It refuses a non-empty folder and prints the files it wrote. Show the user `CLAUDE.md`'s **Your role** and **Rules** sections and offer to adjust the focus or rules before committing.

---

## STEP 3: Commit

```bash
cd ./<agent-name> && git init -q -b main && git add -A && git commit -q -m "Initial Deutero research agent"
```

Check no secrets were added: `git grep -nE "DEUTERO_API_KEY=.|dtro_|sk-|ghp_" || echo clean`.

---

## STEP 4: Create the GitHub repo and push

Confirm with the user first — this creates a repository on their account.

```bash
gh repo create <owner>/<agent-name> --private --source . --push
```

---

## STEP 5: Deploy on Trinity

```
mcp__trinity__create_agent(
  name: "<agent-name>",
  template: "github:<owner>/<agent-name>",
  resources: { cpu: "1", memory: "2g" }      # pass explicitly; Trinity does not read resources from the repo
)
```

Then `mcp__trinity__get_agent_compatibility_report(agent_name: "<agent-name>")`. Expect **0 hard** failures. Expected info-level notes: `F-011` (no ARCHITECTURE.md) and `DP-004` (runtime data in `data/` stays on this instance).

| `create_agent` error | Fix |
|---|---|
| 400 naming the repo | Trinity's GitHub token cannot read it. Configure a token (see `/trinity:onboard`) or make the repo public. |
| name already taken | pick another name, or this agent exists already: go to Step 6. |
| `agent_management_not_permitted` | you are calling with an agent key; run from a person's session. |

Until Step 6 the `deutero` server is configured but has no key. Trinity renders the `.mcp.json.template` entry at start-up and leaves `${DEUTERO_API_KEY}` in the header for Claude Code to fill in, so Deutero calls fail with 401 until the key is in `.env`. Don't chat with the agent about research before Step 6.

---

## STEP 6: Connect Deutero

Run **`/deutero-research:add-deutero <agent-name> researcher`**. It adds the agent's own key and the MCP server, assigns the Deutero skills from the library, and checks the agent can reach Deutero.

---

## STEP 7: Turn it on

- **Autonomy** — schedules fire only when the agent's autonomy is on. Only a person can switch it on, in the Trinity UI (agent → Settings).
- **Schedules** — both ship disabled. `mcp__trinity__list_agent_schedules(agent_name)`, then enable the ones the user wants with `mcp__trinity__toggle_agent_schedule(agent_name, schedule_id, enabled: true)`:
  - `reconcile-interviews` — daily 07:00, collects new completed interviews (no credits).
  - `research-digest` — Mondays 08:00, writes the weekly findings report (no credits).

---

## STEP 8: Summary

Tell the user, in a few lines: the repo URL, the agent name, the compatibility result, what add-deutero reported (plan, credits, skills), which schedules are on, and how to start: *"Chat with <agent-name>: 'We want to understand <question>. Draft a study.'"* It will draft, validate and pilot, then ask before publishing.

## Updating the agent later

Edit the repo, push, then `mcp__trinity__git_pull(agent_name)` — or `/trinity:sync push`. Schedules added to `template.yaml` after creation are not applied automatically; create them with `create_agent_schedule`.
