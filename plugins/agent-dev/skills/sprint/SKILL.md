---
name: sprint
description: Human-supervised development cycle — orchestrates roadmap → claim → autoplan → implement → commit for one skill issue
argument-hint: "[issue-number]"
allowed-tools: Bash, Read, Skill
automation: manual
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Sprint

Walks through one complete agent development cycle for a single issue. The implement step is intentionally human-driven — this skill frames and bookends it. The autonomous equivalent is `/work-loop`.

## When to Use

- You want to work on a specific backlog issue with full context at each step
- You want autoplan analysis before touching any skill files
- You're onboarding to the agent and want a guided workflow

## Process

### Step 1: Roadmap Check

Invoke `/roadmap` to show the skill-grouped backlog. This surfaces which skills have the most open work and helps choose a focus area.

If `$ARGUMENTS` is provided (a specific issue number), skip roadmap and go directly to Step 2 with that issue.

### Step 2: Claim

Invoke `/claim` (or `/claim $ARGUMENTS` if an issue number was provided).

If already in-progress from a previous session, continue with that issue and skip to Step 3.

### Step 3: Autoplan

Invoke `/autoplan` on the claimed issue.

The plan will identify:
- Which SKILL.md is affected
- Which section to change
- The right tool to use (adjust-playbook vs create-playbook)
- Any risks

Wait for the plan output before proceeding.

### Step 4: Implement (Human Step)

Print clearly:

```
## Ready to Implement

Based on the autoplan, run one of:

  /adjust-playbook $SKILL_NAME  — to modify an existing skill
  /create-playbook              — to scaffold a new skill

Make your changes, then return here and confirm to commit.
```

Ask the user: "Type 'done' when the implementation is complete, or 'abort' to stop without committing."

If 'abort': do nothing. Leave the issue in-progress for the next session.

### Step 5: Commit

Invoke `/commit` to stage the changed skill files, write the commit message, and close the issue.

### Step 6: Finish

```
## Sprint Complete

Issue #$NUMBER closed.

Run `/sprint` again to start the next issue, or `/backlog` to review remaining work.
```

## Outputs

- One issue moved from todo → done
- One git commit with issue traceability
- Full context at each step before acting

## Notes

- Sprint always works one issue at a time — for bulk processing, use `/work-loop`
- If you want to skip straight to committing (already implemented), run `/commit` directly
- If you want to plan without claiming, run `/autoplan $ISSUE_NUMBER` directly
