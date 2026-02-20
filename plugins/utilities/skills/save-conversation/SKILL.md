---
name: save-conversation
description: Save the current conversation as a structured markdown file for selective history preservation. Use when a conversation is worth keeping for future reference.
disable-model-invocation: false
user-invocable: true
argument-hint: "[topic-name]"
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
metadata:
  version: "1.0"
  created: 2025-02-20
  author: Ability.ai
---

# Save Conversation

Capture the current conversation as a markdown file in a standardized folder structure. Unlike automatic session logs, this is selective - only save conversations worth preserving.

---

## When to Use

- Completed a meaningful task you want to reference later
- Had a discussion with important decisions or insights
- Debugging session with a solution worth documenting
- Research conversation with findings to preserve
- Any conversation that shouldn't disappear into the void

---

## Configuration

### Storage Location

Default: `saved-conversations/` in the current working directory.

Create a `.conversation-config` file to customize:

```
storage_path: ./my-conversations
```

Or use environment variable: `CONVERSATION_STORAGE_PATH`

---

## Workflow

### Step 1: Determine Topic Name

If provided as argument (`$ARGUMENTS`), use it.

Otherwise, derive from the conversation:
- Identify the primary goal or topic discussed
- Use lowercase-with-hyphens format
- Be descriptive: `debug-auth-token-refresh` not `debugging`
- Prefix with category when appropriate: `research-`, `fix-`, `setup-`

If unclear, ask the user for a topic name.

### Step 2: Check Storage Location

Check for `.conversation-config` file:

```bash
cat .conversation-config 2>/dev/null || echo "not found"
```

Check environment variable:
```bash
echo "${CONVERSATION_STORAGE_PATH:-not set}"
```

Default to `saved-conversations/` if neither exists.

### Step 3: Generate Filename

Format: `YYYY-MM-DD_[topic-name].md`

Example: `2025-02-20_debug-auth-token-refresh.md`

If file already exists, append incrementing number:
- `2025-02-20_topic.md`
- `2025-02-20_topic-2.md`
- `2025-02-20_topic-3.md`

### Step 4: Analyze Conversation

Review the current conversation to extract:

1. **Context**: What triggered this conversation? What was the starting point?
2. **Goal**: What was the user trying to accomplish?
3. **Key Exchanges**: The important back-and-forth (not every message)
4. **Decisions Made**: Choices and their rationale
5. **Actions Taken**: What was actually done (files changed, commands run)
6. **Outcome**: What was the result? Successful? Partial? Needs follow-up?
7. **Insights**: Learnings, gotchas, or things to remember

### Step 5: Generate Markdown

Structure the file as:

```markdown
# [Topic Title]

**Date:** YYYY-MM-DD HH:MM
**Duration:** [Approximate conversation length]
**Outcome:** [Success | Partial | Needs Follow-up | Research]

## Summary

[2-4 sentence overview of what happened]

## Context

[What triggered this conversation? What was the starting state?]

## Goal

[What was the user trying to accomplish?]

## Key Exchanges

### [Exchange 1 Topic]

**User:** [Summarized request or question]

**Claude:** [Summarized response or action]

[Repeat for other significant exchanges]

## Decisions Made

- **[Decision]:** [Rationale]
- **[Decision]:** [Rationale]

## Actions Taken

- [Action 1] → [Result]
- [Action 2] → [Result]

## Outcome

[What was accomplished? What's the final state?]

## Insights

- [Insight or learning 1]
- [Insight or learning 2]

## Follow-up

- [ ] [Any remaining tasks or things to revisit]

---

*Saved from conversation on YYYY-MM-DD*
```

### Step 6: Create Directory and Save

```bash
mkdir -p [storage_path]
```

Write the markdown file:

```bash
# Use Write tool to save the file
```

### Step 7: Confirm to User

Report:

```
Conversation saved to: [full path]

Summary:
- Topic: [topic name]
- Date: [date]
- Outcome: [outcome status]
- [N] key exchanges captured
- [N] actions documented
```

---

## Extraction Guidelines

### What to Include

- **Key decisions**: Choices with significant impact
- **Important commands/code**: Working solutions, not debugging attempts
- **Insights**: Things learned that weren't obvious
- **Final state**: What exists now after the conversation

### What to Exclude

- Trivial exchanges ("Let me check that", "Sure")
- Failed attempts and debugging dead-ends (unless they contain lessons)
- Repeated/redundant information
- Overly detailed step-by-step (summarize instead)

### Summarization Level

| Conversation Type | Detail Level |
|-------------------|--------------|
| Quick fix/task | Brief - just outcome and solution |
| Complex debugging | Medium - include key discoveries |
| Research/exploration | Detailed - capture findings |
| Decision-making | Focus on options considered and rationale |

---

## Examples

### Example 1: Debugging Session

```
User: /save-conversation debug-api-timeout

Extracted:
- Context: API calls failing with 504 errors
- Goal: Fix timeout issues in production
- Key exchange: Identified retry logic bug
- Decision: Increased timeout to 30s, added exponential backoff
- Actions: Modified api-client.ts, deployed to staging
- Outcome: Success - errors resolved
- Insight: Default axios timeout was too low for our backend
```

### Example 2: Research Discussion

```
User: /save-conversation

Claude: What topic should I use for this conversation?

User: comparing-auth-libraries

Extracted:
- Context: Evaluating auth options for new project
- Goal: Choose between Auth0, Clerk, and custom JWT
- Key exchanges: Pros/cons discussion, pricing analysis
- Decision: Go with Clerk for this project
- Actions: None (research only)
- Outcome: Research complete
- Insights: Clerk has better DX, Auth0 better enterprise features
```

---

## Tips

- **Save meaningful conversations only**: This is selective archival, not automatic logging
- **Name descriptively**: Future you should understand the topic from the filename
- **Save before context fades**: Best to save right after concluding
- **Edit after saving**: The generated file is a starting point - refine if needed

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [save-playbook](../../playbook-builder/skills/save-playbook/) | Save as reusable workflow, not just record |
| [json-memory:update-memory](../../json-memory/skills/update-memory/) | Update persistent agent memory |
| [brain-memory:create-note](../../brain-memory/skills/create-note/) | Create atomic knowledge note |
