---
name: memory-jq
description: Efficiently update JSON memory fields using jq patterns
user-invocable: true
argument-hint: "<operation> <path> <value>"
allowed-tools: Read, Bash
---

# Memory JQ

Efficiently update JSON memory fields without loading the entire file.

## Arguments

`$ARGUMENTS` - Operation in format: `<operation> <json-path> [value]`

Operations:
- `set` - Set a field value
- `append` - Add to an array
- `increment` - Increment a number
- `get` - Read a field value

## Common Patterns

### Set a simple field
```bash
jq '.profile.name = "Value"' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Set with variable (use --arg)
```bash
jq --arg val "New Value" '.profile.name = $val' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Append to array
```bash
jq '.memory.key_facts += ["New fact to remember"]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Update timestamp
```bash
jq '.metadata.last_updated = now | todate' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Increment counter
```bash
jq '.metadata.total_interactions += 1' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Add entity
```bash
jq '.entities += [{"type": "person", "name": "John", "relationship": "client"}]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Update nested field
```bash
jq '.context.active_topics = ["topic1", "topic2"]' memory/memory_index.json > tmp.json && mv tmp.json memory/memory_index.json
```

### Read a field (get operation)
```bash
jq '.profile.name' memory/memory_index.json
```

### Read array length
```bash
jq '.memory.key_facts | length' memory/memory_index.json
```

## Execution

1. Parse the user's `$ARGUMENTS` to determine operation
2. Construct the appropriate jq command
3. Execute with atomic write (tmp file + mv)
4. Report the change made

## Safety

- Always use tmp file pattern to avoid corruption
- Validate JSON after write with `jq '.' memory/memory_index.json`
- Report errors if jq fails
