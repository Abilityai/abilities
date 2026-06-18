---
name: add-pipeline-stage
description: Append a new stage to an existing pipeline.yaml — asks for stage id, skill, timeout, retry policy, and position in the DAG. Validates DAG acyclicity and syncs the read surface.
argument-hint: "<pipeline-slug> [stage-id]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-05-23
  author: Ability.ai
  changelog:
    - "1.0: Initial version — appends a new stage to an existing pipeline.yaml with retry/timeout defaults, DAG acyclicity checks, and skill-existence validation"
---

# Add Pipeline Stage

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-pipeline-stage vX.Y — recent: <summary>`. Then proceed.

Extend an existing pipeline with a new stage. Edits `projects/<slug>/pipeline.yaml` non-destructively and revalidates.

Use this instead of editing `pipeline.yaml` by hand when you want guardrails on retry/timeout defaults, DAG acyclicity, and skill-existence checks.

## Process

### Step 1: Resolve pipeline

Expect `<pipeline-slug>` as the first positional argument. If missing, list `projects/*/pipeline.yaml` and ask which one.

Validate that `projects/<slug>/pipeline.yaml` exists. If not, suggest `/add-pipeline` to create it.

### Step 2: Read current pipeline

```bash
PIPELINE_FILE="projects/$SLUG/pipeline.yaml"
yq '.stages[].id' "$PIPELINE_FILE"  # existing stage IDs
```

Show the user the current stage list (compact: `id (skill) → next`).

### Step 3: Ask stage parameters

**Q1 — Stage id**
- Free text. Validate: `^[a-z][a-z0-9-]{0,40}$`. Refuse if it collides with an existing stage id (suggest a different id).
- If passed as second positional arg, skip this question.

**Q2 — Skill to invoke**
- Free text. Validate: `[ -d .claude/skills/<skill-name> ]`. If the skill doesn't exist, warn but allow (user may scaffold it after).
- Show available skills from `ls .claude/skills/` as a hint.

**Q3 — Position in DAG**
Use `AskUserQuestion` with options:
- `Append at end` (runs after the current last stage) — most common
- `After a specific stage` (free-text picker among existing stage ids)
- `Parallel to a stage` (same `depends_on` as the picked stage — fan-out)
- `Terminal — no successor` (runs on cycle but no `depends_on` points to a successor; useful for measurement/audit stages)

**Q4 — Timeout (seconds)**
- Default 600. Common values: 300 (5m), 600 (10m), 1800 (30m), 3600 (1h), 7200 (2h).
- Free-text integer.

**Q5 — Retry policy**
- `Standard` — `max_attempts: 2, backoff_seconds: [60, 300]`
- `Aggressive` — `max_attempts: 3, backoff_seconds: [60, 300, 1800]`
- `No retry` — `max_attempts: 1`
- `Custom` — ask for max_attempts and backoff sequence

**Q6 — On failure**
- `escalate` (default) — file an operator-queue item after retries exhausted
- `retry` — keep retrying (use only for transient external dependencies)
- `halt` — stop the cycle, mark instance blocked, don't escalate (rare)
- `advance` — skip the stage and continue (only for nice-to-have stages)

**Q7 — Preconditions (optional)**
Offer common templates the user can pick (multi-select):
- `credential_present` — ask for key names
- `file_exists` — ask for path
- `external_reachable` — ask for URL
- `subscription_active` — ask for subscription_id
- `stage_output_present` — ask for stage + key
- `None`

### Step 4: Build the stage entry

Compose the YAML fragment:

```yaml
  - id: <STAGE_ID>
    skill: <SKILL>
    timeout_seconds: <TIMEOUT>
    retry:
      max_attempts: <N>
      backoff_seconds: [<...>]
    depends_on: [<inferred from Q3>]
    preconditions:
      - kind: <KIND>
        <params>
    on_failure: <ACTION>
    description: ""
```

Omit empty fields (e.g. `preconditions: []` → don't include the key).

### Step 5: Insert into pipeline.yaml

Use `yq` to append to `.stages` (preserves comments and other top-level keys):

```bash
yq -i ".stages += [<stage-yaml>]" "$PIPELINE_FILE"
```

If Q3 was "After a specific stage" or "Parallel to a stage", also add a transition entry:

```bash
yq -i ".transitions += [{\"from\": \"<from>\", \"to\": \"<STAGE_ID>\", \"on\": \"stage_completed\"}]" "$PIPELINE_FILE"
```

### Step 6: Validate

Invoke `validate-pipeline`:

```
Skill: validate-pipeline
Args: <SLUG>
```

If validation fails:
1. Show the error.
2. Offer to roll back the edit (`yq -i 'del(.stages[-1])' "$PIPELINE_FILE"` if it was an append).
3. Or let the user fix it manually and re-validate.

### Step 7: Sync read surface

```bash
cp "$PIPELINE_FILE" "$HOME/.trinity/pipelines/$SLUG.yaml"
date -u +%Y-%m-%dT%H:%M:%SZ > "$HOME/.trinity/pipelines/$SLUG.last_synced"
```

### Step 8: Summary

```
## Stage `<STAGE_ID>` added to `<SLUG>`

Position: <description from Q3>
Skill:    <SKILL_NAME>
Timeout:  <N>s
Retry:    <max_attempts> attempts, backoff <[...]>
On fail:  <ACTION>

~/.trinity/pipelines/<SLUG>.yaml synced.

Heartbeat will pick up the new stage on the next tick.
Run /pipeline-tick to evaluate immediately.
```

---

## Error handling

| Situation | Action |
|---|---|
| Pipeline slug doesn't exist | Suggest `/add-pipeline <slug>` |
| Stage id collides | Refuse, ask for a different id |
| Skill doesn't exist | Warn, continue (user may scaffold) |
| Validation fails after insert | Offer rollback or manual fix |
| Cycle introduced (DAG ack) | Refuse — show the cycle path; ask user to revise `depends_on` |
| yq not installed | Stop and ask user to install — too risky to hand-patch yaml |
