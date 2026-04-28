---
name: install-github-backlog
description: Add GitHub Issues backlog workflow to any agent — creates the full development cycle (backlog, claim, close, groom, roadmap, autoplan, commit, sprint, work-loop)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "2.0"
  created: 2026-04-14
  updated: 2026-04-28
  author: Ability.ai
  changelog:
    - "2.0: Full skill set — added groom, roadmap, autoplan, commit, sprint; renamed pick-work→claim, close-work→close"
    - "1.0: Initial version with backlog, pick-work, close-work, work-loop"
---

# Install GitHub Backlog

Add GitHub Issues task management to any Claude Code agent. This wizard creates skills directly in your agent's `.claude/skills/` directory — no plugin dependency, fully self-contained.

**What you get:**

| Skill | Purpose |
|-------|---------|
| `/backlog` | Priority-ordered view of open issues |
| `/roadmap` | Strategic view grouped by skill area |
| `/groom` | Tag issues with `skill:*` labels, set priorities |
| `/claim` | Grab the next task, mark it in-progress |
| `/autoplan` | Analyze a skill issue before implementing |
| `/close` | Close an issue without a git commit |
| `/commit` | Stage skill file changes, commit, close issue |
| `/sprint` | Human-supervised develop cycle (one issue end-to-end) |
| `/work-loop` | Autonomous processing (schedulable on Trinity) |

> The agent's repository becomes its task queue. Issues = work items. Skills = the units of work.

---

## Process

### Step 1: Verify Environment

```bash
git remote get-url origin 2>/dev/null
```

If not a git repo or no GitHub remote, stop and explain:
"This skill requires a GitHub repository. Initialize with `git init` and `gh repo create`."

### Step 2: Verify gh CLI

```bash
gh auth status 2>&1 | head -3
```

If not authenticated, tell user to run `! gh auth login` and re-run.

### Step 3: Check for Existing Skills

```bash
ls .claude/skills/ 2>/dev/null
```

List which of the target skills already exist. If any do, ask:
- **Overwrite** — Replace with fresh versions
- **Skip existing** — Only create missing ones
- **Cancel** — Abort

### Step 4: Ask Workflow Preferences

Use AskUserQuestion:
- **Header:** "Work Loop Schedule"
- **Question:** "How should the autonomous work-loop run?"
- **Options:**
  1. Daily at 9am (`0 9 * * *`) — recommended
  2. Every 4 hours (`0 */4 * * *`)
  3. Manual only (no schedule)

### Step 5: Create Skill Directories

```bash
mkdir -p .claude/skills/backlog
mkdir -p .claude/skills/roadmap
mkdir -p .claude/skills/groom
mkdir -p .claude/skills/claim
mkdir -p .claude/skills/autoplan
mkdir -p .claude/skills/close
mkdir -p .claude/skills/commit
mkdir -p .claude/skills/sprint
mkdir -p .claude/skills/work-loop
```

### Step 6: Create /backlog Skill

Write `.claude/skills/backlog/SKILL.md`:

```markdown
---
name: backlog
description: Show current GitHub Issues backlog — what's in progress, what's next, priorities
argument-hint: "[all|in-progress|blocked|p0|p1|p2]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Backlog

View the agent's task backlog from GitHub Issues, ordered by priority.

## Process

### Step 1: Parse Arguments
- No args → overview (in-progress + P0 todos + P1 todos)
- `all` → all open issues
- `in-progress` → only in-progress
- `blocked` → only blocked
- `p0` / `p1` / `p2` → that priority

### Step 2: Query

```bash
# In-progress
gh issue list --label "status:in-progress" --state open --json number,title,labels,updatedAt

# P0 todos
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,labels

# P1 todos
gh issue list --label "priority:p1" --label "status:todo" --state open --json number,title,labels --limit 5
```

### Step 3: Format

Show a markdown table per section. Include total open count and link to GitHub Issues.

Run `/roadmap` for a skill-grouped view, or `/claim` to start the next issue.
```

### Step 7: Create /roadmap Skill

Write `.claude/skills/roadmap/SKILL.md`:

