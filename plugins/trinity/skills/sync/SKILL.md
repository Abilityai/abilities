---
name: sync
description: Synchronize this agent with one or more remote instances on Trinity via GitHub. Supports multiple remotes and branch-based versioning.
argument-hint: "[status|push|pull|deploy|remotes|add-remote|set-default|schedules] [@remote] [branch]"
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash, Read, Write, Grep, Glob, mcp__trinity__list_agents, mcp__trinity__chat_with_agent, mcp__trinity__list_operator_queue, mcp__trinity__get_operator_queue_item, mcp__trinity__list_agent_schedules, mcp__trinity__create_agent_schedule, mcp__trinity__update_agent_schedule, mcp__trinity__toggle_agent_schedule
metadata:
  version: "2.3.0"
  created: 2025-02-05
  author: eugene
  changelog:
    - "2.3.0: Unified remote registry — sync's config is now `.trinity-remote.yaml` (was `.trinity-sync.yaml`), the same file `/trinity:onboard` writes and `/trinity:loop` reads. Fixes the onboard→sync handoff (sync now resolves the agent name onboard recorded instead of re-guessing). Schema gains onboard's machine-maintained `instance`/`profile`/`deployed_at` fields; migrates legacy single-remote files in place"
    - "2.2.0: Schedule reconciliation (Phase 7) — diff template.yaml schedules: against live Trinity schedules on push/pull/deploy/status; new `schedules` subcommand to reconcile on demand"
    - "2.1.1: Quote argument-hint — unquoted brackets broke YAML frontmatter, making the skill invisible"
    - "2.1: After syncing a remote, check its Operating Room queue and report any open ops notifications"
    - "2.0: Multi-remote support - one local agent can sync to multiple Trinity instances"
    - "1.1: Genericized - works with any agent via dynamic name detection"
    - "1.0: Initial version"
---

# Agent Synchronization Skill

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `sync vX.Y — recent: <summary>`. Then proceed.

Synchronize the local agent with one or more remote instances on Trinity. Supports multiple remotes (e.g., production, staging, development) and branch-based versioning.

## Multi-Remote Architecture

A single local agent can have multiple remote counterparts on Trinity:

```
┌─────────────────────┐
│   LOCAL AGENT       │
│   (development)     │
└─────────┬───────────┘
          │
    ┌─────┴─────┬──────────────┐
    ▼           ▼              ▼
┌────────┐ ┌─────────┐ ┌──────────────┐
│ prod   │ │ staging │ │ dev          │
│ @main  │ │ @staging│ │ @experimental│
│ ───────│ │ ────────│ │ ─────────────│
│my-agent│ │my-agent │ │my-agent-dev  │
│        │ │-staging │ │              │
└────────┘ └─────────┘ └──────────────┘
   Trinity Platform Instances
```

## Configuration

Remote instances are configured in `.trinity-remote.yaml` at the agent root. This is the **single registry of this agent's remote Trinity instances** — the same file `/trinity:onboard` writes at deploy time and `/trinity:loop` reads to find its remote counterpart. Sync owns the multi-remote and branch fields; onboard maintains the deploy-tracking fields (`instance`, `profile`, `deployed_at`).

```yaml
# .trinity-remote.yaml
#   Remote Trinity instances of this agent.
#   instance / profile / deployed_at are machine-maintained by onboard — safe to leave as-is.
default: prod  # Which remote to use when none specified

remotes:
  prod:
    agent: my-agent                       # Trinity agent name        (sync)
    branch: main                          # Branch this remote tracks (sync)
    instance: https://trinity.example.com # Trinity URL deployed on    (onboard)
    profile: default                      # CLI profile to reach it    (onboard)
    deployed_at: 2026-06-16T12:00:00Z     # Last deploy, ISO 8601      (onboard)
    description: Production instance

  staging:
    agent: my-agent-staging
    branch: staging
    description: Staging for testing

  dev:
    agent: my-agent-dev
    branch: experimental
    description: Development/experimental
```

