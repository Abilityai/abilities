---
name: pipeline-tick
description: Heartbeat that advances pipelines through their stages — reads ~/.trinity/pipelines/*.yaml + ~/.trinity/pipeline-state/**/*.json, evaluates each instance, advances or retries or escalates. Invoked by scheduler every 15 minutes.
allowed-tools: Bash, Read, Write, Edit, Glob, Skill, Agent
automation: autonomous
user-invocable: true
metadata:
  version: "1.1"
  author: agent-dev
  source: agent-dev:add-pipeline
  changelog:
    - "1.1: Drop the pre-check premise — the hook is removed (Trinity's agent-global pre-check contract cannot express a safe gate: any stdout replaces the calling schedule's message); the tick itself is the cheap no-op filter. New Step 9 materializes the dashboard.yaml Pipelines table rows after state writes"
    - "1.0: Initial version — heartbeat that advances pipelines through their stages (advance/retry/escalate/wait/complete), atomic state writes, ~/.trinity read-surface sync"
---

# Pipeline Tick

The heartbeat loop for every pipeline installed in this agent. One pass = one evaluation across every pipeline + instance. Cheap when nothing needs attention — Steps 1–3 are pure reads, and a pass where every instance is waiting ends after the one-line summary. (There is deliberately **no** pre-check gate: Trinity's pre-check hook is agent-global and any stdout it emits replaces the calling schedule's message, so skip logic lives here instead.)

## Invariants

- `~/.trinity/pipelines/*.yaml` is the pipeline manifest read surface (write-through copy of `projects/<slug>/pipeline.yaml`).
- `~/.trinity/pipeline-state/<pipeline_id>/<instance_id>.json` is the state read/write surface (write-through copy of `projects/<slug>/instances/<instance>/state.json`).
- This skill **never** edits `pipeline.yaml`. It only reads it. Pipeline edits go through `/add-pipeline-stage` or manual edit + `/validate-pipeline`.
- This skill is the **only** writer of `state.json`. Other skills (recover, pause, resume) write via this same skill or via well-defined operator commands.

## Process

### Step 1: Enumerate pipelines

```bash
ls ~/.trinity/pipelines/*.yaml 2>/dev/null
```

If none, exit cleanly: "No pipelines installed."

### Step 2: For each pipeline, enumerate instances

For each `~/.trinity/pipelines/<slug>.yaml`:

```bash
PIPELINE_ID=$(yq '.pipeline_id' ~/.trinity/pipelines/<slug>.yaml)
INSTANCES_DIR=$(yq '.instances.path' ~/.trinity/pipelines/<slug>.yaml)
STATUS_FILTER=$(yq '.instances.status_filter' ~/.trinity/pipelines/<slug>.yaml)
```

Resolve `INSTANCES_DIR` relative to the agent root. List subdirectories whose `config.yaml` matches `status_filter` (default `[active]`).

### Step 3: For each instance, load state and decide

Read `~/.trinity/pipeline-state/$PIPELINE_ID/$INSTANCE_ID.json`. If missing, scaffold from `state.json.template` shape (status `idle`, empty stages map).

Apply decision rules **in priority order** — stop at the first match:

1. **Open escalation unresolved** → action `wait`
   - Check `state.open_escalations[]`. If any has no `resolved_at`, wait.
2. **Current stage `in_progress` and not yet timed out** → action `wait`
   - `now - stages[current_stage].started_at < pipeline.stages[current_stage].timeout_seconds` → wait.
3. **Current stage `in_progress` and timed out** → action `retry` or `escalate`
   - Compare `stage_attempt` vs `stage_max_attempts`. Under limit → `retry` with backoff. At limit → `escalate`.
4. **Current stage `last_status == "failed"`** → action `retry` or `escalate`
   - Same logic as (3).
5. **Current stage `last_status == "completed"`** →
   - Find next stage via `transitions[]` (or default `depends_on` ordering).
   - Evaluate the next stage's `preconditions[]` and `gates[]`.
   - All satisfied → action `advance`.
   - Any unsatisfied → action `wait`, record `blockers[]` in state.
6. **No next stage (terminal reached)** → action `complete_cycle`.

### Step 4: Execute the chosen action

**`advance`:**
1. Update state: `current_stage = next_stage`, `stage_entered_at = now`, `stage_attempt = 1`, `stages[next_stage].started_at = now`, `stages[next_stage].last_status = "in_progress"`.
2. Write state (atomic — write to `.tmp` then rename).
3. Sync to `~/.trinity/pipeline-state/$PIPELINE_ID/$INSTANCE_ID.json`.
4. Emit event `pipeline.$PIPELINE_ID.$INSTANCE_ID.stage_advanced` via Trinity MCP if available.
5. Trigger the stage skill: invoke `Skill` with `skill: <stages[next_stage].skill>` and `args: instance=$INSTANCE_ID pipeline=$PIPELINE_ID`.

