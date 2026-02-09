---
name: file-indexer
description: Generate a comprehensive file system index with directory tree, file sizes, and modification dates. Use when re-indexing files, updating file index, exploring directory structure, or when user says "re-index files".
allowed-tools: Read, Bash, Write
---

# File System Indexer

Generate comprehensive directory tree views with file sizes and modification dates.

## Quick Commands

### Index Current Workspace
```bash
python3 scripts/index-files.py
```

### Index Specific Directory
```bash
python3 scripts/index-files.py /path/to/directory
```

### Index with Custom Output
```bash
python3 scripts/index-files.py /path/to/directory /path/to/output.md
```

## Output Format

The generated index includes:
- **Header**: Generation timestamp and source directory
- **Tree View**: Hierarchical directory structure with:
  - File/folder sizes in human-readable format
  - Modification dates (YYYY-MM-DD HH:MM:SS)
  - Proper tree characters for visual hierarchy

## Default Paths

| Resource | Path |
|----------|------|
| Default Output | `memory/file_index.md` in workspace |
| Default Directory | Current working directory |

## Exclusions

The indexer automatically skips:
- `.git` directories
- `node_modules` directories
- `__pycache__` directories
- `.venv` and `venv` directories
- Hidden files/folders (starting with `.`) except `.claude`

## Usage Examples

- "Re-index the files" - Run indexer on workspace
- "Update file index" - Regenerate memory/file_index.md
- "Index this directory" - Run on current or specified path
- "Show directory structure" - Generate and display tree view

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Permission denied` | Can't read directory | Check folder permissions, run with appropriate access |
| `Script not found` | Wrong path to index-files.py | Run script from plugin's scripts directory |
| `Output file not writable` | Can't write to memory/ | Check output path permissions, create directory if missing |
| `Python not found` | Python3 not installed | Install Python 3.8+ |
| Indexing takes too long | Very large directory | Consider adding more exclusions or indexing subdirectories separately |
| Missing files in index | Files in excluded directories | Check exclusion list, add exceptions if needed |
