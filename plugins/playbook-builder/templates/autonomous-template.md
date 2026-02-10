# Autonomous Playbook Template

Use this template for playbooks that run on schedule without human intervention.

**Characteristics:**
- Safe to run completely unattended
- No approval gates
- Must handle all errors gracefully
- Should notify on failure (email, Slack, etc.)

---

```yaml
---
name: ${PLAYBOOK_NAME}
description: ${DESCRIPTION}
automation: autonomous
schedule: "${CRON_EXPRESSION}"
allowed-tools: ${TOOLS}
metadata:
  version: "1.0"
  created: ${DATE}
  author: ${AUTHOR}
---

# ${PLAYBOOK_TITLE}

## Purpose
${PURPOSE_ONE_SENTENCE}

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| ${SOURCE_1} | ${PATH_1} | ✓ | | ${DESC_1} |
| ${SOURCE_2} | ${PATH_2} | ✓ | ✓ | ${DESC_2} |

## Prerequisites
- ${PREREQ_1}
- ${PREREQ_2}

## Notifications

On failure, notify via:
- ${NOTIFICATION_METHOD}: ${NOTIFICATION_TARGET}

---

## Process

### Step 1: Read Current State

Read fresh copies of all state dependencies:

1. Read `${PATH_1}`:
   ```bash
   cat ${PATH_1}
   ```
   - Verify: ${VALIDATION_1}

2. Read `${PATH_2}`:
   ```bash
   cat ${PATH_2}
   ```
   - Verify: ${VALIDATION_2}

If any read fails, abort and notify.

### Step 2: ${ACTION_1_NAME}

${ACTION_1_INSTRUCTIONS}

Expected outcome:
- ${EXPECTED_1}

### Step 3: ${ACTION_2_NAME}

${ACTION_2_INSTRUCTIONS}

Expected outcome:
- ${EXPECTED_2}

### Step 4: Write Updated State

Save all changes made during execution:

1. Update `${PATH_2}`:
   - ${WHAT_CHANGED}

2. Log execution:
   ```bash
   echo "$(date -Iseconds) - ${PLAYBOOK_NAME} completed" >> logs/playbook.log
   ```

3. Verify state consistency:
   - ${VERIFICATION}

---

## Outputs
- ${OUTPUT_1}
- ${OUTPUT_2}

## State Changes Summary
- `${PATH_2}`: ${CHANGE_SUMMARY}
- `logs/playbook.log`: Execution logged

## Error Handling

This playbook handles errors automatically:

| Error | Recovery | Notification |
|-------|----------|--------------|
| ${ERROR_1} | ${RECOVERY_1} | ${NOTIFY_1} |
| ${ERROR_2} | ${RECOVERY_2} | ${NOTIFY_2} |

If unrecoverable:
1. Log error to `logs/playbook-errors.log`
2. Send notification: ${NOTIFICATION_METHOD}
3. Exit without partial state changes

## Completion Checklist
- [ ] All state dependencies read fresh
- [ ] ${TASK_CHECK_1}
- [ ] ${TASK_CHECK_2}
- [ ] All state updates written
- [ ] Execution logged
```

---

## Example: Daily Metrics Collection

```yaml
---
name: daily-metrics
description: Collect and store daily performance metrics
automation: autonomous
schedule: "0 6 * * *"
allowed-tools: Bash, WebFetch, Write
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Daily Metrics Collection

## Purpose
Fetch metrics from all services and store in metrics history.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Config | `config/metrics.yaml` | ✓ | | Service endpoints |
| History | `data/metrics-history.jsonl` | | ✓ | Append daily metrics |
| Summary | `data/metrics-latest.json` | | ✓ | Current snapshot |

## Prerequisites
- API keys configured in `.env`
- Network access to metric endpoints

## Notifications

On failure, notify via:
- Slack: #ops-alerts channel

---

## Process

### Step 1: Read Current State

1. Read `config/metrics.yaml`:
   - Parse endpoint list
   - Verify all endpoints configured

2. Load API keys from environment:
   ```bash
   [ -n "$METRICS_API_KEY" ] || exit 1
   ```

### Step 2: Fetch Metrics

For each endpoint in config:
1. Call API endpoint
2. Parse response
3. Extract key metrics

Collect into single metrics object with timestamp.

### Step 3: Calculate Aggregates

- Daily totals
- Comparison to yesterday
- Week-over-week trends

### Step 4: Write Updated State

1. Append to `data/metrics-history.jsonl`:
   - Add timestamped metrics record

2. Overwrite `data/metrics-latest.json`:
   - Current day's full metrics

3. Log execution:
   ```bash
   echo "$(date -Iseconds) - daily-metrics completed" >> logs/playbook.log
   ```

---

## Outputs
- Metrics record in history
- Updated latest snapshot

## Error Handling

| Error | Recovery | Notification |
|-------|----------|--------------|
| API timeout | Retry 3x with backoff | Warn if all fail |
| Parse error | Log raw response | Alert |
| Write failure | Retry once | Critical alert |

## Completion Checklist
- [ ] All endpoints queried
- [ ] History file appended
- [ ] Latest snapshot updated
- [ ] Execution logged
```
