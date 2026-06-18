---
name: loop
description: Run a remote Trinity agent task in a sequential, bounded loop — a fixed number of iterations or until a stop signal, with optional response chaining. Fires server-side via run_agent_loop (caller can disconnect), then polls and renders progress. The remote, durable counterpart to Claude Code's local /loop.
argument-hint: "[status|stop] [@agent] <message> [<N> times] [every <N>m|s] [until <condition>]"
disable-model-invocation: true
user-invocable: true
allowed-tools: AskUserQuestion, Read, Skill, mcp__trinity__list_agents, mcp__trinity__run_agent_loop, mcp__trinity__get_loop_status, mcp__trinity__stop_loop
metadata:
  version: "1.5.1"
  created: 2026-06-09
  author: Ability.ai
  changelog:
    - "1.5.1: Reworded the connection prerequisite to the canonical block shared with /trinity:sync and /trinity:onboard — delegates to /trinity:connect (the single connection owner), reconnect via /mcp, never the CLI/curl"
    - "1.5: Resolve the remote from the unified `.trinity-remote.yaml` registry — read the `default` remote's `agent` under `remotes:` (with legacy single-remote fallback). Provenance now accurate: the file is genuinely written by both /trinity:onboard and /trinity:sync"
    - "1.4: Default local watch after firing — dynamic /loop (ScheduleWakeup) polls get_loop_status, reports changes/stalls/terminal state; skipped on fire-and-forget or when local /loop is unavailable"
    - "1.3: Until sentinel must be tied to verifiable evidence (not self-assessment); stall detection in status/observe; timeout_per_run recommended for Until mode; durable artifacts in agent files, not {{previous_response}}"
    - "1.2: No @agent now defaults to this agent's remote copy (.trinity-remote.yaml / name match); fire without confirmation when the task is clear"
    - "1.1: Surface modifiers in argument-hint and Usage (count, every-cadence, until); document 1h delay ceiling with redirect to schedules"
    - "1.0.1: Quote argument-hint — unquoted brackets broke YAML frontmatter, making the skill invisible"
    - "1.0: Initial version — modeled on Claude Code's /loop, backed by the run_agent_loop server primitive"
---

# /trinity:loop — run a remote agent in a sequential loop

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `loop vX.Y — recent: <summary>`. Then proceed.

The remote counterpart to Claude Code's built-in `/loop`. Where `/loop` re-invokes **your local session** on a cadence, `/trinity:loop` hands one bounded, sequential loop to a **remote Trinity agent**: you fire it once with `run_agent_loop`, get a `loop_id`, and can walk away — the backend runs every iteration in order, optionally chaining each response into the next, and exits on a hard cap or a stop signal.

Use it for iterative refinement, agentic retry, and bounded polling that must outlive your session and the 60-second MCP timeout.

## Usage

```
/trinity:loop [@agent] <message>             start a loop (default verb)
/trinity:loop status <loop_id>               show per-run progress
/trinity:loop stop <loop_id>                 request a graceful stop
```

No `@agent` means **this agent's remote copy** — the usual case is looping your own remote counterpart on Trinity.

Modifiers, anywhere in the message:

```
<N> times | x<N> | max <N>      iteration cap (max_runs, 1–100; default 5)
every <N>m | every <N>s         pause between iterations (delay_seconds, up to 1h)
until <condition> | stop when … Until mode — exits early on the [[DONE]] sentinel
```

Examples:

```
/trinity:loop @researcher draft section {{run}} of the report, 5 times
/trinity:loop refine the report until every TODO marker is resolved — stop when none remain
/trinity:loop @ci-agent run the test suite until it passes, max 10
/trinity:loop @monitor poll the deploy every 2m until it's healthy
/trinity:loop status loop_a1b2c3
/trinity:loop stop loop_a1b2c3
```

## Trigger

User wants to:
- Run a remote agent task N times, in order, optionally feeding each answer into the next
- Loop an agent until it signals done / a condition is met
- Poll something on the remote on a bounded cadence without holding a connection open
- "loop this agent", "run it until it passes", "iterate 5 times on the remote", "keep retrying until done"

Do **not** use this for a single remote turn (use `chat_with_agent`) or a parallel batch (use `fan_out`). This is the **sequential** primitive.

## Prerequisite — Trinity MCP connection

The `mcp__trinity__*` tools below need a live connection. If they're unavailable (or a call errors with no connection), run **`/trinity:connect`** — it authenticates and writes `.mcp.json` (or refreshes it from your stored profile) — then reconnect with `/mcp` (full restart only as a fallback) and resume. Never fall back to the Trinity CLI or `curl`.

---

## Parsing (in priority order)

Parse the input into `verb`, `@agent`, and the loop spec. Mirror `/loop`'s parsing discipline — resolve the cheap structural tokens first, then read intent.

