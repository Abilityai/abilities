# Manual Playbook Template

Use this template for playbooks that require full human control throughout execution.

**Characteristics:**
- Only runs when explicitly invoked by user
- Never scheduled automatically
- Human monitors entire execution
- Use for dangerous, irreversible, or sensitive operations

---

```yaml
---
name: ${PLAYBOOK_NAME}
description: ${DESCRIPTION}
automation: manual
allowed-tools: ${TOOLS}
metadata:
  version: "1.0"
  created: ${DATE}
  author: ${AUTHOR}
---

# ${PLAYBOOK_TITLE}

## Purpose
${PURPOSE_ONE_SENTENCE}

## When to Use
- ${TRIGGER_1}
- ${TRIGGER_2}

## Warnings
- ${WARNING_1}
- ${WARNING_2}

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| ${SOURCE_1} | ${PATH_1} | ✓ | ✓ | ${DESC_1} |
| ${SOURCE_2} | ${PATH_2} | ✓ | | ${DESC_2} |

## Prerequisites
- ${PREREQ_1}
- ${PREREQ_2}
- **Human operator must be present throughout execution**

## Inputs
- `$0`: ${ARGUMENT_1_DESC} (required)
- `$1`: ${ARGUMENT_2_DESC} (optional)

---

## Pre-Flight Checks

Before starting, verify:

1. [ ] ${CHECK_1}
2. [ ] ${CHECK_2}
3. [ ] ${CHECK_3}
4. [ ] Backup created: ${BACKUP_LOCATION}

If any check fails, **do not proceed**.

---

## Process

### Step 1: Read Current State

Read and display all relevant state:

1. Read `${PATH_1}`:
   ```bash
   cat ${PATH_1}
   ```

2. Read `${PATH_2}`:
   ```bash
   cat ${PATH_2}
   ```

**Present full state summary before proceeding.**

### Step 2: Confirm Intent

Display what this playbook will do:

```
## Action Summary

This playbook will:
- ${ACTION_1}
- ${ACTION_2}

Affected resources:
- ${RESOURCE_1}
- ${RESOURCE_2}

Estimated impact:
- ${IMPACT_1}
- ${IMPACT_2}
```

Ask: "Proceed with ${PLAYBOOK_NAME}? (yes/no)"

### Step 3: ${ACTION_1_NAME}

${ACTION_1_INSTRUCTIONS}

**After each sub-step, display result and wait for confirmation.**

Sub-steps:
1. ${SUBSTEP_1}
   - Expected: ${EXPECTED_1}
   - Confirm before continuing

2. ${SUBSTEP_2}
   - Expected: ${EXPECTED_2}
   - Confirm before continuing

### Step 4: ${ACTION_2_NAME}

${ACTION_2_INSTRUCTIONS}

**This step is ${REVERSIBLE_OR_NOT}.**

### Step 5: Verify Results

Check that actions completed correctly:

1. Verify ${VERIFICATION_1}:
   ```bash
   ${VERIFICATION_COMMAND_1}
   ```
   Expected: ${EXPECTED_RESULT_1}

2. Verify ${VERIFICATION_2}:
   ```bash
   ${VERIFICATION_COMMAND_2}
   ```
   Expected: ${EXPECTED_RESULT_2}

**If verification fails:**
- Do not proceed to state write
- See Error Recovery section
- Human must decide next action

### Step 6: Write Updated State

Only after successful verification:

1. Update `${PATH_1}`:
   - ${CHANGE_1}

2. Log action:
   ```bash
   echo "$(date -Iseconds) - ${PLAYBOOK_NAME} executed by $(whoami)" >> logs/manual-ops.log
   ```

3. Commit (if applicable):
   ```bash
   git add ${PATHS}
   git commit -m "${COMMIT_MESSAGE}"
   ```

---

## Outputs
- ${OUTPUT_1}
- ${OUTPUT_2}

## State Changes Summary
- `${PATH_1}`: ${CHANGE_SUMMARY}
- `logs/manual-ops.log`: Execution recorded

## Rollback Procedure

If something goes wrong:

### Immediate Rollback (within session)
${IMMEDIATE_ROLLBACK_STEPS}

### Delayed Rollback (after session)
${DELAYED_ROLLBACK_STEPS}

### Point of No Return
After ${POINT_OF_NO_RETURN}, rollback is not possible:
- ${MITIGATION_1}
- ${MITIGATION_2}

## Error Recovery

| Error | Symptom | Recovery |
|-------|---------|----------|
| ${ERROR_1} | ${SYMPTOM_1} | ${RECOVERY_1} |
| ${ERROR_2} | ${SYMPTOM_2} | ${RECOVERY_2} |

**If unrecoverable error:**
1. Stop immediately
2. Do not attempt state write
3. Contact: ${ESCALATION_CONTACT}
4. Preserve logs for investigation

## Completion Checklist
- [ ] Pre-flight checks passed
- [ ] Backup verified
- [ ] Intent confirmed
- [ ] All actions completed
- [ ] All verifications passed
- [ ] State updates written
- [ ] Logged to manual-ops.log

## Post-Execution

After successful completion:
1. ${POST_ACTION_1}
2. ${POST_ACTION_2}
3. Notify: ${WHO_TO_NOTIFY}
```

