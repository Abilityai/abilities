---
name: create-dashboard-playbook
description: Generate an agent-specific skill that updates dashboard.yaml for Trinity. Analyzes agent purpose, proposes metrics, gets user approval, then creates a schedulable update-dashboard skill.
disable-model-invocation: false
user-invocable: true
argument-hint: "[dashboard-name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Create Dashboard Playbook

Generate an agent-specific skill that keeps `dashboard.yaml` updated for Trinity-compatible agents. The generated skill can be scheduled via `/trinity-schedules` to maintain a live dashboard.

## What This Creates

A new skill in `.claude/skills/update-dashboard/SKILL.md` that:

- Gathers current metrics and status from agent data sources
- Writes an updated `dashboard.yaml` to `/home/developer/dashboard.yaml`
- Is designed to run on a schedule (e.g., hourly via Trinity cron)
- Uses widget types appropriate for the agent's purpose

---

## STEP 1: Gather Context

Analyze the agent to understand its purpose and available data:

### 1.1 Read Agent Identity

```
Read CLAUDE.md (or README.md if no CLAUDE.md exists)
```

Extract:
- Agent name and purpose
- Primary responsibilities
- Key workflows and capabilities

### 1.2 Discover Data Sources

```
Glob for potential data files:
- *.json, *.yaml, *.yml in workspace root
- memory/, data/, logs/, state/ directories
- Any *_log.md, *_state.*, *_history.* files
```

### 1.3 Inventory Existing Skills

```
Glob: .claude/skills/*/SKILL.md
```

Note skill names - they indicate what the agent does.

### 1.4 Check for Existing Dashboard

```
Read dashboard.yaml (if exists)
```

If exists, use current structure as baseline.

---

## STEP 2: Propose Dashboard Metrics

Based on analysis, propose a dashboard structure. Consider these metric categories:

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

## STEP 3: User Approval Gate

**CRITICAL: Present proposed metrics and get explicit approval before generating the skill.**

Use AskUserQuestion to present the proposed dashboard:

```
## Proposed Dashboard Metrics

Based on my analysis of this agent, I recommend the following dashboard structure:

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
- {computed}: for {metric}

Would you like to:
1. Approve this structure
2. Add more metrics
3. Remove some metrics
4. Modify specific widgets
```

**Wait for user confirmation before proceeding.**

If user wants changes:
- Iterate on the proposal
- Present updated version
- Get approval again

---

## STEP 4: Generate the Update-Dashboard Skill

Once approved, create `.claude/skills/update-dashboard/SKILL.md`:

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

{For each approved data source, include specific instructions}

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

Construct the dashboard with gathered values:

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

**Widget Field Reference** (use exact field names):
- `text` widget: use `content` (not `text` or `value`)
- `list` widget: use `items` (not `values` or `list`)
- `link` widget: use `url` (not `href` or `link`)

---

## STEP 3: Write Dashboard

```
Write dashboard.yaml to /home/developer/dashboard.yaml
```

---

## STEP 4: Confirm Update

Report what was updated:

```
Dashboard updated at {timestamp}

Metrics refreshed:
- {metric1}: {value}
- {metric2}: {value}
- ...

Next scheduled update: {if scheduled}
```
```

---

## STEP 5: Customize Generated Skill

Tailor the generated skill based on approved metrics:

### For Each Metric Type

**metric widget** - Include data extraction logic:
```yaml
- type: metric
  label: "{label}"
  value: {extracted_value}
  trend: {up|down if trackable}
  unit: "{unit}"
```

**status widget** - Include status determination logic:
```yaml
- type: status
  label: "{label}"
  value: "{status_text}"
  color: {green|yellow|red based on condition}
```

**progress widget** - Include calculation:
```yaml
- type: progress
  label: "{label}"
  value: {calculated_percentage}
  color: {color based on threshold}
```

**list widget** - Include list extraction:
```yaml
- type: list
  title: "{title}"
  items:
    {extracted_list_items}
  style: bullet
  max_items: 10
```

**table widget** - Include row extraction:
```yaml
- type: table
  title: "{title}"
  columns:
    - { key: col1, label: "Column 1" }
    - { key: col2, label: "Column 2" }
  rows:
    {extracted_rows}
  max_rows: 10
```

---

## STEP 6: Write and Confirm

Write the generated skill to `.claude/skills/update-dashboard/SKILL.md`

Present completion summary:

```
## Dashboard Playbook Created

**Skill:** /update-dashboard
**Location:** .claude/skills/update-dashboard/SKILL.md
**Dashboard output:** /home/developer/dashboard.yaml

### Metrics Included

{List of approved metrics with sources}

### Data Sources

{List of files/commands used}

### Usage

Run manually:
```
/update-dashboard
```

Schedule on Trinity (recommended):
```
/trinity-schedules add update-dashboard --cron "0 * * * *"  # Hourly
/trinity-schedules add update-dashboard --cron "*/15 * * * *"  # Every 15 min
```

### Customization

Edit `.claude/skills/update-dashboard/SKILL.md` to:
- Add new metrics
- Change data sources
- Modify refresh logic
- Adjust widget styling
```

---

## Widget Type Reference

For reference when proposing and generating widgets:

| Type | Required Fields | Optional Fields |
|------|-----------------|-----------------|
| metric | label, value | trend, trend_value, unit, description |
| status | label, value, color | - |
| progress | label, value | color |
| text | content | size, color, align |
| markdown | content | - |
| table | columns, rows | title, max_rows |
| list | items | title, style, max_items |
| link | label, url | external, style, color |
| image | src, alt | caption |
| divider | - | - |
| spacer | - | size |

**Color options:** green, red, yellow, gray, blue, orange, purple

---

## Examples

### Example 1: Research Agent

```
/create-dashboard-playbook

Proposed metrics:
- Research cycles completed (metric)
- Current status: Idle/Researching (status)
- Queue depth (metric)
- Recent findings (list)
- Sources consulted (metric)

Data sources:
- research_state.json
- findings_log.md
```

### Example 2: Data Pipeline Agent

```
/create-dashboard-playbook

Proposed metrics:
- Records processed today (metric with trend)
- Pipeline status (status)
- Processing queue (progress)
- Error count (metric)
- Recent jobs (table)

Data sources:
- pipeline_state.yaml
- job_history.json
- error_log.md
```

### Example 3: Content Agent

```
/create-dashboard-playbook

Proposed metrics:
- Content items created (metric)
- Publishing status (status)
- Draft queue (progress)
- Recent publications (list)
- External links (link widgets)

Data sources:
- content_index.json
- publish_log.md
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity-schedules` | Schedule the update-dashboard skill |
| `/trinity-onboard` | Initial Trinity setup |
| `/create-heartbeat` | Client-side polling alternative |
