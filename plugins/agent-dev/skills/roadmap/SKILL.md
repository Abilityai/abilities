---
name: roadmap
description: Strategic view of the agent backlog — open issues grouped by skill, showing which areas have the most work
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Roadmap

Shows the agent backlog grouped by affected skill rather than by priority. Use this to understand which parts of the agent need the most work, and to choose a sprint focus area. For the day-to-day priority-ordered view, use `/backlog`.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | No | Open issues |
| GitHub Labels | skill:*, priority:*, status:* | Yes | No | Group and filter |

## Process

### Step 1: Verify GitHub CLI

```bash
gh auth status 2>&1 | head -3
```

### Step 2: Fetch Open Issues

```bash
gh issue list --state open --json number,title,labels,updatedAt --limit 100
```

### Step 3: Group by Skill

Parse the `skill:*` label from each issue. Group issues into buckets:

- One bucket per `skill:<name>` label present
- A separate bucket for **project-level** issues (no skill label)

For each bucket, sort issues by priority (p0 → p1 → p2 → unset).

### Step 4: Format Output

```
## Agent Roadmap

### skill:adjust-playbook (3 open)
| # | Title | Priority | Status |
|---|-------|----------|--------|
| 14 | Fix archive flag behavior | p0 | todo |
| 9  | Support batch adjustments | p1 | todo |
| 11 | Better breaking-change detection | p2 | todo |

### skill:work-loop (2 open)
| # | Title | Priority | Status |
|---|-------|----------|--------|
| 6  | Handle blocked issues more gracefully | p1 | todo |
| 3  | Add skill-routing by label | p1 | in-progress |

### skill:groom (1 open)
| # | Title | Priority | Status |
|---|-------|----------|--------|
| 18 | Support bulk priority assignment | p2 | todo |

### Project-level (2 open)
| # | Title | Priority | Status |
|---|-------|----------|--------|
| 1  | Add onboarding checklist to README | p2 | todo |
| 5  | Update plugin.json description | p2 | todo |

---
Total open: 8 issues across 3 skills + project-level

Tip: Run `/groom` to tag untagged issues, or `/claim` to start the highest priority item.
```

### Step 5: Highlight Focus Recommendation

If there are p0 issues, note the urgency: "P0 items need immediate attention."

If a skill has many open issues, note it as a likely sprint focus.

## Outputs

- Skill-grouped issue view
- Priority ordering within each group
- Count of untagged (project-level) issues
- Focus area recommendation

## Error Handling

| Error | Action |
|-------|--------|
| gh not authenticated | Tell user to run `! gh auth login` |
| No open issues | Report "No open issues — backlog is clear" |
| No skill labels used | Suggest running `/groom` first |
