# JSON Memory Plugin

Structured JSON memory system with efficient jq-based updates and action logging.

## Installation

```bash
/plugin install json-memory@abilityai
```

## Skills

| Skill | Description |
|-------|-------------|
| `/json-memory:setup-memory` | Initialize the memory system |
| `/json-memory:load-memory` | Load context at session start |
| `/json-memory:update-memory` | Save changes after a session |
| `/json-memory:memory-jq <op> <path> [value]` | Direct jq-based field updates |

## Setup

Run `/json-memory:setup-memory` to initialize. Creates:

```
memory/
├── memory_index.json   # Primary structured memory
├── memory_map.yaml     # Index of memory components
└── action_log.txt      # Reverse-chronological action history
```

## Memory Structure

The `memory_index.json` contains these sections:

```json
{
  "metadata": { "schema_version", "last_updated", "total_interactions" },
  "profile": { "name", "role", "context", "objectives" },
  "preferences": { "communication_style", "tools" },
  "memory": { "key_facts", "decisions", "project_overviews" },
  "context": { "active_topics", "recent_work", "scratchpad" },
  "entities": [{ "type", "name", "relationship", "importance" }],
  "tasks": { "active": [], "completed": [] },
  "custom": {}
}
```

## Key Principles

### Selective Loading
Never load the entire memory file. Use jq queries:

```bash
# Load only profile and context
jq '{profile, context}' memory/memory_index.json
```

### Atomic Updates
Use the tmp file pattern to avoid corruption:

```bash
jq '.field = "value"' file.json > tmp.json && mv tmp.json file.json
```

### Action Log Format
Newest entries at top, load last 50 lines:

```
2025-01-15 14:30:00 - Completed task X
2025-01-15 14:00:00 - Started working on Y
```

## Common JQ Patterns

```bash
# Set a field
/json-memory:memory-jq set .profile.name "Agent Name"

# Append to array
/json-memory:memory-jq append .memory.key_facts "Important fact"

# Increment counter
/json-memory:memory-jq increment .metadata.total_interactions

# Read a field
/json-memory:memory-jq get .profile.name
```

## Workflow

1. **Session Start**: Run `/json-memory:load-memory`
2. **During Session**: Use `/json-memory:memory-jq` for quick updates
3. **Session End**: Run `/json-memory:update-memory` to persist changes

## CLAUDE.md Integration

Setup adds memory instructions to CLAUDE.md ensuring the agent:
- Loads memory selectively at session start
- Uses jq patterns for efficient updates
- Maintains action log for continuity
