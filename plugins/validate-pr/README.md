# Validate PR

Validate pull requests against security and documentation standards before merge.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install validate-pr@abilityai
```

## Usage

```bash
/validate-pr 123
/validate-pr https://github.com/org/repo/pull/123
```

## What It Checks

### Security Validation

| Check | Pattern |
|-------|---------|
| API Keys | `sk-*`, `pk-*`, `ghp_*`, `AKIA*` |
| Tokens | OAuth tokens, JWT patterns |
| Secrets | Hardcoded passwords, API keys in strings |
| Emails | Real email addresses (not examples) |
| IPs | Public IP addresses |
| Files | `.env`, `credentials.json`, `*.pem`, `*.key` |

### Documentation

| Check | When Required |
|-------|---------------|
| Changelog | Always recommended |
| README | New features, API changes |

### Code Quality

- Changes focused on stated purpose
- No unrelated refactoring
- Follows existing patterns
- Consistent error handling

## Output

```markdown
## PR Validation Report

**PR**: #123 - Add user authentication
**Author**: developer
**Branch**: feature/auth → main
**Files Changed**: 12 (+450/-23)

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Documentation | ✅ | Changelog updated |
| Security Check | ✅ | No issues found |
| Code Quality | ⚠️ | Minor suggestions |

### Security Checklist

- [x] No API keys or tokens
- [x] No real email addresses
- [x] No IP addresses
- [x] No .env files
- [x] No hardcoded secrets
- [x] No credential files

### Recommendation

**APPROVE**

All security checks pass. Minor code suggestions noted.
```

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Passed |
| ❌ | Failed - must fix |
| ⚠️ | Warning - review needed |
| ➖ | Not applicable |

## Files

- `commands/validate-pr.md` - Command definition

## License

MIT
