# Workspace Tools Plugin

File indexing and workspace organization tools for Claude Code.

## Installation

```bash
/plugin install workspace-tools@abilityai
```

## Skills

### `/file-indexer` - Generate File Index

Create a comprehensive directory tree with file sizes and modification dates.

```
/file-indexer                           # Index current workspace
/file-indexer /path/to/directory        # Index specific directory
```

**Output includes:**
- Hierarchical tree view with visual connectors
- File and directory sizes (human-readable)
- Modification timestamps
- Entry count summary

**Default output:** `memory/file_index.md`

**Automatic exclusions:**
- `.git`, `node_modules`, `__pycache__`
- `.venv`, `venv`, `dist`, `build`
- Hidden files (except `.claude`)

### `/workspace-discipline` - File Organization Rules

Enforces workspace organization when creating files.

**Loaded automatically** when you're about to create files.

**Decision tree:**
1. Persistent project work → `docs/` or project folder
2. Generated assets → `assets/reports/`, `assets/visuals/`
3. Session-specific work → `session-files/YYYY-MM-DD_activity/`
4. Scripts/utilities → `scripts/[functional-area]/`
5. Multi-session projects → `projects/[project-name]/`

**File naming:** Always `snake_case` (lowercase with underscores)

## Recommended Structure

```
your-workspace/
├── docs/               # Persistent documentation
├── scripts/            # Utility scripts
├── assets/             # Generated assets
│   ├── reports/
│   └── visuals/
├── projects/           # Multi-session project work
├── session-files/      # Temporary session outputs
│   └── 2025-01-25_client_outreach/
└── memory/             # Agent state (file_index.md lives here)
```

## Example Index Output

```markdown
# File System Index

**Generated:** Sat Jan 25 14:30:00 UTC 2025
**Directory:** /Users/you/project

---

[1.2M 2025-01-25 14:30:00]  ./
├── [156K 2025-01-25 10:00:00]  docs/
│   ├── [ 12K 2025-01-20 09:00:00]  api-guide.md
│   └── [  8K 2025-01-22 11:00:00]  setup.md
├── [ 45K 2025-01-25 14:00:00]  scripts/
│   └── [ 45K 2025-01-25 14:00:00]  automation/
└── [1.0M 2025-01-25 14:30:00]  assets/

---

*Index contains 47 entries*
```

## License

MIT
