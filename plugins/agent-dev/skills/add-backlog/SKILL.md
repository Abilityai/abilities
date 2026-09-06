---
name: install-github-backlog
description: Add GitHub Issues backlog workflow to any agent — creates the full development cycle (backlog, claim, close, groom, roadmap, autoplan, commit, sprint, work-loop)
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "2.1"
  created: 2026-04-14
  updated: 2026-09-06
  author: Ability.ai
  changelog:
    - "2.1: The installer no longer embeds its own copies of the nine workflow skills — it copies the standalone agent-dev skills (backlog, roadmap, groom, claim, autoplan, close, commit, sprint, work-loop) from the plugin at install time. The embedded copies had drifted from the maintained skills (e.g. work-loop 1.0 vs 1.3, backlog argument hints); now there is one authoring home, also mirrored into the trinity-skills library for assignment on Trinity"
    - "2.0: Full skill set — added groom, roadmap, autoplan, commit, sprint; renamed pick-work→claim, close-work→close"
    - "1.0: Initial version with backlog, pick-work, close-work, work-loop"
---

# Install GitHub Backlog

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `install-github-backlog vX.Y — recent: <summary>`. Then proceed.

Add GitHub Issues task management to any Claude Code agent. This wizard copies the plugin's standalone workflow skills into your agent's `.claude/skills/` directory — the installed agent has no runtime plugin dependency, and the skills are the same files Trinity instances assign from the `trinity-skills` library.

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

Set `$SCHEDULE` from the chosen option (empty for manual only).

### Step 5: Prepare the skills directory

```bash
mkdir -p .claude/skills
```

### Step 6: Copy the nine runtime skills from the plugin

The workflow skills are authored **once**, as standalone skills in this plugin (`/agent-dev:backlog`, `roadmap`, `groom`, `claim`, `autoplan`, `close`, `commit`, `sprint`, `work-loop`) and mirrored into the public `trinity-skills` library, where Trinity instances assign them to agents and re-inject updates automatically. This installer copies the same files — it never carries its own versions:

```bash
for s in backlog roadmap groom claim autoplan close commit sprint work-loop; do
  SRC="${CLAUDE_PLUGIN_ROOT}/skills/$s"
  [ -d "$SRC" ] || { echo "missing $SRC — is the agent-dev plugin installed?"; exit 1; }
  rm -rf ".claude/skills/$s" && cp -R "$SRC" ".claude/skills/$s"
done
ls .claude/skills/{backlog,roadmap,groom,claim,autoplan,close,commit,sprint,work-loop}/SKILL.md
```

Respect the Step 3 answer: with **skip existing**, only copy the missing ones.

Apply the Step 4 schedule choice to the work-loop copy — the standalone skill ships a default `schedule:`; replace it with the chosen cron, or delete the line for manual-only:

```bash
if [ -n "$SCHEDULE" ]; then
  sed -i.bak -E "s|^schedule: .*$|schedule: \"$SCHEDULE\"|" .claude/skills/work-loop/SKILL.md
else
  sed -i.bak -E "/^schedule: /d" .claude/skills/work-loop/SKILL.md
fi
rm -f .claude/skills/work-loop/SKILL.md.bak
```

**Copies are frozen at install time.** Re-run this installer (Step 3 → *Overwrite*) after `/plugin marketplace update` to pick up newer skill versions — or, on Trinity, assign the nine skills from the library instead and let the platform keep them current.


### Step 7: Create GitHub Labels

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

### Step 8: Update CLAUDE.md

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

### Step 9: Summary

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
