# /trinity:create-dashboard

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
disable-model-invocation: true
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

## STEP 4: Confirm Update

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

### chart (line/bar/area)
```yaml
- type: chart
  chart_type: line|bar|area
  title: "{title}"
  height: 200
  x_label: "X Axis"
  y_label: "Y Axis"
  legend: true
  series:
    - label: "{series_name}"
      color: blue
      data: [{x: "label1", y: 10}, {x: "label2", y: 20}]
```

### chart (pie/donut)
```yaml
- type: chart
  chart_type: pie|donut
  title: "{title}"
  height: 200
  segments:
    - { label: "Category A", value: 45, color: blue }
    - { label: "Category B", value: 30, color: green }
```

### link
```yaml
- type: link
  label: "{label}"
  url: "{url}"
  external: true
```

**Colors:** green, red, yellow, gray, blue, orange, purple

**Layout notes:**
- Use `layout: list` (not `layout: single`)
- Grid layouts support `columns: 1` to `columns: 4` max
- Use `content` for text widgets (not `text` or `value`)
- Use `items` for list widgets (not `values` or `list`)

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

Schedule on Trinity:
  /trinity-schedules add update-dashboard --cron "0 * * * *"   # Hourly
  /trinity-schedules add update-dashboard --cron "*/15 * * * *" # Every 15 min
```

---

## Notes

- This skill creates/overwrites `.claude/skills/update-dashboard/SKILL.md`
- If an update-dashboard skill already exists, back it up first
- The generated skill is designed for Trinity's cron scheduler
- Dashboard output path `/home/developer/dashboard.yaml` is Trinity's expected location
