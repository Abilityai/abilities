---
name: pipeline-status
description: Show the current state of every pipeline instance in this agent — stage, health, last advance, open escalations. Reads ~/.trinity/pipeline-state/.
argument-hint: "[pipeline-slug]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
  source: agent-dev:add-pipeline
---

# Pipeline Status

Operator view. Read-only. Same data the Trinity dashboard panel shows.

## Process

### Step 1: Scope

If `$ARGUMENTS` is a pipeline slug, restrict to that pipeline. Otherwise show every pipeline.

### Step 2: Load state files

```bash
if [ -n "$ARGUMENTS" ]; then
  STATE_FILES=$(ls ~/.trinity/pipeline-state/$ARGUMENTS/*.json 2>/dev/null)
else
  STATE_FILES=$(ls ~/.trinity/pipeline-state/*/*.json 2>/dev/null)
fi
```

If none, print `No pipeline state found. Has /add-pipeline run?` and exit.

### Step 3: Format table

For each state file, extract via `jq`:
- `pipeline_id`
- `instance_id`
- `status`
- `current_stage` (or "—" if idle)
- `stage_attempt / stage_max_attempts` (if running)
- `health`
- `last_advanced_at` (humanized: "3m ago", "2h ago", "1d ago")
- `open_escalations | length`

Print one row per instance, grouped by `pipeline_id`. Bold the header. Use a simple markdown table.

Example output:

```
## columns

| Instance       | Status   | Stage       | Attempt | Health | Last advance | Escalations |
|---             |---       |---          |---      |---     |---           |---          |
| moltbook-eco   | running  | synthesize  | 1/2     | green  | 2h ago       | 0           |
| ai-adoption    | blocked  | collect     | 1/3     | yellow | 18h ago      | 0           |

## another-pipeline
…
```

### Step 4: Suggest follow-ups

If any instance shows `escalated` or `blocked`, suggest `/pipeline-recover <pipeline> <instance>`. If any shows `paused`, suggest `/pipeline-resume`. Otherwise nothing.
