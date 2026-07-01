---
name: sync-fleet-to-head
description: Ensure every fleet agent on Trinity is running its GitHub HEAD, non-destructively (never discards local changes). Scope comes from the orchestration narrative — only agents declared in fleet/orchestration.md + fleet/system-map.yaml are touched.
when_to_use: When you want to verify or bring the fleet's Trinity agents up to their appropriate GitHub HEAD after upstream changes — "check the agents are on latest", "sync the fleet to HEAD", "are any agents behind their repo", periodic fleet git hygiene. Pull-only and non-destructive; it never force-resets and never pushes.
automation: gated
allowed-tools: Read, Grep, Skill, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_git_sync_state, mcp__trinity__get_git_status, mcp__trinity__git_pull, mcp__trinity__chat_with_agent, mcp__trinity__get_git_log
effort: high
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-01
  author: orchestrator
  changelog:
    - "1.0: Initial version — narrative-scoped fleet HEAD sync; non-destructive pull ladder (clean -> stash_reapply), stash-reapply-warning detection, trivial-conflict union-resolve via chat_with_agent, ahead/no-repo/out-of-scope handling; two approval gates"
---

# Sync Fleet to HEAD

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `sync-fleet-to-head vX.Y — recent: <summary>`. Then proceed.

## Purpose

Bring every **fleet** agent deployed on Trinity up to its **appropriate GitHub HEAD**, while **never destroying local changes**. "Which agents" is decided by the **orchestration narrative**, not by a raw Trinity listing: the roster in `fleet/orchestration.md` (§3 Nodes) and the machine-readable `fleet/system-map.yaml` define scope. An agent that is live on Trinity but absent from the narrative is reported, not pulled.

This is **pull-only and non-destructive**. It uses `clean` then escalates to `stash_reapply`; it **never** uses `force_reset` / `reset_to_main_preserve_state`, and it **never pushes**. Agents that are *ahead* of their remote (unpushed local commits) are flagged and left untouched.

ultrathink — git edge cases (rebase-vs-dirty-tree, partial stash pops, real merge conflicts, per-agent key scope) are the whole point of this playbook. Reason about each agent's state before acting; when in doubt, stop and preserve.

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Orchestration narrative (scope + intent) | `fleet/orchestration.md` | ✓ | |
| System map (nodes: `ref`, `source`) | `fleet/system-map.yaml` | ✓ | |
| Live Trinity agents | `mcp__trinity__list_agents` | ✓ | |
| Per-agent git state | `mcp__trinity__get_git_sync_state`, `get_git_status`, `get_git_log` | ✓ | |
| Agent workspaces (remote) | `mcp__trinity__git_pull` (pull only) | | ✓ |
| Conflict resolution (remote) | `mcp__trinity__chat_with_agent` | | ✓ |
| System map refresh (when stale) | `/discover-agents` | | ✓ (writes `fleet/system-map.yaml`) |

## Prerequisites

- Trinity MCP (`trinity` server) reachable and callable (`mcp__trinity__*`).
- `fleet/orchestration.md` and `fleet/system-map.yaml` exist. If the map is missing or clearly stale versus live Trinity, refresh it first (see Step 1 — composes `/discover-agents`).
- A Trinity key with scope to read git state and pull for the in-scope agents. Some agents may be owned by **teammates** (another Trinity user); `git_pull` is available to owners **and shared accessors**, and `get_git_*` obeys per-agent permission. Insufficient scope → skip that agent and flag it, never fail the whole run.

## Composes

- `/discover-agents` — rebuilds `fleet/system-map.yaml` from `fleet/sources.yaml` and live Trinity. Invoked only when the map is missing or stale; this playbook otherwise **reads** the map, it does not regenerate it.

## Process

### Step 1: Load scope from the narrative

1. Read `fleet/orchestration.md` (§3 Nodes) for the human-facing fleet roster and intent.
2. Read `fleet/system-map.yaml` `agents:` block — the machine-readable roster. For each entry derive:
   - **`trinity_name`** = the deployed name to act on. It is the `deployed_name` field if present, else the last path segment of `ref:` (e.g. `trinity://default/researcher-prod` → `researcher-prod`). The map key is the *logical* name; the deployable Trinity name lives in `deployed_name`/`ref:`. Always act on `trinity_name`.
   - **`repo`** = `source:`/`github_repo:` — if it starts with `github:` the agent is GitHub-backed (strip the prefix → `Org/repo`); a local path (`../…`, `/…`, `~…`) or non-github source means **no repo → skip with a note**.
