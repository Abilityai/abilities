---
name: commit
description: Commit changed skill files and close the in-progress issue — writes a traceability commit message referencing the issue number
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Commit

Stage changed skill files, write a commit message tied to the in-progress issue, and close the issue with a summary. The single action that closes the loop between a GitHub issue and a SKILL.md change.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | Yes | Close the in-progress issue |
| Git working tree | ./ | Yes | Yes | Stage and commit skill files |

## Prerequisites

- `gh` CLI authenticated
- Git repo with at least one commit (not bare)
- Work is in-progress (a claimed issue exists)

## Process

### Step 1: Find the In-Progress Issue

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 5
```

If an issue number was passed as `$ARGUMENTS`, use that instead.

If multiple in-progress issues, ask which one this commit closes.

### Step 2: Check for Changes

```bash
git status --short
```

Surface all modified, added, or deleted files. Flag anything that is NOT a SKILL.md or agent configuration file (CLAUDE.md, template.yaml) — confirm the user wants to include it.

If there are no changes at all: report "Nothing to commit. Did `/adjust-playbook` or `/create-playbook` run yet?"

### Step 3: Stage Files

Stage all changed agent files:

```bash
git add .claude/skills/
git add CLAUDE.md  # if modified
```

If other files were modified, confirm before staging.

Show the staged diff summary:

```bash
git diff --cached --stat
```

### Step 4: Compose Commit Message

Derive the commit message from the issue:

- If the issue has a `skill:*` label: `[$SKILL_NAME]: $SHORT_DESCRIPTION (closes #$NUMBER)`
- If project-level: `[agent]: $SHORT_DESCRIPTION (closes #$NUMBER)`
- Short description = condensed version of issue title (lowercase, imperative)

Examples:
- `[adjust-playbook]: detect breaking interface changes (closes #14)`
- `[work-loop]: route skill issues by label (closes #3)`
- `[agent]: update onboarding section in CLAUDE.md (closes #1)`

Show the message and ask for confirmation or edits.

### Step 5: Commit

```bash
git commit -m "$(cat <<'EOF'
$COMMIT_MESSAGE
EOF
)"
```

### Step 6: Close the Issue

Add a completion comment:

```bash
gh issue comment $NUMBER --body "## Completed

$SUMMARY_FROM_DIFF

Committed: \`$COMMIT_SHA\`

---
*Closed via /commit*"
```

Update labels and close:

```bash
gh issue edit $NUMBER --remove-label "status:in-progress" --add-label "status:done"
gh issue close $NUMBER --reason completed
```

### Step 7: Confirm

```
## Committed and Closed

Commit: $COMMIT_SHA
Issue: #$NUMBER closed — $TITLE

Next: `/backlog` or `/claim` for the next issue.
```

## Outputs

- Git commit with issue-linked message
- Issue labeled `status:done` and closed
- Summary comment on the issue

## Error Handling

| Error | Action |
|-------|--------|
| Nothing staged | Report, ask if /adjust-playbook ran |
| No in-progress issue | Ask for issue number |
| Commit fails | Show error, do not close issue |
| Issue close fails | Report — commit already done, close manually |