**`retry`:**
- If `stage_attempt < stage_max_attempts`:
  - Increment `stage_attempt`.
  - Compute backoff: `pipeline.stages[current].retry.backoff_seconds[stage_attempt - 1]`. Set `next_check_at = now + backoff`.
  - Write state.
  - When backoff has elapsed (next tick), re-trigger the stage skill.
- Else fall through to `escalate`.

**`escalate`:**
1. Build escalation message from `pipeline.escalation.template` with substitutions.
2. Determine `suggested_actions` key by inspecting last error (precondition kind, timeout, generic).
3. File operator-queue item via Trinity MCP `send_notification` with `context: { pipeline_id, instance_id, stage, last_error }`. Capture returned `queue_id`.
4. Append to `state.open_escalations[]`: `{ queue_id, filed_at, stage, reason }`.
5. Set `state.status = "escalated"`.
6. Write state. Emit `pipeline.$PIPELINE_ID.$INSTANCE_ID.escalated` event.

**`wait`:**
- Update `state.next_check_at` to a sensible value (15min default, or precondition retry interval).
- If blockers were collected in step 3, write them to `state.blockers[]` for visibility.
- Write state. No event.

**`complete_cycle`:**
1. Set `state.last_completed_cycle_at = now`, `state.status = "idle"`, `state.current_stage = null`.
2. Increment `state.metrics.cycles_completed`.
3. Write state. Emit `pipeline.$PIPELINE_ID.$INSTANCE_ID.cycle_completed` event.

### Step 5: Precondition evaluation reference

For each precondition in the next stage's `preconditions[]`:

| Kind | Check |
|---|---|
| `credential_present` | Call Trinity MCP `get_credential_status` with `keys`. All present + non-expired → pass. |
| `file_exists` | Resolve `path` relative to `instances/<instance>/`. `[ -f "$resolved" ]` → pass. |
| `external_reachable` | `curl -sIo /dev/null -w '%{http_code}' --max-time 5 "$url"` → 2xx/3xx → pass. |
| `subscription_active` | Trinity MCP `get_agent_auth` with `subscription_id` → status `active` → pass. |
| `stage_output_present` | Look up `state.stages[stage].last_output_summary`, check `key` exists. |

If a kind is unknown, record blocker `precondition_kind_unknown:<kind>` and `wait`.

### Step 6: Branching via stage output

v1 has no transition condition expressions. To branch, a stage skill writes an explicit `next_stage` field into its output JSON. When determining the next stage:

1. Check `state.stages[just_completed_stage].last_output` for a `next_stage` field. If present and the referenced stage exists, route there.
2. Otherwise, fall back to the default transition table (sequential by `depends_on`, or the first matching entry in `transitions[]`).

If the output specifies a `next_stage` that doesn't exist in the pipeline, record a blocker `unknown_next_stage:<name>` and `wait` — don't guess.

### Step 7: Atomic state writes

```bash
TMP="${STATE_FILE}.tmp.$$"
jq '. + { updated_at: "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'" }' "$STATE_FILE" > "$TMP"
mv "$TMP" "$STATE_FILE"
# Sync to ~/.trinity/pipeline-state/
cp "$STATE_FILE" "$HOME/.trinity/pipeline-state/$PIPELINE_ID/$INSTANCE_ID.json"
```

### Step 8: Append to stage log

For every state transition, append a line to `instances/$INSTANCE_ID/stage-logs/$(date +%Y-%m-%dT%H)-$STAGE.json` with `{ ts, action, from_stage, to_stage, attempt, reason }`. Logs are append-only — never edited or deleted by this skill.

### Step 9: Refresh the dashboard table (if present)

If `dashboard.yaml` exists and contains the section marked `managed by /add-pipeline`, rewrite that table widget's `rows:` — one row per pipeline × instance, from the state just written:

```yaml
rows:
  - { pipeline: <pipeline_id>, instance: <instance_id>, stage: <current_stage or —>, status: <status>, health: <green|yellow|red per pipeline.yaml health rollup>, last_advanced: <stages[current_stage].started_at or last_completed_cycle_at> }
```

Trinity renders `dashboard.yaml` values as-is — it does not read other files or compute anything — so this materialization is what keeps the UI current. Touch only the managed section's `rows:`; never other sections. Skip silently if the file or the managed section is absent.

## Refusing to act

If `pipeline.yaml` is syntactically invalid (yq parse error) or missing required fields (`pipeline_id`, `stages`, `heartbeat`), refuse to act on that pipeline and file a high-priority escalation with the parser error. Other pipelines continue normally.

Run `/validate-pipeline <slug>` to surface the same errors interactively.

## Output

End with a one-line summary:

```
Tick complete: <N> pipelines, <M> instances. Actions: <advance: X, retry: Y, escalate: Z, wait: W, complete: C>.
```
