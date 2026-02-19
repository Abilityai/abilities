---
name: search-files
description: Search the file index for files matching a pattern or keyword
user-invocable: true
argument-hint: "<search-term>"
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Search Files

Search the file index for files matching the given pattern.

## Arguments

`$ARGUMENTS` - The search term (filename pattern, extension, or keyword)

## Step 1: Load Index

Read `memory/file_index.md` to search within indexed files.

## Step 2: Search Strategy

Based on the search term:

**If extension search** (e.g., ".py", ".md"):
- Filter index for files with that extension
- Report count and list

**If filename pattern** (e.g., "config", "test"):
- Search index for matching filenames
- Use Glob for verification if needed

**If directory search** (e.g., "src/", "tests/"):
- Filter index to show that directory's contents

## Step 3: Report Results

Output:
- Number of matches found
- List of matching files with paths
- Sizes if available from index

If no matches in index, suggest:
- Running `/file-indexing:refresh-index` if index might be stale
- Using Glob directly for real-time search
