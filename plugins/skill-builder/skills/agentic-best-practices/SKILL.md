---
name: agentic-best-practices
description: Guides Claude in applying best practices for complex multi-step tasks. Use when starting a new project, tackling complex work, planning implementation, or when user says "be thorough", "do this properly", or "follow best practices".
---

# Agentic Best Practices

Apply these principles when working on complex, multi-step tasks.

## Core Principles

### 1. Understand Before Acting

- **Read before writing**: Never modify code you haven't read
- **Explore the codebase**: Use Glob/Grep to understand existing patterns
- **Check for prior art**: Look for similar implementations before creating new ones
- **Understand dependencies**: Know what your changes might affect

### 2. Plan Incrementally

- **Break down large tasks**: Decompose into small, verifiable steps
- **Work in iterations**: Complete one step, verify, then proceed
- **Maintain working state**: Never leave the codebase broken between steps
- **Commit checkpoints**: Save progress at logical milestones

### 3. Verify Continuously

- **Test after each change**: Run relevant tests immediately
- **Check your work**: Re-read files after editing to confirm changes
- **Validate assumptions**: If you assume something, verify it
- **Watch for errors**: Pay attention to tool output and error messages

### 4. Communicate Clearly

- **State what you're doing**: Brief explanation before each action
- **Report outcomes**: Confirm success or explain failures
- **Ask when uncertain**: Use AskUserQuestion for ambiguous requirements
- **Summarize progress**: Provide status updates on long tasks

## Execution Checklist

Before starting work:
- [ ] Understand the full scope of the request
- [ ] Identify files that will be affected
- [ ] Check for existing patterns to follow
- [ ] Plan the sequence of changes

During execution:
- [ ] Make one logical change at a time
- [ ] Verify each change before proceeding
- [ ] Handle errors immediately, don't skip them
- [ ] Keep the user informed of progress

After completion:
- [ ] Verify all changes are correct
- [ ] Run tests if available
- [ ] Summarize what was done
- [ ] Note any follow-up items

## Anti-Patterns to Avoid

**Do NOT:**
- Make changes based on assumptions without verifying
- Skip error messages or warnings
- Make multiple unrelated changes at once
- Leave debugging code or temporary fixes
- Over-engineer beyond what was requested
- Proceed when requirements are unclear

## When to Ask vs Proceed

**Ask the user when:**
- Multiple valid approaches exist
- Requirements are ambiguous
- Changes have significant scope
- Destructive actions are needed

**Proceed autonomously when:**
- Task is clearly defined
- Following established patterns
- Making minor, safe changes
- Fixing obvious bugs

## Skill Portability

Keep skills self-contained and reusable across agents:
- **No hardcoded credentials**: Skills reference env vars, agents provide them
- **Agent owns configuration**: API keys, account IDs, paths live in agent's `.env` or config
- **Skills are pure logic**: Workflow + instructions only, no secrets

```
agent-workspace/
├── .env                 # Agent's credentials (CLOUDINARY_KEY, etc.)
└── .claude/skills/
    └── upload-media/    # Skill references $CLOUDINARY_KEY, doesn't define it
```

## Error Recovery

When something fails:
1. **Stop** - Don't continue with broken state
2. **Diagnose** - Read the error message carefully
3. **Fix** - Address the root cause
4. **Verify** - Confirm the fix worked
5. **Continue** - Resume from a known-good state
