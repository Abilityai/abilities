---
name: validate-config
description: Check for drift in environment variable definitions across docker-compose.yml, .env.example, and the application codebase. Detects missing declarations, undocumented variables, and inconsistent defaults.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
argument-hint: ""
automation: manual
---

# Validate Config

Detect configuration drift across environment variable declarations. Ensures every variable used in code is declared in `.env.example`, and every declaration in docker-compose matches what the app actually needs.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Env example | `.env.example` | ✅ | | Declared env vars with defaults |
| Docker Compose | `docker-compose.yml`, `docker-compose.*.yml` | ✅ | | Container env declarations |
| Source code | `src/` | ✅ | | Variables read at runtime |
| Config report | `docs/reports/config-{date}.md` | | ✅ | Saved output |

## Process

### Step 1: Extract Variables from .env.example

```bash
grep -E '^[A-Z_]+=|^# [A-Z_]+=' .env.example 2>/dev/null | grep -v '^#' | cut -d= -f1 | sort
```

Build a set: **declared_vars**.

### Step 2: Extract Variables from docker-compose

```bash
# Extract env vars from all compose files
grep -rE '^\s+[A-Z_]+=|\$\{[A-Z_]+\}' docker-compose*.yml 2>/dev/null | grep -oE '[A-Z_]{2,}' | sort -u
```

Build a set: **compose_vars**.

### Step 3: Extract Variables from Source Code

```bash
# Python: os.environ, os.getenv, settings.
grep -rn "os\.environ\[.\|os\.getenv(\|settings\." src/ 2>/dev/null | grep -oE "['\"][A-Z_]{2,}['\"]" | tr -d "'\""  | sort -u

# Node/JS: process.env.
grep -rn "process\.env\." src/ 2>/dev/null | grep -oE "process\.env\.[A-Z_]+" | sed 's/process\.env\.//' | sort -u
```

Build a set: **code_vars**.

### Step 4: Compare .env.example vs Code

Find:
- **In code but not in .env.example**: Undocumented variables — operators won't know what to set
- **In .env.example but not in code**: Stale declarations — potentially safe to remove

```bash
# Set comparison (adapt to available shell tools)
comm -23 <(sort code_vars.txt) <(sort declared_vars.txt)  # in code, not declared
comm -23 <(sort declared_vars.txt) <(sort code_vars.txt)  # declared, not in code
```

**Severity**:
- Code but not declared: HIGH
- Declared but not in code: INFORMATIONAL

### Step 5: Compare docker-compose vs .env.example

Find:
- **In compose but not in .env.example**: Compose sets variables that aren't documented for developers
- **In .env.example but not in compose**: Documented but not injected into containers

**Severity**: HIGH for variables required by compose that have no documented default.

### Step 6: Check for Missing Required Variables

Variables with no default in `.env.example` (empty value or marked `REQUIRED`) should have:
- Documentation comment explaining what they are
- Instructions in README or CLAUDE.md for how to obtain them

```bash
grep -E '^[A-Z_]+=($|REQUIRED|CHANGEME|TODO)' .env.example 2>/dev/null
```

**Severity**: INFORMATIONAL — flag for documentation quality.

### Step 7: Generate Config Report

Save to `docs/reports/config-{date}.md` and print summary:

```markdown
## Config Validation Report

**Date**: [date]
**Sources checked**: .env.example, docker-compose.yml, src/

### Summary

| Check | Status | Count |
|-------|--------|-------|
| In code, not declared in .env.example | ✅ / ❌ | N |
| Declared in .env.example, not in code | ✅ / ⚠️ | N |
| In docker-compose, not in .env.example | ✅ / ❌ | N |
| Required vars without documentation | ✅ / ⚠️ | N |

### Findings

#### High (undocumented required vars)
[list or "None"]

#### Informational (stale or undocumented)
[list or "None"]

### Recommendation
**[CLEAN / DRIFT DETECTED — update .env.example or remove stale entries]**
```

## Completion Checklist

- [ ] Variables extracted from .env.example
- [ ] Variables extracted from docker-compose
- [ ] Variables extracted from source code
- [ ] .env.example vs code compared
- [ ] docker-compose vs .env.example compared
- [ ] Required variables without documentation flagged
- [ ] Report saved
- [ ] Recommendation produced
