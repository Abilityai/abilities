---
name: [playbook-name]
description: [What it does and when to use it — third person, key use case first]
automation: manual
allowed-tools: [tools]
user-invocable: true
metadata:
  version: "1.0"
  created: [YYYY-MM-DD]
  author: [author]
  changelog:
    - "1.0: Initial version — [one-line summary]"
---

# [Playbook Name]

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `[playbook-name] vX.Y — recent: <summary>`. Then proceed.

[One-line statement of what this playbook does.] Interactive — the operator drives; the skill structures the session. Never scheduled.

## Purpose

[What this playbook accomplishes and why it needs the operator in the loop throughout.]

## State Dependencies

| Source | Location | Read | Write | Notes |
|--------|----------|------|-------|-------|
| [name] | [path or API] | ✓ | ✓ | [what it holds] |

## Prerequisites

- [Env keys, tools, and files that must exist]

## Process

### Step 1: Read Current State

[Read every state source before presenting anything.]

### Step 2: [Present Findings / Options]

[Show the operator what the data says; ask only where the input is genuinely theirs to give.]

### Step 3: [Execute the Operator's Choice]

[Instructions.]

### Final Step: Write Updated State

[Write every ✓-Write source, including decisions made and their rationale.]

## Completion Checklist

- [ ] [Decisions recorded with rationale]
- [ ] [State written and consistent with the session]

## Error Recovery

- [Failure mode] → [handling]
