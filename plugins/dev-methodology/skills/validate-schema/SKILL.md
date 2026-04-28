---
name: validate-schema
description: Check for drift between schema definitions, migrations, and architecture documentation. Detects when the live schema diverges from what's documented or when migrations are out of sync with the model definitions.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
argument-hint: ""
automation: manual
---

# Validate Schema

Detect drift between database schema definitions, migration files, and architecture documentation. Run weekly or after any schema-related PR merges.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Schema definitions | `src/*/schema.py`, `src/*/models.py`, etc. | ✅ | | ORM models / type definitions |
| Migration files | `migrations/`, `alembic/`, etc. | ✅ | | Applied migrations |
| Architecture | `docs/memory/architecture.md` | ✅ | | Documented schema |
| Schema report | `docs/reports/schema-{date}.md` | | ✅ | Saved output |

## Process

### Step 1: Locate Schema and Migration Files

```bash
# Find model/schema definitions
find src/ -name "schema.py" -o -name "models.py" -o -name "types.py" 2>/dev/null

# Find migration files
find . -type d -name "migrations" -o -name "alembic" 2>/dev/null
ls migrations/ 2>/dev/null || ls alembic/versions/ 2>/dev/null
```

### Step 2: Extract Model Definitions

Read schema/model files and extract:
- Table/collection names
- Column/field names and types
- Relationships and foreign keys
- Indexes and constraints

### Step 3: Extract Migration History

Read the migration files and determine:
- What the migration history adds up to (final applied state)
- The most recent migration's timestamp
- Any migrations marked as squashed or pending

### Step 4: Compare Schema vs Migrations

Check that every column/field defined in `schema.py` has a corresponding migration:
- New fields without a migration = drift
- Fields removed from schema but migration not written = drift

```bash
# Check if there are uncommitted migration changes
# (example for Alembic)
alembic check 2>/dev/null || echo "alembic not available — manual check required"
```

**Severity**: CRITICAL if a production field has no migration path.

### Step 5: Compare Schema vs Architecture Documentation

Read `docs/memory/architecture.md` and extract documented data models.

Check:
- Every table/collection documented in architecture.md exists in schema.py
- Every field documented in architecture.md exists in schema.py
- No undocumented tables or fields added without architecture.md update

**Severity**: HIGH for undocumented tables; INFORMATIONAL for undocumented fields.

### Step 6: Check for Orphaned Migrations

Migrations that reference columns or tables no longer in the schema:

```bash
# Find references to dropped tables in recent migrations
grep -rn "drop_table\|DropColumn\|op\.drop" migrations/ 2>/dev/null | tail -20
```

**Severity**: INFORMATIONAL — flag for review.

### Step 7: Generate Drift Report

Save to `docs/reports/schema-{date}.md` and print summary:

```markdown
## Schema Validation Report

**Date**: [date]
**Schema file(s)**: [paths]
**Latest migration**: [id or timestamp]

### Drift Summary

| Check | Status | Details |
|-------|--------|---------|
| Schema ↔ Migrations | ✅ / ❌ | [N fields without migrations] |
| Schema ↔ Architecture docs | ✅ / ❌ | [N undocumented tables/fields] |
| Orphaned migrations | ✅ / ⚠️ | [N orphans] |

### Findings

#### Critical
[list or "None"]

#### High
[list or "None"]

### Recommendation
**[CLEAN / DRIFT DETECTED — update migrations or architecture.md]**
```

## Completion Checklist

- [ ] Schema and migration file locations identified
- [ ] Model definitions extracted
- [ ] Migration history extracted
- [ ] Schema vs migrations compared
- [ ] Schema vs architecture documentation compared
- [ ] Orphaned migrations checked
- [ ] Report saved
- [ ] Recommendation produced
