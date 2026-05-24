---
name: add-pipeline
description: Scaffold a Trinity-compatible long-running pipeline inside any agent — creates projects/&lt;slug&gt;/{project.md, pipeline.yaml, instances/}, copies pipeline-tick/status/recover/pause/resume skills into .claude/skills/, sets up the ~/.trinity/ read surface, extends the pre-check gate, installs the heartbeat schedule, and adds a dashboard panel.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-05-23
  author: Ability.ai
---

# Add Pipeline

Add a long-running, multi-stage **pipeline** to any Trinity-compatible agent. Implements the canonical pipeline spec: the agent owns the DAG and stage logic; Trinity owns the read surface (`~/.trinity/pipelines/*.yaml` + `~/.trinity/pipeline-state/**/*.json`); a single heartbeat skill (`pipeline-tick`) owns advancement, retry, and escalation.

**Who this is for:** any agent whose work decomposes into a multi-stage cycle that runs continuously (or on cron) across one or more independent instances/tenants/zones. Columns, ingestion pipelines, per-customer onboarding flows, scheduled research crawls — anything where "what stage is each tenant in" is a question worth asking.

**What gets installed:**

| Artifact | Location | Purpose |
|---|---|---|
| `projects/<slug>/project.md` | agent repo | human-readable project description |
| `projects/<slug>/pipeline.yaml` | agent repo | canonical DAG definition (you edit this) |
| `projects/<slug>/instances/` | agent repo | one subdir per tenant/zone (populate via `/add-pipeline-instance`) |
| `.claude/skills/pipeline-tick/` | agent repo | the heartbeat — autonomous, scheduled |
| `.claude/skills/pipeline-status/` | agent repo | operator view |
| `.claude/skills/pipeline-recover/` | agent repo | operator override |
| `.claude/skills/pipeline-pause/` | agent repo | operator pause |
| `.claude/skills/pipeline-resume/` | agent repo | operator resume |
| `~/.trinity/pipelines/<slug>.yaml` | user home | write-through copy — Trinity's read surface |
| `~/.trinity/pipeline-state/<slug>/` | user home | per-instance state, read by dashboards and other agents |
| `~/.trinity/pre-check` | user home | advisory marker — emits a reason when pipeline-tick has work, always fires the schedule otherwise (see Step 6 for why) |
| `dashboard.yaml` panel | agent repo (if present) | Trinity UI shows a row per instance |
| heartbeat schedule | Trinity MCP (if available) | `pipeline-<slug>-heartbeat` cron `*/15 * * * *` |

---

## Process

### Step 1: Preflight

Run from inside the target agent directory (or ask for the path). Verify:

```bash
# Must be an agent root (CLAUDE.md present)
[ -f CLAUDE.md ] || ask_user_for_agent_path

# Must have a .claude/skills/ directory (create if missing)
mkdir -p .claude/skills

# Must have jq + yq available (used by templates and validators)
command -v jq >/dev/null 2>&1 || warn "jq not installed — runtime skills will fail. Install: brew install jq"
command -v yq >/dev/null 2>&1 || warn "yq not installed — runtime skills will fail. Install: brew install yq"
```

If `CLAUDE.md` is missing, ask the user to point to the correct directory or run `/create-agent` first.

### Step 2: Gather pipeline metadata

Use `AskUserQuestion` (one question at a time, or batch if you prefer):

**Q1 — Pipeline slug** (free text)
- "Short identifier for this pipeline, lowercase-kebab-case (e.g. `columns`, `ingest`, `onboarding`). Used as the directory name and the `pipeline_id` in yaml."
- Validate: matches `^[a-z][a-z0-9-]{1,40}$`. Refuse if `projects/<slug>/` already exists (suggest `/add-pipeline-stage` to extend, or pick a different slug).

**Q2 — Pipeline display name** (free text)
- "Human-readable name (e.g. 'Columns Production Pipeline')."

**Q3 — One-line description** (free text)
- "What does this pipeline do? One or two sentences."

**Q4 — Heartbeat cadence**
- `*/15 * * * *` (every 15 minutes — recommended default)
- `0 * * * *` (hourly — for slow-moving pipelines)
- `*/5 * * * *` (every 5 minutes — for time-sensitive flows)
- Custom (free text cron expression)

**Q5 — Install runtime skills?**
- `Yes — install all five` (pipeline-tick, pipeline-status, pipeline-recover, pipeline-pause, pipeline-resume) — recommended
- `Only the heartbeat` (just pipeline-tick; skip operator skills) — for headless agents
- `Skip — I'll wire my own` — only scaffold the project files

If any of the five runtime skill directories already exist under `.claude/skills/`, ask: overwrite / skip existing / cancel.

### Step 3: Scaffold project directory

```bash
SLUG="<pipeline-slug from Q1>"
mkdir -p "projects/$SLUG/instances"
mkdir -p "projects/$SLUG/skills"  # for stage-skill symlinks if the user wants them grouped
```

