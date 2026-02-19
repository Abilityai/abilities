---
name: setup-index
description: Initialize file indexing for this workspace. Creates file_index.md with directory structure.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(ls:*)
  - Bash(find:*)
  - AskUserQuestion
---

# Setup File Index

Initialize file indexing for this workspace.

## Step 1: Ask Configuration Questions

Use AskUserQuestion to ask the user:

**Question 1**: "Which directories should be indexed?"
- Options:
  - "Current directory only" - Index only the root
  - "All directories (Recommended)" - Full recursive index
  - "Specific directories" - Let me specify which ones

**Question 2**: "What should be excluded from the index?"
- Options:
  - "Standard exclusions (Recommended)" - node_modules, .git, __pycache__, .venv, dist, build
  - "Minimal exclusions" - Only .git
  - "Custom exclusions" - Let me specify

## Step 2: Create Index Configuration

Create `memory/index_config.json` with the user's choices:

```json
{
  "root": ".",
  "exclude_patterns": ["node_modules", ".git", "__pycache__", ".venv", "dist", "build", "*.pyc", ".DS_Store"],
  "include_sizes": true,
  "include_dates": true,
  "last_indexed": null
}
```

## Step 3: Generate Initial Index

Run the indexing command based on configuration:

```bash
find . -type f \
  ! -path "*/node_modules/*" \
  ! -path "*/.git/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/.venv/*" \
  ! -name "*.pyc" \
  ! -name ".DS_Store" \
  -exec ls -lh {} \; 2>/dev/null | \
  awk '{print $9, $5, $6, $7, $8}' | sort
```

## Step 4: Write file_index.md

Create `memory/file_index.md` with format:

```markdown
# File Index

Last updated: [ISO timestamp]

## Directory Tree

[tree structure]

## Files by Directory

### /path/to/dir
| File | Size | Modified |
|------|------|----------|
| file.txt | 1.2K | 2025-01-15 |
```

## Step 5: Confirm Setup

Tell the user:
- File index created at `memory/file_index.md`
- Use `/file-indexing:refresh-index` to update
- Use `/file-indexing:search-files` to search

Add to CLAUDE.md if it exists:
```markdown
## File Index
- Index location: `memory/file_index.md`
- Refresh with: `/file-indexing:refresh-index`
```