```markdown
---
name: roadmap
description: Strategic view of the agent backlog — open issues grouped by skill area
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Roadmap

Issues grouped by `skill:*` label. Use this to see which areas of the agent need the most work. For the daily priority view, use `/backlog`.

## Process

### Step 1: Fetch

```bash
gh issue list --state open --json number,title,labels,updatedAt --limit 100
```

### Step 2: Group by Skill

Parse the `skill:*` label from each issue. One section per skill. Issues with no skill label go into "Project-level". Within each group, sort by priority.

### Step 3: Format

Show a markdown table per skill section with issue number, title, priority, status. End with total count and a focus recommendation (skill with most P0/P1 work).

Suggest `/groom` if many issues lack skill labels, or `/claim` to start the highest priority item.
```

### Step 8: Create /groom Skill

Write `.claude/skills/groom/SKILL.md`:

```markdown
---
name: groom
description: Groom the backlog — tag issues with skill:* labels, set missing priorities, flag stale in-progress work
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Groom

Audit open issues: tag them with the skill they affect, verify priorities, flag stale in-progress work.

## Process

### Step 1: Discover Skills

```bash
ls .claude/skills/
```

Build list of skill names. Create `skill:*` labels for each:

```bash
gh label create "skill:$SKILL_NAME" --color "0075CA" --description "Issues affecting $SKILL_NAME" 2>/dev/null || true
```

### Step 2: Tag Untagged Issues

```bash
gh issue list --state open --json number,title,body,labels --limit 100
```

For each issue without a `skill:*` label: show title/body, suggest which skill it affects (or project-level), confirm, apply label:

```bash
gh issue edit $NUMBER --add-label "skill:$SKILL_NAME"
```

### Step 3: Check Priorities

List issues missing `priority:*` labels. Offer to assign them in batch.

### Step 4: Flag Stale In-Progress

List in-progress issues not updated in 48+ hours. Offer to move them back to `status:todo`.

### Step 5: Summary

Report: X tagged, Y prioritized, Z stale flagged. Suggest `/roadmap` or `/claim`.
```

### Step 9: Create /claim Skill

Write `.claude/skills/claim/SKILL.md`:

```markdown
---
name: claim
description: Claim the next issue from the backlog — picks highest priority todo, moves to in-progress
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Claim

Select the next issue and mark it in-progress.

## Process

### Step 1: Check Current Work

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 1
```

If already in-progress: ask to continue, park it, or cancel.

### Step 2: Select Issue

If `$ARGUMENTS` provided: load that issue number.

Otherwise find highest priority todo (P0 → P1 → P2 → any todo):

```bash
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1
```

### Step 3: Move to In-Progress

```bash
gh issue edit $ISSUE_NUMBER --remove-label "status:todo" --add-label "status:in-progress"
gh issue comment $ISSUE_NUMBER --body "Claimed — starting work."
```

### Step 4: Present Issue

Show full issue. If `skill:*` label present, surface it:
"This issue is tagged `skill:$SKILL_NAME`. Open `.claude/skills/$SKILL_NAME/SKILL.md`."

Suggest next steps: `/autoplan` to plan before implementing, or `/sprint` for the full guided cycle.
```

### Step 10: Create /autoplan Skill

Write `.claude/skills/autoplan/SKILL.md`:

```markdown
---
name: autoplan
description: Analyze a skill issue before implementing — reads the affected SKILL.md and produces a focused change plan
argument-hint: "[issue-number]"
allowed-tools: Bash, Read, Glob
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Autoplan

Read a claimed issue and the SKILL.md it affects. Produce a clear implementation plan before touching any files.

## Process

### Step 1: Load Issue

If `$ARGUMENTS` provided, load that issue. Otherwise find current in-progress:

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

### Step 2: Identify Affected Skill

Look for `skill:*` label. If missing, infer from title/body and confirm.

### Step 3: Read the Skill

```bash
cat .claude/skills/$SKILL_NAME/SKILL.md
```

If the skill doesn't exist yet, treat as new skill.

### Step 4: Analyze

Compare issue requirements against the current SKILL.md. Identify:
- Which section(s) change (step, frontmatter, output format, error handling)
- Interface impact (argument-hint, name, automation mode changes)
- Whether it's a breaking change (needs `--archive` flag in adjust-playbook)
- Recommended tool: `/adjust-playbook $SKILL_NAME` or `/create-playbook`

### Step 5: Output Plan

```
## Autoplan: #N — Title

Skill: `$SKILL_NAME`
Implement with: /adjust-playbook $SKILL_NAME

### What to Change
1. [specific change]
2. [specific change]

### Risks
- [risk or "None"]
```
```

### Step 11: Create /close Skill

Write `.claude/skills/close/SKILL.md`:

```markdown
---
name: close
description: Close the current issue without a git commit — use /commit instead when skill files changed
argument-hint: "\"summary of what was done\""
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Close