3. **Freshness check:** if `fleet/system-map.yaml` is missing, or its `agents:` set diverges materially from `list_agents` (Step 2), invoke `/discover-agents` to refresh, then re-read. Do not hand-edit the map.

The set of `trinity_name` values with a `github:` source is the **in-scope candidate list**. Nothing outside this list gets pulled.

### Step 2: Reconcile with live Trinity

Call `mcp__trinity__list_agents` once. Join to the narrative roster by `trinity_name` and partition:

- **In-scope + GitHub-backed + live** → survey for HEAD (Step 3).
- **No repo** (local template / system agent) → skip; list under "no repo".
- **Live but not in the narrative** → **out of scope**; list under "on Trinity, not in fleet narrative" and suggest `/discover-agents` if it should be adopted. Do **not** pull it.
- **In narrative but not live** → drift; flag under "declared but not running".

### Step 3: Survey git state (read-only)

For every in-scope + GitHub-backed agent, call `get_git_sync_state` (compact — gives `ahead_working` / `behind_working`). Run them in parallel. Prefer `get_git_sync_state` over `get_git_status` for the survey — `get_git_status` can return enormous change lists (committed cache dirs, todos) that add nothing here. Classify each:

- **at-HEAD** — behind 0, ahead 0 → no action.
- **behind** — behind > 0, ahead 0 → will pull.
- **ahead** — ahead > 0, behind 0 → **unpushed local commits**; flag, do **not** touch (not behind = nothing to pull; pushing is out of scope).
- **diverged** — ahead > 0 and behind > 0 → attempt non-destructive pull; likely needs manual resolution (Step 6).

### Step 4: Present the plan — [APPROVAL GATE]

Show a single table and wait for approval before any pull:

```
agent (trinity)          repo                          behind  ahead  planned action
researcher-prod          your-org/researcher             2      0     pull -> HEAD (non-destructive)
analyst-prod             your-org/analyst               29      0     pull -> HEAD (non-destructive)
writer-prod              your-org/writer                 0      2     NONE (unpushed commits — flag only)
scheduler                (local template)                -      -     skip (no repo)
some-other-agent         (not in narrative)              -      -     skip (out of scope)
```

State plainly: pulls are non-destructive (never force-reset, never push); ahead agents are left alone. Get a yes before mutating. If there is nothing to pull, report and stop here.

### Step 5: Pull behind/diverged agents (non-destructive)

For each agent to pull, walk this ladder — stop at the first success:

1. `git_pull(strategy: "clean")`.
   - Success → done for this agent.
   - **409 with unstaged/uncommitted changes** (`"cannot pull with rebase: You have unstaged changes"`) → `clean` rebases and refuses on a dirty tree. This is expected; escalate to step 2. Nothing was changed.
2. `git_pull(strategy: "stash_reapply")` — stashes local changes, pulls, reapplies.
   - `success: true` with **no** warning → done; local changes preserved.
   - `success: true` **with `"Could not reapply local changes"`** in the message → the stash pop hit a conflict. **The local changes are NOT lost** (retained in the stash + left as conflict markers), but they are not applied. Go to Step 6. **Do not** treat this as clean success.
   - 409 real merge conflict → Step 6.

**Never** call `git_pull(strategy: "force_reset")` and **never** call `reset_to_main_preserve_state` — both discard local history. If a divergence genuinely can't be resolved non-destructively, hand it to the human (Step 6); do not force.

### Step 6: Conflict handling — [APPROVAL GATE for anything non-trivial]

Call `get_git_status` for the agent and find unmerged paths (`UU` / `AA` / `DD`).

- **Trivial, union-mergeable files** — `.gitignore`, lock files, append-only logs/manifests: resolve by keeping **both** sides (dedupe, drop nothing unique) via `chat_with_agent`, then `git add` the file. Only after confirming **no** unmerged paths remain, `git stash drop` the auto-stash. **Never drop a stash that did not fully apply.** Delegation shape that works:

  ```
  chat_with_agent(
    agent_name=<trinity_name>, parallel=true, allowed_tools=["Bash"],
    message="Resolve the `.gitignore` merge conflict by keeping the union of both
             sides (remove <<<<<<< / ======= / >>>>>>> markers, keep every unique
             line). git add it. Confirm no remaining UU/AA/DD paths. Only then
             `git stash drop` the top 'auto-stash before pull' entry. Do NOT commit
             or push. Leave untracked files untouched. Print final `git status --short`,
             `git rev-parse --short HEAD`, and `git stash list`.")
  ```