Only `agent` is required per remote; `branch` defaults to `main`, and the onboard fields are optional (present once the remote has been deployed to). Sync never needs `instance`/`profile`/`deployed_at` and leaves them untouched.

**Legacy single-remote file:** Older `.trinity-remote.yaml` files written by onboard had top-level `agent:`/`instance:` keys and no `remotes:` block. When you encounter that shape, fold it into the unified form as the `default` remote (preserve its `agent`/`instance`/`profile`/`deployed_at`) before proceeding.

**If no config exists:** Falls back to auto-detection (template.yaml name or directory name) as a single "default" remote.

## Quick Commands

### Status & Discovery
- `/trinity-sync` or `/trinity-sync status` - Show all remotes and their sync status
- `/trinity-sync status @prod` - Check status of specific remote
- `/trinity-sync remotes` - List configured remotes
- `/trinity-sync branches` - List available branches (local and remote)

### Syncing
- `/trinity-sync push` - Push to default remote on its tracked branch
- `/trinity-sync push @staging` - Push to staging remote
- `/trinity-sync push @prod main` - Push main branch to prod remote
- `/trinity-sync pull` - Pull from default remote
- `/trinity-sync pull @staging` - Pull from staging remote

### Deployment
- `/trinity-sync deploy experimental` - Deploy branch to default remote
- `/trinity-sync deploy @staging experimental` - Deploy branch to specific remote

### Configuration
- `/trinity-sync add-remote <name> <agent-name> [branch]` - Add a new remote
- `/trinity-sync set-default <name>` - Change default remote
- `/trinity-sync remove-remote <name>` - Remove a remote configuration

### Schedules
- `/trinity-sync schedules` - Reconcile `template.yaml` schedules against the default remote's live schedules
- `/trinity-sync schedules @staging` - Reconcile schedules on a specific remote

## Arguments

$ARGUMENTS

## Remote Resolution

When a command is executed, resolve the target remote:

1. **Explicit `@remote`**: Use that remote's config
2. **Environment variable**: `TRINITY_SYNC_TARGET=staging`
3. **Default from config**: The `default:` field in `.trinity-remote.yaml`
4. **Auto-detect**: If no config exists, detect from template.yaml or directory name

```bash
# Resolution order
resolve_remote() {
  if [[ "$1" =~ ^@ ]]; then
    echo "${1#@}"  # Strip @ prefix
  elif [[ -n "$TRINITY_SYNC_TARGET" ]]; then
    echo "$TRINITY_SYNC_TARGET"
  elif [[ -f .trinity-remote.yaml ]]; then
    grep "^default:" .trinity-remote.yaml | cut -d: -f2 | tr -d ' '
  else
    echo "default"  # Will use auto-detection
  fi
}
```

## Configuration File Procedures

### Load Configuration

```bash
# Check for config file
if [[ -f .trinity-remote.yaml ]] && grep -q "^remotes:" .trinity-remote.yaml; then
  # Unified multi-remote format
  # Each remote has: agent, branch, description (+ onboard's instance/profile/deployed_at)

  # Get default remote
  DEFAULT_REMOTE=$(grep "^default:" .trinity-remote.yaml | cut -d: -f2 | tr -d ' ')

  # Get list of remote names
  REMOTES=$(grep "^  [a-z].*:$" .trinity-remote.yaml | sed 's/://g' | tr -d ' ')
elif [[ -f .trinity-remote.yaml ]] && grep -q "^agent:" .trinity-remote.yaml; then
  # LEGACY single-remote file from an older onboard (top-level agent/instance, no remotes:).
  # Migrate it in place: wrap the single remote as the "default" before continuing.
  AGENT_NAME=$(grep "^agent:" .trinity-remote.yaml | cut -d: -f2 | tr -d ' ')
  DEFAULT_REMOTE="default"
  # Rewrite into unified form, preserving instance/profile/deployed_at as the default remote's fields.
  # (Offer this migration to the user; don't discard the deploy-tracking fields.)
else
  # No config - create implicit default from auto-detection
  if [[ -f template.yaml ]]; then
    AGENT_NAME=$(grep "^name:" template.yaml | cut -d: -f2 | tr -d ' ')
  else
    AGENT_NAME=$(basename "$(pwd)")
  fi

  # Check env override
  [[ -n "$TRINITY_AGENT_NAME" ]] && AGENT_NAME="$TRINITY_AGENT_NAME"

  DEFAULT_REMOTE="default"
  # Implicit single remote: agent=$AGENT_NAME, branch=current
fi
```

