---
name: security-check
description: Pre-commit security validation. Scans staged/modified files for secrets, API keys, credentials, PII, and sensitive data before committing.
disable-model-invocation: true
allowed-tools: Bash(git *), Grep
automation: manual
---

# Pre-Commit Security Check

Validate that staged changes don't contain sensitive information before committing.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Git Staged | `git diff --cached` | ✅ | | Staged changes |
| Git Modified | `git diff HEAD` | ✅ | | Unstaged changes |

## Step 1: Determine Files to Check

```bash
# Check if there are staged files
STAGED=$(git diff --cached --name-only 2>/dev/null)

if [ -n "$STAGED" ]; then
  echo "=== Checking STAGED files ==="
  echo "$STAGED"
  DIFF_CMD="git diff --cached -U0"
  FILES_CMD="git diff --cached --name-only"
else
  echo "=== No staged files. Checking all MODIFIED files ==="
  FILES=$(git diff --name-only HEAD 2>/dev/null)
  if [ -z "$FILES" ]; then
    echo "No modified files to check."
    exit 0
  fi
  echo "$FILES"
  DIFF_CMD="git diff -U0 HEAD"
  FILES_CMD="git diff --name-only HEAD"
fi
```

## Step 2: Run Security Checks

### Check 1: API Keys and Tokens (CRITICAL)

```bash
git diff --cached -U0 2>/dev/null | grep -E 'sk-[a-zA-Z0-9]{20,}' | grep -v 'skip\|sketch\|skill'
git diff --cached -U0 2>/dev/null | grep -E '(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{22,})'
git diff --cached -U0 2>/dev/null | grep -E 'xox[baprs]-[a-zA-Z0-9-]{10,}'
git diff --cached -U0 2>/dev/null | grep -E '(AIza[a-zA-Z0-9_-]{35}|ya29\.[a-zA-Z0-9_-]{50,})'
git diff --cached -U0 2>/dev/null | grep -E 'AKIA[A-Z0-9]{16}'
```

### Check 2: Email Addresses (HIGH)

```bash
git diff --cached -U0 2>/dev/null | grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | grep -vE '(example\.(com|org|net)|placeholder|test@|user@|noreply@|nobody@|admin@localhost|root@localhost|@users\.noreply\.github\.com)'
```

### Check 3: IP Addresses (HIGH)

```bash
git diff --cached -U0 2>/dev/null | grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' | grep -vE '^(127\.|0\.0\.0\.|255\.255\.|192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)'
```

### Check 4: .env Files (CRITICAL)

```bash
git diff --cached --name-only 2>/dev/null | grep -E '^\.env$|/\.env$|\.env\.[^e]' | grep -v '\.example'
```

### Check 5: Hardcoded Secrets in Code (CRITICAL)

```bash
git diff --cached -U0 2>/dev/null | grep -iE '(password|passwd|secret|token|api_key|apikey|auth_token|access_token|private_key|client_secret)\s*[=:]\s*["\x27][^"\x27\$]{8,}["\x27]' | grep -vE '(process\.env|os\.environ|os\.getenv|getenv|ENV\[|config\[|\$\{|example|placeholder|your[_-]|changeme|xxx|test|dummy|fake|mock|sample)'
```

### Check 6: Private Key Content (CRITICAL)

```bash
git diff --cached -U0 2>/dev/null | grep -E '-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----'
```

### Check 7: Internal URLs/Domains (MEDIUM)

```bash
git diff --cached -U0 2>/dev/null | grep -iE '(internal\.|\.internal|\.local|\.corp|\.lan|\.priv|staging\.[a-z]+\.(com|net|org)|dev\.[a-z]+\.(com|net|org))' | grep -vE '(localhost|127\.0\.0\.1|example\.com|\.local/)'
```

### Check 8: Credential Files (CRITICAL)

```bash
git diff --cached --name-only 2>/dev/null | grep -iE '(credentials\.json|service.?account.*\.json|\.pem$|\.key$|id_rsa|id_ed25519|id_dsa|\.p12$|\.pfx$|\.jks$|htpasswd|\.keystore|\.truststore)'
```

## Step 3: Generate Report

After running all checks, produce a report:

```markdown
## Security Check Results

### Summary
| Check | Status | Findings |
|-------|--------|----------|
| API Keys/Tokens | ✅/❌ | count |
| Email Addresses | ✅/❌ | count |
| IP Addresses | ✅/❌ | count |
| .env Files | ✅/❌ | count |
| Hardcoded Secrets | ✅/❌ | count |
| Private Keys | ✅/❌ | count |
| Internal URLs | ✅/❌ | count |
| Credential Files | ✅/❌ | count |

### Verdict
- **BLOCK COMMIT** - Critical issues found
- OR **REVIEW REQUIRED** - Issues need human review
- OR **SAFE TO COMMIT** - No sensitive data detected
```

## Severity Levels

| Level | Action | Examples |
|-------|--------|----------|
| **CRITICAL** | Do NOT commit | API keys, tokens, passwords, private keys |
| **HIGH** | Remove before commit | Real emails, production IPs |
| **MEDIUM** | Review carefully | .env files, internal URLs |
| **LOW** | Verify intentional | Domain names, placeholders |

## Completion Checklist

- [ ] All 8 security checks executed
- [ ] Verdict rendered (BLOCK/REVIEW/SAFE)
