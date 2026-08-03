---
name: [playbook-name]
description: [What it does and when to use it — third person, key use case first]
automation: gated
schedule: "[5-field cron — optional; a scheduled gated run prepares work and parks it at the gate]"
disable-model-invocation: false   # keep false if scheduled — the scheduler's message reaches this skill via model invocation
allowed-tools: [tools]            # include Skill if it composes child skills
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

[One-line statement of what this playbook does.] Prepares work autonomously; nothing irreversible or outbound happens without operator approval at the gate.

## Purpose

[What this playbook accomplishes and what specifically needs a human decision.]

## State Dependencies

| Source | Location | Read | Write | Notes |
|--------|----------|------|-------|-------|
| [name] | [path or API] | ✓ | ✓ | [what it holds] |

## Prerequisites

- [Env keys, tools, and files that must exist — fail with a named, actionable error if missing]

## Process

### Step 1: Read Current State

[Read every state source. Handle the missing/first-run case explicitly.]

### Step 2: [Prepare the Work]

[Draft/stage everything reviewable — the gate shows finished work, not intentions.]

### Step 3: [APPROVAL GATE] — [what needs approval]

Present to the operator:

- [The exact diff / draft / list they must see to decide]

Wait for approval before proceeding. If this run is headless (scheduled), park the prepared work in [state file / operator queue] and end the run — the operator resumes interactively. Never auto-approve.

### Step 4: [Apply Approved Work]

[Apply exactly what was approved; record rejections with rationale.]

### Final Step: Write Updated State

[Write every ✓-Write source, including the record of what was approved/rejected.]

## Completion Checklist

- [ ] Approved items applied exactly as shown; rejected items recorded with rationale
- [ ] [State written and consistent with what was reported]

## Error Recovery

- [Failure mode] → [handling]
- Ambiguous outbound failure → verify against live state before any retry; never blind-retry