### Create Default Config

When running `/trinity-sync add-remote` with no existing config, create one:

```yaml
# Auto-generated .trinity-remote.yaml
default: prod

remotes:
  prod:
    agent: {detected-agent-name}
    branch: main
    description: Primary production instance
```

### Add Remote Procedure

`/trinity-sync add-remote <name> <agent-name> [branch]`

1. Load or create `.trinity-remote.yaml`
2. Verify remote name doesn't already exist
3. Verify agent exists on Trinity: `mcp__trinity__list_agents`
4. Add new remote entry:
   ```yaml
   <name>:
     agent: <agent-name>
     branch: <branch|main>
     description: Added via trinity-sync
   ```
5. If this is the first explicit remote, set as default

### Remove Remote Procedure

`/trinity-sync remove-remote <name>`

1. Verify remote exists in config
2. If removing default, require new default to be specified
3. Remove the remote entry
4. Update config file

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

### Phase 0: Remote Resolution

Before any operation, resolve which remote(s) to target:

```
1. Parse command for @remote specifier
2. Load .trinity-remote.yaml (if exists)
3. Resolve target remote:
   - Explicit @remote → use that config
   - $TRINITY_SYNC_TARGET → use that
   - Config default → use that
   - No config → auto-detect single remote

4. Extract remote config:
   - agent_name: Trinity agent name
   - tracked_branch: Branch this remote should track
   - description: For display
```

**For status without @remote:** Show ALL configured remotes.

### Phase 1: Discovery

Gather state from local and target remote(s):

**Local state:**
```bash
git status
git branch -a
git log -5 --oneline
git remote -v
```

**Remote state (via MCP):**
For each targeted remote, query the Trinity agent:
- Current branch: `git branch --show-current`
- Git status: `git status`
- Recent commits: `git log -5 --oneline`
- Any uncommitted changes

**Multi-remote status display:**
```
Remote Status Summary
─────────────────────────────────────────────────
 Remote     Agent              Branch    Status
─────────────────────────────────────────────────
 prod*      my-agent           main      ✓ In sync @ abc1234
 staging    my-agent-staging   staging   ↑ Local ahead by 2 commits
 dev        my-agent-dev       feature/x ✗ Remote has uncommitted changes
─────────────────────────────────────────────────
* = default remote
```

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

Based on analysis, command, and target remote:

**If `/trinity-sync push` or `/trinity-sync push @remote`:**
1. Resolve target remote (default if not specified)
2. Get remote's tracked branch from config
3. Ensure local changes are committed
4. Push: `git push origin <tracked-branch>`
5. Tell remote agent to fetch and checkout:
   ```
   mcp__trinity__chat_with_agent(
     agent_name: <remote.agent>,
     message: "git fetch origin && git checkout <tracked-branch> && git pull origin <tracked-branch>"
   )
   ```
6. Verify both at same HEAD

**If `/trinity-sync push @remote <branch>`:**
1. Resolve target remote
2. Ensure local changes are committed on specified branch
3. If branch doesn't exist remotely: `git push -u origin <branch>`
4. Otherwise: `git push origin <branch>`
5. Tell remote agent to fetch and checkout the branch
6. **Update remote config** if branch differs from tracked:
   - Ask: "Update @remote to track <branch>? (y/n)"
   - If yes, update `.trinity-remote.yaml`

