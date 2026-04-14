---
name: install-github-backlog
description: Add GitHub Issues backlog workflow to any agent — creates /backlog, /pick-work, /close-work, and /work-loop skills directly in the agent
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-14
  author: Ability.ai
---

# Install GitHub Backlog

Add GitHub Issues task management to any Claude Code agent. This wizard creates skills directly in your agent's `.claude/skills/` directory — no plugin dependency, fully self-contained.

**What you get:**
- `/backlog` — View current workload by priority and status
- `/pick-work` — Grab the next task, mark it in-progress
- `/close-work` — Complete work with summary comment
- `/work-loop` — Autonomous processing (schedulable on Trinity)
- CLAUDE.md section explaining the workflow
- GitHub labels for status and priority tracking

> The agent's repository becomes its task queue. Issues = work items.

---

## Process

### Step 1: Verify Environment

Check we're in a git repo with a GitHub remote:

```bash
git remote get-url origin 2>/dev/null
```

If not a git repo or no GitHub remote, stop and explain:
- "This skill requires a GitHub repository. Initialize with `git init` and `gh repo create`."

Extract owner/repo from the remote URL for later use.

### Step 2: Verify gh CLI

```bash
gh auth status 2>&1 | head -3
```

If not authenticated, tell user to run `! gh auth login` and re-run the wizard.

### Step 3: Check for Existing Skills

```bash
ls -la .claude/skills/backlog 2>/dev/null
ls -la .claude/skills/pick-work 2>/dev/null
ls -la .claude/skills/close-work 2>/dev/null
ls -la .claude/skills/work-loop 2>/dev/null
```

If any exist, ask user:
- **Overwrite** — Replace existing skills with fresh versions
- **Skip** — Keep existing, only add missing ones
- **Cancel** — Abort wizard

### Step 4: Ask Workflow Preferences

Use AskUserQuestion:
- **Question:** "How should the agent handle its work loop?"
- **Header:** "Work Loop"
- **Options:**
  1. **Scheduled (Recommended)** — Run automatically via Trinity on a schedule (e.g., every 4 hours)
  2. **Manual only** — Only run when explicitly invoked with `/work-loop`
  3. **Continuous** — Keep processing until backlog is empty (use with caution)

### Step 5: Create Skill Directories

```bash
mkdir -p .claude/skills/backlog
mkdir -p .claude/skills/pick-work
mkdir -p .claude/skills/close-work
mkdir -p .claude/skills/work-loop
```

### Step 6: Create /backlog Skill

Write `.claude/skills/backlog/SKILL.md`:

```markdown
---
name: backlog
description: Show current GitHub Issues backlog — what's in progress, what's next, priorities
argument-hint: "[all|in-progress|blocked]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: github-backlog
---

# Backlog

View the agent's task backlog from GitHub Issues.

## Process

### Step 1: Parse Arguments

- `/backlog` or `/backlog status` → Show overview (in-progress + next up)
- `/backlog all` → Show all open issues by priority
- `/backlog in-progress` → Show only in-progress items
- `/backlog blocked` → Show blocked items

### Step 2: Verify GitHub CLI

```bash
gh auth status 2>&1 | head -3
```

If not authenticated, tell user to run `! gh auth login`.

### Step 3: Check Labels Exist

```bash
gh label list --json name --jq '.[].name' | grep -E '^(status:|priority:)' | sort
```

If missing required labels, offer to create them:

```bash
gh label create "status:todo" --color "0E8A16" --description "Ready to work"
gh label create "status:in-progress" --color "FBCA04" --description "Currently working"
gh label create "status:blocked" --color "D93F0B" --description "Waiting on something"
gh label create "status:done" --color "6E5494" --description "Finished"
gh label create "priority:p0" --color "B60205" --description "Do now"
gh label create "priority:p1" --color "D93F0B" --description "Do soon"
gh label create "priority:p2" --color "FBCA04" --description "Do eventually"
```

### Step 4: Query Issues

**For overview (default):**

```bash
# In-progress
gh issue list --label "status:in-progress" --state open --json number,title,labels,assignees,updatedAt

# Next up (P0 todos)
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,labels,assignees