Write `projects/$SLUG/project.md`:

```markdown
---
name: <Pipeline Display Name>
status: active
created: <YYYY-MM-DD>
owner: <agent-name from CLAUDE.md or env user>
pipeline_id: <SLUG>
---

# <Pipeline Display Name>

<one-line description from Q3>

## Stages

Stages live in `pipeline.yaml`. Edit there or use `/add-pipeline-stage <slug>` to extend.

## Instances

Instances live in `instances/<instance-slug>/`. Add new ones via `/add-pipeline-instance <slug> <instance-slug>`.

## Operations

- `/pipeline-status <slug>` — current state of every instance
- `/pipeline-recover <slug> <instance>` — unstick a blocked instance
- `/pipeline-pause` / `/pipeline-resume` — maintenance toggles
```

Write `projects/$SLUG/pipeline.yaml` from `templates/pipeline.yaml.template`, substituting:
- `{{PIPELINE_ID}}` → slug
- `{{PIPELINE_NAME}}` → display name
- `{{PIPELINE_DESCRIPTION}}` → description

Substitute the cron expression from Q4 in the `heartbeat.cron` field.

### Step 4: Copy runtime skills into the agent

For each runtime skill the user selected in Q5, copy the corresponding template:

```bash
SKILL_DIR="<this-skill-dir>"  # the add-pipeline skill's own directory

for skill in pipeline-tick pipeline-status pipeline-recover pipeline-pause pipeline-resume; do
  if [ "$skill" not in selected_skills ]; then continue; fi
  mkdir -p ".claude/skills/$skill"
  cp "$SKILL_DIR/templates/$skill.md" ".claude/skills/$skill/SKILL.md"
done
```

These templates are ready to use as-is. No placeholder substitution.

### Step 5: Set up the ~/.trinity/ read surface

```bash
mkdir -p "$HOME/.trinity/pipelines"
mkdir -p "$HOME/.trinity/pipeline-state/$SLUG"

# Write-through copy (not symlink — symlinks don't always traverse Docker volumes).
# pipeline-tick will refresh this on every state write.
cp "projects/$SLUG/pipeline.yaml" "$HOME/.trinity/pipelines/$SLUG.yaml"
```