**If `/trinity-sync deploy <branch>` or `/trinity-sync deploy @remote <branch>`:**
1. Resolve target remote
2. Verify branch/tag exists: `git ls-remote --heads --tags origin <branch>`
3. Check remote working tree is clean (or only runtime state)
4. Tell remote to: `git fetch origin && git checkout <branch> && git pull origin <branch>`
5. Verify remote is on correct branch at expected HEAD
6. Update remote's tracked branch in config

**If `/trinity-sync pull` or `/trinity-sync pull @remote`:**
1. Resolve target remote
2. Get the remote's current branch
3. Discard any local runtime changes: `git checkout -- .`
4. Pull: `git pull origin <remote-branch>`
5. Verify at same HEAD as remote

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

### Phase 6: Operator Queue Check

After syncing a remote (push/pull/deploy) — and for each remote shown in a `status` check — review the agent's Operating Room queue and surface any items awaiting human attention.

For each targeted remote, using its resolved Trinity agent name:

```
mcp__trinity__list_operator_queue(agent_name: <remote.agent>)
```

Treat items that are not already resolved/closed as **open**. For each open item, optionally fetch detail with `mcp__trinity__get_operator_queue_item(<id>)` to summarize what it needs.

Report back to the user:
- **No open items:** one line — `✓ Operating Room: no open notifications for <remote>`
- **Open items:** list them so the user can act:

```
⚠ Operating Room: <N> open notification(s) for <remote> (<agent>)
  • [<id>] <title/summary> — <status>
  • [<id>] <title/summary> — <status>
```

This is report-only — the sync skill never resolves or answers queue items; it just makes the user aware they exist.

## Phase 7: Schedule Reconciliation

Schedules are declared in `template.yaml` under a `schedules:` block (the design source of truth — schema defined in `/trinity:onboard` Step 3a) and materialized as live cron jobs on each Trinity instance. They drift: someone edits `template.yaml`, or an operator adds/removes a schedule on a live agent. This phase keeps the declared catalog and the live instance aligned.

**When it runs:**
- `push` / `pull` / `deploy` — after the code sync completes, reconcile the target remote's schedules (the agent's capabilities just changed; its schedules should match).
- `status` — **report only**: show declared-vs-live drift, change nothing.
- `schedules` subcommand — reconcile on demand against the resolved remote(s).

**Procedure** — for each targeted remote, using its resolved Trinity agent name:

1. **Read declared schedules** from local `template.yaml`. If there's no `schedules:` block, skip this phase entirely.
2. **List live schedules:** `mcp__trinity__list_agent_schedules(agent_name: <remote.agent>)`.
3. **Match by `id`** — the catalog `id` is stamped as a `[id]` prefix in each live schedule's `name`. Diff:

   | Case | Condition | push/pull/deploy action | status action |
   |------|-----------|-------------------------|---------------|
   | **Create** | Declared, no live match | `create_agent_schedule(...)`, `enabled` from manifest, `[id]`-prefixed name | report "would create" |
   | **Update** | Declared + live, cron/message/timezone/etc. differ | `update_agent_schedule(...)` to match manifest (never touch `enabled`) | report "would update" |
   | **In sync** | Declared + live, identical | nothing | — |
   | **Drift** | Live `[id]` not in manifest | **report, never delete** | report |

4. **Never flip `enabled` on an existing schedule** — turning schedules on/off on a live agent is the operator's decision (`toggle_agent_schedule`). The manifest's `enabled` is applied only at create time. Reconcile keeps *configuration* in sync, not *activation*.
5. **Deletions are never automatic.** A live schedule with no matching declaration is surfaced as drift for the operator to resolve (remove on the instance, or add to `template.yaml`).

**Report:**

```
Schedule Reconciliation — prod (my-agent)
─────────────────────────────────────────────────
 id              Cron        State     Action
─────────────────────────────────────────────────
 weekly-report   0 9 * * 1   enabled   ✓ in sync
 daily-digest    0 7 * * *   enabled   ↑ updated (cron changed)
 monthly-roll    0 0 1 * *   disabled  + created (operator can enable)
─────────────────────────────────────────────────
⚠ Drift: "[adhoc] manual cleanup" is live but not in template.yaml — left as-is
```

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

