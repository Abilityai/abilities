---
name: release
description: Cut a release — runs the pre-release checklist, bumps the version, generates release notes, creates and tags the release PR. Recommended to run after all in-dev issues are confirmed shippable.
allowed-tools: Bash, Read, Write, Grep
user-invocable: true
argument-hint: "[version-tag]"
automation: gated
---

# Release

Automate the release cut process: pre-release checklist, version bump, release notes, PR creation, and tagging.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | GitHub repo | ✅ | ✅ | In-dev issues to close |
| Git log | current branch | ✅ | | Commits since last release |
| Version file | `pyproject.toml`, `package.json`, etc. | ✅ | ✅ | Version bump |
| Changelog | `docs/memory/changelog.md` | ✅ | ✅ | Release notes |

## Arguments

- `$ARGUMENTS`: Version tag (e.g., `v1.2.0`, `cli-v0.4.0`). If omitted, suggests next version based on git tags.

## Process

### Step 1: Determine Version

If no version argument provided:
```bash
# Get latest tag
git describe --tags --abbrev=0 2>/dev/null || echo "No tags yet"
```

Suggest next version following semver. Confirm with user before continuing.

### Step 2: Pre-Release Checklist

Run validation gates. Do NOT proceed if any CRITICAL item fails.

```bash
# 1. No open P0 issues
gh issue list --label "priority-p0" --state open --json number,title

# 2. No open P1 issues that are blocking
gh issue list --label "priority-p1,status-blocked" --state open --json number,title

# 3. Tests pass
# (invoke test-runner or check CI status)
gh run list --limit 5 --json status,conclusion,name
```

Present checklist:
```markdown
## Pre-Release Checklist

- [ ] No open P0 issues
- [ ] No blocked P1 issues  
- [ ] Tests passing (CI green)
- [ ] In-dev issues confirmed shippable
```

**GATE**: Ask user to confirm checklist before continuing.

### Step 3: Collect In-Dev Issues

```bash
gh issue list --label "status-in-dev" --state open --json number,title
```

These issues will be closed by the release PR via `Closes #N`.

### Step 4: Generate Release Notes

```bash
# Commits since last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  git log ${LAST_TAG}..HEAD --oneline --no-merges
else
  git log --oneline --no-merges -20
fi
```

Format release notes:

```markdown
## Release [version] — [date]

### What's in this release
[group commits by type: features, fixes, refactors, docs]

### Issues closed
Closes #N #M #P ...
```

### Step 5: Update Changelog

Prepend the release notes to `docs/memory/changelog.md`.

### Step 6: Commit Release Prep

```bash
git add docs/memory/changelog.md
git commit -m "chore: release $VERSION"
```

### Step 7: Create Release PR

```bash
gh pr create \
  --title "Release $VERSION" \
  --body "$(cat release-notes.md)" \
  --base main
```

**GATE**: Show the PR URL and ask:
> "PR created at [url]. Review it, then tell me to tag when ready."

### Step 8: Tag After Merge

After user confirms the PR is merged:

```bash
git checkout main
git pull
git tag $VERSION
git push --tags
```

### Step 9: Summary

```markdown
## Release Complete: [version]

| Step | Status |
|------|--------|
| Pre-release checklist | ✅ |
| Release notes generated | ✅ |
| Changelog updated | ✅ |
| PR created | ✅ #[pr-number] |
| Tag pushed | ✅ [version] |
| Issues to close | #N, #M, #P (auto-closes on PR merge) |
```

## Completion Checklist

- [ ] Version determined
- [ ] Pre-release checklist passed
- [ ] In-dev issues collected
- [ ] Release notes generated
- [ ] Changelog updated
- [ ] Release PR created
- [ ] Tag pushed after merge