Record `last_synced` marker so the heartbeat can detect drift:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ > "$HOME/.trinity/pipelines/$SLUG.last_synced"
```

### Step 6: Extend ~/.trinity/pre-check

The pre-check script emits an advisory reason when pipeline-tick has work pending. **It always fires the schedule** — skip logic belongs inside pipeline-tick itself, not here. Multiple pipelines coexist by sharing one script with a single managed block (it scans every `~/.trinity/pipeline-state/*/*.json`).

> ⚠️ **Why this constraint matters.** Trinity's pre-check API is **agent-global** — the same `~/.trinity/pre-check` is consulted before every scheduled skill on the agent, not just pipeline-tick. If the block ever returns empty stdout, Trinity silences **every** schedule on the agent (digests, heartbeats, batch jobs, the lot). Earlier versions of this template made that mistake. The block default MUST be `echo "fire"`.

```bash
PRE_CHECK="$HOME/.trinity/pre-check"
BLOCK_TEMPLATE="$SKILL_DIR/templates/pre-check-block.sh"

# Create pre-check if it doesn't exist
if [ ! -f "$PRE_CHECK" ]; then
  echo "#!/usr/bin/env bash" > "$PRE_CHECK"
  echo "# ~/.trinity/pre-check — heartbeat gate" >> "$PRE_CHECK"
  echo "set -e" >> "$PRE_CHECK"
  chmod +x "$PRE_CHECK"
fi

# Migrate or install the block
if grep -q "BEGIN add-pipeline block v2" "$PRE_CHECK"; then
  echo "add-pipeline block v2 already present in pre-check — skipping."
elif grep -q "BEGIN add-pipeline block" "$PRE_CHECK"; then
  # v1 block present — rewrite it in place (v1 returned empty stdout when idle,
  # silencing all other agent schedules; v2 defaults to "fire").
  echo "⚠️  Found v1 add-pipeline block in pre-check — replacing with v2 (default-fire)."
  TMP=$(mktemp)
  awk '
    /BEGIN add-pipeline block/ {skip=1; next}
    /END add-pipeline block/   {skip=0; next}
    !skip
  ' "$PRE_CHECK" > "$TMP"
  echo "" >> "$TMP"
  cat "$BLOCK_TEMPLATE" >> "$TMP"
  mv "$TMP" "$PRE_CHECK"
  chmod +x "$PRE_CHECK"
else
  echo "" >> "$PRE_CHECK"
  cat "$BLOCK_TEMPLATE" >> "$PRE_CHECK"
fi
```

Installing a second pipeline doesn't require editing pre-check again — the block scans all pipelines.

### Step 7: Install heartbeat schedule via Trinity MCP

If Trinity MCP is configured (check `.mcp.json` or `~/.trinity/config`), install the schedule:

```
Use the Trinity MCP tool create_agent_schedule with:
  agent_name: <inferred from agent dir or asked>
  schedule_name: "pipeline-<SLUG>-heartbeat"
  cron: "<from Q4>"
  skill: "pipeline-tick"
  pre_check: "~/.trinity/pre-check"
  description: "Heartbeat for the <display name> pipeline."
```

If Trinity MCP is not available, print:

```
⚠️  Trinity MCP not detected. Heartbeat schedule NOT installed.

To install later:
  1. Onboard this agent to Trinity:  /trinity:onboard
  2. Re-run this skill OR install the schedule manually:
       create_agent_schedule(
         agent_name="<agent>",
         schedule_name="pipeline-<SLUG>-heartbeat",
         cron="<cron>",
         skill="pipeline-tick"
       )
  3. Until then, trigger the heartbeat manually with `/pipeline-tick`.
```

The pipeline still works locally without Trinity — it just won't auto-advance.

### Step 8: Extend dashboard.yaml (if present)

```bash
if [ -f dashboard.yaml ]; then
  # Check if a pipelines panel already exists
  if ! grep -q "^pipelines:" dashboard.yaml; then
    cat >> dashboard.yaml <<'EOF'

# Added by /add-pipeline — managed block, do not edit by hand
pipelines:
  panel_type: pipeline_table
  source: ~/.trinity/pipeline-state/
  columns: [pipeline_id, instance_id, status, current_stage, health, last_advanced_at, open_escalations]
  group_by: pipeline_id
  sort_by: [pipeline_id, instance_id]
EOF
  fi
else
  echo "ℹ️  No dashboard.yaml found — skipping panel registration. Trinity dashboard will not show pipeline state until a dashboard.yaml is created."
fi
```

### Step 9: Validate (advisory)

Invoke the `validate-pipeline` skill on the new pipeline as a sanity check:

```
Skill: validate-pipeline
Args: <SLUG>
```

This is a linter — it prints a report and refreshes `~/.trinity/pipelines/<SLUG>.yaml` on a clean pass. Errors don't block this skill from finishing the scaffold (the user can edit `pipeline.yaml` and re-run `/validate-pipeline` later), but warnings should be surfaced.

### Step 10: Summary

Print:

```
## Pipeline `<SLUG>` installed

### Files created
- projects/<SLUG>/project.md
- projects/<SLUG>/pipeline.yaml
- projects/<SLUG>/instances/  (empty — add via /add-pipeline-instance <SLUG> <instance>)
- .claude/skills/pipeline-tick/SKILL.md
- .claude/skills/pipeline-status/SKILL.md
- .claude/skills/pipeline-recover/SKILL.md
- .claude/skills/pipeline-pause/SKILL.md
- .claude/skills/pipeline-resume/SKILL.md
- ~/.trinity/pipelines/<SLUG>.yaml
- ~/.trinity/pipeline-state/<SLUG>/
- ~/.trinity/pre-check  (extended)
- dashboard.yaml panel  (if present)

### Heartbeat
Schedule: pipeline-<SLUG>-heartbeat at `<cron>`
Status: <installed via Trinity MCP | NOT installed — see Step 7>

### Next steps
1. Open projects/<SLUG>/pipeline.yaml and replace the example stage with your real stages,
   OR run /add-pipeline-stage <SLUG> <stage-id> --skill <skill-name>
2. Add at least one instance:  /add-pipeline-instance <SLUG> <instance-slug>
3. Validate:  /validate-pipeline <SLUG>
4. Test the heartbeat manually:  /pipeline-tick
5. Check state:  /pipeline-status <SLUG>
```

---

## Error handling

| Situation | Action |
|---|---|
| Not in an agent dir (no CLAUDE.md) | Ask for path or refuse |
| Pipeline slug already exists | Refuse — suggest `/add-pipeline-stage` to extend, or pick new slug |
| Runtime skill already exists | Ask: overwrite, skip, or cancel |
| jq/yq missing | Warn, continue; runtime skills will need them installed before use |
| Trinity MCP unavailable | Skip schedule install, print manual instructions |
| dashboard.yaml has conflicting `pipelines:` key | Warn, leave existing alone, suggest manual review |
| pre-check has un-marked content | Append our block but warn the user to review |
| pre-check has v1 add-pipeline block (no `v2` marker) | Auto-rewrite to v2 (v1 emitted empty stdout when idle, silencing every other schedule on the agent — see Step 6) |

## Idempotency

Re-running this skill on the same agent with the same slug should refuse, not silently rewrite. Use `/add-pipeline-stage` or edit `pipeline.yaml` directly to extend an existing pipeline.

Re-running with a **different** slug should add a second pipeline cleanly — both share the same `~/.trinity/pre-check` block (no second copy needed), both get their own `~/.trinity/pipelines/<slug>.yaml`, both get their own heartbeat schedule.
