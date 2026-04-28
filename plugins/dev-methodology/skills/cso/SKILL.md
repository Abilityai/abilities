---
name: cso
description: Security audit in CSO (Chief Security Officer) mode. --diff scans branch changes only; --comprehensive scans the full codebase. Checks secrets, dependencies, auth boundaries, injection vectors, and platform-specific patterns.
allowed-tools: Bash, Read, Grep, Glob
user-invocable: true
argument-hint: "[--diff | --comprehensive]"
automation: manual
---

# CSO Security Audit

Run a security audit in Chief Security Officer mode. Two scopes available:

- `--diff` — scans changes on the current branch vs base. Fast, recommended for every P0/P1 PR.
- `--comprehensive` — scans the full codebase. Slower, recommended weekly or before major releases.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Git diff | current branch | ✅ | | Branch changes (--diff mode) |
| Source code | `src/` | ✅ | | Full codebase (--comprehensive mode) |
| Architecture | `docs/memory/architecture.md` | ✅ | | Auth boundaries, integration points |
| Dependencies | `requirements.txt`, `package.json`, etc. | ✅ | | Dependency inventory |
| Security reports | `docs/security-reports/` | | ✅ | Saved output |

## Arguments

- `--diff` — scope to branch changes only (default if no argument provided)
- `--comprehensive` — scope to full codebase

## Process

### Step 1: Determine Scope

```bash
# --diff mode
git diff main...HEAD

# --comprehensive mode
find src/ -type f -name "*.py" -o -name "*.ts" -o -name "*.js"
```

### Step 2: Secrets Scan

Scan for hardcoded credentials in scope:

```bash
# API keys and tokens
grep -rE '(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[A-Z0-9]{16})' [scope]

# Generic secrets pattern
grep -rE '(password|secret|token|api_key)\s*[=:]\s*["'"'"'][^"'"'"'\$]{8,}["'"'"']' [scope] | grep -v 'example\|placeholder\|test\|dummy'

# .env files in diff
git diff --name-only | grep -E '^\.env$|\.env\.[^e]' | grep -v example
```

**Severity**: CRITICAL

### Step 3: Dependency Audit

Check for known-vulnerable packages:

```bash
# Python
pip-audit 2>/dev/null || safety check 2>/dev/null || echo "No pip-audit/safety available"

# Node
npm audit --json 2>/dev/null || yarn audit --json 2>/dev/null || echo "No npm/yarn audit available"
```

Flag: new dependencies added in diff that haven't been reviewed.

**Severity**: HIGH for known CVEs, INFORMATIONAL for new unreviewed deps.

### Step 4: Auth Boundary Audit

Review authentication and authorization patterns:

1. List all HTTP route handlers in scope
2. For each route: verify auth middleware is applied before handler
3. Check for authorization (ownership check, not just authentication)
4. Verify admin endpoints are protected by role check

```bash
# Example patterns to find unprotected routes (adapt to framework)
grep -rn "@router\.\|app\.route\|@app\." src/ | grep -v "login\|health\|docs\|static"
```

**Severity**: CRITICAL for unauthenticated routes that should require auth.

### Step 5: Injection Vectors

Check for injection vulnerabilities:

- **SQL injection**: string interpolation in queries (see /review SQL check)
- **Command injection**: `subprocess`, `os.system`, `exec`, `eval` with user input
- **Path traversal**: file operations with user-controlled paths without sanitization
- **Template injection**: user input rendered in server-side templates without escaping
- **SSRF**: user-controlled URLs passed to HTTP clients

**Severity**: CRITICAL

### Step 6: Platform-Specific Patterns

Check for patterns specific to the project's architecture (read from `architecture.md`):

- Webhook handlers: is the incoming payload signature verified?
- Background jobs: are job arguments sanitized before use?
- File uploads: are file types and sizes validated? Are files stored outside web root?
- Third-party integrations: are API responses validated before use?

**Severity**: HIGH

### Step 7: Security Configuration

Check for misconfigurations:

- Debug mode enabled in production config
- CORS set to `*` (wildcard) without justification
- Overly permissive file permissions
- Missing security headers (CSP, HSTS, X-Frame-Options)
- Session cookies missing `Secure` and `HttpOnly` flags

**Severity**: HIGH

### Step 8: Generate Report

Save to `docs/security-reports/cso-{mode}-{date}.md` and print summary:

```markdown
## CSO Security Audit

**Mode**: [diff | comprehensive]
**Scope**: [branch name or "full codebase"]
**Date**: [date]

### Summary

| Category | CRITICAL | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| Secrets | 0 | 0 | 0 | 0 |
| Dependencies | 0 | 0 | 0 | 0 |
| Auth Boundaries | 0 | 0 | 0 | 0 |
| Injection | 0 | 0 | 0 | 0 |
| Platform Patterns | 0 | 0 | 0 | 0 |
| Configuration | 0 | 0 | 0 | 0 |

### Findings

#### CRITICAL
[list or "None"]

#### HIGH
[list or "None"]

### Recommendation
**[CLEAR / REVIEW REQUIRED / BLOCK — RESOLVE CRITICALS]**
```

## Severity Reference

| Level | Action |
|-------|--------|
| **CRITICAL** | Block merge or deploy — must be resolved |
| **HIGH** | Fix before next release |
| **MEDIUM** | Track and address in upcoming sprint |
| **LOW** | Informational — review at discretion |

## Completion Checklist

- [ ] Scope determined (diff or comprehensive)
- [ ] Secrets scan completed
- [ ] Dependency audit completed
- [ ] Auth boundaries reviewed
- [ ] Injection vectors checked
- [ ] Platform-specific patterns checked
- [ ] Security configuration checked
- [ ] Report generated and saved
- [ ] Summary recommendation produced
