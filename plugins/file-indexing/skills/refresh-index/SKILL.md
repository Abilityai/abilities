---
name: refresh-index
description: Refresh the file index with current directory state
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls:*)
  - Bash(find:*)
  - Bash(wc:*)
---

# Refresh File Index

Update the file index to reflect current workspace state.

## Step 1: Load Configuration

Read `memory/index_config.json` to get exclusion patterns.

If config doesn't exist, use defaults:
- Exclude: node_modules, .git, __pycache__, .venv, dist, build, *.pyc, .DS_Store

## Step 2: Generate Fresh Index

Build exclusion flags from config, then run:

```bash
find . -type f [exclusion flags] -exec ls -lh {} \; 2>/dev/null
```

## Step 3: Format and Write

Update `memory/file_index.md`:

1. Update "Last updated" timestamp
2. Regenerate directory tree
3. Update file listings with current sizes/dates
4. Add summary stats at top:
   - Total files indexed
   - Total size
   - Directories covered

## Step 4: Report Changes

Compare with previous index if available:
- New files added
- Files removed
- Files with size changes

Output summary to user.
