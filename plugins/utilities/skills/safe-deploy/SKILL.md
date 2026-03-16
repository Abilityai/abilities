---
name: safe-deploy
description: Safe deployment workflow for SSH-accessible docker-compose stacks. Subcommands: update (backup→pull→rebuild→restart→validate), rollback (revert commit + optional DB restore), diagnose (health analysis). Use when deploying, rolling back, or checking deployment health.
disable-model-invocation: false
user-invocable: true
argument-hint: "[update|rollback|diagnose]"
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Safe Deploy

Safe deployment operations for docker-compose-based services over SSH. Three subcommands covering the full deploy lifecycle.

---

## Prerequisites

Configure via environment variables or a local `.env` file:

```bash
SSH_HOST=<ip or hostname>
SSH_USER=<username, default: ubuntu>
SSH_KEY=<path to key, default: ~/.ssh/id_rsa>
APP_PATH=<remote app directory, default: ~/app>
COMPOSE_FILE=<compose file, default: docker-compose.yml>
BACKUP_DIR=<backup directory on remote, default: ~/backups>
DB_PATH=<path to database file, default: ~/app/app.db>
```

Connection setup (used in all subcommands):

```bash
source .env 2>/dev/null || true
SSH_HOST=${SSH_HOST:-""}
SSH_USER=${SSH_USER:-"ubuntu"}
SSH_KEY=${SSH_KEY:-"~/.ssh/id_rsa"}
APP_PATH=${APP_PATH:-"~/app"}
COMPOSE=${COMPOSE_FILE:-"docker-compose.yml"}
BACKUP_DIR=${BACKUP_DIR:-"~/backups"}
DB_PATH=${DB_PATH:-"$APP_PATH/app.db"}
RUN="ssh -i $SSH_KEY $SSH_USER@$SSH_HOST"
```

If `SSH_HOST` is empty, check for a `scripts/run.sh` wrapper.

---

## Subcommand: `update`

Full deployment: backup → pull → rebuild → restart → validate.

### Step U1: Pre-deploy Check

Check for running long-lived processes before proceeding:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps --format json 2>/dev/null | grep -c running || docker compose -f $COMPOSE ps | grep -c Up"
```

Warn the user if active processes are running. Ask: "Proceed with deployment? Active processes may be interrupted."

Check disk space before proceeding:

```bash
$RUN "df -h $APP_PATH | tail -1 | awk '{print \$5}'"
```

If disk usage >85%, warn the user.

### Step U2: Backup Database

Create a timestamped backup before any changes:

```bash
BACKUP_TS=$(date +%Y-%m-%d-%H%M%S)
$RUN "mkdir -p $BACKUP_DIR && cp $DB_PATH $BACKUP_DIR/app-${BACKUP_TS}.db 2>/dev/null && echo 'backup: ok' || echo 'backup: skipped (no DB found)'"
```

Record the current git commit for rollback reference:

```bash
PREV_COMMIT=$($RUN "cd $APP_PATH && git rev-parse HEAD")
echo "Previous commit: $PREV_COMMIT"

# Also capture the new commit after pull (used in deploy log)
# NEW_COMMIT set after Step U3
```

### Step U3: Pull Latest Code

```bash
$RUN "cd $APP_PATH && git fetch origin && git pull --ff-only"
```

Show what changed:

```bash
NEW_COMMIT=$($RUN "cd $APP_PATH && git rev-parse HEAD")
$RUN "cd $APP_PATH && git log --oneline ${PREV_COMMIT}..HEAD"
```

### Step U4: Rebuild

Check if docker base images or dependencies changed. If so, rebuild:

```bash
# Check if Dockerfile or requirements changed
$RUN "cd $APP_PATH && git diff ${PREV_COMMIT}..HEAD --name-only | grep -E 'Dockerfile|requirements|package.json|pyproject' | head -5"
```

If dependency files changed, do a full rebuild:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE build --no-cache"
```

Otherwise, a lighter rebuild:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE build"
```

### Step U5: Restart Services

Graceful restart:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE up -d --remove-orphans"
```

Wait for services to stabilize:

```bash
sleep 5
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps"
```

### Step U6: Validate Post-Deploy

Run the diagnose subcommand (see below) to validate the deployment.

Also check for critical config requirements:

