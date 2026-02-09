---
name: trinity-sync
description: Synchronize this agent with its remote counterpart running on Trinity via GitHub. Supports branch-based versioning for deploying different agent configurations.
argument-hint: [push|pull|status|deploy <branch>|branches]
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash, Read, Grep, mcp__trinity__list_agents, mcp__trinity__chat_with_agent
metadata:
  version: "1.1"
  created: 2025-02-05
  author: eugene
  changelog:
    - "1.1: Genericized - works with any agent via dynamic name detection"
    - "1.0: Initial version"
---

# Agent Synchronization Skill

Synchronize the local agent with its remote counterpart running on Trinity. Supports branch-based versioning for deploying different agent configurations.

## Agent Name Detection

This skill automatically detects the agent name using these methods (in order):

1. **template.yaml** (preferred):
   ```bash
   grep "^name:" template.yaml 2>/dev/null | cut -d: -f2 | tr -d ' '
   ```

2. **Directory name** (fallback):
   ```bash
   basename "$(pwd)"
   ```

3. **Environment variable** (override):
   ```bash
   echo "$TRINITY_AGENT_NAME"
   ```

## Quick Commands

- `/trinity-sync` or `/trinity-sync status` - Check sync status between local and remote
- `/trinity-sync pull` - Pull changes from remote (if remote is ahead)
- `/trinity-sync push` - Push local changes to remote on current branch
- `/trinity-sync push <branch>` - Push and deploy a specific branch to remote
- `/trinity-sync deploy <branch>` - Deploy an existing branch/tag to remote
- `/trinity-sync branches` - List available branches (local and remote)

## Arguments

$ARGUMENTS

## Directory Structure: What Syncs vs What's Discardable

**CRITICAL:** Know the difference between agent identity and runtime state:

| Path | Type | Sync? | Description |
|------|------|-------|-------------|
| `.claude/skills/` | **AGENT VALUE** | YES | Agent capabilities - THIS IS THE AGENT |
| `.claude/agents/` | **AGENT VALUE** | YES | Sub-agent definitions |
| `.claude/commands/` | **AGENT VALUE** | YES | Command definitions |
| `memory/` | **AGENT VALUE** | YES | Schedules, persistent state |
| `scripts/` | **AGENT VALUE** | YES | Python/bash scripts |
| `source-of-truth/` | **AGENT VALUE** | YES | Business documentation |
| `CLAUDE.md` | **AGENT VALUE** | YES | Main agent instructions |
| `template.yaml` | **AGENT VALUE** | YES | Trinity metadata |
| `.claude/debug/` | Runtime | Discard | Debug logs |
| `.claude/projects/` | Runtime | Discard | Project cache |
| `.claude/statsig/` | Runtime | Discard | Analytics state |
| `.claude/todos/` | Runtime | Discard | Temporary todos |
| `session-files/` | Runtime | Discard | Session-specific work |
| `content/` | Runtime | Discard | Large generated content |

**Never** run `git checkout -- .claude/skills/` - this destroys agent capabilities!

## Branch-Based Versioning

Use branches to maintain different versions or configurations of the agent:

| Branch Pattern | Purpose | Example |
|----------------|---------|---------|
| `main` | Production-stable version | Default deployment |
| `experimental` | Testing new features | `/trinity-sync deploy experimental` |
| `v1.x`, `v2.x` | Tagged stable releases | `/trinity-sync deploy v1.5` |
| `feature/*` | Work-in-progress features | `/trinity-sync push feature/new-skill` |

### Typical Workflow

```
# 1. Create experimental branch locally
git checkout -b experimental

# 2. Make changes, test locally
# ... edit skills, memory, etc ...

# 3. Push and deploy to remote for testing
/trinity-sync push experimental

# 4. If successful, merge to main
git checkout main && git merge experimental

# 5. Deploy main to remote
/trinity-sync push
```

## Sync Procedure

### Phase 1: Discovery

Gather state from both agents:

**Local state:**
```bash
git status
git branch -a
git log -5 --oneline
git remote -v
```

