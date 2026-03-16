---
name: docker-ops
description: Docker Compose service management over SSH. Subcommands: logs (view service logs with filtering), restart (graceful service restart), telemetry (CPU/memory/disk/container stats), cleanup (prune Docker resources, dry-run by default). Use for day-to-day container operations.
disable-model-invocation: false
user-invocable: true
argument-hint: "[logs|restart|telemetry|cleanup] [service] [options]"
allowed-tools: Read, Bash, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Docker Ops

Day-to-day Docker Compose service management over SSH. Four subcommands for the most common operations.

---

## Prerequisites

Configure via environment variables or a local `.env` file:

```bash
SSH_HOST=<ip or hostname>
SSH_USER=<username, default: ubuntu>
SSH_KEY=<path to key, default: ~/.ssh/id_rsa>
APP_PATH=<remote app directory, default: ~/app>
COMPOSE_FILE=<compose file, default: docker-compose.yml>
```

Connection setup:

```bash
source .env 2>/dev/null || true
SSH_HOST=${SSH_HOST:-""}
SSH_USER=${SSH_USER:-"ubuntu"}
SSH_KEY=${SSH_KEY:-"~/.ssh/id_rsa"}
APP_PATH=${APP_PATH:-"~/app"}
COMPOSE=${COMPOSE_FILE:-"docker-compose.yml"}
RUN="ssh -i $SSH_KEY $SSH_USER@$SSH_HOST"
```

Parse `$ARGUMENTS` to extract the subcommand and options.

---

## Subcommand: `logs [service] [lines] [--errors]`

View logs from one or all services. Supports filtering to errors only.

### Argument Parsing

From `$ARGUMENTS`:
- First word after `logs`: service name (or `all` / omitted = all services)
- Second word: number of lines (default: 100)
- `--errors` flag: filter to error lines only

### Execution

Single service:

```bash
SERVICE=$1
LINES=${2:-100}
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=$LINES --timestamps $SERVICE 2>&1"
```

All services:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=$LINES --timestamps 2>&1"
```

With `--errors` flag:

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=$LINES $SERVICE 2>&1 | grep -iE 'error|exception|traceback|critical|fatal|warning'"
```

Time-based filter (e.g. `logs backend --since=1h`):

```bash
SINCE=${SINCE:-"1h"}
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --since=$SINCE $SERVICE 2>&1"
```

### Named Container Logs (non-compose)

If the service name doesn't match a compose service, try as a Docker container name directly:

```bash
$RUN "docker logs --tail=$LINES --timestamps $SERVICE 2>&1"
```

---

## Subcommand: `restart [service|all]`

Graceful restart of one or all services.

### Execution

Single service:

```bash
SERVICE=$1
$RUN "cd $APP_PATH && docker compose -f $COMPOSE restart $SERVICE && echo 'restarted: $SERVICE'"
```

All services (ordered stop/start to respect dependencies):

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE down && docker compose -f $COMPOSE up -d"
```

### Post-restart Check

Wait 5 seconds, then verify:

```bash
sleep 5
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps"
```

Flag any containers not in `Up` state after restart.

### Named Container (non-compose)

```bash
$RUN "docker restart $SERVICE && sleep 3 && docker inspect $SERVICE --format '{{.State.Status}}'"
```

---

## Subcommand: `telemetry`

Collect resource usage statistics.

### System Resources

```bash
# Disk usage
$RUN "df -h / /var /tmp 2>/dev/null | head -6"

# Memory
$RUN "free -h"

# CPU load
$RUN "uptime && nproc"

# Top processes by memory
$RUN "ps aux --sort=-%mem | head -10"
```

### Docker Resources

```bash
# Container resource usage (live snapshot)
$RUN "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}' 2>/dev/null"

# Container status
$RUN "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null"

# Docker disk usage
$RUN "docker system df 2>/dev/null"
```

### Compose Service Status

```bash
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps"
```

### Output Summary

Present as a clean table:

```
RESOURCE TELEMETRY
─────────────────────────────────
Host: $SSH_HOST
Time: [timestamp]

DISK
  /        XX% used (XG of XG)

MEMORY
  Used: XG / Total: XG (XX%)

LOAD
  1m: X.XX  5m: X.XX  15m: X.XX  (N CPUs)

CONTAINERS
  [name]   CPU: X%  MEM: XM / XM  (XX%)
  ...

DOCKER DISK
  Images:    X.XGB
  Containers: XMB
  Volumes:   X.XGB
  Build cache: XMB
```

Highlight any metric above warning thresholds:
- Disk >85% — WARNING
- Memory >80% — WARNING
- Any container CPU sustained >80% — WARNING
- Docker disk >10GB — NOTE

---

## Subcommand: `cleanup [--execute]`

Prune Docker resources. **Dry-run by default** — requires `--execute` to make changes.

### Dry Run (default)

Estimate reclaimable space:

```bash
$RUN "docker system df 2>/dev/null"

# List unused images
$RUN "docker images -f dangling=true --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' 2>/dev/null | head -20"

# List stopped containers
$RUN "docker ps -a -f status=exited --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>/dev/null | head -20"

# Unused volumes
$RUN "docker volume ls -f dangling=true 2>/dev/null | head -20"
```

Report estimated reclaim:

```
DRY RUN — No changes made
─────────────────────────────────
Dangling images:   N items (~XGB reclaimable)
Stopped containers: N items
Unused volumes:    N items
Build cache:       ~XGB

To execute cleanup, run: /docker-ops cleanup --execute
```

### Execute

Only when `--execute` is explicitly passed:

```bash
# Prune all unused resources (with confirmation from user already given)
$RUN "docker system prune -f 2>&1"

# Optionally prune volumes (more aggressive — ask first)
# $RUN "docker volume prune -f 2>&1"
```

Show before/after disk usage:

```bash
$RUN "df -h / | tail -1"
$RUN "docker system df 2>/dev/null"
```

**Do not prune volumes without explicit user confirmation** — volumes may contain persistent data.

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [investigate-incident](../investigate-incident/) | Full incident investigation using logs |
| [safe-deploy](../safe-deploy/) | Deploy updates or roll back |
| [bug-report](../bug-report/) | File a GitHub issue from a log finding |
