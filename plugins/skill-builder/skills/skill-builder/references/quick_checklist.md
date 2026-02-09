# Skill Creation Quick Checklist

## Before You Start
- [ ] Identified 2-3 concrete use cases
- [ ] Tools identified (built-in or MCP)
- [ ] Reviewed example skills
- [ ] Planned folder structure

## During Development

### Structure
- [ ] Folder named in `kebab-case` (no spaces, underscores, or capitals)
- [ ] `SKILL.md` file exists (exact spelling, case-sensitive)
- [ ] NO `README.md` inside skill folder

### Frontmatter
- [ ] YAML has `---` delimiters at start and end
- [ ] `name` field: kebab-case, matches folder name
- [ ] `description` includes:
  - [ ] WHAT it does
  - [ ] WHEN to use it (trigger phrases)
  - [ ] Key capabilities
- [ ] No XML tags (`<` `>`) anywhere
- [ ] Under 1024 characters for description

### Instructions
- [ ] Clear, actionable steps
- [ ] Examples provided
- [ ] Error handling included
- [ ] References linked (not inline)

## Before Upload/Deployment
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)

## After Deployment
- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions

---

## Quick Reference: Frontmatter Fields

```yaml
---
# Required
name: skill-name                    # kebab-case, max 64 chars
description: What + When to use     # max 1024 chars

# Optional - Invocation Control
disable-model-invocation: true      # Only user can invoke
user-invocable: false               # Only Claude can invoke
argument-hint: "[arg1] [arg2]"      # Autocomplete hint

# Optional - Execution
allowed-tools: Read, Grep, Glob     # Restrict available tools
context: fork                       # Run in subagent
agent: Explore                      # Subagent type

# Optional - Metadata
license: MIT
compatibility: "Requires Python 3.9+"
metadata:
  author: Your Name
  version: 1.0.0
---
```

## Quick Reference: String Substitutions

| Variable | Example | Result |
|----------|---------|--------|
| `$ARGUMENTS` | `/skill foo bar` | `foo bar` |
| `$ARGUMENTS[0]` or `$0` | `/skill foo bar` | `foo` |
| `$ARGUMENTS[1]` or `$1` | `/skill foo bar` | `bar` |
| `${CLAUDE_SESSION_ID}` | - | Session UUID |

## Quick Reference: Dynamic Context

```markdown
Current branch: !`git branch --show-current`
Recent commits: !`git log --oneline -5`
```

Commands in `!`backticks`` run before skill loads.