**Remote state (via MCP):**
Ask the remote agent for:
- Current branch: `git branch --show-current`
- Git status: `git status`
- Recent commits: `git log -5 --oneline`
- Any uncommitted changes

### Phase 2: Analysis

Compare the states and classify:

| Scenario | Local Status | Remote Status | Action |
|----------|-------------|---------------|--------|
| In Sync | Same HEAD, clean | Same HEAD, clean | Nothing to do |
| Local Ahead | Ahead by N commits | Behind | Push to GitHub, remote pulls |
| Remote Ahead | Behind | Ahead by N commits | Local pulls from GitHub |
| Both Changed | Uncommitted changes | Uncommitted changes | Review diffs, decide winner |
| Diverged | Different commits | Different commits | Merge required (rare) |
| Different Branches | On branch X | On branch Y | Branch switch needed |

### Phase 3: Classify Uncommitted Changes

**Runtime state (ALWAYS discard):**
- `.claude/debug/` - Debug logs
- `.claude/projects/` - Project cache
- `.claude/statsig/` - Analytics state
- `.claude/todos/` - Temporary todos
- `session-files/` - Session work
- `content/` - Generated content
- `.npm/`, `.venv/`, `node_modules/`
- Any file in `.gitignore`

**Agent value (MUST sync - this is the agent itself):**
- `.claude/skills/` - Agent capabilities
- `.claude/agents/` - Sub-agent definitions
- `.claude/commands/` - Command definitions
- `memory/` - Schedules and persistent state
- `scripts/` - Automation scripts
- `source-of-truth/` - Business documentation
- `CLAUDE.md` - Main agent instructions
- `template.yaml` - Trinity metadata

**Deletions are suspicious** - Usually accidental, verify the content wasn't just refactored elsewhere.

### Phase 4: Execute Sync

Based on analysis and command:

**If `/trinity-sync push` (current branch):**
1. Ensure local changes are committed
2. Push: `git push origin <current-branch>`
3. Tell remote to fetch and checkout: `git fetch origin && git checkout <branch> && git pull origin <branch>`
4. Verify both at same HEAD

**If `/trinity-sync push <branch>`:**
1. Ensure local changes are committed
2. If branch doesn't exist remotely, push with tracking: `git push -u origin <branch>`
3. Otherwise: `git push origin <branch>`
4. Tell remote to fetch and checkout the branch
5. Verify both at same HEAD on specified branch

**If `/trinity-sync deploy <branch>`:**
1. Verify branch/tag exists on remote: `git ls-remote --heads --tags origin <branch>`
2. Check remote working tree is clean (or only runtime state)
3. Tell remote to: `git fetch origin && git checkout <branch> && git pull origin <branch>`
4. Verify remote is on correct branch at expected HEAD

**If `/trinity-sync pull`:**
1. Discard any local runtime changes: `git checkout -- .`
2. Pull: `git pull origin <current-branch>`
3. Verify at same HEAD as remote

**If both have uncommitted changes:**
1. Compare the diffs
2. Determine which changes are meaningful vs accidental
3. Winner keeps changes, loser discards
4. Commit meaningful changes
5. Push/pull to sync

### Phase 5: Verification

Confirm both agents report:
- Same branch checked out
- Same HEAD commit hash
- Clean working tree (or only runtime state uncommitted)

## Branch Operations

### List Branches

```bash
# Local branches
git branch

# Remote branches
git branch -r

# All branches with last commit
git branch -av
```

### Create and Push New Branch

```bash
# Create locally
git checkout -b <branch-name>

# Push with tracking
git push -u origin <branch-name>
```

### Deploy Existing Branch to Remote

The remote agent needs to:
1. Stash or discard runtime changes
2. Fetch latest from origin
3. Checkout the target branch
4. Pull latest for that branch

**Remote commands (sent via MCP):**
```bash
# Discard ONLY runtime state (not skills/agents/commands/memory/scripts)
git checkout -- .claude/debug/ 2>/dev/null || true
git checkout -- .claude/projects/ 2>/dev/null || true
git checkout -- .claude/statsig/ 2>/dev/null || true
git checkout -- .claude/todos/ 2>/dev/null || true
git checkout -- session-files/ 2>/dev/null || true

# Fetch and switch
git fetch origin
git checkout <branch>
git pull origin <branch>

# Verify
git branch --show-current
git log -1 --oneline
```

