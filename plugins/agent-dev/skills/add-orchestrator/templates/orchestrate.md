---
name: orchestrate
description: Put the fleet to work — read fleet/system-map.yaml + live Trinity MCP to route a task to the best-fit agent, fan out across many, or roll out a catalog agent ephemerally (deploy → chat → tear down). Orchestration is agent-owned; no central DAG.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__get_agent_health, mcp__trinity__chat_with_agent, mcp__trinity__fan_out, mcp__trinity__deploy_system, mcp__trinity__deploy_local_agent, mcp__trinity__stop_agent, mcp__trinity__start_agent, mcp__trinity__delete_agent
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.1: Call deployed agents by their live deployed_name (not the map key/template name) — avoids standing up duplicates when the two differ; use live status/health from the map; reads the map directly (no /compose-system needed for an existing fleet); guarded report swallows auth-scope failures"
    - "1.0: Initial version — routes a task to the best-fit fleet agent, fans out across a set, or rolls out a catalog agent ephemerally (deploy → chat → tear down); plans dry when Trinity MCP is absent"
---

# Orchestrate

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `orchestrate vX.Y — recent: <summary>`. Then proceed.

Drive the fleet. Given a task, decide **who** should do it (matching against `fleet/system-map.yaml`), **how** (single agent, fan-out, or a short chain), and — for agents that only exist as repos — **roll one out ephemerally, use it, and spin it down**.

**Argument:** the task / goal in plain language, e.g. `/orchestrate research Acme Corp then draft a competitive battlecard`.

**Invariant:** this agent owns the orchestration. Trinity brokers the calls (`chat_with_agent`, `fan_out`) and the lifecycle (`deploy_*` / `stop_agent` / `delete_agent`); there is no central DAG engine. Multi-step flows are sequenced *here*, in this skill.

---

## Process

### Step 1: Load the map + check the substrate

```bash
[ -f fleet/system-map.yaml ] || { echo "No fleet/system-map.yaml — run /discover-agents first."; exit 1; }
```

Read the map directly — for a fleet already on Trinity this is all you need (no `/compose-system`, no manifest). Detect Trinity MCP. If it's **absent**, you can still produce a **routing plan** (Step 2–3) but not execute — say so up front and end at the plan.

If the map's `generated:` is old or `fleet/sources.yaml` has changed since, suggest re-running `/discover-agents` first (don't force it).

### Step 2: Interpret the task → pick a pattern

Match the task against each agent's `role`, `summary`, `capabilities[].does`, and `tags`. Choose one of Trinity's three execution shapes:

| Pattern | When | Trinity call |
|---|---|---|
| **Single** | one agent clearly best-fits | `chat_with_agent` |
| **Fan-out** | same task over many inputs / a whole role-group | `fan_out` |
| **Chain** | task has ordered steps spanning agents (research → write) | sequential `chat_with_agent`, feeding each result into the next |

If the best-fit agent is ambiguous (two plausible matches, or none scores well), use `AskUserQuestion` to let the operator pick — show the candidates with their `summary` and match reason. Never silently guess when the match is weak.

### Step 3: Resolve each chosen agent to something runnable

For each agent the plan needs:

- **`deployed: true`** → call it by its **`deployed_name`** from the map, *not* the map key or `template.yaml` name (they often differ, e.g. `ruby` → `ruby-internal`). Calling the wrong name would miss the live agent and risk deploying a duplicate. If `status` is `stopped`, `mcp__trinity__start_agent` first; check `mcp__trinity__get_agent_health` before sending real work; if unhealthy, report and offer an alternate.
- **catalog-only (`deployed: false`)** → it must be rolled out. Confirm the ephemeral plan **once, up front**: list which agents will be created and that they'll be **torn down when the task completes**. On approval:
  - GitHub source → deploy a one-agent ephemeral system from the ref:
    - `mcp__trinity__deploy_system` with a minimal manifest `{name: "eph-<agent>-<short-id>", agents: {<agent>: {template: github:Org/repo}}, permissions: {preset: none}}`
    - (or `mcp__trinity__deploy_local_agent` for a local source)
  - Record every agent created this run in an **ephemeral set** for teardown.
  - Wait until `get_agent_health` reports ready before dispatching.

Vary the `<short-id>` per run by using the task index/name — do not rely on random or timestamp inside the manifest.

### Step 4: Dispatch

- **Single:** `chat_with_agent(<deployed_name>, task)` → capture the response. (Ephemerals created this run: use the name they were deployed under.)
- **Fan-out:** `fan_out(task, <deployed_names or agent set>)` → collect results.
- **Chain:** call agents in order; inject the prior result into the next prompt (`… given: <previous_response> …`). For long server-side sequential runs, `/trinity:loop` (`run_agent_loop`) is the durable option — mention it if the chain is long-running.

Capture each agent's output. Keep a running transcript of who did what.

### Step 5: Tear down ephemerals

For every agent in the ephemeral set (created in Step 3):

- `mcp__trinity__stop_agent` (always — reversible).
- `mcp__trinity__delete_agent` to fully remove it (this is the "spin down" the ephemeral pattern promises; it was authorized once in Step 3, so proceed — but if the run **failed**, stop but **do not delete**, so the operator can inspect it, and say so).

Never stop or delete an agent that was **not** created by this run (i.e. anything `deployed: true` in the map). Those are persistent fleet members.

### Step 6: Report

```
Task: <task>
Pattern: <single | fan-out | chain>
Agents:
  - <agent> (<deployed | ephemeral>) → <one-line result>
Ephemerals torn down: <list | none>
Result: <synthesized outcome>
```

Publish a guarded Trinity report (`report_type: <agent>.orchestration_run`, `display_hint: markdown`). Guard against **both** the tool being absent **and** an auth-scope error (the report tool needs an agent-scoped key; an admin/user MCP key raises a permission error) — swallow either and continue.

---

## Error handling

| Situation | Action |
|---|---|
| No `fleet/system-map.yaml` | Send user to `/discover-agents`; stop |
| Trinity MCP absent | Produce the routing plan only; explain that execution needs `/trinity:connect` first |
| No agent matches the task | Say so; suggest adding a suitable repo to `fleet/sources.yaml`, or a catalog agent to roll out |
| Chosen deployed agent unhealthy | Report health; offer an alternate or abort |
| Ephemeral deploy fails | Report the error; tear down anything already created this run; abort the task |
| Task failed mid-chain | Stop ephemerals but **don't delete** them (preserve for inspection); report where it broke |
