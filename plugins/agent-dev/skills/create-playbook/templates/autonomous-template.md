---
name: [playbook-name]
description: [What it does and when to use it — third person, key use case first]
automation: autonomous
schedule: "[5-field cron]"
disable-model-invocation: false   # required for scheduled playbooks — the scheduler's message reaches this skill via model invocation
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

[One-line statement of what this playbook does.] Runs unattended: no approval gates, no questions to the user, one task type per invocation — the scheduler handles repetition.

## Purpose

[What this playbook accomplishes and why it is safe to run without a human.]

## State Dependencies

| Source | Location | Read | Write | Notes |
|--------|----------|------|-------|-------|
| [name] | [path or API] | ✓ | ✓ | [what it holds] |

## Prerequisites

- [Env keys, tools, and files that must exist — fail with a named, actionable error if missing]

## Composes

<!-- Optional: child skills this playbook invokes. Every child must be autonomous-safe
     (no gates, no questions) — autonomy is transitive. A child using `context: fork`
     must set `background: false` or the fork is reaped at turn-end in a headless run. -->

- `/[child-skill]` — [why]

## Process

### Step 1: Read Current State

[Read every state source. Handle the missing/first-run case explicitly.]

### Step 2: [Work]

[One task type. The whole run completes in under 45 minutes. Any job over ~10 minutes
is decoupled to an OS-level cron/systemd/sidecar + done-marker — this run only triggers
it and verifies the artifact moved (mtime advanced AND count > 0), never trusting exit codes.]

### Step N: Write Updated State

[Write every ✓-Write source. State on disk must match what the run reports.]

### Final Step: Report (guarded)

If the `mcp__trinity__report` tool is available, publish the run's result — `report_type: "[agent].[result]"` (lower_snake), a short `title`, a JSON `payload`, and a `display_hint` (`table` / `kpi` / `markdown` / `timeline`). If the tool is absent (running locally), skip silently — reporting is an upgrade, never a gate.

## Completion Checklist

- [ ] [State written and consistent with what was reported]
- [ ] [Artifact verified moved — never declared done off an exit code]
- [ ] [Failures alerted via [channel] — a silent failure is a failure of the playbook]

## Error Recovery

- [Failure mode] → [handling — must resolve without a human: alert, park, or retry once; never hang]
