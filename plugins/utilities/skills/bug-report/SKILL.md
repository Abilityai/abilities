---
name: bug-report
description: Create a sanitized GitHub issue from a production incident or bug. Redacts sensitive data (IPs, credentials, paths, user data) before submitting to a public or shared repo. Use after investigating an incident or when a reproducible bug is found.
disable-model-invocation: false
user-invocable: true
argument-hint: "[issue title or description]"
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-03-16
  author: Ability.ai
---

# Bug Report

Create a well-structured GitHub issue from an incident or observed bug. Automatically sanitizes sensitive data before submission so it's safe to post to a public or shared repository.

---

## Prerequisites

Requires `gh` CLI authenticated and configured:

```bash
gh auth status
```

The target repository should be set in the environment or prompted:

```bash
GITHUB_REPO=${GITHUB_REPO:-""}  # e.g. "org/repo"
```

---

## Step 1: Gather Bug Information

Read from `$ARGUMENTS` or ask the user:

1. **Title**: Short description of the bug (1 line)
2. **Source**: From a recent incident report? From observation? From logs?
3. **Repo**: Which GitHub repo to file against

If an incident report file exists (e.g. `incidents/*.md`), offer to use it as input:

```bash
ls incidents/*.md 2>/dev/null | sort -r | head -5
```

---

## Step 2: Collect Raw Content

If based on an incident report, read it:

```bash
# Read most recent incident report
LATEST=$(ls incidents/*.md 2>/dev/null | sort -r | head -1)
cat "$LATEST"
```

Otherwise, ask the user to paste or describe:
- Observed behavior
- Expected behavior
- Steps to reproduce
- Relevant error messages or log snippets
- Environment (OS, version, config)

---

## Step 3: Sanitize Sensitive Data

Before writing the issue, replace all sensitive data with safe placeholders.

**Redaction rules:**

| Pattern | Replace with |
|---------|-------------|
| Private IP addresses (10.x, 172.16-31.x, 100.x, 192.168.x) | `[INTERNAL-IP]` |
| Public IP addresses | `[REDACTED-IP]` |
| Tailscale IPs (100.x.x.x) | `[TAILSCALE-IP]` |
| API keys, tokens, secrets (anything matching `key=...`, `token=...`, `secret=...`, `password=...`, `Bearer ...`) | `[REDACTED-SECRET]` |
| SSH private key content | `[REDACTED-KEY]` |
| Email addresses of users | `[USER-EMAIL]` |
| Full filesystem paths with usernames (e.g. `/home/alice/`) | replace username with `[USER]` |
| Database connection strings | `[REDACTED-DB-URL]` |
| Instance-specific hostnames or subdomains | `[INSTANCE-HOSTNAME]` |
| GCP project IDs | `[GCP-PROJECT]` |

Apply these substitutions mentally when drafting the issue body.

---

## Step 4: Draft the Issue

Structure:

```markdown
## Bug Description

[Clear, concise description of the problem. What breaks, when, how often?]

## Observed Behavior

[What actually happens]

## Expected Behavior

[What should happen instead]

## Steps to Reproduce

1. [Step]
2. [Step]
3. [Step]

## Environment

- Version/commit: [git commit hash or version]
- Deployment type: [docker-compose / kubernetes / etc.]
- OS: [if relevant]

## Error Output

```
[Sanitized log excerpts or error messages]
```

## Additional Context

[Any other relevant info — recent deployments, config changes, timing]
```

---

## Step 5: Review with User

Show the user the full sanitized issue draft before submitting.

Ask:
1. "Does this look correct and properly sanitized?"
2. "Any additional context to add?"
3. "Ready to submit?"

Do not submit without explicit confirmation.

---

## Step 6: Submit Issue

If confirmed, determine the repo:

```bash
# Use configured repo or ask
REPO=${GITHUB_REPO:-""}
if [ -z "$REPO" ]; then
  echo "No GITHUB_REPO set. Please provide repo (e.g. org/repo):"
fi
```

Submit:

```bash
gh issue create \
  --repo "$REPO" \
  --title "[title]" \
  --body "[sanitized body]" \
  --label "bug"
```

Optionally add to a project board if `GITHUB_PROJECT` is set:

```bash
ISSUE_URL=$(gh issue create --repo "$REPO" --title "[title]" --body "[body]" --label "bug" --json url -q .url)
gh project item-add ${GITHUB_PROJECT:-""} --owner "${REPO%%/*}" --url "$ISSUE_URL" 2>/dev/null || true
```

---

## Step 7: Confirm

Report to user:
- Issue URL
- Issue number
- Labels applied
- Project board (if added)

Save the issue URL to the incident report if one exists:

```bash
# Append to incident report
echo "\n## GitHub Issue\n$ISSUE_URL" >> "$LATEST" 2>/dev/null || true
```

---

## Sanitization Checklist

Before finalizing, verify the issue body contains none of:

- [ ] Internal IP addresses
- [ ] API keys or tokens
- [ ] User email addresses or PII
- [ ] Absolute filesystem paths with real usernames
- [ ] Instance-specific hostnames
- [ ] Database passwords or connection strings
- [ ] Any value from a `.env` file

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [investigate-incident](../investigate-incident/) | Investigate the incident first |
| [safe-deploy](../safe-deploy/) | Deploy a fix or roll back |
