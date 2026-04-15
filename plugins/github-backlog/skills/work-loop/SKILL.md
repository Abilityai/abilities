---
name: work-loop
description: Autonomous work loop — process backlog issues until empty or time limit reached
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
automation: autonomous
schedule: "0 9 * * *"  # Daily at 9am — adjust as needed
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-04-14
  author: Ability.ai
---

# Work Loop

Autonomous heartbeat skill that processes the GitHub Issues backlog. Continues in-progress work or picks the next task, executes it, closes when done, and repeats.

## Purpose

Run on a schedule (or manually) to autonomously work through the agent's task backlog. The agent decides how to execute each task based on the issue content and its available skills.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Task backlog |
| GitHub Labels | status:*, priority:* | Yes | Yes | Track status |
| Agent Skills | .claude/skills/ | Yes | No | Available capabilities |
| CLAUDE.md | ./CLAUDE.md | Yes | No | Agent identity and guidelines |

## Prerequisites

- `gh` CLI authenticated
- Repository has required labels (status:todo, status:in-progress, priority:*)
- Agent has skills to handle the types of issues in backlog

## Process

### Step 1: Initialize Loop

Record start time. The loop must complete within 40 minutes to stay under the 45-minute reliability threshold.

```bash
LOOP_START=$(date +%s)
MAX_DURATION=2400  # 40 minutes in seconds
```

Read CLAUDE.md to understand agent capabilities and guidelines.

### Step 2: Check for In-Progress Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

If an issue is in-progress:
- This is the current task
- Parse the issue body for requirements
- Continue working on it (skip to Step 4)

If no in-progress work, proceed to Step 3.

### Step 3: Pick Next Task

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

### Step 4: Execute Task

Parse the issue body to understand requirements. The issue should contain:
- Clear description of what needs to be done
- Acceptance criteria (if applicable)
- Any relevant context

**Determine execution approach:**

1. **Skill invocation**: If the issue references a specific skill (e.g., "run /deploy" or "execute /generate-report"), invoke that skill
2. **Direct execution**: If the task is clear enough, execute it directly using available tools
3. **Sub-agent delegation**: For complex tasks, spawn an Agent to handle it

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

### Step 5: Complete Task

When task is done:

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY_OF_WORK_DONE

---
*Completed by agent work-loop*"

gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 6: Check Time and Loop

```bash
CURRENT=$(date +%s)
ELAPSED=$((CURRENT - LOOP_START))
```

If elapsed < MAX_DURATION (40 minutes):
- Return to Step 2 (check for next task)

If elapsed >= MAX_DURATION:
- Log: "Time limit approaching. Pausing work loop."
- If work is in-progress, add comment: "Pausing work loop due to time limit. Will continue on next scheduled run."
- Exit successfully

## Outputs

- Issues processed (moved from todo → done)
- Progress comments on each issue
- Completion summaries on closed issues
- Blocked issues flagged with reasons

## Error Recovery

| Error | Recovery |
|-------|----------|
| `gh` not authenticated | Log error, exit — user must run `! gh auth login` |
| Issue update fails | Log error, continue to next issue |
| Task execution fails | Mark issue as blocked with error details, continue to next |
| Time limit reached | Graceful exit with status comment on any in-progress issue |
| Network failure | Retry once, then log and exit |

## Completion Checklist

- [ ] Checked for in-progress work
- [ ] Processed available tasks by priority
- [ ] Added progress comments
- [ ] Closed completed issues with summaries
- [ ] Respected 40-minute time limit
- [ ] Logged final status
