---
name: create-dashboard
description: Generate an agent-specific `/update-dashboard` skill that keeps `dashboard.yaml` current for Trinity. Analyzes the agent's purpose and data sources, proposes metrics, gets user approval, then scaffolds a schedulable skill.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
metadata:
  version: "1.3.2"
  created: 2026-05-27
  author: Ability.ai
  changelog:
    - "1.3.2: Trinity dev ed5904906 truth sync — a different value at the same ts now corrects a metric point in place (ent#729; never record a correction at a new ts; the summary counts `corrected`); the git-sync note no longer says the container never pulls (ent#703) — the point is that git sync never refreshes the metric registry; bound widgets document `dims:` for dimensioned metrics"
    - "1.3.1: Platform-truth refresh (Trinity dev 1a1deb2b, the ent#476 metrics merge, 2026-09-22) — Phase 4.1 now says what actually happens on a deployed agent: an in-container edit to template.yaml metrics: is invisible to the backend until refresh_metric_definitions (or a restart), because auto-sync pushes and never pulls; malformed entries are dropped and reported as D-009. The generated /update-dashboard drops its kpi_snapshot report step — the metric store is the history, a KPI report was a second store for the same number (operator ruling 2026-09-21). Generated-skill block moved to a four-backtick outer fence (Gate 1 B4)"
    - "1.3: Declared business metrics (trinity-enterprise#482; contract ent#477/#478/#479) — Phase 3 also proposes which of the approved numbers become DECLARED metrics, Phase 4 writes or extends `template.yaml metrics:` (name, type, label, cadence = the schedule, status values) and the generated /update-dashboard gains STEP 4: record the same numbers as points via `record_metrics` (guarded, silent off Trinity; `metric_undeclared` → `refresh_metric_definitions`); widget templates gain the `metric:` binding (a bound widget reads the recorded series — no hand-typed value)"
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

**Declared metrics (recorded as time series, not just displayed):**
- `{snake_case_name}` — {type} — cadence {schedule interval} — from {source}
- `{agent}_state` — status — values {healthy|degraded|error}
(These go into `template.yaml metrics:`; the platform validates every recorded point against them.)

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

## PHASE 4: Declare the Metrics, then Generate the Skill

### 4.1 Write or extend `template.yaml metrics:`

For each approved *declared* metric add an entry (create the block if absent; never remove an existing entry — the platform keeps its history and marks a dropped declaration `retired`):

```yaml
metrics:
  - name: {snake_case_name}          # unique, snake_case
    type: {counter|gauge|percentage|status|duration|bytes}
    label: "{Display label}"
    description: "{what it measures}"
    cadence: {6h}                    # = the /update-dashboard schedule; a point later than 2× this shows as STALE
    direction: {up_good|down_good|neutral}
    aggregation: {last|sum|avg}
    values:                          # status type only
      - {value: healthy, color: green, label: Healthy}
```

Trinity reads this block at create / git pull / container start (trinity-enterprise#477). If the agent is already deployed, **nothing on the backend sees an edit the agent makes to its own `template.yaml`** — the in-container git sync (push and pull) never notifies the backend's metric registry — so call `refresh_metric_definitions` right after writing the block (idempotent; the agent must be running, 409 otherwise), or restart the agent. A malformed entry is dropped from the registry and reported as compatibility finding D-009; its points then come back `metric_undeclared`.

### 4.2 Generate the skill

Create `.claude/skills/update-dashboard/SKILL.md`:

````markdown
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

## STEP 4: Record declared metrics (Trinity)

If the `mcp__trinity__record_metrics` tool is available (running on Trinity), post the same numbers as **points** against the metrics declared in `template.yaml metrics:` — the only way a number enters Trinity as data (time series, freshness, canvas charts read it; `dashboard.yaml` is only the live snapshot):

```
record_metrics(points=[
  {"metric": "{name}", "value": {number}},
  {"metric": "{agent}_state", "value": "healthy"}
], execution_id="{from the Execution Context block, when present}")
```

Only declared metrics (`metric_undeclared` → declare it in `template.yaml`, call `refresh_metric_definitions`, retry once); one point per metric per run (identity is metric + ts + dims — re-sending the same value is deduplicated, and a different value at the same `ts` corrects the stored point in place (counted as `corrected`); keep the `ts` of the period the number describes, never record a correction at a new `ts`); a `status` value must be one of its declared `values`. Skip **silently** when the tool is absent or refuses with an agent-scoped-key error — the dashboard write still succeeds. Trinity is the upgrade, never the gate.

---

## STEP 5: Confirm Update

Report:
- Dashboard updated at {timestamp}
- Metrics refreshed with current values
- Points recorded: {n} recorded, {m} deduplicated, {k} corrected (Trinity only)
- Next scheduled update: {if scheduled}
````

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

**Bound to a declared metric (preferred when one exists):**
```yaml
- type: metric
  id: {stable_snake_case_id}
  metric: {declared_metric_name}   # reads the recorded series: value, point time, stale flag, sparkline
  label: "{label}"
  # dims: {region: emea}   # only for a metric declared with dimensions: — selects ONE series; without it the tile shows the folded aggregate
  # value / unit / trend are optional on a bound widget — the platform fills them
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