---

## Example: Database Migration

```yaml
---
name: migrate-database
description: Run database schema migration with full human oversight
automation: manual
allowed-tools: Bash, Read, Write
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Database Migration

## Purpose
Apply schema migration to production database with full human control.

## When to Use
- New schema version ready for production
- After successful staging validation
- During maintenance window

## Warnings
- **PRODUCTION DATABASE** - all actions affect live data
- **Downtime possible** - plan for service interruption
- **Backup required** - do not proceed without verified backup

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Migration | `migrations/pending/` | ✓ | | SQL migration files |
| Schema | `schema_version.txt` | ✓ | ✓ | Current version |
| Backup | `backups/` | | ✓ | Pre-migration backup |

## Prerequisites
- Migration tested on staging
- Maintenance window scheduled
- DBA on standby
- **Human operator must be present throughout**

## Inputs
- `$0`: Migration version (e.g., "v2.3.0")

---

## Pre-Flight Checks

Before starting, verify:

1. [ ] Staging migration successful (link to test run)
2. [ ] Backup completed within last hour
3. [ ] Maintenance window active
4. [ ] DBA contactable
5. [ ] Rollback script tested

If any check fails, **do not proceed**.

---

## Process

### Step 1: Read Current State

1. Check current schema version:
   ```bash
   cat schema_version.txt
   ```

2. List pending migrations:
   ```bash
   ls -la migrations/pending/
   ```

3. Verify database connectivity:
   ```bash
   psql -c "SELECT version();" $DATABASE_URL
   ```

**Display state and confirm before proceeding.**

### Step 2: Confirm Intent

```
## Migration Summary

Current version: [X.Y.Z]
Target version: $0

Migrations to apply:
1. [migration_001.sql] - [description]
2. [migration_002.sql] - [description]

Estimated duration: [N minutes]
Downtime required: [yes/no]
```

Ask: "Proceed with migration to $0? (yes/no)"

### Step 3: Create Pre-Migration Backup

```bash
pg_dump $DATABASE_URL > backups/pre-migration-$(date +%Y%m%d-%H%M%S).sql
```

Verify backup:
```bash
ls -la backups/ | tail -1
```

**Confirm backup created before continuing.**

### Step 4: Apply Migrations

For each migration file:

1. Display migration SQL
2. Ask for confirmation
3. Apply:
   ```bash
   psql $DATABASE_URL < migrations/pending/[file].sql
   ```
4. Show result
5. Confirm success before next migration

**If any migration fails, STOP and see Error Recovery.**

### Step 5: Verify Results

1. Check schema version:
   ```bash
   psql -c "SELECT version FROM schema_info;" $DATABASE_URL
   ```
   Expected: $0

2. Run smoke tests:
   ```bash
   ./scripts/db-smoke-test.sh
   ```
   Expected: All tests pass

3. Check application connectivity:
   ```bash
   curl -s https://api.example.com/health | jq .database
   ```
   Expected: "connected"

**If any verification fails, STOP. Human must decide: rollback or investigate.**

### Step 6: Write Updated State

1. Update version file:
   ```bash
   echo "$0" > schema_version.txt
   ```

2. Move applied migrations:
   ```bash
   mv migrations/pending/*.sql migrations/applied/
   ```

3. Log execution:
   ```bash
   echo "$(date -Iseconds) - migrate-database $0 by $(whoami)" >> logs/manual-ops.log
   ```

4. Commit:
   ```bash
   git add schema_version.txt migrations/
   git commit -m "Apply database migration $0"
   ```

---

## Rollback Procedure

### Immediate Rollback
```bash
psql $DATABASE_URL < backups/pre-migration-[timestamp].sql
echo "[previous version]" > schema_version.txt
```

### Point of No Return
After data migrations (not just schema), rollback may lose data.
- Export affected tables before proceeding
- Have DBA review rollback plan

## Completion Checklist
- [ ] Pre-flight checks passed
- [ ] Backup created and verified
- [ ] All migrations applied
- [ ] Smoke tests passed
- [ ] Application healthy
- [ ] Version file updated
- [ ] Migrations moved to applied/
- [ ] Logged to manual-ops.log

## Post-Execution

1. End maintenance window
2. Notify team in #deployments
3. Monitor error rates for 30 minutes
4. Close migration ticket
```
