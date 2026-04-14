# GitHub Backlog Plugin

Manage agent tasks via GitHub Issues. Your agent's repo becomes its task queue — issues are work items, labels track status, and the agent can autonomously process its backlog.

## Concept

**Agent = Repository. Tasks = Issues.**

Every agent lives in a GitHub repository. This plugin treats that repo's Issues as the agent's task backlog. The agent can:
- View its current workload
- Pick up the next task
- Update progress via labels and comments  
- Close completed work with summaries
- Run autonomous work loops on a schedule

## Installation

```bash
/plugin install github-backlog@abilityai
```

## Required Labels

Create these labels in your repo (the plugin will offer to create them on first use):

**Status labels:**
- `status:todo` — Ready to work
- `status:in-progress` — Currently working
- `status:blocked` — Waiting on something
- `status:done` — Finished (or just close the issue)

**Priority labels:**
- `priority:p0` — Do now
- `priority:p1` — Do soon
- `priority:p2` — Do eventually

## Skills

### /backlog

Show current backlog state — what's in progress, what's next, priorities.

```bash
/backlog              # Show overview
/backlog all          # Show all open issues
/backlog in-progress  # Show current work
```

### /pick-work

Grab the next task from the backlog. Selects highest-priority `status:todo` issue, moves it to `status:in-progress`, and returns the issue details.

```bash
/pick-work            # Pick highest priority todo
/pick-work 42         # Pick specific issue #42
```

### /close-work

Mark current work done. Adds a summary comment, moves to `status:done` (or closes), and clears the in-progress state.

```bash
/close-work "Implemented the feature, added tests"
```

### /work-loop

Autonomous heartbeat skill. Checks for in-progress work (continues it) or picks the next todo. Executes the work, closes when done, loops until backlog is clear or time limit reached.

**For scheduled execution via Trinity:**
```yaml
schedule: "0 */4 * * *"  # Every 4 hours
```

## Integration with Agent CLAUDE.md

Add this to your agent's CLAUDE.md to enable backlog awareness:

```markdown
## Task Management

This agent manages its work via GitHub Issues in this repository.

- **View backlog**: `/backlog`
- **Start work**: `/pick-work` 
- **Complete work**: `/close-work "summary"`
- **Autonomous mode**: `/work-loop` (scheduled via Trinity)

### Issue Format

When creating issues for this agent, include:
- Clear title describing the task
- Body with requirements/acceptance criteria
- Appropriate priority label (priority:p0/p1/p2)
- Leave status:todo label (or no status label — defaults to todo)
```

## Work Loop Behavior

The `/work-loop` skill is designed for autonomous scheduled execution:

1. Check for `status:in-progress` issues assigned to this agent
2. If found, continue that work
3. If not, pick highest priority `status:todo`
4. Parse the issue body for requirements
5. Execute the work (invoke appropriate skills or act directly)
6. Add progress comments to the issue
7. When complete, close with summary
8. Repeat until backlog empty or 40-minute limit reached

The agent decides *how* to do the work based on the issue content and its own capabilities.

## License

MIT
