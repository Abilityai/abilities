---
name: publish
description: Push committed changes to remote repository. Use when the user says "publish", "push changes", "push to remote", "deploy", or needs to push local commits to GitHub/origin.
allowed-tools: Bash(git push:*), Bash(git status:*), Bash(git log:*), Bash(git remote:*)
---

# Publish Agent State

Push all committed local changes to the remote GitHub repository.

## Quick Start

```bash
# Check and push
git status --short
git log --oneline origin/main..HEAD 2>/dev/null
git push origin main
```

## Workflow

### Step 1: Pre-Push Checks

**Check for uncommitted changes:**
```bash
git status --short
```

If uncommitted changes exist:
- Warn the user
- Suggest running `/commit` first
- Do NOT proceed until acknowledged

**Check for unpushed commits:**
```bash
git log --oneline origin/main..HEAD 2>/dev/null || echo "No unpushed commits"
```

If no commits to push:
- Inform user: "Nothing to push - already in sync with remote"
- Exit early

### Step 2: Show What Will Be Pushed

```bash
git log --oneline origin/main..HEAD
```

Display:
- Number of commits
- Brief summary of each commit
- Ask for confirmation if >5 commits

### Step 3: Push to Remote

```bash
git push origin main
```

## Post-Push Report

After successful push, confirm:
- Commits pushed successfully
- Remote repository URL
- Current sync status

```
Published successfully:
- Pushed: 3 commits to origin/main
- Repository: github.com/user/repo
- Status: In sync with remote
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Push rejected | Remote has new commits | Run `/sync` instead |
| Authentication failed | SSH key or credentials issue | Check git remote configuration |
| Permission denied | No write access | Verify repository permissions |

**If push is rejected:**
```
Push was rejected - remote has new commits.

Solution: Run /sync to pull changes first, then push.
```

## Safety Notes

- **Never force push** to main/master
- Always show what commits will be pushed before pushing
