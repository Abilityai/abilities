---
name: work-loop
description: Autonomous work loop — pick one backlog issue, execute it, close it, exit. Re-invoked by scheduler for the next.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
automation: autonomous
schedule: "0 9 * * *"  # Daily at 9am — adjust as needed
user-invocable: true
metadata:
  version: "1.3"
  created: 2026-04-14
  updated: 2026-05-03
  author: Ability.ai
---

# Work Loop

Autonomous skill that picks one issue from the backlog, executes it, and exits. The scheduler re-invokes it for the next issue — one issue per context window.

## Purpose

Run on a schedule (or manually) to autonomously advance the agent's task backlog. Each invocation handles exactly one issue, keeping context focused and noise-free. The cron handles iteration; this skill handles execution.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Task backlog |
| GitHub Labels | status:*, priority:*, skill:* | Yes | Yes | Track status and route by skill |
| Agent Skills | .claude/skills/ | Yes | No | Available capabilities |
| CLAUDE.md | ./CLAUDE.md | Yes | No | Agent identity and guidelines |

## Prerequisites

- `gh` CLI authenticated
- Repository has required labels (status:todo, status:in-progress, priority:*)
- Agent has skills to handle the types of issues in backlog

## Process

### Step 1: Check for In-Progress Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

If an issue is in-progress:
- This is the current task
- Parse the issue body for requirements
- Continue working on it (skip to Step 3)

If no in-progress work, proceed to Step 2.

### Step 2: Pick Next Task

Find highest priority todo:

```bash
# P0 first
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1

# Then P1
gh issue list --label "priority:p1" --label "status:todo" --state open --json number,title,body,labels --limit 1

# Then P2
gh issue list --label "priority:p2" --label "status:todo" --state open --json number,title,body,labels --limit 1

# Then any todo
gh issue list --label "status:todo" --state open --json number,title,body,labels --limit 1
```

If no tasks found:
- Log: "Backlog empty. Work loop complete."
- Exit successfully

If task found:
- Move to in-progress:
  ```bash
  gh issue edit $NUMBER --remove-label "status:todo" --add-label "status:in-progress"
  gh issue comment $NUMBER --body "Starting work on this issue."
  ```

### Step 3: Execute Task

Parse the issue body to understand requirements. The issue should contain:
- Clear description of what needs to be done
- Acceptance criteria (if applicable)
- Any relevant context

**Determine execution approach:**

Check for a `skill:*` label on the issue first:

- **`skill:*` label present**: This issue requires modifying or creating a skill file — it needs human input via `/sprint`. Mark it blocked:
  ```bash
  gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
  gh issue comment $NUMBER --body "Blocked: skill development issue — requires human sprint (/sprint #$NUMBER)"
  ```
  Continue to the next issue.

- **No skill label (project-level)**: Determine approach:
  1. **Skill invocation**: If the issue references a specific skill (e.g., "run /groom" or "run /roadmap"), invoke that skill
  2. **Direct execution**: If the task is clear and doesn't require wizard tools, execute directly
  3. **Sub-agent delegation**: For complex research or analysis tasks, spawn an Agent

**Add progress comments** as work proceeds:

```bash
gh issue comment $NUMBER --body "Progress: $UPDATE"
```

**Handle blockers**: If the task cannot be completed:
- Add blocker comment explaining why
- Move to blocked status:
  ```bash
  gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
  gh issue comment $NUMBER --body "Blocked: $REASON"
  ```
- Continue to next task

### Step 4: Complete Task

When task is done:

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY_OF_WORK_DONE

---
*Completed by agent work-loop*"

gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

## Outputs

- Issues processed (moved from todo → done)
- Progress comments on each issue
- Completion summaries on closed issues
- Blocked issues flagged with reasons

## Error Recovery

| Error | Recovery |
|-------|----------|
| `gh` not authenticated | Log error, exit — user must run `! gh auth login` |
| Issue update fails | Log error, exit |
| Task execution fails | Mark issue as blocked with error details, exit |
| Network failure | Retry once, then log and exit |

## Completion Checklist

- [ ] Checked for in-progress work
- [ ] Picked next task by priority
- [ ] Added progress comments
- [ ] Closed completed issue with summary
- [ ] Logged final status
