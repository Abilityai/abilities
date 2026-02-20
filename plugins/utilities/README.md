# Utilities Plugin

General-purpose utility skills for conversation management, session archival, and agent productivity.

## Installation

```bash
/plugin install utilities@abilityai
```

## Skills

### save-conversation

Save the current conversation as a structured markdown file for selective history preservation.

**Usage:**
```bash
/save-conversation [topic-name]
```

**Examples:**
```bash
# With explicit topic
/save-conversation debug-auth-timeout

# Let Claude derive topic from conversation
/save-conversation
```

**Output Location:** `saved-conversations/YYYY-MM-DD_topic-name.md`

**Customize Location:** Create `.conversation-config`:
```
storage_path: ./my-conversations
```

Or set environment variable: `CONVERSATION_STORAGE_PATH`

## Why Selective Saving?

Unlike automatic session logs that capture everything, this skill lets you selectively preserve conversations that matter:

- **Important decisions** with rationale documented
- **Solved problems** you might encounter again
- **Research findings** worth referencing
- **Complex workflows** you want to remember

Most conversations don't need to be saved. The ones that do deserve structure and context, not just raw transcripts.

## Output Format

Each saved conversation includes:

- **Summary**: Quick overview
- **Context**: What triggered the conversation
- **Goal**: What was being accomplished
- **Key Exchanges**: Important back-and-forth (summarized)
- **Decisions Made**: Choices and rationale
- **Actions Taken**: What actually changed
- **Outcome**: Final result
- **Insights**: Learnings and gotchas
- **Follow-up**: Remaining tasks

## License

MIT
