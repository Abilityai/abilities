---
name: create-dashboard
description: Generate an agent-specific `/update-dashboard` skill that keeps `dashboard.yaml` current for Trinity. Analyzes the agent's purpose and data sources, proposes metrics, gets user approval, then scaffolds a schedulable skill.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
metadata:
  version: "1.2"
  created: 2026-05-27
  author: Ability.ai
  changelog:
    - "1.2: Chart widget templates removed — `type: chart` never existed in Trinity (the agent-server validator strips it, the frontend has no renderer); trend lines come from the platform's Dynamic Dashboards enrichment instead: metric/progress widgets get auto-captured history + sparklines, keyed by a stable `id:` field (now taught). Added markdown widget template and a no-YAML-anchors caution (hardened loader rejects aliases, trinity#1965)"
    - "1.1.3: Report guard also swallows the `requires an agent-scoped API key` refusal (Trinity mcp-server reports.ts, in v0.9.0) — a user/admin-key session sees mcp__trinity__report but cannot publish; skip silently, never retry"
    - "1.1.2: The generated /update-dashboard is built to run on cron, so it ships disable-model-invocation: false — true made it unreachable to the scheduler. Scheduling instructions replaced: /trinity-schedules is retired, so declare the cron in template.yaml schedules: and reconcile, with the ent#89 literal-true rule and the autonomy gate both called out"
    - "1.1.1: Note that reports are a rolling history — pruned past agent_reports_retention_days (default 90 days), not a permanent archive"
    - "1.1: Generated /update-dashboard now also emits a guarded {agent}.kpi_snapshot report (display_hint kpi) after writing the dashboard — the same headline numbers accumulate as an append-only history on the Reports tab alongside the live snapshot; skipped silently off-Trinity"
    - "1.0: Initial version — generate an agent-specific /update-dashboard skill that gathers metrics from the agent's data sources and writes a schedulable dashboard.yaml for Trinity"
---

# /trinity:create-dashboard

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `create-dashboard vX.Y — recent: <summary>`. Then proceed.

Generate an agent-specific `/update-dashboard` skill that keeps `dashboard.yaml` current for Trinity. Analyzes the agent's purpose and data sources, proposes metrics, gets user approval, then creates a schedulable skill.

## Trigger

User wants to:
- Add a dashboard to an existing agent
- Create or regenerate dashboard metrics
- "create dashboard", "add dashboard", "setup dashboard"

## What This Creates

A new skill at `.claude/skills/update-dashboard/SKILL.md` that:
- Gathers current metrics from agent data sources
- Writes `dashboard.yaml` to `/home/developer/dashboard.yaml`
- Is designed to run on a schedule (e.g., hourly via Trinity cron)
- Uses widget types appropriate for the agent's purpose

---

## PHASE 1: Gather Context

### 1.1 Read Agent Identity

Read `CLAUDE.md` (or `README.md` if no CLAUDE.md exists).

Extract:
- Agent name and purpose
- Primary responsibilities
- Key workflows and capabilities

### 1.2 Discover Data Sources

Glob for potential data files:
- `*.json`, `*.yaml`, `*.yml` in workspace root
- `memory/`, `data/`, `logs/`, `state/` directories
- Any `*_log.md`, `*_state.*`, `*_history.*` files

### 1.3 Inventory Existing Skills

```bash
ls -la .claude/skills/*/SKILL.md 2>/dev/null
```

Note skill names - they indicate what the agent does.

### 1.4 Check for Existing Dashboard

Read `dashboard.yaml` if it exists - use current structure as baseline.

---

## PHASE 2: Propose Dashboard Metrics

Based on analysis, propose a dashboard structure. Consider these categories:

### Status Metrics (always include)
- **Agent Status**: Running/Idle/Error state
- **Last Activity**: When agent last performed work
- **Health Check**: Any error counts or issues

### Activity Metrics (based on agent purpose)
- **Task Counts**: Items processed, completed, pending
- **Progress**: Completion percentage for ongoing work
- **Throughput**: Rate of work (items/hour, etc.)

### Domain-Specific Metrics (from data sources)
- Extract from JSON/YAML state files
- Parse from log files
- Query from databases if applicable

### Quick Links (if relevant)
- External dashboards, reports, or resources
- Related documentation

---

## PHASE 3: User Approval Gate

**CRITICAL: Present proposed metrics and get explicit approval before generating.**

Present the proposal:

```
## Proposed Dashboard Metrics

Based on my analysis of this agent, I recommend:

### Section 1: Status Overview
- [metric] Agent Status (status widget, green/yellow/red)
- [metric] Last Updated (text widget)
- [metric] Uptime/Health (metric widget)

### Section 2: Activity
- [metric] Tasks Completed (metric widget with trend)
- [progress] Current Progress (progress widget)
- [list] Recent Activity (list widget, last 5 items)

### Section 3: {Domain-Specific}
- {proposed metrics based on data sources}

---

**Data Sources I'll Use:**
- {file1}: for {metric}
- {file2}: for {metric}

Would you like to:
1. Approve this structure
2. Add more metrics
3. Remove some metrics
4. Modify specific widgets
```

**Wait for user confirmation before proceeding.**

If user wants changes, iterate and re-present.

---

## PHASE 4: Generate the Skill

Create `.claude/skills/update-dashboard/SKILL.md`:

```markdown
---
name: update-dashboard
description: Update dashboard.yaml with current agent metrics and status
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# Update Dashboard

Refresh the Trinity dashboard with current agent metrics.

## Output Location

Write to: `/home/developer/dashboard.yaml`

---

## STEP 1: Gather Current Metrics

{For each approved data source, include specific extraction instructions}

### Read State Files
```
Read {state_file_path}
Extract: {specific_fields}
```

### Parse Logs (if applicable)
```
Bash: tail -n 100 {log_file} | grep -c "pattern"
```

### Compute Derived Metrics
```
{calculations or aggregations}
```

---

## STEP 2: Build Dashboard YAML

```yaml
title: "{Agent Name} Dashboard"
refresh: 30

sections:
  - title: "Status"
    layout: grid
    columns: 3
    widgets:
      {approved widgets with value placeholders}

  - title: "{Section 2}"
    layout: {layout}
    widgets:
      {approved widgets}
```

---

## STEP 3: Write Dashboard

Write to `/home/developer/dashboard.yaml`

---

## STEP 4: Publish a KPI snapshot report (Trinity)

If the `mcp__trinity__report` tool is available (i.e. running on Trinity), also publish the same headline numbers as a report so they accumulate as an **append-only history** alongside the live dashboard snapshot (the dashboard is overwritten each refresh; reports are not — though they are pruned past `agent_reports_retention_days`, default 90 days):

- `report_type`: `{agent-name}.kpi_snapshot`
- `display_hint`: `kpi`
- `payload`: `{ "tiles": [ {"label": "...", "value": "...", "unit": "..."} ] }`, built from the same values you just wrote to the dashboard.

Skip this step **silently** if the tool isn't available — or if it refuses with `The report tool requires an agent-scoped API key` (a session connected with a user/admin key sees the tool but cannot report; never retry) — the dashboard refresh above still succeeds. Reporting is an upgrade, not a requirement.

---

## STEP 5: Confirm Update

Report:
- Dashboard updated at {timestamp}
- Metrics refreshed with current values
- Next scheduled update: {if scheduled}
```

---

## PHASE 5: Widget Generation Reference

When generating the skill, use these widget templates:

### metric
```yaml
- type: metric
  id: {stable_snake_case_id}   # keeps platform-tracked history attached to this widget
  label: "{label}"
  value: {extracted_value}
  trend: up|down
  unit: "{unit}"
```

### status
```yaml
- type: status
  label: "{label}"
  value: "{status_text}"
  color: green|yellow|red
```

### progress
```yaml
- type: progress
  id: {stable_snake_case_id}   # keeps platform-tracked history attached to this widget
  label: "{label}"
  value: {percentage}
  color: green|yellow|red
```

### list
```yaml
- type: list
  title: "{title}"
  items: {extracted_items}
  style: bullet
  max_items: 10
```

### table
```yaml
- type: table
  title: "{title}"
  columns:
    - { key: col1, label: "Column 1" }
    - { key: col2, label: "Column 2" }
  rows: {extracted_rows}
  max_rows: 10
```

### markdown
```yaml
- type: markdown
  content: |
    **{heading}**
    {markdown_body}
```

### link
```yaml
- type: link
  label: "{label}"
  url: "{url}"
  external: true
```

**Colors:** green, red, yellow, gray, blue, orange, purple

**Valid widget types** (anything else is stripped by the agent-server validator): `metric`, `status`, `progress`, `text`, `markdown`, `table`, `list`, `link`, `image`, `divider`, `spacer`. There is **no `chart` type** — do not generate one.

**Trends & sparklines come from the platform, not the YAML:** Trinity's Dynamic Dashboards layer captures each metric/progress widget's value on every dashboard fetch and renders a sparkline + computed trend automatically once history accumulates. History is keyed by the widget's `id:` field (fallback is the widget's position, so reordering or inserting widgets orphans history) — always give metric and progress widgets a stable `id`. A hand-set `trend:`/`trend_value:` overrides the computed one; omit them to let the platform calculate.

**Layout notes:**
- Use `layout: list` (not `layout: single`)
- Grid layouts support `columns: 1` to `columns: 4` max
- Use `content` for text widgets (not `text` or `value`)
- Use `items` for list widgets (not `values` or `list`)
- Never emit YAML anchors/aliases (`&`/`*`) — Trinity's hardened YAML loader rejects them (trinity#1965) and the whole dashboard fails to parse

---

## PHASE 6: Completion Summary

```
## Dashboard Skill Created

**Skill:** /update-dashboard
**Location:** .claude/skills/update-dashboard/SKILL.md
**Output:** /home/developer/dashboard.yaml

### Metrics Included
{List of approved metrics with sources}

### Usage

Run manually:
  /update-dashboard

Schedule on Trinity — declare it in template.yaml (the design source of truth):

  schedules:
    - name: Hourly dashboard refresh
      cron: "0 * * * *"
      message: "/update-dashboard"
      enabled: true          # a literal YAML true — anything else lands disabled (ent#89)
      timezone: UTC

Then run /trinity:onboard (or /trinity:sync) to reconcile it onto the instance,
and make sure the agent's autonomy toggle is ON — while autonomy is off the
scheduler skips every cron trigger and writes no execution row, so an enabled
schedule is silently inert.
```

---

## Notes

- This skill creates/overwrites `.claude/skills/update-dashboard/SKILL.md`
- If an update-dashboard skill already exists, back it up first
- The generated skill is designed for Trinity's cron scheduler
- Dashboard output path `/home/developer/dashboard.yaml` is Trinity's expected location
