---
name: setup-memory
description: Initialize JSON-based memory system with structured sections
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(mkdir:*)
  - AskUserQuestion
---

# Setup JSON Memory

Initialize a structured JSON memory system for persistent agent state.

## Step 1: Ask Configuration

Use AskUserQuestion:

**Question 1**: "What type of agent is this memory for?"
- Options:
  - "Business assistant" - Profile, entities, tasks focus
  - "Personal assistant" - Preferences, reminders focus
  - "Technical agent" - Context, project tracking focus
  - "General purpose (Recommended)" - All sections

**Question 2**: "Should the memory track action history?"
- Options:
  - "Yes (Recommended)" - Creates action_log.txt
  - "No" - Memory only, no action log

## Step 2: Create Directory Structure

```bash
mkdir -p memory
```

## Step 3: Create Memory Index

Write `memory/memory_index.json`:

```json
{
  "metadata": {
    "schema_version": "1.0",
    "created": "[ISO timestamp]",
    "last_updated": "[ISO timestamp]",
    "total_interactions": 0
  },
  "profile": {
    "name": null,
    "role": null,
    "context": null
  },
  "preferences": {
    "communication_style": null,
    "tools": []
  },
  "memory": {
    "key_facts": [],
    "decisions": [],
    "project_overviews": []
  },
  "context": {
    "active_topics": [],
    "recent_work": [],
    "scratchpad": null
  },
  "entities": [],
  "tasks": {
    "active": [],
    "completed": []
  },
  "custom": {}
}
```

## Step 4: Create Action Log (if enabled)

Write `memory/action_log.txt`:

```
# Action Log
# Format: YYYY-MM-DD HH:MM:SS - Action description
# Newest entries at top

[ISO timestamp] - Memory system initialized
```

## Step 5: Create Memory Map

Write `memory/memory_map.yaml`:

```yaml
# Memory System Map
# High-signal index of memory components

memory_index:
  path: memory/memory_index.json
  load: selective  # Use jq queries, not full load
  sections:
    - profile
    - preferences
    - context
    - entities

action_log:
  path: memory/action_log.txt
  load_lines: 50  # Most recent entries

custom_files: []
```

## Step 6: Update CLAUDE.md

Add memory configuration:

```markdown
## Memory System

JSON-based persistent memory in `memory/` folder.

### Loading Memory
Use `/json-memory:load-memory` to load context at session start.
Load selectively - don't read entire memory_index.json.

### Updating Memory
Use `/json-memory:memory-jq` for efficient field updates.
Use `/json-memory:update-memory` after significant changes.

### Memory Sections
- `profile` - User/agent identity
- `preferences` - Settings and styles
- `memory.key_facts` - Important facts to remember
- `context` - Current work state
- `entities` - People, projects, orgs
- `tasks` - Active and completed items

### Action Log
`memory/action_log.txt` - Reverse chronological action history.
Newest entries at top. Load last 50 lines for context.
```

## Step 7: Confirm

Report:
- Memory system created at `memory/`
- Use `/json-memory:load-memory` to load context
- Use `/json-memory:update-memory` to save changes
