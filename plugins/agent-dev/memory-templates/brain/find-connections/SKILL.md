---
name: find-connections
description: Discover connections between notes in the Brain vault
user-invocable: true
argument-hint: "[note-name or 'all']"
allowed-tools: Read, Grep, Glob, Write
---

# Find Connections

Discover and map connections between notes in the Brain vault.

## Arguments

`$ARGUMENTS` - Either a specific note name or "all" for vault-wide analysis

## Step 1: Load Notes

**If specific note:**
- Read the target note
- Extract its key concepts, tags, and existing links

**If "all" or no argument:**
- Scan `Brain/02-Permanent/` for recent notes (last 14 days)
- Or sample 20 random notes for analysis

## Step 2: Extract Concepts

For each note, identify:
- Main topic/thesis
- Key terms and concepts
- Existing `[[wiki-links]]`
- Tags from frontmatter

## Step 3: Find Semantic Connections

Search for related notes:

```
For each key concept:
  Grep in Brain/02-Permanent/ for the concept
  Exclude the source note itself
  Track which notes mention this concept
```

## Step 4: Classify Connection Types

Categorize found connections:

- **Direct links**: Already linked with `[[note]]`
- **Potential links**: Share concepts but not linked
- **Thematic clusters**: Notes on same broad topic
- **Bridge opportunities**: Could connect two unlinked clusters

## Step 5: Generate Report

Output connection map:

```markdown
## Connection Analysis for [Note/Vault]

### Direct Connections (X notes)
- [[Note A]] - explicitly linked
- [[Note B]] - explicitly linked

### Suggested Connections (X notes)
- **Note C** - shares concept "X" (high relevance)
- **Note D** - shares tags [tag1, tag2]

### Thematic Clusters
1. **Cluster: Topic Name** (X notes)
   - Note 1, Note 2, Note 3

### Isolated Notes (no connections)
- Note X - consider linking to [suggestions]
```

## Step 6: Offer Actions

Ask user:
- "Would you like me to add these suggested connections to the notes?"
- "Should I create a MOC (Map of Content) for any cluster?"

If yes, update the notes' Connections section with new `[[links]]`.

## Step 7: Update Changelog

Append to `Brain/CHANGELOG.md`:

```markdown
## [Today's Date]
- Connection analysis: Found X new connections
- Clusters identified: [list]
```
