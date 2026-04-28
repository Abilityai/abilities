---
name: validate-architecture
description: Validate the codebase against the architectural invariants documented in architecture.md. Checks naming conventions, dependency directions, API patterns, auth enforcement, and structural rules. Run weekly or before major releases.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
argument-hint: ""
automation: manual
---

# Validate Architecture

Validate the live codebase against the architectural invariants documented in `docs/memory/architecture.md`. Produces a violations report. Run weekly or before any major release.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Architecture | `docs/memory/architecture.md` | ✅ | | Invariants and patterns |
| Source code | `src/` | ✅ | | Implementation to validate |
| Validation report | `docs/reports/architecture-{date}.md` | | ✅ | Saved output |

## Process

### Step 1: Read Architecture Invariants

Read `docs/memory/architecture.md` and extract:
- Layer boundaries (what can import what)
- Naming conventions (file names, class names, function names)
- API pattern requirements (auth, versioning, error format)
- Database access rules (which layers can query directly)
- Any explicitly documented invariants or constraints

### Step 2: Naming Conventions

Check that files, classes, functions, and modules follow documented naming patterns.

```bash
# Example: check for files that violate snake_case convention in Python
find src/ -name "*.py" | grep -E '[A-Z]' | grep -v '__pycache__'

# Example: check route handler naming
grep -rn "def [A-Z]" src/api/ 2>/dev/null
```

Flag deviations from documented conventions.

**Severity**: INFORMATIONAL (unless architecture.md marks as REQUIRED)

### Step 3: Layer Dependency Directions

Verify that imports respect documented layer boundaries. For example, if architecture specifies "routers never import from other routers directly":

```bash
# Check for cross-imports between router modules
grep -rn "from.*router import\|import.*router" src/api/routers/ | grep -v "^.*#"
```

Adapt the checks to the actual layer boundaries defined in `architecture.md`.

**Severity**: HIGH for violations of documented "never" constraints.

### Step 4: API Pattern Compliance

For every HTTP route handler in scope, verify:

1. Auth middleware is present (unless route is documented as public)
2. Response format matches documented standard
3. Error handling follows documented pattern
4. Versioning convention followed (e.g., `/api/v1/`)

```bash
# Find all route definitions
grep -rn "@router\.\|@app\.route\|app\." src/api/ | grep -E "get|post|put|patch|delete"
```

**Severity**: HIGH for missing auth on non-public routes.

### Step 5: Database Access Rules

If architecture defines which layers can access the database directly:

```bash
# Check for direct DB imports outside allowed layers
grep -rn "from.*database import\|import.*db\|Session\|engine" src/ | grep -v "src/services/\|src/models/"
```

**Severity**: HIGH for violations.

### Step 6: Documented Invariant Checks

For each invariant explicitly listed in `architecture.md`, write and run a targeted check. Report each as:
- **PASS** — invariant holds
- **FAIL** — violation found (with file/line reference)
- **SKIP** — cannot be automatically verified

### Step 7: Generate Validation Report

Save to `docs/reports/architecture-{date}.md` and print summary:

```markdown
## Architecture Validation Report

**Date**: [date]
**Architecture version**: [last modified date of architecture.md]

### Invariant Results

| Invariant | Status | Violations |
|-----------|--------|------------|
| Naming conventions | ✅ PASS | 0 |
| Layer boundaries | ⚠️ FAIL | 2 |
| API auth patterns | ✅ PASS | 0 |
| DB access rules | ✅ PASS | 0 |

### Violations

#### Layer Boundaries (2)
- `src/api/routers/users.py:15` — imports from `src/api/routers/auth.py` directly
- ...

### Recommendation
**[CLEAN / VIOLATIONS FOUND — review before next release]**
```

## Completion Checklist

- [ ] architecture.md read and invariants extracted
- [ ] Naming conventions checked
- [ ] Layer dependency directions checked
- [ ] API pattern compliance checked
- [ ] Database access rules checked
- [ ] Documented invariants checked
- [ ] Report saved
- [ ] Summary recommendation produced
