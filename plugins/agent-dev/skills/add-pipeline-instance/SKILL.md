---
name: add-pipeline-instance
description: Scaffold a new instance (tenant / zone / case) of an existing pipeline — creates projects/&lt;slug&gt;/instances/&lt;instance&gt;/{config.yaml, state.json} and syncs state.json to ~/.trinity/pipeline-state/.
argument-hint: "<pipeline-slug> <instance-slug> [--from <existing-instance>]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-05-23
  author: Ability.ai
---

# Add Pipeline Instance

Add an independent runtime instance to an existing pipeline. Each instance runs the same DAG with its own state and config — a zone, a tenant, a case, a customer.

The pipeline is the DAG. The instance is *who the DAG runs for*.

## Process

### Step 1: Resolve pipeline + instance slug

Expect `<pipeline-slug> <instance-slug>` as positional args. If missing, prompt.

Validate:
- `projects/<pipeline-slug>/pipeline.yaml` exists (else suggest `/add-pipeline`).
- `<instance-slug>` matches `^[a-z][a-z0-9-]{1,40}$`.
- `projects/<pipeline-slug>/instances/<instance-slug>/` does **not** already exist (else refuse — picking a new slug, or use `/pipeline-resume` if you meant to reactivate).

### Step 2: Optional — clone from an existing instance

If `--from <existing-instance>` was passed, copy that instance's `config.yaml` as the starting point. Useful when most fields are identical across tenants/zones.

```bash
SRC="projects/$PIPELINE/instances/$FROM/config.yaml"
[ -f "$SRC" ] || error "Source instance not found"
mkdir -p "projects/$PIPELINE/instances/$INSTANCE"
cp "$SRC" "projects/$PIPELINE/instances/$INSTANCE/config.yaml"
```

Otherwise, scaffold a minimal `config.yaml`:

```yaml
# Instance config for <INSTANCE> in pipeline <PIPELINE>
status: active                  # active | inactive — controls whether heartbeat evaluates
name: "<Human Name>"

# Per-instance overrides — merge over pipeline.yaml defaults.
# Common keys: sources, tags, filters, schema, PIRs, target outputs.
# Add what your stages need:
overrides: {}
```

### Step 3: Ask config questions

These are intentionally minimal — instance-specific fields depend on the pipeline. Ask only what the pipeline needs.

**Q1 — Display name** (free text)
- "Human-readable name for this instance."

**Q2 — Initial status**
- `active` (default) — heartbeat evaluates immediately
- `inactive` — scaffold only, don't run until manually activated

**Q3 — Open config for editing?**
- `Yes — open in $EDITOR` (recommended for the first instance of a pipeline)
- `No — accept the scaffold, I'll edit later`

If yes, drop a generated comment block at the top of `config.yaml` listing the keys the pipeline's stages reference (parse stage skills' SKILL.md frontmatter / arg hints for hints, best-effort).

### Step 4: Initialize state.json

Read the template, substitute, write:

```bash
SKILL_DIR="<this-skill-dir>"  # or resolve via $CLAUDE_PLUGIN_ROOT if set
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
AGENT_NAME=$(yq '.name // ""' template.yaml 2>/dev/null || basename "$PWD")

sed -e "s|{{PIPELINE_ID}}|$PIPELINE|g" \
    -e "s|{{INSTANCE_ID}}|$INSTANCE|g" \
    -e "s|{{AGENT_NAME}}|$AGENT_NAME|g" \
    -e "s|{{CREATED_AT}}|$NOW|g" \
  "$SKILL_DIR/../add-pipeline/templates/state.json.template" \
  > "projects/$PIPELINE/instances/$INSTANCE/state.json"
```

If the chosen initial status is `inactive`, set `status: "paused"` in state.json and add a `paused_at` timestamp.

### Step 5: Create supporting directories

```bash
mkdir -p "projects/$PIPELINE/instances/$INSTANCE/stage-logs"
mkdir -p "projects/$PIPELINE/instances/$INSTANCE/artifacts"
mkdir -p "projects/$PIPELINE/instances/$INSTANCE/escalations"
```

If the agent has a `.gitignore`, suggest adding `projects/*/instances/*/artifacts/` and `projects/*/instances/*/stage-logs/` if not already covered (ask, don't auto-edit).

### Step 6: Sync to ~/.trinity/pipeline-state/

```bash
mkdir -p "$HOME/.trinity/pipeline-state/$PIPELINE"
cp "projects/$PIPELINE/instances/$INSTANCE/state.json" \
   "$HOME/.trinity/pipeline-state/$PIPELINE/$INSTANCE.json"
```

### Step 7: Trigger an initial heartbeat (optional)

Ask: "Run /pipeline-tick now to evaluate this instance immediately?"

If yes and status is `active`, invoke `pipeline-tick`. The first tick will detect the new instance (status `idle`), check preconditions for the first stage, and either `advance` or `wait`.

### Step 8: Summary

```
## Instance `<INSTANCE>` added to pipeline `<PIPELINE>`

Files:
- projects/<PIPELINE>/instances/<INSTANCE>/config.yaml
- projects/<PIPELINE>/instances/<INSTANCE>/state.json
- projects/<PIPELINE>/instances/<INSTANCE>/{stage-logs,artifacts,escalations}/
- ~/.trinity/pipeline-state/<PIPELINE>/<INSTANCE>.json

Status: <active | paused>

Next:
- Edit config.yaml if the scaffold needs more fields:  $EDITOR projects/<PIPELINE>/instances/<INSTANCE>/config.yaml
- See state:  /pipeline-status <PIPELINE>
- Trigger heartbeat:  /pipeline-tick
- Pause/resume:  /pipeline-pause <PIPELINE> <INSTANCE>
```

---

## Error handling

| Situation | Action |
|---|---|
| Pipeline doesn't exist | Suggest `/add-pipeline` |
| Instance slug already exists | Refuse — pick new slug, or `/pipeline-resume` if reactivating |
| `--from` source missing | Error and stop |
| state.json template missing | Stop — installer is broken; reinstall `agent-dev:add-pipeline` |
| Write fails (permissions) | Show error, no partial state |