Mark the current in-progress issue done without creating a git commit. If skill files were modified, use `/commit` instead.

## Process

### Step 1: Check for Changes

```bash
git status --short
```

If SKILL.md files appear, warn: "Skill files were modified. Run `/commit` to close the issue with a git commit."

### Step 2: Find Issue

```bash
gh issue list --label "status:in-progress" --state open --json number,title --limit 5
```

### Step 3: Get Summary

Use `$ARGUMENTS` or ask for a summary.

### Step 4: Comment and Close

```bash
gh issue comment $NUMBER --body "## Completed\n\n$SUMMARY\n\n---\n*Closed via /close*"
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

Confirm: "Closed #N — $TITLE. Run `/claim` for the next issue."
```

### Step 12: Create /commit Skill

Write `.claude/skills/commit/SKILL.md`:

```markdown
---
name: commit
description: Commit changed skill files and close the in-progress issue with a traceability commit message
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Commit

Stage changed skill files, write a commit message tied to the in-progress issue, and close it.

## Process

### Step 1: Find Issue

If `$ARGUMENTS` provided, use that. Otherwise:

```bash
gh issue list --label "status:in-progress" --state open --json number,title,labels --limit 5
```

### Step 2: Check Changes

```bash
git status --short
```

If no changes: "Nothing to commit — did `/adjust-playbook` or `/create-playbook` run yet?"

Stage skill files:

```bash
git add .claude/skills/
git add CLAUDE.md 2>/dev/null || true
git diff --cached --stat
```

### Step 3: Compose Message

Format: `[$SKILL_NAME]: $description (closes #$NUMBER)`
- Use the `skill:*` label for the prefix, or `[agent]` for project-level issues.
- Description: lowercase imperative, derived from issue title.

Show and confirm before committing.

### Step 4: Commit

```bash
git commit -m "$COMMIT_MESSAGE"
```

### Step 5: Close Issue

```bash
gh issue comment $NUMBER --body "## Completed\n\nCommitted: $(git rev-parse --short HEAD)\n\n---\n*Closed via /commit*"
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

Confirm: "Committed and closed #N. Run `/claim` for the next issue."
```

### Step 13: Create /sprint Skill

Write `.claude/skills/sprint/SKILL.md`:

```markdown
---
name: sprint
description: Human-supervised development cycle — roadmap → claim → autoplan → implement → commit for one issue
argument-hint: "[issue-number]"
allowed-tools: Bash, Read, Skill
automation: manual
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Sprint

Guided cycle for one issue: shows roadmap, claims an issue, runs autoplan, then waits while you implement, then commits.

## Process

### Step 1: Roadmap

Invoke `/roadmap` to show the skill-grouped backlog. Skip if `$ARGUMENTS` provided.

### Step 2: Claim

Invoke `/claim` (or `/claim $ARGUMENTS`).

### Step 3: Autoplan

Invoke `/autoplan` on the claimed issue.

### Step 4: Implement (Human Step)

Print:

```
Ready to implement. Run:

  /adjust-playbook $SKILL_NAME  — to modify an existing skill
  /create-playbook              — to scaffold a new skill

Type 'done' when complete, or 'abort' to leave in-progress for next session.
```

### Step 5: Commit

If 'done': invoke `/commit` to close the issue and create a git commit.
If 'abort': leave issue in-progress, exit gracefully.
```

### Step 14: Create /work-loop Skill

Write `.claude/skills/work-loop/SKILL.md` using the schedule from Step 4:

```markdown
---
name: work-loop
description: Autonomous work loop — process backlog issues until empty or time limit reached
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
automation: autonomous
schedule: "$SCHEDULE"
user-invocable: true
metadata:
  version: "1.0"
  author: agent-dev
---

# Work Loop

Autonomous heartbeat that processes the GitHub Issues backlog. Picks next issue, executes it, closes when done, repeats.

## Process

### Step 1: Initialize

```bash
LOOP_START=$(date +%s)
MAX_DURATION=2400  # 40 minutes
```

Read CLAUDE.md for agent capabilities.

### Step 2: Check In-Progress

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

If found, continue that work (Step 4). If not, proceed to Step 3.

### Step 3: Pick Next Task

```bash
gh issue list --label "priority:p0" --label "status:todo" --state open --json number,title,body,labels --limit 1
# Then P1, P2, then any todo
```

If backlog empty: log "Backlog empty. Work loop complete." and exit.

Move to in-progress:
```bash
gh issue edit $NUMBER --remove-label "status:todo" --add-label "status:in-progress"
gh issue comment $NUMBER --body "Starting work on this issue."
```

### Step 4: Execute Task

Check for `skill:*` label first:

- **skill label present**: This needs human sprint. Mark blocked:
  ```bash
  gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
  gh issue comment $NUMBER --body "Blocked: skill development issue — requires /sprint #$NUMBER"
  ```
  Continue to next issue.

- **Project-level**: Execute based on issue content:
  1. If issue references a skill, invoke it
  2. If task is clear, execute directly
  3. For complex tasks, spawn an Agent

Add progress comments as work proceeds.

Handle blockers:
```bash
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:blocked"
gh issue comment $NUMBER --body "Blocked: $REASON"
```

### Step 5: Complete Task

```bash
gh issue comment $NUMBER --body "## Completed\n\n$SUMMARY\n\n---\n*Completed by work-loop*"
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 6: Check Time and Loop

```bash
ELAPSED=$(( $(date +%s) - LOOP_START ))
```

If under 40 min: return to Step 2. Otherwise: graceful exit with status comment on any in-progress issue.
```

### Step 15: Create GitHub Labels

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

Note: `skill:*` labels are created dynamically by `/groom` based on the skills in `.claude/skills/`.

### Step 16: Update CLAUDE.md

Read the current CLAUDE.md and add a Task Management section:

```markdown
## Task Management

This agent manages its work via GitHub Issues in this repository. Issues map to skill development tasks and project-level work.

**Development Workflow:**
1. `/groom` — Tag issues with the skill they affect (`skill:*` labels), set priorities
2. `/roadmap` — See which skills have the most open work
3. `/claim` — Take the next issue, mark in-progress
4. `/autoplan` — Analyze the issue against the current SKILL.md before implementing
5. `/adjust-playbook` or `/create-playbook` — Make the change
6. `/commit` — Stage skill files, write commit, close issue

**Or use `/sprint`** for the full guided cycle in one command.

**Autonomous mode:** `/work-loop` processes project-level issues on schedule; skill issues are flagged for human sprint.

**Skills:**
| Skill | Purpose |
|-------|---------|
| `/backlog` | Priority-ordered view of open issues |
| `/roadmap` | Skill-grouped strategic view |
| `/groom` | Tag issues with skill labels, verify priorities |
| `/claim` | Grab next task, mark in-progress |
| `/autoplan` | Analyze issue before implementing |
| `/close` | Close issue (no git commit) |
| `/commit` | Commit skill changes and close issue |
| `/sprint` | Full human-supervised cycle |
| `/work-loop` | Autonomous loop for project-level issues |

**Labels:**
- `status:todo` / `status:in-progress` / `status:blocked` / `status:done`
- `priority:p0` (do now) / `priority:p1` (do soon) / `priority:p2` (do eventually)
- `skill:<name>` — which skill this issue affects (created by `/groom`)
```

### Step 17: Summary

```
## GitHub Backlog Installed

### Skills Created

| Skill | Location |
|-------|----------|
| `/backlog` | `.claude/skills/backlog/SKILL.md` |
| `/roadmap` | `.claude/skills/roadmap/SKILL.md` |
| `/groom` | `.claude/skills/groom/SKILL.md` |
| `/claim` | `.claude/skills/claim/SKILL.md` |
| `/autoplan` | `.claude/skills/autoplan/SKILL.md` |
| `/close` | `.claude/skills/close/SKILL.md` |
| `/commit` | `.claude/skills/commit/SKILL.md` |
| `/sprint` | `.claude/skills/sprint/SKILL.md` |
| `/work-loop` | `.claude/skills/work-loop/SKILL.md` |

### Labels Created
- `status:todo`, `status:in-progress`, `status:blocked`, `status:done`
- `priority:p0`, `priority:p1`, `priority:p2`
- `skill:*` labels created dynamically by `/groom`

### Next Steps

1. Create your first issue:
   ```bash
   gh issue create --title "First task" --body "Requirements here" --label "priority:p1" --label "status:todo"
   ```
2. Tag it: `/groom`
3. View by skill: `/roadmap`
4. Start working: `/sprint`
5. Go autonomous (Trinity): schedule `/work-loop`

Your agent now has a full development workflow.
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