1. **Leading verb**: if the first token is `status` or `stop`, that's the verb and the next token is a `loop_id`. Jump to that section. Otherwise the verb is `start`.
2. **`@agent` token**: an `@name` token anywhere selects the target agent. Strip it from the message.
3. **Iteration count**: a count phrase (`5 times`, `x5`, `10 iterations`, `max 10`) sets `max_runs`. If none is given, default to a sensible cap (`max_runs: 5`) and say so.
4. **Mode signal**: an *until-condition* (`until it passes`, `until tests are green`, `until done`, `stop when …`) → **Until mode**. Otherwise → **Fixed mode**.
5. **Cadence**: a `every <N>m`/`every <N>s` clause sets `delay_seconds`. Strip it from the message. The API caps it at 3600 — if the user asks for a period over 1 hour, don't silently clamp: tell them a loop isn't the right tool for that cadence and point them to a Trinity schedule (`create_agent_schedule` with a cron expression) instead.

If the remaining message is empty, show the usage block and stop.

---

## The two modes

`/trinity:loop` has exactly the two modes `/loop` has — the loop body is server-side instead of cron/`ScheduleWakeup`, but the shape is identical.

| `/loop` (local) | `/trinity:loop` (remote) | Engine |
|---|---|---|
| Fixed-interval (`/loop 5m`) — runs every tick, you stop it | **Fixed mode** — runs exactly `max_runs` times, then `max_runs_reached` | `max_runs`, optional `delay_seconds` |
| Dynamic (`/loop check the deploy`) — model self-paces, ends on a condition | **Until mode** — runs until a response contains `stop_signal`, capped by `max_runs` | `stop_signal` (sentinel `[[DONE]]`) + `max_runs` safety cap |
| — (no chaining) | **Chaining** (either mode) — feed each answer into the next | `{{run}}`, `{{previous_response}}` |

### Fixed mode
The default. Set `max_runs: N`. The loop runs N times and stops with `stop_reason: max_runs_reached`. Use for "do this N times" and bounded polling (add `delay_seconds`).

### Until mode
Triggered by an until-condition. Set a `stop_signal` (use `[[DONE]]`) **and** a `max_runs` safety cap (the loop will not run forever — the cap always wins). Then **rewrite the message so the agent emits the sentinel when the condition is met** — this is the crucial step. For example:

> `run the test suite. If every test passes, paste the passing output and end your reply with [[DONE]]. Otherwise, report what failed.`

Tie the sentinel to **verifiable evidence** (test output, an HTTP 200, zero remaining TODOs), not self-assessment — models skew positive grading their own work, so a gameable condition ("until it's good", "until it's tight") will exit on the first pass. If the user's condition is subjective, rewrite it into something checkable or keep the cap low.

The loop exits early with `stop_reason: stop_signal_matched` on the first iteration whose response contains `[[DONE]]`.

### Chaining (orthogonal to mode)
If the task refines or builds on prior output ("refine", "improve each pass", "continue from the last draft"), template the message with the substitution helpers:
- `{{run}}` → the 1-indexed iteration number
- `{{previous_response}}` → the trailing 2000 chars of the previous iteration's response (empty on run 1)

Example: `Draft section {{run}} of the report. Stay consistent with what came before: {{previous_response}}`

`{{previous_response}}` is lossy (trailing 2000 chars) — fine as a hint, not as the artifact. When iterations build a real artifact (a draft, a migration, a report), instruct the agent to keep it in a file in its workspace and re-read it each run: `Refine the draft in report.md — read it first, improve it, write it back.` The remote agent's filesystem persists across runs; the loop context doesn't.

---

## Verb: `start`

### PHASE 1 — Resolve the target agent

1. If an `@agent` was given, use it.
2. Otherwise, default to **the remote copy of this agent** — the primary use case is looping your own remote counterpart. Resolve it:
   - Read `.trinity-remote.yaml` at the repo root if present (the shared remote registry written by `/trinity:onboard` and `/trinity:sync`) and use the `agent` of its `default` remote under `remotes:`. For a legacy single-remote file (top-level `agent:`, no `remotes:`), use that `agent` directly.
   - Otherwise call `mcp__trinity__list_agents` and match this agent's own name (from `template.yaml` or the working directory name).
3. Only if no remote counterpart can be found, fall back to `mcp__trinity__list_agents`: exactly one agent → use it; several → `AskUserQuestion` with the agents as options (label = name, description = its purpose/status). Prefer a `running` agent — a loop needs the agent up.

### PHASE 2 — Design the loop

From the parse, assemble the `run_agent_loop` arguments:
- `agent_name` — from Phase 1
- `message` — the task, with `{{run}}`/`{{previous_response}}` woven in if chaining; for Until mode, with the explicit "end your reply with `[[DONE]]` when …" instruction appended
- `max_runs` — the count, or the default cap (1–100)
- `stop_signal` — `[[DONE]]` for Until mode; omit for Fixed mode
- `delay_seconds` — from any cadence clause (0–3600); omit if none
- `timeout_per_run` — set it for Until-mode loops (a hung iteration silently stalls the whole sequence); size it to the task, e.g. 600 for a test suite. For Fixed mode, set only if the task is long-running; else omit to inherit the agent default (10–7200)
- `model` — only if the user named one (e.g. `claude-opus-4-8`); else omit

