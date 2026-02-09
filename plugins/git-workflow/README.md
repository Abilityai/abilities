# Git Workflow Plugin

Streamlined git workflow commands for Claude Code with built-in safety checks and best practices.

## Installation

```bash
/plugin install git-workflow@abilityai
```

## Skills

### `/commit` - Checkpoint Your Work

Create meaningful git commits to save your progress.

```
/commit                    # Auto-generate commit message from changes
/commit fix login bug      # Use provided message
```

**Safety features:**
- Never commits `.env`, `.mcp.json`, or credential files
- Skips empty commits
- Shows what will be committed before proceeding

### `/sync` - Pull and Push

Synchronize local and remote repository state using pull-rebase-push workflow.

```
/sync                      # Fetch, pull --rebase, push
```

**Safety features:**
- Warns about uncommitted changes
- Never force pushes without explicit approval
- Handles merge conflicts with guidance
- Shows commit summary before pushing

### `/publish` - Push to Remote

Push committed changes to the remote repository.

```
/publish                   # Push all committed changes
```

**Safety features:**
- Checks for uncommitted changes first
- Shows what commits will be pushed
- Suggests `/sync` if push is rejected

## Workflow Example

```
# Make some changes...
/commit add user validation

# Sync with team changes
/sync

# Or just push your commits
/publish
```

## What Gets Committed

**Included by default:**
- `memory/` - Agent state
- `.claude/memory/` - Claude-specific memory
- `outputs/` - Generated content
- `CLAUDE.md` - Project instructions
- `template.yaml` - Configuration

**Never committed:**
- `.mcp.json` - Contains credentials
- `.env` - Contains secrets
- `*.log` - Temporary logs

## License

MIT
