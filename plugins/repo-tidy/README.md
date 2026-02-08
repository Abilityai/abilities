# Repo Tidy

Audit and clean up repository structure - find orphan files, outdated docs, and misplaced configs.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install repo-tidy@abilityai
```

## Usage

```bash
/tidy                    # Full audit of all areas
/tidy docs               # Audit only docs/ folder
/tidy root               # Audit only root folder
/tidy tests              # Audit only tests/ folder
/tidy config             # Audit only config/ folder
/tidy --report-only      # Generate report without any changes
```

## What It Does

### Phase 1: Safe Cleanup (Automatic)
Deletes regenerable artifacts without asking:
- `__pycache__/` directories
- `*.pyc`, `*.pyo` files
- Test output files
- `.DS_Store` files

### Phase 2: Audit
Checks for issues in different scopes:

**Root Folder:**
- Stray markdown files
- Scripts that should be in `scripts/`
- Configs that should be in `config/`
- Temporary/backup files

**Docs Folder:**
- Outdated documentation
- Orphan files not in index
- Stale drafts (>90 days old)
- Docs for removed features

**Tests Folder:**
- Orphan test outputs
- Stale fixtures
- Tests for removed features

**Config Folder:**
- Empty template directories
- Unused configurations

### Phase 3: Report
Generates a structured report with:
- Issues by severity (HIGH/MEDIUM/LOW)
- Confidence levels
- Recommended actions

### Phase 4: Approval
Asks for confirmation before:
- Archiving files (preserves structure in `archive/`)
- Relocating misplaced files
- Deleting orphan files

## Core Principles

1. **Never break code** - Only touches non-code files
2. **Report before action** - Always shows what it will do
3. **Archive over delete** - Preserves files in `archive/`
4. **Safe deletes are automatic** - Only for regenerable artifacts
5. **Everything else needs approval** - You stay in control

## Example Report

```markdown
## Tidy Report - 2026-02-08

### Safe Cleanup Completed
| Type | Count | Space Freed |
|------|-------|-------------|
| __pycache__ | 15 | 2.3 MB |
| .pyc | 42 | 1.1 MB |

### HIGH Priority Issues
| File | Issue | Recommendation |
|------|-------|----------------|
| `old-spec.md` | Old prefix | Archive |
| `backup.json` | Temporary file | Delete |

### MEDIUM Priority Issues
| File | Issue | Recommendation |
|------|-------|----------------|
| `draft-feature.md` | Stale draft (120 days) | Archive or finalize |
```

## Files

- `skills/tidy/SKILL.md` - Main skill definition
- `skills/tidy/reference.md` - Detailed audit procedures

## License

MIT
