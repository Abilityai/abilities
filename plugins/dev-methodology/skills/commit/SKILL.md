---
name: commit
description: Commit, push, and link to GitHub Issues
allowed-tools: Bash
user-invocable: true
automation: manual
---

# Commit

Commit changes and link to relevant GitHub Issues.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Git Status | Working directory | ✅ | | Staged/unstaged changes |
| Git Log | `.git/` | ✅ | | Recent commit style |
| Git Diff | Working directory | ✅ | | Changes to commit |
| GitHub Issues | GitHub repo | ✅ | | Issue to reference |
| GitHub Labels | GitHub repo | | ✅ | Update issue status label |
| Git Commit | `.git/` | | ✅ | New commit created |
| Git Remote | Remote repository | | ✅ | Push to origin |

## Usage

```
/commit [message]
/commit closes #17
/commit fixes #23 - added validation
```

## Process

### Step 1: Check Status

```bash
git status
git diff --stat
```

### Step 2: Stage Changes

Stage specific files (avoid `.env`, credentials):
```bash
git add <files>
```

### Step 3: Commit with Issue Reference

Include issue reference in commit message when applicable:
- `Closes #N` - closes issue when merged
- `Fixes #N` - closes issue (for bugs)
- `Refs #N` - references without closing

```bash
git commit -m "$(cat <<'EOF'
<type>: <description>

<optional body>

Closes #N

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 4: Push

```bash
git push
```

### Step 5: Update Issue Status

Move issue to "Review" state per SDLC workflow:
```bash
# Remove in-progress label, add review label
gh issue edit <N> --remove-label "status-in-progress" --add-label "status-review"

# Verify
gh issue view <N> --json state,title,labels
```

Note: Only applies when issue was in `status-in-progress`. Skip if no issue reference.

## Commit Types

| Type | Use |
|------|-----|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no new feature/fix) |
| `docs` | Documentation |
| `chore` | Maintenance |

## Completion Checklist

- [ ] Changes staged (specific files, no secrets)
- [ ] Commit message follows type convention
- [ ] Issue reference included (Closes/Fixes/Refs #N)
- [ ] Co-Authored-By line present
- [ ] Push successful
- [ ] Issue moved to `status-review` (if applicable)
