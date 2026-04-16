---
name: create-note
description: Create a new permanent note in the Brain vault with proper metadata
user-invocable: true
argument-hint: "<note-title>"
allowed-tools: Read, Write, Glob, Grep
---

# Create Note

Create a new atomic note in the Brain vault.

## Arguments

`$ARGUMENTS` - The note title or topic

## Step 1: Generate Note Metadata

Create the note with proper YAML frontmatter:

```yaml
---
created: [today's date YYYY-MM-DD]
updated: [today's date YYYY-MM-DD]
created_by: claude
updated_by: claude
tags: []
---
```

## Step 2: Determine Note Type

Based on the content/title, place the note in:

- **Raw idea/capture** → `Brain/00-Inbox/Quick Captures/`
- **External source material** → `Brain/01-Sources/`
- **Processed insight** → `Brain/02-Permanent/`
- **Index/overview** → `Brain/03-MOCs/`
- **Article/content** → `Brain/04-Output/Articles/`

Default to `Brain/02-Permanent/` for most notes.

## Step 3: Check for Duplicates

Search existing notes for similar titles or content:

```
Grep for the main keywords in Brain/02-Permanent/
```

If similar notes exist:
- Show user the potential duplicates
- Ask if they want to proceed or link to existing

## Step 4: Write the Note

Create the file with kebab-case filename:
- Title: "My Great Insight" → `my-great-insight.md`

Structure:
```markdown
---
[frontmatter]
---

# [Title]

[Main content - atomic, single idea]

## Key Points

- Point 1
- Point 2

## Connections

- [[Related Note]] - relationship description
```

## Step 5: Update Changelog

Append to `Brain/CHANGELOG.md`:

```markdown
## [Today's Date]
- Created: [note-title] in 02-Permanent/
```

## Step 6: Report

Tell user:
- Note created at [path]
- Suggest running `/brain-memory:find-connections` to discover links
