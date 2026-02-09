---
name: commit
description: Create a meaningful git commit to checkpoint current agent state. Use when the user says "commit", "save changes", "checkpoint", "commit my work", or asks to save progress to git.
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*), Bash(git log:*)
argument-hint: [optional commit message]
---

# Commit Agent State

Create a meaningful git commit to checkpoint the current agent state. Run once per session at natural breakpoints or session end.

## Quick Start

```bash
# Check current status
git status

# Stage and commit with auto-generated message
git add memory/ .claude/memory/ outputs/ CLAUDE.md template.yaml 2>/dev/null || true
git commit -m "Update agent state"
```

## Workflow

### 1. Review Changes

Analyze what files have been modified:

```bash
git status
git diff --cached --stat  # Staged changes
git diff --stat           # Unstaged changes
git log --oneline -5      # Recent commits for style reference
```

### 2. Stage Appropriate Files

**Stage these directories:**
- `memory/` - Agent's persistent state
- `.claude/memory/` - Claude-specific memory
- `outputs/` - Generated content
- `CLAUDE.md` - Agent instruction updates
- `template.yaml` - Configuration changes

**NEVER stage these files:**
- `.mcp.json` - Contains credentials
- `.env` - Contains credentials
- `*.log` - Temporary logs
- Any files with API keys or secrets

```bash
git add memory/ .claude/memory/ outputs/ CLAUDE.md template.yaml 2>/dev/null || true
```

### 3. Create Commit

If user provided a message via arguments, use that. Otherwise, analyze changes and create a descriptive message:

**Good commit message examples:**
- "Update schedule.json with 5 new LinkedIn posts"
- "Add memory context from content planning session"
- "Update CLAUDE.md with new workflow documentation"

**Format guidelines:**
- Keep subject line under 72 characters
- Summarize what was accomplished (the "why")
- Use conventional commit format if appropriate

```bash
git commit -m "Your message here"
```

### 4. Show Results

After committing, report:
- The commit hash
- Summary of what was committed
- Any files that were intentionally skipped

## Commit Message Examples

| Change Type | Message Example |
|-------------|-----------------|
| Schedule updates | "Update schedule.json with 5 new LinkedIn posts" |
| Memory updates | "Add memory context from content planning session" |
| Config changes | "Update CLAUDE.md with new workflow documentation" |
| State sync | "Sync: YYYY-MM-DD HH:MM:SS" |
| Multi-file | "Update agent state: schedule, replies, memory" |

## Error Handling

**No changes to commit:**
- Show "Nothing to commit, working tree clean"
- Don't create empty commits

**Sensitive files detected:**
- Warn user if staging .env, .mcp.json, or credential files
- Do NOT commit without explicit approval

**Commit fails:**
- Show error message
- Suggest checking git status
