#!/usr/bin/env python3
"""
File System Indexer
Generates a comprehensive directory tree with file sizes and modification dates.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.DS_Store'}

# Hidden folders to include
INCLUDE_HIDDEN = {'.claude'}

def format_size(size_bytes):
    """Format size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes:4d}"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}K"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}M"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}G"

def get_dir_size(path):
    """Calculate total size of a directory."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                if should_include(entry.name, is_dir=True):
                    total += get_dir_size(entry.path)
    except (PermissionError, OSError):
        pass
    return total

def should_include(name, is_dir=False):
    """Check if file/directory should be included."""
    if name in SKIP_DIRS:
        return False
    if name.startswith('.'):
        return name in INCLUDE_HIDDEN
    return True

def build_tree(path, prefix="", is_last=True, max_depth=10, current_depth=0):
    """Build tree structure recursively."""
    lines = []
    path = Path(path)

    if current_depth > max_depth:
        return lines

    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        entries = [e for e in entries if should_include(e.name, e.is_dir())]
    except (PermissionError, OSError):
        return lines

    for i, entry in enumerate(entries):
        is_last_entry = (i == len(entries) - 1)
        connector = "└── " if is_last_entry else "├── "

        try:
            stat = entry.stat(follow_symlinks=False)
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            if entry.is_dir(follow_symlinks=False):
                size = get_dir_size(entry.path)
                size_str = format_size(size)
                lines.append(f"{prefix}{connector}[{size_str:>4} {mtime}]  {entry.name}/")

                # Recurse into directory
                extension = "    " if is_last_entry else "│   "
                lines.extend(build_tree(
                    entry.path,
                    prefix + extension,
                    is_last_entry,
                    max_depth,
                    current_depth + 1
                ))
            else:
                size_str = format_size(stat.st_size)
                lines.append(f"{prefix}{connector}[{size_str:>4} {mtime}]  {entry.name}")

        except (PermissionError, OSError) as e:
            lines.append(f"{prefix}{connector}[ERROR]  {entry.name} - {e}")

    return lines

def generate_index(target_dir, output_file=None):
    """Generate the file index."""
    target_path = Path(target_dir).resolve()

    if not target_path.exists():
        print(f"Error: Directory does not exist: {target_path}")
        sys.exit(1)

    # Default output to memory/file_index.md in current working directory
    if output_file is None:
        output_file = Path.cwd() / "memory" / "file_index.md"
    else:
        output_file = Path(output_file)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")

    # Build tree
    print(f"Indexing: {target_path}")

    # Get root directory size
    root_size = get_dir_size(target_path)
    root_mtime = datetime.fromtimestamp(target_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    tree_lines = build_tree(target_path)

    # Generate markdown content
    content = f"""# File System Index

**Generated:** {timestamp}
**Directory:** {target_path}

---

```
[{format_size(root_size):>4} {root_mtime}]  ./
{chr(10).join(tree_lines)}
```

---

*Index contains {len(tree_lines)} entries*
"""

    # Write output
    output_file.write_text(content)
    print(f"Index saved to: {output_file}")
    print(f"Total entries: {len(tree_lines)}")

    return str(output_file)

if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) >= 2:
        target = sys.argv[1]
    else:
        # Default to current working directory
        target = Path.cwd()

    output = sys.argv[2] if len(sys.argv) >= 3 else None

    generate_index(target, output)
