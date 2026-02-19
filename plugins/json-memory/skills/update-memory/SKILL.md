---
name: update-memory
description: Update memory after a session with new information and actions
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(jq:*)
  - Bash(mv:*)
  - Bash(date:*)
---

# Update Memory

Update the memory system after a session with new information.

## Step 1: Update Action Log

Prepend new actions to `memory/action_log.txt`:

```bash
# Get current timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Prepend new entry (newest at top)
echo "$timestamp - [Action description]" | cat - memory/action_log.txt > tmp.txt && mv tmp.txt memory/action_log.txt
```

Format each action as:
- `YYYY-MM-DD HH:MM:SS - Brief description of what was done`

## Step 2: Update Context

Update current work state:

```bash
jq '.context.recent_work = ["task1", "task2"] | .context.active_topics = ["topic1"]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

## Step 3: Add Key Facts (if learned)

If new important facts were learned:

```bash
jq '.memory.key_facts += ["New important fact"]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

## Step 4: Update Entities (if new)

If new people/projects/orgs were encountered:

```bash
jq '.entities += [{"type": "person", "name": "Name", "relationship": "role", "added": "YYYY-MM-DD"}]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

## Step 5: Record Decisions (if made)

If significant decisions were made:

```bash
jq '.memory.decisions += [{"date": "YYYY-MM-DD", "decision": "What was decided", "rationale": "Why"}]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

## Step 6: Update Metadata

Always update timestamps and counters:

```bash
jq '.metadata.last_updated = now | todate | .metadata.total_interactions += 1' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

## Step 7: Report

Summarize what was updated:
- X actions logged
- X new facts added
- X entities updated
- Metadata timestamp refreshed
