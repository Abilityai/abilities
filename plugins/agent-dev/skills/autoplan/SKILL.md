---
name: autoplan
description: Analyze a skill issue before implementing — reads the affected SKILL.md, identifies what changes are needed and any risks
argument-hint: "[issue-number]"
allowed-tools: Bash, Read, Glob
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-04-28
  author: Ability.ai
---

# Autoplan

Analyze an open issue before touching any files. Reads the affected skill's SKILL.md, understands the current behavior, and produces a focused implementation plan. Run this after `/claim` and before `/adjust-playbook` or `/create-playbook`.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| GitHub Issues | Current repo | Yes | No | Issue to analyze |
| SKILL.md files | .claude/skills/*/SKILL.md | Yes | No | Current playbook behavior |
| CLAUDE.md | ./CLAUDE.md | Yes | No | Agent identity and constraints |

## Process

### Step 1: Identify the Issue

**If $ARGUMENTS provided:** load that issue number.

**If no argument:** find current in-progress issue:

```bash
gh issue list --label "status:in-progress" --state open --json number,title,body,labels --limit 1
```

If none in-progress, ask user to provide an issue number or run `/claim` first.

### Step 2: Load the Issue

```bash
gh issue view $NUMBER --json number,title,body,labels
```

### Step 3: Identify Affected Skill

Look for a `skill:*` label on the issue. Extract the skill name.

If no skill label:
- Infer from the issue title/body (e.g., "fix claim flow" → likely `claim`)
- Confirm with user: "This looks like it affects `claim`. Is that right, or is it project-level?"

If project-level (no specific skill): note that and skip to Step 6.

### Step 4: Read the Affected Skill

```bash
cat .claude/skills/$SKILL_NAME/SKILL.md
```

If skill doesn't exist yet (this is a new skill issue), note that and skip to Step 5b.

### Step 5a: Analyze the Change (existing skill)

Compare the issue requirements against the current SKILL.md. Identify:

**What section(s) change:**
- Frontmatter (name, description, tools, automation type)?
- A specific step in the Process?
- A new step added?
- Output format changes?
- Error handling?

**Interface impact:**
- Does `argument-hint` change? (affects how users call the skill)
- Does the skill `name` change? (breaking — requires `--archive` flag in adjust-playbook)
- Does `automation` mode change? (autonomous ↔ manual has significant implications)
- Does this affect `work-loop` routing behavior?

**Complexity:**
- Small (1-2 step edits) → `/adjust-playbook $SKILL_NAME`
- Substantial (full flow redesign) → consider `--archive` + new version

### Step 5b: Plan the New Skill (new skill)

If this is a new skill that doesn't exist yet:
- Determine the appropriate tier (Simple / Stateful / Full Playbook)
- List required tools
- Sketch the step flow from the issue requirements
- Note integration points with other skills or work-loop

### Step 6: Produce the Plan

Output a clear, terse implementation plan:

```
## Autoplan: #$NUMBER — $TITLE

**Skill affected:** `$SKILL_NAME`
**Change type:** [Step edit | New step | Interface change | New skill | Project-level]
**Implement with:** `/adjust-playbook $SKILL_NAME` [or `/create-playbook`]

### What to Change

1. [Specific change 1 — which section, what to add/modify]
2. [Specific change 2]

### Risks / Watch-outs

- [e.g., "Changing argument-hint is a user-visible interface change"]
- [e.g., "This step runs in work-loop — verify autonomous compatibility"]
- [e.g., "None — isolated step edit"]

### Recommended Approach

[One sentence: adjust-playbook with specific instruction, or create-playbook with tier]
```

## Outputs

- Section-level analysis of the affected SKILL.md
- Targeted implementation plan
- Risk flags for interface changes, automation changes, or work-loop impact

## Error Handling

| Error | Action |
|-------|--------|
| No in-progress issue and no argument | Ask for issue number or run /claim |
| Skill directory not found | Note as new skill — plan from scratch |
| Issue has no skill label | Infer from content, confirm with user |
