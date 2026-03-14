---
name: refactor-audit
description: Audit codebase for refactoring candidates. Identifies complexity issues, large files/functions, code duplication, and maintainability problems. Outputs report to docs/reports/.
disable-model-invocation: true
argument-hint: "[scope] [--quick]"
automation: manual
---

# Refactor Audit

Analyze code to identify refactoring candidates with complexity-based thresholds.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Source Code | `src/` | ✅ | | Files to analyze |
| Audit Report | `docs/reports/refactor-audit-{date}.md` | | ✅ | Generated report |

## Usage

```
/refactor-audit                    # Full src/ scan
/refactor-audit backend            # Only src/backend/
/refactor-audit frontend           # Only src/frontend/
/refactor-audit src/backend/app.py # Single file
/refactor-audit --quick            # Top 10 issues only
```

## Arguments

- `$ARGUMENTS` - Scope (backend/frontend/path) and flags

## Procedure

### Phase 1: Parse Arguments

Determine scope from `$ARGUMENTS`:
- Empty or "all" -> `src/`
- "backend" -> `src/backend/`
- "frontend" -> `src/frontend/`
- Path (contains `/` or file extension) -> use as-is
- "--quick" flag -> limit to top 10 issues

### Phase 2: Run Analysis

#### For Python files:
```bash
find [scope] -name "*.py" -exec wc -l {} \; | awk '$1 > 500 {print}'
```

#### For JavaScript/TypeScript files:
```bash
find [scope] -name "*.js" -o -name "*.ts" -o -name "*.vue" -o -name "*.tsx" | xargs wc -l | awk '$1 > 400 {print}'
```

### Phase 3: Categorize Findings

**P0 Critical** - Must fix:
- Files >1000 lines
- Functions >200 lines
- Cyclomatic complexity >30

**P1 High** - Strongly recommended:
- Files 800-1000 lines
- Functions 100-200 lines
- Significant duplication (>10 similar lines)

**P2 Medium** - Recommended:
- Files 500-800 lines
- Functions 50-100 lines
- Parameters >7
- Nesting depth >4

**P3 Low** - Nice to have:
- Files 300-500 lines
- Functions 30-50 lines
- Minor duplication (6-10 lines)

### Phase 4: Generate Report

Save report at `docs/reports/refactor-audit-YYYY-MM-DD.md` with summary table, critical issues, hotspots, and recommendations.

### Phase 5: Report Location

Confirm report saved and provide summary with top 3 hotspots.

## Completion Checklist

- [ ] Scope correctly parsed from arguments
- [ ] Analysis run (complexity, file sizes, duplication)
- [ ] Findings categorized by severity (P0-P3)
- [ ] Hotspots identified (files with multiple issues)
- [ ] Report saved to `docs/reports/`
- [ ] Summary output provided
