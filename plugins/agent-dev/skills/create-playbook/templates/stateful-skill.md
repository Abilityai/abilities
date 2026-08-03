---
name: [skill-name]
description: [What it does and when to use it — third person, key use case first]
allowed-tools: [tools]
user-invocable: true
metadata:
  version: "1.0"
  created: [YYYY-MM-DD]
  author: [author]
  changelog:
    - "1.0: Initial version — [one-line summary]"
---

# [Skill Name]

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `[skill-name] vX.Y — recent: <summary>`. Then proceed.

[One-line statement of what this skill does.]

## Purpose

[What this skill accomplishes and when to reach for it.]

## State Dependencies

| Source | Location | Read | Write | Notes |
|--------|----------|------|-------|-------|
| [name] | [path or API] | ✓ | ✓ | [what it holds] |

## Process

### Step 1: Read Current State

[Read every source above before changing anything. Handle the missing/first-run case explicitly.]

### Step 2: [Step Name]

[Instructions.]

### Final Step: Write Updated State

[Write every ✓-Write source. State on disk must match what the skill reports.]

## Outputs

- [What the skill produces]