If a key parameter is genuinely ambiguous (e.g. mode unclear, or no agent could be resolved), ask **one** focused `AskUserQuestion`. Don't interrogate — infer sensible defaults and state them.

### PHASE 3 — Fire

If the task is clear — agent resolved, mode and cap unambiguous — call `mcp__trinity__run_agent_loop` **immediately, without asking for confirmation**, and show the resolved plan alongside the handle it returns:

```
Agent:    researcher
Mode:     Until ([[DONE]]), cap 10
Delay:    none
Message:  run the test suite. If every test passes, end your reply with [[DONE]] …
```

Confirm first only when something genuinely warrants it: a key parameter was ambiguous and you had to guess, or the cost is outsized (large `max_runs` × expensive `model` — see Guardrails). One question max, then fire.

### PHASE 4 — Report the handle

The server starts iterating right away — like `/loop`, the first run happens **now**, not on some later tick. Report:
- the `loop_id` (the user needs it to check or stop — always surface it, the way `/loop` surfaces its job ID)
- the mode and cap
- how to come back: `/trinity:loop status <loop_id>` and `/trinity:loop stop <loop_id>`
- that they can disconnect; the loop also appears on the agent's **Loops** tab in the Trinity web UI

### PHASE 5 — Local watch (default)

After reporting the handle, start a lightweight local watch **by default** — skip it only if the user said fire-and-forget (or equivalent), or the session is headless. Invoke Claude Code's built-in dynamic `/loop` skill (no interval — it self-paces via `ScheduleWakeup`) with a watch prompt like:

> check trinity loop `<loop_id>` via `mcp__trinity__get_loop_status`; post one line only when something changed (`run N/M · status · cost`) or the loop looks stalled (near-identical consecutive responses — suggest `/trinity:loop stop <loop_id>`); when status is terminal, report `stop_reason` and the final response, then end the loop

Pace the watch to the loop: hint the expected iteration time (`delay_seconds` + typical run duration) in the prompt so wakeups aren't wasted. Tell the user the watch is on and that they can stop it anytime (say "stop watching" or Esc) — the remote loop keeps running either way. If the local `/loop` skill isn't available in this harness, skip the watch and just point to `/trinity:loop status <loop_id>`.

### PHASE 6 — Observe on demand

If the user asks to look right now, poll `mcp__trinity__get_loop_status` and render the per-run summary as a table — `run_number · status · cost · duration · response preview`. Re-poll on request rather than busy-looping. Stop polling once `status` is terminal (`completed` / `stopped` / `failed` / `interrupted`) and report the `stop_reason` and final response.

**Watch for stalls**: if consecutive responses are near-identical (same failure, same output, no state change), the loop is burning budget without progress — flag it and suggest `/trinity:loop stop <loop_id>`. The cap alone won't catch a stalled loop running under the limit.

---

## Verb: `status`

Call `mcp__trinity__get_loop_status` with the `loop_id` and render:
- header: `status`, `stop_reason` (if terminal), `runs_completed / max_runs`, total cost
- a per-run table: `# · status · cost · duration · response preview`
- the last full response below the table
- a stall warning if recent responses are near-identical with no progress — suggest `stop` rather than letting it run to the cap

If no `loop_id` was given and none is in this session's context, ask for it — there is no MCP "list loops" call, but loops are visible on the agent's **Loops** tab and in the execution timeline (tagged with `loop_id`) in the Trinity web UI.

## Verb: `stop`

Call `mcp__trinity__stop_loop` with the `loop_id`. It returns:
- `stopping` — the in-flight iteration finishes, then the loop exits with `stop_reason: user_stopped`. Report that the current run will complete.
- `already_done` — the loop had already reached a terminal state; report its final status via `get_loop_status`.

---

## Recipes

- **Iterative refinement** (Fixed + chaining): `Improve this draft. Previous version: {{previous_response}}` · `max_runs: 4`. Four progressively-refined passes.
- **Agentic retry** (Until): `Attempt the migration. If it succeeds, end with [[DONE]]; otherwise fix the error and we'll retry.` · `stop_signal: [[DONE]]` · `max_runs: 8`. Stops as soon as it works, bounded at 8 tries.
- **Bounded polling** (Until + delay): `Check the deploy health endpoint. If healthy, reply [[DONE]]; else report status.` · `stop_signal: [[DONE]]` · `delay_seconds: 120` · `max_runs: 30`. Polls every 2 min for up to an hour, exits the moment it's healthy.

---

## Guardrails

- **The cap is the safety net.** Always set `max_runs` even in Until mode — `stop_signal` is best-effort (the agent has to emit it); the cap is guaranteed. Bounds: `max_runs` 1–100, `delay_seconds` 0–3600, `timeout_per_run` 10–7200.
- **One loop, one handle.** Always echo the `loop_id`. A loop the user can't find is a loop they can't stop.
- **Sequential, not parallel.** If the user wants the *same* task across many agents/inputs at once, that's `fan_out`, not this.
- **Cost compounds.** N iterations = up to N task executions against the agent's budget. For large `max_runs` × expensive `model`, say so in the Phase 3 plan before firing.
