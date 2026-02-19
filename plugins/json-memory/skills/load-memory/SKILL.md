---
name: load-memory
description: Load memory context at session start using selective queries
user-invocable: true
allowed-tools:
  - Read
  - Bash(jq:*)
---

# Load Memory

Load memory context efficiently at session start.

## Purpose

Load relevant memory sections without reading the entire JSON file.
Use selective jq queries to extract only needed context.

## Step 1: Load Core Identity

```bash
jq '{profile, preferences}' memory/memory_index.json
```

This gives agent identity and communication preferences.

## Step 2: Load Active Context

```bash
jq '{context, active_tasks: .tasks.active}' memory/memory_index.json
```

This shows current work state and pending tasks.

## Step 3: Load Key Facts

```bash
jq '.memory.key_facts' memory/memory_index.json
```

Important facts the agent should always know.

## Step 4: Load Recent Actions

```bash
head -50 memory/action_log.txt
```

Last 50 actions for continuity context.

## Step 5: Load Relevant Entities

```bash
jq '.entities | map(select(.importance == "critical" or .importance == "high"))' memory/memory_index.json
```

Only high-importance entities to avoid context bloat.

## Step 6: Present Summary

Output a concise memory summary:

```markdown
## Memory Loaded

**Profile**: [name] - [role]
**Communication**: [style]
**Active Topics**: [list]
**Key Facts**: [count] facts loaded
**Pending Tasks**: [count] tasks
**Recent Actions**: [last 3 actions]
```

## Selective Loading

The agent should NOT load everything. Priority:
1. Profile & preferences (always)
2. Active context (always)
3. Key facts (always)
4. Pending tasks (always)
5. Entities (high importance only)
6. Decisions (only if relevant to current task)

## Memory Map

Check `memory/memory_map.yaml` for custom files to load.