# P1 todos  
gh issue list --label "priority:p1" --label "status:todo" --state open --json number,title,labels,assignees --limit 5
```

### Step 5: Format Output

Present results clearly:

```
## Backlog Overview

### In Progress (1)
| # | Title | Priority | Updated |
|---|-------|----------|---------|
| 42 | Implement feature X | p1 | 2h ago |

### Next Up — P0 (2)
| # | Title |
|---|-------|
| 45 | Critical bug fix |
| 46 | Urgent deploy |

### Queued — P1 (3)
| # | Title |
|---|-------|
| 48 | Add new endpoint |

**Total open: 6 issues**
```
```

### Step 7: Create /pick-work Skill

Write `.claude/skills/pick-work/SKILL.md`:

```markdown
---
name: pick-work
description: Pick the next task from the backlog — selects highest priority todo, moves to in-progress
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: github-backlog
---

# Pick Work

Select the next task from the GitHub Issues backlog and mark it as in-progress.

## Process

### Step 1: Check Current Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 1
```

If an issue is already in-progress, report it and ask:
1. Continue that work
2. Park it and pick something new
3. Cancel

### Step 2: Select Issue

**If specific issue number provided ($ARGUMENTS):**

```bash
gh issue view $ARGUMENTS --json number,title,body,labels,state
```

**If no argument — find highest priority todo:**

```bash
# Try P0 first
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1

# Then P1, P2, then any todo without priority
```

### Step 3: Move to In-Progress

```bash
gh issue edit $ISSUE_NUMBER --remove-label "status:todo" --add-label "status:in-progress"
gh issue comment $ISSUE_NUMBER --body "Started working on this."
```

### Step 4: Present Issue

Display the full issue for work:

```
## Picked: #42 — Implement feature X

**Priority:** p1

### Requirements

[Issue body here]

---

**Status:** Now in-progress

When done, run `/close-work "summary of what was done"`
```
```

### Step 8: Create /close-work Skill

Write `.claude/skills/close-work/SKILL.md`:

```markdown
---
name: close-work
description: Mark current work done — adds summary comment, updates labels, closes issue
argument-hint: "\"summary of what was done\""
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: github-backlog
---

# Close Work

Complete the current in-progress task with a summary.

## Process

### Step 1: Find In-Progress Issue

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 1
```

If no in-progress issue, report "No work currently in progress."

If multiple in-progress, list them and ask which to close.

### Step 2: Validate Summary

The argument should be a summary of what was done. If empty, ask for a summary.

### Step 3: Add Completion Comment

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY

---
*Completed by agent*"
```

### Step 4: Update Labels and Close

```bash
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 5: Report

```
## Closed: #42 — Implement feature X

Summary: $SUMMARY

Next: Run `/backlog` to see remaining work or `/pick-work` for the next task.
```
```

### Step 9: Create /work-loop Skill

Write `.claude/skills/work-loop/SKILL.md`. Customize based on the workflow preference from Step 4:

```markdown
---
name: work-loop
description: Autonomous work loop — process backlog issues until empty or time limit reached
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
automation: autonomous
schedule: "0 */4 * * *"  # Every 4 hours — adjust or remove based on preference
user-invocable: true
metadata:
  version: "1.0"
  author: github-backlog
---

# Work Loop

Autonomous heartbeat that processes the GitHub Issues backlog. Continues in-progress work or picks the next task, executes it, closes when done, and repeats.

## Purpose

Run on a schedule (via Trinity) or manually to work through the agent's task backlog. The agent decides how to execute each task based on the issue content and its available skills.

## Process

### Step 1: Initialize Loop

Record start time. Complete within 40 minutes to stay under reliability threshold.

Read CLAUDE.md to understand agent capabilities.

### Step 2: Check for In-Progress Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

If found, continue that work. If not, proceed to Step 3.

### Step 3: Pick Next Task

Find highest priority todo:

```bash
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1
```

If none, try P1, P2, then any todo. If backlog empty, exit successfully.

If task found, move to in-progress:

```bash
gh issue edit $NUMBER --remove-label "status:todo" --add-label "status:in-progress"
gh issue comment $NUMBER --body "Starting work on this issue."
```

### Step 4: Execute Task

Parse the issue body for requirements. Execute based on content:

1. **Skill invocation**: If issue mentions a skill, invoke it
2. **Direct execution**: If task is clear, execute directly
3. **Sub-agent**: For complex tasks, spawn an Agent

Add progress comments as work proceeds.

**Handle blockers**: If task cannot be completed:
```bash
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
gh issue comment $NUMBER --body "Blocked: $REASON"
```

### Step 5: Complete Task

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY

---
*Completed by agent work-loop*"

gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 6: Check Time and Loop

If under 40 minutes elapsed, return to Step 2. Otherwise, gracefully exit.

## Trinity Scheduling

Deploy to Trinity and schedule this skill to run automatically:

```bash
trinity deploy .
trinity schedules create work-loop --cron "0 */4 * * *"
```

The agent will process its backlog every 4 hours without manual intervention.
```

