---
name: search-brain
description: Search the Brain vault for notes matching a query
user-invocable: true
argument-hint: "<search-query>"
allowed-tools: Read, Grep, Glob
---

# Search Brain

Search the Brain vault for notes matching a query.

## Arguments

`$ARGUMENTS` - The search query (keywords, tags, or phrases)

## Step 1: Determine Search Type

Analyze the query:

- **Tag search** (starts with #): Search frontmatter tags
- **Title search** (quoted): Search note titles/filenames
- **Content search** (default): Full-text search

## Step 2: Execute Search

**For content search:**
```
Grep pattern="$ARGUMENTS" path="Brain/"
```

**For tag search:**
```
Grep pattern="tags:.*$ARGUMENTS" path="Brain/"
```

**For title/filename:**
```
Glob pattern="Brain/**/*$ARGUMENTS*.md"
```

## Step 3: Rank Results

Order results by relevance:
1. Exact title matches
2. Title contains query
3. Content matches with context
4. Tag matches

## Step 4: Present Results

Format output:

```markdown
## Search Results for "$ARGUMENTS"

Found X notes:

### 1. Note Title
**Path**: Brain/02-Permanent/note-title.md
**Created**: 2025-01-15
**Preview**: ...matching context with **highlighted** terms...

### 2. Another Note
...
```

## Step 5: Suggest Actions

Based on results:
- "No results? Try `/brain-memory:create-note $ARGUMENTS`"
- "Want to see connections? Run `/brain-memory:find-connections <note-name>`"