```bash
# Check required env vars are present on remote (keys only, values hidden)
# Adapt the grep pattern to match your app's critical env var prefixes
FIRST_SERVICE=$($RUN "cd $APP_PATH && docker compose -f $COMPOSE config --services 2>/dev/null | head -1")
$RUN "docker compose -f $COMPOSE exec -T $FIRST_SERVICE env 2>/dev/null | grep -E '^(DATABASE|SECRET|API_KEY|AUTH|TOKEN)' | sed 's/=.*/=PRESENT/' || echo 'env check skipped'"
```

### Step U7: Write Deploy Log

Save a deployment log locally:

```bash
DEPLOY_DATE=$(date +%Y-%m-%d-%H%M%S)
mkdir -p deploys
cat > deploys/${DEPLOY_DATE}.md << EOF
# Deploy — $DEPLOY_DATE

**Commit before:** $PREV_COMMIT
**Commit after:** $NEW_COMMIT
**DB backup:** $BACKUP_DIR/app-${BACKUP_TS}.db
**Status:** [fill in]

## Changes
$($RUN "cd $APP_PATH && git log --oneline ${PREV_COMMIT}..HEAD 2>/dev/null")

## Validation
[fill in]
EOF
```

Report: commit hashes, what changed, backup location, service status.

---

## Subcommand: `rollback`

Revert to the previous commit with optional database restore.

### Step R1: Identify Rollback Target

Get available rollback points:

```bash
$RUN "cd $APP_PATH && git log --oneline -10"
```

Ask the user:
1. Which commit to roll back to? (default: previous commit)
2. Restore database backup? (yes/no — warn that this loses any data written after that backup)

List available DB backups:

```bash
$RUN "ls -lt $BACKUP_DIR/*.db 2>/dev/null | head -10"
```

### Step R2: Confirm

Show the user exactly what will happen:

```
Rolling back to: [commit hash] — [commit message]
DB restore: [yes — from backup: YYYY-MM-DD-HHMMSS.db | no]

This will:
1. Stop all services
2. git reset --hard [commit]
3. [Restore DB from backup]
4. Rebuild and restart services

Proceed? (yes/no)
```

Do not proceed without explicit confirmation.

### Step R3: Execute Rollback

```bash
# Stop services
$RUN "cd $APP_PATH && docker compose -f $COMPOSE down"

# Revert code
TARGET_COMMIT=${TARGET_COMMIT:-"HEAD~1"}
$RUN "cd $APP_PATH && git reset --hard $TARGET_COMMIT"

# Restore DB if requested
if [ "$RESTORE_DB" = "yes" ]; then
  $RUN "cp $BACKUP_DIR/$SELECTED_BACKUP $DB_PATH"
fi

# Restart
$RUN "cd $APP_PATH && docker compose -f $COMPOSE up -d"
```

### Step R4: Validate

Run diagnose subcommand to verify the rollback succeeded.

---

## Subcommand: `diagnose`

Health analysis of the deployed services. Safe to run at any time.

### Step D1: Container Status

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps"
```

Flag any containers not in `Up` state.

### Step D2: Recent Errors

```bash
# Errors in last 15 minutes across all services
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --since=15m 2>&1 | grep -iE 'error|exception|traceback|critical' | tail -30"
```

### Step D3: Restart Count

```bash
$RUN "docker inspect \$(docker ps -q) --format '{{.Name}}: restarts={{.RestartCount}}' 2>/dev/null | grep -v ': restarts=0'"
```

Flag any container with >2 restarts.

### Step D4: Health Endpoint

```bash
BACKEND_PORT=${BACKEND_PORT:-8000}
STATUS=$($RUN "curl -s -o /dev/null -w '%{http_code}' http://localhost:$BACKEND_PORT/health 2>/dev/null || echo 'unreachable'")
echo "Health endpoint: $STATUS"
```

### Step D5: Resource Check

```bash
$RUN "df -h / | tail -1 && free -h | grep Mem"
```

Warn if disk >85% or memory >90%.

### Step D6: Summary

Output a clear status:

```
DEPLOYMENT HEALTH
─────────────────────────────────
Containers:  [N running / N total]
Errors:      [none | N found]
Restarts:    [none | N containers restarting]
Health API:  [200 OK | FAILED]
Disk:        [X% used]
Memory:      [X% used]

Status: [HEALTHY | DEGRADED | CRITICAL]
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [investigate-incident](../investigate-incident/) | Full incident investigation |
| [docker-ops](../docker-ops/) | View logs, restart individual services |
| [bug-report](../bug-report/) | File a GitHub issue after a failed deploy |
