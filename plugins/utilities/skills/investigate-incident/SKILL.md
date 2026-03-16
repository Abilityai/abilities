---
name: investigate-incident
description: Structured production incident investigation. Collects evidence from logs, metrics, and DB, classifies severity, and produces a root cause report. Use when something is broken in production.
disable-model-invocation: false
user-invocable: true
argument-hint: "[service-name or description]"
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Investigate Incident

Conduct a structured investigation of a production incident. Collect evidence systematically, classify severity, and produce a report with root cause hypotheses.

---

## Prerequisites

This skill expects SSH access to the affected system. Configure via environment variables or a local `.env` file:

```bash
SSH_HOST=<ip or hostname>
SSH_USER=<username>
SSH_KEY=<path to key, default: ~/.ssh/id_rsa>
APP_PATH=<path to app on remote, default: ~/app>
COMPOSE_FILE=<docker-compose file, default: docker-compose.yml>
```

Load connection config:

```bash
source .env 2>/dev/null || true
SSH_HOST=${SSH_HOST:-""}
SSH_USER=${SSH_USER:-"ubuntu"}
SSH_KEY=${SSH_KEY:-"~/.ssh/id_rsa"}
APP_PATH=${APP_PATH:-"~/app"}
COMPOSE=${COMPOSE_FILE:-"docker-compose.yml"}
RUN="ssh -i $SSH_KEY $SSH_USER@$SSH_HOST"
```

If `SSH_HOST` is empty, check for a `scripts/run.sh` wrapper and use that instead.

---

## Phase 1: Establish Context

Ask the user (or read from `$ARGUMENTS`):

1. What is the reported symptom?
2. When did it start (approximate time)?
3. What service or component is affected?
4. Were any deployments or config changes made recently?

Restate the incident scope before proceeding.

---

## Phase 2: Classify Initial Severity

Use this matrix to set an initial severity (update after evidence):

| Severity | Criteria |
|----------|----------|
| **P0** | Complete outage — no users can access the system |
| **P1** | Major feature broken — significant portion of users affected |
| **P2** | Degraded performance or partial feature failure |
| **P3** | Minor issue, cosmetic, or affects few users |

---

## Phase 3: Collect Evidence

Work through each evidence category. Skip sections that don't apply.

### 3.1 Service Health

```bash
# Container status
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps"

# Recent restarts
$RUN "cd $APP_PATH && docker compose -f $COMPOSE ps --format json 2>/dev/null | grep -E 'Status|Restarts' || docker compose -f $COMPOSE ps"
```

### 3.2 Recent Errors — All Services

```bash
# All services — errors in last 100 lines
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=100 2>&1 | grep -iE 'error|exception|traceback|critical|fatal' | tail -50"

# Specific service errors (substitute your service name)
# $RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=100 <service-name> 2>&1 | grep -iE 'error|exception|traceback|critical|fatal' | tail -50"

# All services — recent logs with timestamps
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --tail=50 --timestamps 2>&1 | tail -100"
```

### 3.3 Resource Metrics

```bash
# Disk usage
$RUN "df -h / /var 2>/dev/null | head -5"

# Memory and load
$RUN "free -h && uptime"

# Top processes
$RUN "ps aux --sort=-%mem | head -15"

# Docker resource usage
$RUN "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' 2>/dev/null | head -20"
```

### 3.4 Application-Level Health

```bash
# Health endpoint (adjust port and path as needed)
APP_PORT=${APP_PORT:-8000}
HEALTH_PATH=${HEALTH_PATH:-"/health"}
$RUN "curl -s -o /dev/null -w '%{http_code}' http://localhost:$APP_PORT$HEALTH_PATH || echo 'health check failed'"

# Recent activity across all services
$RUN "cd $APP_PATH && docker compose -f $COMPOSE logs --since=30m 2>&1 | grep -v DEBUG | tail -80"
```

### 3.5 Database Integrity (if applicable)

```bash
# SQLite integrity check
DB_PATH=${DB_PATH:-"$APP_PATH/app.db"}
$RUN "sqlite3 $DB_PATH 'PRAGMA integrity_check;' 2>/dev/null || echo 'DB check skipped (not SQLite or path not set)'"

# List tables to understand schema (adapt queries to your app)
$RUN "sqlite3 $DB_PATH '.tables' 2>/dev/null || echo 'skipped'"
```

### 3.6 Recent Deployments

```bash
# Last git commits on remote
$RUN "cd $APP_PATH && git log --oneline -10"

# Uncommitted changes
$RUN "cd $APP_PATH && git status --short"

# Recent config changes
$RUN "cd $APP_PATH && git log --oneline --diff-filter=M -- .env docker-compose*.yml 2>/dev/null | head -5"
```

### 3.7 All Containers (if applicable)

```bash
# Full container inventory including stopped
$RUN "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | grep -v NAMES"

# Containers not in healthy Up state
$RUN "docker ps --format '{{.Names}}\t{{.Status}}' | grep -v 'Up [0-9]'"
```

---

## Phase 4: Analyze Evidence

Review all collected evidence and identify:

1. **Error patterns** — repeated errors, tracebacks, specific failure messages
2. **Resource pressure** — disk >90%, memory >80%, high load
3. **Timing correlation** — does the issue align with a deployment, cron, or traffic spike?
4. **Cascading failures** — one service failure causing others
5. **Configuration drift** — missing env vars, wrong values, mismatches between services

---

## Phase 5: Form Hypotheses

List 2–5 probable root causes ranked by likelihood. For each:

- **Hypothesis**: What might be causing this
- **Evidence for**: What you observed that supports it
- **Evidence against**: What contradicts it
- **Verification step**: How to confirm or rule out

---

## Phase 6: Generate Incident Report

Create a markdown report. Save to `incidents/` directory if it exists, otherwise current directory:

```bash
INCIDENT_DATE=$(date +%Y-%m-%d-%H%M)
INCIDENT_FILE="incidents/${INCIDENT_DATE}-incident.md"
mkdir -p incidents
```

Report structure:

```markdown
# Incident Report — [YYYY-MM-DD HH:MM]

**Severity:** [P0 / P1 / P2 / P3]
**Status:** [Investigating / Identified / Mitigating / Resolved]
**Reported symptom:** [What the user reported]
**Affected service(s):** [List]
**Investigation start:** [Time]

## Timeline

- HH:MM — [Event or observation]

## Evidence Summary

### Errors Found
[Key error messages and patterns]

### Resource State
[Disk, memory, CPU summary]

### Recent Changes
[Git commits, config changes, deployments]

## Root Cause Hypotheses

### Hypothesis 1 — [Title] (HIGH/MEDIUM/LOW confidence)
[Description, evidence for, evidence against, how to verify]

### Hypothesis 2 — [Title]
[...]

## Recommended Next Steps

1. [ ] [Immediate action]
2. [ ] [Verification step]
3. [ ] [Remediation]

## Raw Evidence

[Paste key log excerpts and command outputs]
```

---

## Phase 7: Present Findings

Report to the user:
- Severity classification (revised if needed)
- Top 1–2 hypotheses with confidence
- Immediate recommended actions
- Link to saved incident report

Ask: "Would you like me to proceed with any of the remediation steps, or create a bug report?"

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [bug-report](../bug-report/) | Create a sanitized GitHub issue from this incident |
| [safe-deploy](../safe-deploy/) | Deploy a fix or roll back |
| [docker-ops](../docker-ops/) | View logs or restart services |
