---
name: validate-pr
description: Validate a pull request against the project development methodology and generate a merge decision report.
allowed-tools: Bash, Read, Grep
user-invocable: true
argument-hint: "<pr-number-or-url>"
automation: gated
---

# Validate Pull Request

Validate a pull request against the project development methodology and generate a merge decision report.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| PR Details | GitHub API | ✅ | | PR metadata and diff |
| Changelog | `docs/memory/changelog.md` | ✅ | | Entry check |
| Requirements | `docs/memory/requirements.md` | ✅ | | Req updates |
| Architecture | `docs/memory/architecture.md` | ✅ | | API changes |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | | Flow updates |
| GitHub Issues | GitHub repo | ✅ | | Issue references |

## Usage

```
/validate-pr <pr-number-or-url>
```

## Process

### Step 1: Fetch PR Information

```bash
PR_NUMBER=<extract number from argument>
gh pr view $PR_NUMBER --json title,body,author,baseRefName,headRefName,files,additions,deletions,changedFiles
gh pr diff $PR_NUMBER --name-only
gh pr diff $PR_NUMBER
```

### Step 2: Validate Documentation Updates

#### 2.1 Changelog Entry (REQUIRED)
Check if `docs/memory/changelog.md` is in the changed files list.
- Entry at TOP of recent changes
- Has timestamp format: `### YYYY-MM-DD HH:MM:SS`
- Has emoji prefix
- Includes summary of what changed and why

**If missing**: Flag as FAIL - "Changelog not updated"

#### 2.2 GitHub Issues Update (CONDITIONAL)
Check if PR references a GitHub Issue.

#### 2.3 Requirements Update (CONDITIONAL)
Required if PR adds new functionality or changes feature scope.

#### 2.4 Architecture Update (CONDITIONAL)
Required if PR modifies API endpoints, database schema, or external integrations.

### Step 3: Validate Feature Flows

- Check for feature flow changes in diff
- If feature behavior changed but no flow updated: Flag as WARNING
- Validate feature flow format (required sections, file paths with line numbers)

### Step 4: Security Validation

Run security checks on the PR diff:
- API keys and tokens
- Email addresses
- IP addresses
- .env files
- Hardcoded secrets
- Credential files

### Step 5: Code Quality Assessment

- Changes are focused on stated purpose
- No unrelated refactoring
- Follows existing code style

### Step 6: Requirements Traceability

- PR references a requirement ID or describes the feature
- Changes align with documented requirements

### Step 7: Generate Validation Report

```markdown
## PR Validation Report

**PR**: #[number] - [title]
**Author**: [author]
**Branch**: [head] -> [base]
**Files Changed**: [count] (+[additions]/-[deletions])

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| Changelog | ✅/❌ | [details] |
| GitHub Issues | ✅/❌/➖ | [details or N/A] |
| Requirements | ✅/❌/➖ | [details or N/A] |
| Architecture | ✅/❌/➖ | [details or N/A] |
| Feature Flows | ✅/❌/⚠️ | [details] |
| Security Check | ✅/❌ | [details] |
| Code Quality | ✅/⚠️ | [details] |
| Requirements Trace | ✅/⚠️ | [details] |

### Recommendation

**[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]**
```

## Quick Reference: When Documentation is Required

| Change Type | Changelog | Requirements | Architecture | Feature Flow |
|-------------|-----------|--------------|--------------|--------------|
| Bug fix | ✅ | ➖ | ➖ | ⚠️ if behavior changes |
| New feature | ✅ | ✅ | ⚠️ if API/schema | ✅ |
| Refactor | ✅ | ➖ | ⚠️ if structure | ⚠️ if flow changes |
| API change | ✅ | ⚠️ if scope | ✅ | ✅ |
| Schema change | ✅ | ➖ | ✅ | ⚠️ |

## Completion Checklist

- [ ] PR information fetched
- [ ] Changelog validated
- [ ] GitHub Issues checked
- [ ] Requirements checked
- [ ] Architecture checked
- [ ] Feature flows validated
- [ ] Security checks passed
- [ ] Code quality assessed
- [ ] Requirements traced
- [ ] Report generated
- [ ] Recommendation provided
