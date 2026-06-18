---
name: validate-pipeline
description: Lint a pipeline.yaml — schema check, DAG acyclicity, referenced-skill existence, precondition kind registration. Pure linter — prints a report, writes no files. Heartbeat does not require validation to have run; this is a developer convenience.
argument-hint: "<pipeline-slug>"
allowed-tools: Read, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-05-23
  author: Ability.ai
  changelog:
    - "1.0: Initial version — read-only pipeline.yaml linter checking schema, DAG acyclicity, referenced-skill existence, and precondition kinds; writes no files"
---

# Validate Pipeline

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `validate-pipeline vX.Y — recent: <summary>`. Then proceed.

Read-only linter. Verify a `pipeline.yaml` is structurally sound. Surfaces errors and warnings; **writes no files**.

Run this:
- After any manual edit to `pipeline.yaml`
- Automatically at the end of `/add-pipeline` and `/add-pipeline-stage`
- Before deploying the agent to a new environment

The heartbeat (`pipeline-tick`) reads `pipeline.yaml` directly each tick. It does not require this skill to have run. If you ship a broken `pipeline.yaml`, the heartbeat will fail loudly on the next tick — running the linter just gets you that feedback sooner.

## Process

### Step 1: Resolve target

Expect `<pipeline-slug>` as the single positional argument. If missing, list pipelines and prompt.

Validate `projects/<slug>/pipeline.yaml` exists.

### Step 2: Schema check

Required top-level keys: `schema_version`, `pipeline_id`, `name`, `stages`, `heartbeat`.

```bash
PIPELINE_FILE="projects/$SLUG/pipeline.yaml"

SCHEMA=$(yq '.schema_version // 0' "$PIPELINE_FILE")
[ "$SCHEMA" = "1" ] || error "schema_version must be 1 (got: $SCHEMA)"

ID=$(yq '.pipeline_id // ""' "$PIPELINE_FILE")
[ "$ID" = "$SLUG" ] || error "pipeline_id ($ID) doesn't match directory slug ($SLUG)"

STAGE_COUNT=$(yq '.stages | length' "$PIPELINE_FILE")
[ "$STAGE_COUNT" -gt 0 ] || error "No stages defined"

yq '.heartbeat.cron' "$PIPELINE_FILE" >/dev/null || error "heartbeat.cron is required"
yq '.heartbeat.skill' "$PIPELINE_FILE" >/dev/null || error "heartbeat.skill is required"
```

Collect all errors and report at the end — don't stop on the first one.

### Step 3: Stage-level checks

For each stage in `.stages[]`:

```bash
yq '.stages[] | [.id, .skill, .timeout_seconds, (.retry.max_attempts // 1), (.on_failure // "escalate")] | @tsv' "$PIPELINE_FILE"
```

Verify per stage:
- **id** matches `^[a-z][a-z0-9-]{0,40}$`, unique across all stages
- **skill** is non-empty; `.claude/skills/<skill>/SKILL.md` exists (warn, don't fail — the skill may be authored after the pipeline is defined)
- **timeout_seconds** is a positive integer (default to 600 if missing)
- **retry.max_attempts** is ≥1 (default 1 if missing)
- **retry.backoff_seconds** has length ≥ `max_attempts - 1` (so each retry has a backoff)
- **on_failure** is one of `advance | retry | escalate | halt`
- **depends_on** entries all reference existing stage ids

### Step 4: DAG acyclicity

Build the dependency graph from `depends_on` + explicit `transitions`. Run topological sort:

```python
# Implemented inline (no external deps). Pseudocode:
visited = {}      # node -> 'visiting' | 'done'
def visit(node):
    if visited.get(node) == 'visiting': raise CycleError(path_to_here)
    if visited.get(node) == 'done': return
    visited[node] = 'visiting'
    for dep in graph[node]: visit(dep)
    visited[node] = 'done'
for node in graph: visit(node)
```

If a cycle is found, show the path: `collect → curate → synthesize → collect` and stop. Cycles are a hard fail.

### Step 5: Reject conditional transitions (v1 limitation)

v1 supports sequential transitions only — branching is expressed by having a stage skill emit `next_stage` in its output JSON, and the heartbeat respects it.

For each transition entry, if a `condition` field is present, **hard fail**:

```
Transition <from> → <to> has a `condition` field. Conditional transitions are
not supported in v1. To branch, have the stage skill emit `next_stage` in its
output JSON — pipeline-tick will route accordingly.
```

### Step 6: Precondition kind registration

Recognized kinds (from the spec):
- `credential_present`
- `file_exists`
- `external_reachable`
- `subscription_active`
- `stage_output_present`

For each precondition in `stages[].preconditions[]`:
- If `kind` is in the registered set → ok
- Else → warning (not fail): `Stage "<id>" uses precondition kind "<x>" that pipeline-tick does not know about. The heartbeat will treat unmet preconditions of this kind as permanently unsatisfied. Either rename to a registered kind or extend pipeline-tick.`

### Step 7: Heartbeat sanity

- `heartbeat.cron` is a parseable cron expression (5 or 6 fields, standard characters).
- `heartbeat.skill` equals `pipeline-tick` (warn if not — supported but unusual).
- `heartbeat.pre_check` path exists OR is the standard `~/.trinity/pre-check`.

### Step 8: Sync ~/.trinity/ (only on pass)

If validation passed with no errors, refresh the read surface so the heartbeat picks up the latest yaml:

```bash
cp "$PIPELINE_FILE" "$HOME/.trinity/pipelines/$SLUG.yaml"
date -u +%Y-%m-%dT%H:%M:%SZ > "$HOME/.trinity/pipelines/$SLUG.last_synced"
```

If validation failed, **do not** sync — the heartbeat keeps reading the previous good copy.

### Step 9: Report

If validation passed:

```
✅ Pipeline `<SLUG>` validated.

Stages: <N> (order: collect → curate → synthesize → publish → measure)
Transitions: <M>
Preconditions: <P>
Estimated cycle time (sum of timeouts): <S>s

Read surface synced: ~/.trinity/pipelines/<SLUG>.yaml

Warnings:
- <list — empty if none>
```

If validation failed:

```
❌ Pipeline `<SLUG>` has <N> errors. Read surface NOT synced — pipeline-tick will keep using the previous good copy until you fix and re-validate.

Errors:
1. <error>
2. <error>
…

Warnings:
- <list>

Fix pipeline.yaml and re-run /validate-pipeline <SLUG>.
```

---

## Error handling

| Situation | Action |
|---|---|
| Pipeline doesn't exist | Refuse, suggest `/add-pipeline` |
| pipeline.yaml syntactically invalid (yq parse error) | Report parse error verbatim |
| Cycle detected | Show cycle path, fail |
| Transition with `condition` field | Fail with v1-limitation message |
| Unknown precondition kind | Warn, pass |
| Missing skill referenced by stage | Warn, pass — gives flexibility to scaffold skills after defining the pipeline |

## Invariants

- This skill writes nothing to the agent repo. The only filesystem side effect is refreshing `~/.trinity/pipelines/<slug>.yaml` on a clean pass.
- The heartbeat does not require this skill to have run. v1 keeps the contract simple: `pipeline.yaml` is the only source of truth; the heartbeat reads it directly.
