---
name: setup-brain
description: Initialize a Zettelkasten-style brain vault for knowledge management
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Bash(mkdir:*)
  - AskUserQuestion
---

# Setup Brain Vault

Initialize a Zettelkasten-style knowledge management system.

## Step 1: Ask Configuration

Use AskUserQuestion:

**Question 1**: "Where should the Brain vault be created?"
- Options:
  - "Brain/ folder (Recommended)" - Standard location
  - "Custom location" - Specify a different path

**Question 2**: "What type of knowledge will you primarily store?"
- Options:
  - "General knowledge & insights" - Broad topics
  - "Technical/coding notes" - Development focused
  - "Research & learning" - Academic style
  - "Mixed/All types"

## Step 2: Create Directory Structure

Create the Brain vault structure:

```bash
mkdir -p Brain/00-Inbox/Quick\ Captures
mkdir -p Brain/00-Inbox/Raw\ Materials
mkdir -p Brain/01-Sources/Books
mkdir -p Brain/02-Permanent
mkdir -p Brain/03-MOCs
mkdir -p Brain/04-Output/Articles
mkdir -p Brain/04-Output/Draft\ Posts
mkdir -p Brain/04-Output/Projects
mkdir -p Brain/05-Meta/Changelogs
mkdir -p Brain/05-Meta/Templates
mkdir -p Brain/Document\ Insights
```

## Step 3: Create Essential Files

**Brain/CHANGELOG.md:**
```markdown
# Brain Changelog

## [Session Date]
- Brain vault initialized
- Structure created with standard directories
```

**Brain/04-Output/Articles/ARTICLE-INDEX.md:**
```markdown
# Article Index

Central registry of all articles in the vault.

| Title | Created | Status | Topics |
|-------|---------|--------|--------|
| (none yet) | - | - | - |
```

**Brain/05-Meta/Templates/permanent-note.md:**
```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
created_by: [agent-name]
updated_by: [agent-name]
tags: []
---

# Note Title

[Content goes here]

## Connections

- [[Related Note 1]]
- [[Related Note 2]]
```

## Step 4: Update CLAUDE.md

Add brain configuration to CLAUDE.md:

```markdown
## Brain Vault

Knowledge management using Zettelkasten method.

### Structure
- `Brain/00-Inbox/` - New captures, raw ideas
- `Brain/02-Permanent/` - Atomic, interconnected notes
- `Brain/03-MOCs/` - Maps of Content (indexes)
- `Brain/04-Output/` - Generated content
- `Brain/05-Meta/` - Changelogs and templates

### Note Format
All notes MUST have YAML frontmatter:
- created, updated (dates)
- created_by, updated_by (agent attribution)
- tags (array)

### Commands
- `/brain-memory:create-note` - Create a new permanent note
- `/brain-memory:search-brain` - Search the vault
- `/brain-memory:find-connections` - Discover note relationships
```

## Step 5: Confirm Setup

Report to user:
- Brain vault created at `Brain/`
- X directories created
- Ready to add notes with `/brain-memory:create-note`
