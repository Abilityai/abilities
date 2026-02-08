# Validate Pull Request

Validate a pull request against documentation and security standards before merge.

## Usage

```
/validate-pr <pr-number-or-url>
```

## Instructions

### Step 1: Fetch PR Information

```bash
# Get PR number from argument (extract from URL if needed)
PR_NUMBER=<extract number from argument>

# Fetch PR details
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName,files,additions,deletions,changedFiles

# Get list of changed files
gh pr diff $PR_NUMBER --name-only

# Get the actual diff for analysis
gh pr diff $PR_NUMBER
```

Store this information for validation:
- PR title and description
- Changed files list
- Base and head branches
- Author

### Step 2: Validate Documentation Updates

#### 2.1 Changelog Entry (RECOMMENDED)
Check if `CHANGELOG.md` or similar is in the changed files list.

**If present**, verify:
- [ ] Entry is at the TOP of recent changes (newest first)
- [ ] Has appropriate format
- [ ] Includes summary of what changed and why

#### 2.2 README Updates (CONDITIONAL)
**Required if**:
- PR adds new features
- PR changes public API
- PR modifies installation/setup

### Step 3: Security Validation

Run security checks on the PR diff:

```bash
# Get the full diff
gh pr diff $PR_NUMBER > /tmp/pr_diff.txt
```

#### 3.1 API Keys and Tokens
```bash
grep -iE '(sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22,}|xox[baprs]-[a-zA-Z0-9-]{10,}|ya29\.[a-zA-Z0-9_-]{50,}|AIza[a-zA-Z0-9_-]{35}|AKIA[A-Z0-9]{16})' /tmp/pr_diff.txt
```
- [ ] No API keys or tokens found

#### 3.2 Email Addresses
```bash
grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' /tmp/pr_diff.txt | grep -vE '(example\.com|example\.org|placeholder|test@|user@example|noreply@)'
```
- [ ] No real email addresses (only placeholders allowed)

#### 3.3 IP Addresses
```bash
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' /tmp/pr_diff.txt | grep -vE '^(127\.|0\.0\.0\.0|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|10\.)'
```
- [ ] No public IP addresses exposed

#### 3.4 Environment Files
```bash
gh pr diff $PR_NUMBER --name-only | grep -E '^\.env$|/\.env$' | grep -v '\.example'
```
- [ ] No .env files with real values

#### 3.5 Hardcoded Secrets
```bash
grep -iE '(password|secret|token|api_key|apikey|auth_token|access_token|private_key)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]' /tmp/pr_diff.txt | grep -vE '(process\.env|os\.environ|os\.getenv|\$\{|example|placeholder|your-|changeme|xxx|\\$\\{)'
```
- [ ] No hardcoded secrets

#### 3.6 Credential Files
```bash
gh pr diff $PR_NUMBER --name-only | grep -iE '(credentials\.json|service.?account.*\.json|\.pem$|\.key$|id_rsa|id_ed25519|\.p12$|\.pfx$|htpasswd)'
```
- [ ] No credential files committed

### Step 4: Code Quality Assessment

#### 4.1 Minimal Necessary Changes
Review the diff scope:
- [ ] Changes are focused on the stated purpose
- [ ] No unrelated refactoring
- [ ] No cosmetic changes to unrelated code

#### 4.2 Pattern Compliance
Spot-check changed code against existing patterns:
- [ ] Follows existing code style
- [ ] Uses established patterns for similar operations
- [ ] Error handling consistent with codebase

### Step 5: Generate Validation Report

Create the report in this format:

---

## PR Validation Report

**PR**: #[number] - [title]
**Author**: [author]
**Branch**: [head] → [base]
**Files Changed**: [count] (+[additions]/-[deletions])

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Documentation | ✅/❌/➖ | [details] |
| Security Check | ✅/❌ | [details] |
| Code Quality | ✅/⚠️ | [details] |

### Security Checklist

- [x/] No API keys or tokens
- [x/] No real email addresses
- [x/] No IP addresses
- [x/] No .env files
- [x/] No hardcoded secrets
- [x/] No credential files

### Issues Found

#### Critical (Block Merge)
- [List any critical issues that must be fixed]

#### Warnings (Review Required)
- [List any warnings that need human review]

#### Suggestions (Optional)
- [List any non-blocking suggestions]

### Recommendation

**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**

[Brief justification for the recommendation]

---

## Status Legend

| Icon | Meaning |
|------|---------|
| ✅ | Passed - meets requirements |
| ❌ | Failed - must be fixed before merge |
| ⚠️ | Warning - needs human review |
| ➖ | Not applicable to this PR |
