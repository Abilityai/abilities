---
name: sync-ops-knowledge
description: Keep an ops agent's documentation current with codebase changes. Reviews recent commits in a managed codebase, analyzes operational impact (new config vars, API changes, schema changes), and proposes CLAUDE.md or skill updates. Use periodically or after a new release.
disable-model-invocation: false
user-invocable: true
argument-hint: "[repo-path or --since=7d]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Sync Ops Knowledge

Review recent changes in a managed codebase and update the ops agent's documentation to reflect new operational requirements. Ensures the agent stays current without modifying application code.

---

## Use Case

An ops agent manages a service it doesn't control — it can't modify the source code, but it needs to know:
- New environment variables that must be configured on deploy
- Changed API endpoints that health checks or scripts rely on
- New Docker services or removed services
- Schema migrations that affect backup/restore procedures
- New configuration options the agent should advise on

This skill reviews git history and proposes documentation updates.

---

## Prerequisites

```bash
# Path to the managed codebase (read-only — never modify)
MANAGED_REPO=${MANAGED_REPO:-""}  # e.g. ~/app or a local clone

# Optional: days of history to review (default: 7)
SINCE_DAYS=${SINCE_DAYS:-7}
```

Or SSH-based review of a remote repo:

```bash
SSH_HOST=${SSH_HOST:-""}
SSH_USER=${SSH_USER:-"ubuntu"}
SSH_KEY=${SSH_KEY:-"~/.ssh/id_rsa"}
APP_PATH=${APP_PATH:-"~/app"}
RUN="ssh -i $SSH_KEY $SSH_USER@$SSH_HOST"
```

Parse `$ARGUMENTS` for `--since=Nd` or a repo path.

---

## Step 1: Get Recent Commits

**Local repo:**

```bash
cd $MANAGED_REPO
git log --oneline --since="${SINCE_DAYS} days ago" | head -50
```

**Remote repo:**

```bash
$RUN "cd $APP_PATH && git log --oneline --since='${SINCE_DAYS} days ago' | head -50"
```

Display commit list to user. If no commits in the window, say so and exit.

---

## Step 2: Analyze Each Commit for Ops Impact

For each commit, check what files changed:

```bash
# Local
git show --stat [commit-hash]

# Remote
$RUN "cd $APP_PATH && git show --stat [commit-hash]"
```

**Flag commits that touch ops-relevant files:**

| File pattern | Ops relevance |
|---|---|
| `docker-compose*.yml` | Service changes, new ports, new services |
| `Dockerfile*` | Base image changes, new dependencies |
| `.env.example`, `.env.template` | New required environment variables |
| `requirements*.txt`, `pyproject.toml`, `package.json` | Dependency changes (rebuild required?) |
| `**/migrations/**`, `**/schema*` | Database schema changes |
| `**/health*` | Health check endpoint changes |
| `**/api/**routes*` | API changes scripts may depend on |
| `nginx.conf`, `*.conf` | Config changes |
| `CHANGELOG*`, `RELEASE*` | Official release notes |

Deeply analyze only the flagged commits.

---

## Step 3: Extract Operational Changes

For each flagged commit, read the diff:

```bash
# Local
git show [commit-hash] -- [file]

# Remote
$RUN "cd $APP_PATH && git show [commit-hash] -- [file]"
```

Extract and categorize findings:

### New Environment Variables

Look for new `os.getenv(`, `os.environ[`, `process.env.`, or additions to `.env.example`:

```bash
# Local
git show [commit-hash] -- .env.example | grep "^+" | grep -v "^+++"

# Remote
$RUN "cd $APP_PATH && git show [commit-hash] -- .env.example 2>/dev/null | grep '^+' | grep -v '^+++'"
```

For each new var: Is it required or optional? What does it control?

### New or Removed Docker Services

```bash
git show [commit-hash] -- docker-compose*.yml | grep -E "^\+\s+[a-z].*:" | grep -v "image:|ports:|volumes:|environment:"
```

### Changed Health/API Endpoints

```bash
git show [commit-hash] | grep -E "^\+.*(/health|/api/|/status)" | head -20
```

### Schema Changes

```bash
# Look for migration files
git show --stat [commit-hash] | grep -i "migrat"
```

### Breaking Changes

Look for indicators:
- Config renames (old var removed, new var added)
- Service renames
- Port changes
- Auth mechanism changes

---

## Step 4: Assess Current Documentation

Read the ops agent's own docs:

```bash
# Current CLAUDE.md
cat CLAUDE.md | head -200

# Relevant skill files
ls .claude/skills/ 2>/dev/null || ls skills/ 2>/dev/null
```

Cross-reference findings against what's already documented.

---

## Step 5: Generate Change Report

Produce a structured report:

```markdown
# Ops Knowledge Sync — [DATE]

**Period reviewed:** Last N days ([FROM] → [TO])
**Commits reviewed:** N total, N flagged for ops relevance

## Changes Requiring Documentation Updates

### New Environment Variables
- `NEW_VAR_NAME` — [what it does, required/optional, default value if any]
  - Added in: [commit hash and message]
  - Action needed: Add to instance `.env` template and deployment checklist

### New/Removed Services
- Added: `service-name` — [port, purpose]
- Removed: `old-service` — [confirm removal from health checks]

### API/Endpoint Changes
- `GET /health` now returns `{status, version, uptime}` — update health check parsing
- ...

### Schema Changes
- Migration `YYYY_add_column.sql` adds column X to table Y — backup before next deploy

### Breaking Changes (Action Required)
- `OLD_VAR` renamed to `NEW_VAR` — must update all instance .env files before deploy

## No-Action Changes

[Commits reviewed but no ops impact found]

## Recommended Documentation Updates

1. [ ] Update CLAUDE.md: [specific section]
2. [ ] Update deploy checklist: [what to add]
3. [ ] Update health check scripts: [what to change]
4. [ ] Update `.env.example` or instance templates: [new vars]
```

---

## Step 6: Propose and Apply Updates

Present the report to the user. For each recommended update:

1. Show the current documentation section
2. Show the proposed change (diff format)
3. Ask: "Apply this update? (yes/skip)"

Apply only approved changes using Edit tool.

**Never modify the managed codebase** — only update the ops agent's own files (CLAUDE.md, skills, `.env` templates, checklists).

---

## Step 7: Record Sync

Append to a sync log:

```bash
echo "$(date +%Y-%m-%d): synced ${SINCE_DAYS}d of commits, N changes applied" >> .ops-sync-log
```

Report to user:
- Commits reviewed
- Changes found
- Updates applied
- Next suggested sync date

---

## Tips

- **Run after each release** or at a regular cadence (weekly for fast-moving repos)
- **Pair with a heartbeat schedule** to run automatically
- **Focus on breaking changes** — new env vars and schema migrations are the highest-risk gaps
- The goal is to catch operational requirements *before* a deploy fails because of them

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [safe-deploy](../safe-deploy/) | Apply a deployment with the updated knowledge |
| [investigate-incident](../investigate-incident/) | Investigate if a sync was missed and something broke |
