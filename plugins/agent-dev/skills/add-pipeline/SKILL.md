---
name: add-pipeline
description: Scaffold a Trinity-compatible long-running pipeline inside any agent — creates projects/&lt;slug&gt;/{project.md, pipeline.yaml, instances/}, copies pipeline-tick/status/recover/pause/resume skills into .claude/skills/, sets up the ~/.trinity/ read surface, extends the pre-check gate, installs the heartbeat schedule, and adds a dashboard panel.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
metadata:
  version: "1.2"
  created: 2026-05-23
  updated: 2026-07-02
  author: Ability.ai
  changelog:
    - "1.2: Fleet-orchestrator integration — Step 7 also records the heartbeat in template.yaml's schedules: block (source of truth for /trinity:sync; makes the pipeline discoverable to /add-orchestrator's /discover-agents); when-to-use now names /add-orchestrator + /orchestrate as the cross-agent layer for one-agent-per-tenant fan-out"
    - "1.1: Add 'When to use a pipeline' guidance (multi-instance ≠ multi-tenant); add Skill to allowed-tools and invoke /validate-pipeline canonically (Composition Rule)"
---

# Add Pipeline

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-pipeline vX.Y — recent: <summary>`. Then proceed.

Add a long-running, multi-stage **pipeline** to any Trinity-compatible agent. Implements the canonical pipeline spec: the agent owns the DAG and stage logic; Trinity owns the read surface (`~/.trinity/pipelines/*.yaml` + `~/.trinity/pipeline-state/**/*.json`); a single heartbeat skill (`pipeline-tick`) owns advancement, retry, and escalation.

**When to use a pipeline (and when not):** reach for this only when the work is a *population* of items that each crawl through *multiple stages over many runs*, and you need durable per-item state, isolated retries, and an at-a-glance "what stage is each item in" — e.g. per-customer onboarding, document ingestion, batched research crawls, especially when the whole batch can't finish in one scheduled run. If it's a single recurring task, a scheduled playbook is simpler — don't reach for a pipeline. And mind the boundary: instances are **multi-instance, not multi-tenant** — their *state* is isolated but they all run inside the **same agent** (same credentials, context window, and heartbeat), so for genuinely isolated or large-scale tenants, deploy **one agent per tenant** (Trinity fan-out) rather than one pipeline with many instances — that cross-agent layer is `/add-orchestrator`'s domain: its `/orchestrate` skill does the routing, fan-out, and ephemeral roll-out/tear-down across a fleet, and its `/discover-agents` surfaces this agent's pipelines to the fleet map.

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
| `~/.trinity/pre-check` | user home | heartbeat gate — always emits `fire` so every schedule runs; never emits a message override (see Step 6 for why) |
| `dashboard.yaml` panel | agent repo (if present) | Trinity UI shows a row per instance |
| heartbeat schedule | Trinity MCP (if available) | `pipeline-<slug>-heartbeat` cron `*/15 * * * *` |
| `template.yaml` `schedules:` entry | agent repo (if present) | durable copy of the heartbeat — reconciled by `/trinity:sync`, read by fleet orchestrators (`/discover-agents`) |

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

The pre-check script always emits `fire` so the heartbeat schedule runs. It never emits a message override. Skip / work-detection logic belongs inside pipeline-tick itself, not here. Multiple pipelines share one script with a single managed block — no per-pipeline edits needed.

> ⚠️ **Why this constraint matters.** Trinity's pre-check API is **agent-global** — the same `~/.trinity/pre-check` is consulted before every scheduled skill on the agent, not just pipeline-tick. Two failure modes both silently hijack unrelated schedules:
>
> 1. **Empty stdout** silences every schedule on the agent (digests, heartbeats, batch jobs, the lot). v1 of this template made this mistake.
> 2. **Any non-`fire`/`skip` stdout becomes the message override** applied to whichever schedule called the pre-check — overwriting the intended message of unrelated schedules and making them run whatever the override text says (e.g. `pipeline-tick`) instead of their own work. v2 of this template made this mistake.
>
> The block must emit exactly `echo "fire"` — nothing else.

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
if grep -q "BEGIN add-pipeline block v3" "$PRE_CHECK"; then
  echo "add-pipeline block v3 already present in pre-check — skipping."
elif grep -q "BEGIN add-pipeline block" "$PRE_CHECK"; then
  # v1 or v2 block present — rewrite it in place.
  # v1 returned empty stdout when idle, silencing every other agent schedule.
  # v2 emitted "pipeline-tick: <reason>" when work was pending, which Trinity
  # applies as a message override to whichever schedule called the pre-check —
  # hijacking unrelated schedules into running pipeline-tick. v3 always emits
  # "fire" and never overrides messages.
  echo "⚠️  Found older add-pipeline block in pre-check — replacing with v3 (always fire, no override)."
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

**Also record the schedule in `template.yaml` (if present) — do this whether or not the MCP install succeeded.** The `schedules:` block in `template.yaml` is the source of truth that `/trinity:onboard` / `/trinity:sync` reconcile onto the instance, and it's what fleet orchestrators read (`/discover-agents` from `/add-orchestrator` sources `schedules` from `template.yaml`, not from live Trinity) — a live-only schedule is invisible to both. Grep-guard so re-runs never duplicate:

```bash
if [ -f template.yaml ] && ! grep -q "pipeline-$SLUG-heartbeat" template.yaml; then
  # Append under the existing `schedules:` block, creating the block if absent.
  # Entry shape (matches /trinity:onboard's schedule schema):
  #   - id: pipeline-<SLUG>-heartbeat
  #     name: <Display Name> pipeline heartbeat
  #     cron: "<from Q4>"
  #     message: "Run /pipeline-tick"
  #     purpose: Advance the <SLUG> pipeline — retry, escalate, sync the read surface
  #     enabled: true
  append_schedule_entry   # use yq if available; otherwise append the YAML block textually
fi
```

The `pre_check` wiring stays on the live schedule installed above — the `template.yaml` schedule schema doesn't carry it. If `template.yaml` is absent, skip this and note it in the summary.

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

Invoke `/validate-pipeline <SLUG>` on the new pipeline as a sanity check — call the skill by name (needs `Skill` in `allowed-tools`), don't reimplement its checks here:

```
Invoke `/validate-pipeline <SLUG>`
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
- template.yaml schedules: entry  (added | already present | no template.yaml — heartbeat is live-only and invisible to /trinity:sync and fleet discovery)

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
| `template.yaml` absent | Skip the `schedules:` entry; warn that the heartbeat exists only as a live schedule — invisible to `/trinity:sync` and to fleet orchestrators (`/discover-agents`) |
| dashboard.yaml has conflicting `pipelines:` key | Warn, leave existing alone, suggest manual review |
| pre-check has un-marked content | Append our block but warn the user to review |
| pre-check has v1 or v2 add-pipeline block (no `v3` marker) | Auto-rewrite to v3 (v1 silenced other schedules with empty stdout; v2 hijacked other schedules with a `pipeline-tick:` message override — see Step 6) |

## Idempotency

Re-running this skill on the same agent with the same slug should refuse, not silently rewrite. Use `/add-pipeline-stage` or edit `pipeline.yaml` directly to extend an existing pipeline.

Re-running with a **different** slug should add a second pipeline cleanly — both share the same `~/.trinity/pre-check` block (no second copy needed), both get their own `~/.trinity/pipelines/<slug>.yaml`, both get their own heartbeat schedule and their own grep-guarded `template.yaml` `schedules:` entry.