**IMPORTANT:** Never discard `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, `memory/`, `scripts/`, or `source-of-truth/` - these ARE the agent's capabilities and must be synced.

### Safety Checks Before Branch Switch

Before switching branches on remote, verify:

1. **No meaningful uncommitted changes:**
   ```bash
   # Check for changes OUTSIDE runtime directories
   git status --porcelain | grep -v "^??" | \
     grep -v ".claude/debug/" | \
     grep -v ".claude/projects/" | \
     grep -v ".claude/statsig/" | \
     grep -v ".claude/todos/" | \
     grep -v "session-files/"
   ```
   If this returns changes to skills/agents/commands/memory/scripts, these are meaningful - warn before proceeding.

2. **Branch exists:**
   ```bash
   git ls-remote --heads origin <branch>
   ```
   If branch doesn't exist, offer to push it first.

3. **No merge conflicts expected:**
   Compare current HEAD with target branch for potential issues.

## GitHub Repository

Both agents sync through the shared GitHub repository. GitHub is the source of truth. All meaningful changes must be committed and pushed.

## Key Rules

1. **GitHub is source of truth** - Both agents sync through the shared repo
2. **Agent value MUST sync** - skills/, agents/, commands/, memory/, scripts/ are the agent itself
3. **Runtime files are ephemeral** - Only debug/, projects/, statsig/, todos/, session-files/ can be discarded
4. **Deletions are suspicious** - Usually accidental; verify before accepting
5. **Meaningful changes win** - Additions/improvements over deletions
6. **Fast-forward preferred** - Avoid merge commits when possible
7. **Verify after sync** - Always confirm both agents at same HEAD
8. **Clean before switch** - Only discard runtime state before branch switch
9. **Branches are cheap** - Use them liberally for experiments

## When to Run Sync

- Before starting significant work on either agent
- After completing a major task
- Weekly maintenance
- When you notice drift between agents
- After recovering from errors
- When deploying a new version or experiment

## Example Sessions

### Status Check

```
User: /trinity-sync status

Agent: Let me check the sync status...

[Queries local git status and branch]
[Queries remote agent via MCP]

Status Report:
- Local:  main @ 1cb2c9a (clean)
- Remote: main @ ced8d93 (uncommitted changes in session-files/)

Analysis: Local is 1 commit ahead. Remote has uncommitted runtime changes.

Recommendation: Remote should discard runtime changes and pull.
Run `/trinity-sync push` to execute.
```

### Deploy Experimental Branch

```
User: /trinity-sync deploy experimental

Agent: Deploying 'experimental' branch to remote...

[Verifies branch exists on origin]
[Checks remote working tree status]
[Sends checkout commands to remote agent]

Deployment Complete:
- Remote switched from: main @ ced8d93
- Remote now on: experimental @ 8f3a1b2
- Status: Clean working tree

The remote agent is now running the experimental configuration.
```

### Push New Feature Branch

```
User: /trinity-sync push feature/new-skill

Agent: Pushing 'feature/new-skill' to remote...

[Checks if branch exists on remote]
Branch doesn't exist remotely. Creating...

[Pushes with tracking]
[Tells remote to fetch and checkout]

Push Complete:
- New branch created: feature/new-skill
- Local:  feature/new-skill @ 2c4f8a1
- Remote: feature/new-skill @ 2c4f8a1
- Both in sync

The remote agent is now running feature/new-skill.
```

### List Available Branches

```
User: /trinity-sync branches

Agent: Fetching branch information...

Local Branches:
  * main              1cb2c9a Migrate google-workspace agent
    experimental      8f3a1b2 Test new workflow
    feature/new-skill 3d5e7f9 WIP: Adding skill X

Remote Branches (origin):
    main              1cb2c9a Migrate google-workspace agent
    experimental      8f3a1b2 Test new workflow

Remote Agent Status:
    Currently on: main @ 1cb2c9a
```
