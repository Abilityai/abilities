# Brain Memory Plugin

Zettelkasten-style knowledge management - atomic notes with connections and semantic search.

## Installation

```bash
/plugin install brain-memory@abilityai
```

## Skills

| Skill | Description |
|-------|-------------|
| `/brain-memory:setup-brain` | Initialize the Brain vault structure |
| `/brain-memory:create-note <title>` | Create a new permanent note |
| `/brain-memory:search-brain <query>` | Search notes by content/tags |
| `/brain-memory:find-connections [note]` | Discover relationships between notes |

## Setup

Run `/brain-memory:setup-brain` to initialize. Creates:

```
Brain/
├── 00-Inbox/           # Raw captures, new ideas
│   ├── Quick Captures/
│   └── Raw Materials/
├── 01-Sources/         # External source material
│   └── Books/
├── 02-Permanent/       # Core knowledge (atomic notes)
├── 03-MOCs/            # Maps of Content (indexes)
├── 04-Output/          # Generated content
│   ├── Articles/
│   ├── Draft Posts/
│   └── Projects/
├── 05-Meta/            # System files
│   ├── Changelogs/
│   └── Templates/
├── Document Insights/  # Session-based research
└── CHANGELOG.md        # Activity log
```

## Note Format

All notes use YAML frontmatter:

```yaml
---
created: 2025-01-15
updated: 2025-01-15
created_by: claude
updated_by: claude
tags: [topic, subtopic]
---

# Note Title

[Atomic insight - one idea per note]

## Connections

- [[Related Note]] - how it relates
```

## Key Concepts

### Atomic Notes
Each note contains **one idea**. This enables:
- Easy linking between concepts
- Flexible recombination
- Clear attribution

### Connections
Notes link with `[[wiki-style links]]`. The `/find-connections` skill discovers potential links you haven't made yet.

### Maps of Content (MOCs)
Index notes in `03-MOCs/` that organize related permanent notes by theme.

## Workflow

1. **Capture**: Quick ideas go to `00-Inbox/`
2. **Process**: Refine into atomic notes in `02-Permanent/`
3. **Connect**: Run `/find-connections` to discover links
4. **Create**: Generate articles/content in `04-Output/`

## CLAUDE.md Integration

Setup adds this to your CLAUDE.md:

```markdown
## Brain Vault

- All notes MUST have YAML frontmatter
- One atomic idea per note
- Use [[wiki-links]] for connections
- Update CHANGELOG.md after modifications
```