### Step 10: Create GitHub Labels

Create the required labels if they don't exist:

```bash
# Status labels
gh label create "status:todo" --color "0E8A16" --description "Ready to work" 2>/dev/null || true
gh label create "status:in-progress" --color "FBCA04" --description "Currently working" 2>/dev/null || true
gh label create "status:blocked" --color "D93F0B" --description "Waiting on something" 2>/dev/null || true
gh label create "status:done" --color "6E5494" --description "Finished" 2>/dev/null || true

# Priority labels
gh label create "priority:p0" --color "B60205" --description "Do now" 2>/dev/null || true
gh label create "priority:p1" --color "D93F0B" --description "Do soon" 2>/dev/null || true
gh label create "priority:p2" --color "FBCA04" --description "Do eventually" 2>/dev/null || true
```

### Step 11: Update CLAUDE.md

Read the current CLAUDE.md and add a Task Management section. Insert it after the main capabilities section:

```markdown
## Task Management

This agent manages its work via GitHub Issues in this repository.

**Workflow:**
1. Create issues with clear requirements and priority labels
2. Agent picks highest priority `status:todo` issue
3. Moves to `status:in-progress` while working
4. Closes with summary when complete
5. Repeats until backlog is empty

**Skills:**
| Skill | Purpose |
|-------|---------|
| `/backlog` | View current workload by priority |
| `/pick-work` | Grab next task, mark in-progress |
| `/close-work "summary"` | Complete current task |
| `/work-loop` | Autonomous processing (schedulable) |

**Labels:**
- `status:todo` / `status:in-progress` / `status:blocked` / `status:done`
- `priority:p0` (do now) / `priority:p1` (do soon) / `priority:p2` (do eventually)

**Creating Issues for this Agent:**
- Clear title describing the task
- Body with requirements/acceptance criteria
- Add appropriate priority label
- Leave as `status:todo` (or no status — defaults to todo)

**Autonomous Mode (Trinity):**
Schedule `/work-loop` to run periodically. The agent will process its backlog automatically.
```

Use Edit to insert this section. Find a good insertion point (after Core Capabilities or similar).

### Step 12: Summary

Display completion summary:

```
## GitHub Backlog Installed

### Skills Created

| Skill | Location |
|-------|----------|
| `/backlog` | `.claude/skills/backlog/SKILL.md` |
| `/pick-work` | `.claude/skills/pick-work/SKILL.md` |
| `/close-work` | `.claude/skills/close-work/SKILL.md` |
| `/work-loop` | `.claude/skills/work-loop/SKILL.md` |

### Labels Created

- `status:todo`, `status:in-progress`, `status:blocked`, `status:done`
- `priority:p0`, `priority:p1`, `priority:p2`

### CLAUDE.md Updated

Added Task Management section explaining the workflow.

### Next Steps

1. **Create your first issue:**
   ```bash
   gh issue create --title "First task" --body "Requirements here" --label "priority:p1" --label "status:todo"
   ```

2. **View backlog:** `/backlog`

3. **Start working:** `/pick-work`

4. **Go autonomous (Trinity):**
   ```bash
   trinity deploy .
   trinity schedules create work-loop --cron "0 */4 * * *"
   ```

Your agent now manages its work via GitHub Issues.
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Not a git repo | Stop, explain git init + gh repo create |
| gh not authenticated | Stop, explain `! gh auth login` |
| Skills already exist | Ask: overwrite, skip, or cancel |
| CLAUDE.md not found | Create minimal one or warn |
| Label creation fails | Continue, note which failed |