1. **GitHub is source of truth** - All agents sync through the shared repo
2. **Explicit remote targeting** - Use @remote to target specific instances
3. **Config over convention** - Use `.trinity-remote.yaml` for explicit control
4. **Agent value MUST sync** - skills/, agents/, commands/, memory/, scripts/ are the agent itself
5. **Runtime files are ephemeral** - Only debug/, projects/, statsig/, todos/, session-files/ can be discarded
6. **Deletions are suspicious** - Usually accidental; verify before accepting
7. **Meaningful changes win** - Additions/improvements over deletions
8. **Fast-forward preferred** - Avoid merge commits when possible
9. **Verify after sync** - Always confirm target remote at expected HEAD
10. **Clean before switch** - Only discard runtime state before branch switch
11. **Branches are cheap** - Use them liberally for experiments
12. **Track branch per remote** - Each remote can track a different branch
13. **Schedules reconcile from template.yaml** - The `schedules:` block is the source of truth; reconcile aligns live cron jobs but never toggles activation (operator's call) or deletes drift

## When to Run Sync

- Before starting significant work on any agent instance
- After completing a major task
- Weekly maintenance
- When you notice drift between any remote instances
- After recovering from errors
- When deploying a new version or experiment
- **After creating a new Trinity instance** - add it as a remote
- **When promoting changes** - push to staging, then prod

## Migration from Single to Multi-Remote

If you've been using trinity-sync without a config file:

```
User: /trinity-sync add-remote prod my-agent main

Agent: Creating .trinity-remote.yaml with initial configuration...

✓ Created config with 'prod' as default remote

Your existing workflow continues unchanged:
- `/trinity-sync push` → pushes to prod (my-agent on main)

Now you can add more remotes:
- /trinity-sync add-remote staging my-agent-staging staging
- /trinity-sync add-remote dev my-agent-dev experimental
```

## Environment Variable Override

For CI/CD or scripted usage, set `TRINITY_SYNC_TARGET`:

```bash
# Push to staging in a script
TRINITY_SYNC_TARGET=staging /trinity-sync push

# Or export for session
export TRINITY_SYNC_TARGET=dev
/trinity-sync status  # Shows dev remote
/trinity-sync push    # Pushes to dev
```

This overrides the config default but can still be overridden by explicit `@remote`.

## Example Sessions

### Multi-Remote Status Check

```
User: /trinity-sync status

Agent: Checking sync status for all remotes...

[Queries local git status]
[Queries each configured remote via MCP]

┌─────────────────────────────────────────────────────────────────┐
│ Trinity Sync Status                                             │
├─────────────────────────────────────────────────────────────────┤
│ Local: main @ 1cb2c9a (clean)                                   │
├──────────┬──────────────────┬───────────┬───────────────────────┤
│ Remote   │ Agent            │ Branch    │ Status                │
├──────────┼──────────────────┼───────────┼───────────────────────┤
│ prod*    │ my-agent         │ main      │ ✓ In sync @ 1cb2c9a   │
│ staging  │ my-agent-staging │ staging   │ ↑ Local ahead by 2    │
│ dev      │ my-agent-dev     │ feature/x │ ⚠ Uncommitted changes │
└──────────┴──────────────────┴───────────┴───────────────────────┘
* = default remote

Recommendations:
- staging: Run `/trinity-sync push @staging` to update
- dev: Remote has uncommitted runtime changes, can push anyway
```

### Status of Specific Remote

```
User: /trinity-sync status @staging

Agent: Checking staging remote...

Target: staging → my-agent-staging (tracking: staging branch)

Status Report:
- Local:   staging @ 3f5a7c2 (clean)
- Remote:  staging @ 1cb2c9a (clean, 2 commits behind)

Analysis: Local is 2 commits ahead on staging branch.
Run `/trinity-sync push @staging` to sync.
```

### Push to Specific Remote

```
User: /trinity-sync push @staging

Agent: Pushing to staging remote...

[Push to origin/staging]
[Instructing my-agent-staging to pull]

Push Complete:
- Remote: my-agent-staging
- Branch: staging
- Before: @ 1cb2c9a
- After:  @ 3f5a7c2

Staging environment updated.
```

### Deploy Different Branch to Remote

```
User: /trinity-sync deploy @dev experimental

Agent: Deploying 'experimental' branch to dev remote...

[Verifies branch exists on origin]
[Checks my-agent-dev working tree status]
⚠ Remote has uncommitted changes in session-files/ (runtime state)
[Discarding runtime state]
[Sending checkout commands to my-agent-dev]

Deployment Complete:
- Remote: my-agent-dev
- Switched from: feature/x @ abc1234
- Now on: experimental @ 8f3a1b2

Update config to track this branch? (y/n): y
Updated: dev remote now tracks 'experimental' branch.
```

### Add New Remote

```
User: /trinity-sync add-remote qa my-agent-qa staging

Agent: Adding new remote configuration...

[Verifying my-agent-qa exists on Trinity]
✓ Agent found: my-agent-qa (running)

[Updating .trinity-remote.yaml]

Added remote:
  qa:
    agent: my-agent-qa
    branch: staging
    description: QA testing environment

Current remotes: prod*, staging, dev, qa
```

### List Remotes

```
User: /trinity-sync remotes

Agent: Configured remotes:

┌──────────┬──────────────────┬───────────┬─────────────────────────┐
│ Name     │ Trinity Agent    │ Branch    │ Description             │
├──────────┼──────────────────┼───────────┼─────────────────────────┤
│ prod*    │ my-agent         │ main      │ Primary production      │
│ staging  │ my-agent-staging │ staging   │ Staging for testing     │
│ dev      │ my-agent-dev     │ experim.  │ Development/experimental│
│ qa       │ my-agent-qa      │ staging   │ QA testing environment  │
└──────────┴──────────────────┴───────────┴─────────────────────────┘
* = default remote

Set different default: /trinity-sync set-default <name>
```

### Set Default Remote

```
User: /trinity-sync set-default staging

Agent: Updating default remote...

Previous default: prod
New default: staging

Updated .trinity-remote.yaml

Now `/trinity-sync push` without @remote will target my-agent-staging.
```

### No Config Fallback

```
User: /trinity-sync status
(no .trinity-remote.yaml exists)

Agent: No sync configuration found. Using auto-detection...

Detected agent: my-agent (from template.yaml)

Status Report:
- Local:  main @ 1cb2c9a (clean)
- Remote: main @ 1cb2c9a (clean)
- ✓ In sync

Tip: Run `/trinity-sync add-remote prod my-agent main` to create explicit config.
This enables multi-remote support for staging/dev instances.
```

### List Available Branches

```
User: /trinity-sync branches

Agent: Fetching branch information...

Local Branches:
  * main              1cb2c9a Migrate google-workspace agent
    staging           3f5a7c2 Staging release
    experimental      8f3a1b2 Test new workflow
    feature/new-skill 3d5e7f9 WIP: Adding skill X

Remote Branches (origin):
    main              1cb2c9a Migrate google-workspace agent
    staging           3f5a7c2 Staging release
    experimental      8f3a1b2 Test new workflow

Remote Agent Status:
┌──────────┬──────────────────┬─────────────────────────┐
│ Remote   │ Agent            │ Currently On            │
├──────────┼──────────────────┼─────────────────────────┤
│ prod*    │ my-agent         │ main @ 1cb2c9a          │
│ staging  │ my-agent-staging │ staging @ 3f5a7c2       │
│ dev      │ my-agent-dev     │ experimental @ 8f3a1b2  │
└──────────┴──────────────────┴─────────────────────────┘
```