- **Non-trivial conflicts** (source code, semantic config) → **STOP for this agent.** Do not guess a resolution. Report the conflicted files; the local work is safe in the stash. This is the gate — hand it to the human. Move on to the remaining agents.

Never `git commit` or `git push` during resolution unless the user explicitly asks.

### Final Step: Verify and report

Re-call `get_git_sync_state` for each acted agent and confirm `behind_working == 0`. Then report a compact before → after summary:

- **Pulled to HEAD:** agent → new short SHA.
- **Already at HEAD:** count / list.
- **Left ahead (unpushed commits):** agent (+N) — note these are NOT on their GitHub HEAD by choice; offer to sync them up only if the user asks.
- **Conflicts:** resolved (how) vs handed back (which files).
- **Skipped:** no-repo agents; out-of-scope (not in narrative) agents; declared-but-not-running drift.
- **Permission-skipped:** any agent the key couldn't read/pull.

## Completion Checklist

- [ ] Scope was taken from `fleet/system-map.yaml` / `fleet/orchestration.md`, not a raw `list_agents` sweep.
- [ ] Every in-scope GitHub-backed agent surveyed; classified at-HEAD / behind / ahead / diverged.
- [ ] Plan approved at the gate before any pull.
- [ ] Behind agents pulled via the non-destructive ladder; no `force_reset`, no `reset_to_main_preserve_state`, no push.
- [ ] `stash_reapply` "could not reapply" warnings detected and routed to conflict handling (not mistaken for clean success).
- [ ] No stash dropped unless its changes fully reapplied and staged.
- [ ] Non-trivial conflicts handed to the human, not auto-guessed.
- [ ] Ahead / no-repo / out-of-scope / drift all reported.
- [ ] Post-pull `behind_working == 0` verified for every acted agent.

## Error Recovery

| Situation | Action |
|---|---|
| `fleet/system-map.yaml` missing or stale | Invoke `/discover-agents` to (re)build it, then re-read. |
| `get_git_*` permission denied for an agent | Insufficient key scope — skip, list under "permission-skipped", continue. |
| `clean` returns 409 unstaged changes | Expected on a dirty tree (clean = rebase). Escalate to `stash_reapply`. |
| `stash_reapply` success **with** "Could not reapply local changes" | Stash pop conflicted; go to conflict handling. Local work is in the stash — do not drop it. |
| Real merge conflict on non-trivial files | STOP for that agent; report conflicted paths; leave the stash intact for the human. |
| `chat_with_agent` returns `queued_timeout` | The task is still running — poll `get_execution_result(execution_id)`; do NOT re-send (duplicate-guard will kill it). |
| Agent stopped / unhealthy | Skip git ops for it; flag as "not running". |
| Nothing is behind | Report "all in-scope agents at HEAD" and stop — no gate needed. |

## Operational Notes (hard-won)

- **`clean` == `git pull --rebase`.** It refuses on a dirty working tree; that refusal is safe (nothing changed) and is the trigger to escalate, not an error to surface as failure.
- **`stash_reapply` can "succeed" and still not apply your changes.** Always check the message for the reapply warning.
- **The self-reference:** if this orchestrator is itself deployed on Trinity (often under a different name than this local repo), pulling that entry acts on the **deployed twin**, not this local repo. Resolving its conflicts via `chat_with_agent` is the orchestrator operating on itself — that's expected and fine.
- **Scheduling:** because of the approval gate this can't run fully unattended (it would hang). If you want a cadence, schedule a **survey-only** variant that just reports drift (Steps 1-3), and run the pulls interactively.

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: New git edge case, MCP behavior, or scope-mapping quirk encountered?
- [ ] **Identify improvements**: Could the pull ladder, conflict triage, or narrative-scope parsing be clearer or safer?
- [ ] **Scope check**: Only tactical/execution changes — NOT the core purpose (narrative-scoped, non-destructive, pull-only).
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md; bump `metadata.version` and prepend a `changelog` entry (newest-first).
  - [ ] Keep changes minimal and focused.
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/sync-fleet-to-head/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(sync-fleet-to-head): <brief improvement description>"`
