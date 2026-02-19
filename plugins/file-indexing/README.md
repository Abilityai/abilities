# File Indexing Plugin

File system indexing for workspace awareness - creates and maintains a searchable file index.

## Installation

```bash
/plugin install file-indexing@abilityai
```

## Skills

| Skill | Description |
|-------|-------------|
| `/file-indexing:setup-index` | Initialize file indexing (asks configuration questions) |
| `/file-indexing:refresh-index` | Update the index with current file state |
| `/file-indexing:search-files <term>` | Search indexed files by pattern |

## Setup

Run `/file-indexing:setup-index` to initialize. You'll be asked:

1. **Which directories to index** - All, root only, or specific paths
2. **What to exclude** - Standard exclusions (node_modules, .git, etc.) or custom

## Files Created

```
memory/
├── file_index.md        # The searchable file index
└── index_config.json    # Index configuration
```

## Index Format

The file index (`memory/file_index.md`) contains:

- **Summary stats**: Total files, size, last updated
- **Directory tree**: Visual structure overview
- **File listings**: Organized by directory with sizes and dates

## Usage Patterns

**Quick file search:**
```
/file-indexing:search-files .py
/file-indexing:search-files config
/file-indexing:search-files src/
```

**Keep index current:**
```
/file-indexing:refresh-index
```

## Configuration

Edit `memory/index_config.json` to customize:

```json
{
  "root": ".",
  "exclude_patterns": ["node_modules", ".git", "__pycache__"],
  "include_sizes": true,
  "include_dates": true
}
```
