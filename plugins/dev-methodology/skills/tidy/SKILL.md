---
name: tidy
description: Audit and clean up repository structure. Identifies outdated docs, misplaced files, orphan configs, and test artifacts. Reports findings first and requires approval before making changes (except safe artifacts).
disable-model-invocation: true
argument-hint: "[scope] [--report-only]"
automation: gated
---

# Repository Tidy Skill

Audit and clean up the repository structure without breaking code.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Requirements | `docs/memory/requirements.md` | ✅ | | Feature status |
| Feature Flows | `docs/memory/feature-flows.md` | ✅ | | Active flows |
| Root Files | Project root | ✅ | | Misplaced files |
| Docs Folder | `docs/` | ✅ | | Outdated docs |
| Config Folder | `config/` | ✅ | | Orphan configs |
| Tests Folder | `tests/` | ✅ | | Test artifacts |
| Archive | `archive/` | | ✅ | Archived files |

## Usage

```
/tidy                    # Full audit of all areas
/tidy docs               # Audit only docs/ folder
/tidy root               # Audit only root folder
/tidy tests              # Audit only tests/ folder
/tidy --report-only      # Generate report without any changes
```

## Core Principles

1. **Never break code** - Only touch non-code files
2. **Report before action** - Always generate audit report first
3. **Archive over delete** - Move outdated files to `archive/`
4. **Safe deletes are automatic** - `__pycache__`, `.pyc`, test outputs
5. **Everything else needs approval**

## Procedure

### Phase 1: Safe Cleanup (Automatic)

Delete without asking:
- `__pycache__/` directories
- `*.pyc`, `*.pyo` files
- `.DS_Store` files
- `*.log` files in non-essential locations
- `node_modules/.cache/`

### Phase 2: Audit by Scope

- Root folder: stray files, misplaced configs
- Docs folder: outdated docs, drafts
- Tests folder: orphan test outputs, stale fixtures
- Config folder: unused configs

### Phase 3: Generate Report

Report with tables for each area showing file, issue, and recommendation.

### Phase 4: Wait for Approval

If `--report-only`, stop. Otherwise ask which actions to take.

### Phase 5: Execute Approved Changes

Archive, relocate, or delete as approved.

## Exclusions (Never Touch)

- `.git/`, `node_modules/`, `.venv/`, `venv/`
- `__pycache__/` (auto-cleaned)
- `.claude/`, `archive/`
- `*.db` files, `.env*` files

## Completion Checklist

- [ ] Safe artifacts cleaned
- [ ] Audit report generated
- [ ] User approved changes (or --report-only)
- [ ] Archive directory structure preserved
- [ ] No code files touched
