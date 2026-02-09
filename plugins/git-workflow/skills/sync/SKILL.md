---
name: sync
description: Sync agent state with remote repository (pull then push). Use when the user says "sync", "sync with remote", "pull and push", "update from remote", or needs to synchronize local and remote git state.
allowed-tools: Bash(git pull:*), Bash(git push:*), Bash(git status:*), Bash(git stash:*), Bash(git log:*), Bash(git fetch:*), Bash(git rebase:*)
---

# Sync Agent State

Synchronize the local agent state with the remote GitHub repository. This performs a pull-rebase-push workflow.

## Quick Start

```bash
# Quick sync
git fetch origin && git pull --rebase origin main && git push origin main
```

## Workflow

### Step 1: Fetch and Check Status

```bash
git fetch origin
git status
git branch --show-current
git status -sb  # Remote tracking status
```

Check for unpushed commits:
```bash
git log --oneline origin/main..HEAD 2>/dev/null || echo "No remote tracking yet"
```

### Step 2: Pull Changes (with rebase)

```bash
git pull --rebase origin main
```

**If conflicts occur:**

1. List conflicting files:
   ```bash
   git diff --name-only --diff-filter=U
   ```

2. Show conflict markers in each file

3. Ask user how to resolve:
   - Keep ours
   - Keep theirs
   - Manual merge

4. After resolution:
   ```bash
   git add <resolved-files>
   git rebase --continue
   ```

### Step 3: Push Local Commits

```bash
git push origin main
```

**If push fails (rejected due to remote changes):**
1. Pull again with rebase
2. Resolve any new conflicts
3. Push again

## Safety Checks

| Check | Action |
|-------|--------|
| Uncommitted changes | Warn user, suggest `/commit` first |
| Force push requested | NEVER without explicit approval |
| Large push (>10 commits) | Show what will be pushed, confirm |

## Post-Sync Report

After successful sync, report:
- Number of commits pulled
- Number of commits pushed
- Current sync status with remote

```
Sync complete:
- Pulled: 3 commits from origin/main
- Pushed: 2 commits to origin/main
- Status: Up to date with remote
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Merge conflicts | Divergent history | Resolve manually, then continue |
| Push rejected | Remote has new commits | Pull first, then push |
| Authentication failed | SSH key or credentials | Check git remote, re-auth |
| Detached HEAD | Not on a branch | `git checkout main` |

## Important Notes

- **Never force push** without explicit user approval
- **Always show what will be pushed** before pushing
- **Warn about uncommitted changes** before sync
