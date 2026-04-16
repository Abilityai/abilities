---
name: add-memory
description: Add a memory system to an agent — file awareness, knowledge graph, structured state, or multi-session tracking
argument-hint: "[memory-type]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2026-04-16
  author: Ability.ai
---

# Add Memory

Add a memory system to an existing agent. Memory skills are COPIED into the agent's `.claude/skills/` directory — the agent becomes self-contained with no plugin dependency.

## Memory Types

| Type | Description | Skills Installed |
|------|-------------|------------------|
| **file-index** | File system awareness — creates and maintains a searchable file index | setup-index, refresh-index, search-files |
| **brain** | Zettelkasten-style knowledge graph — atomic notes with connections | setup-brain, create-note, search-brain, find-connections |
| **json-state** | Structured JSON state with jq-based updates and action logging | setup-memory, load-memory, update-memory, memory-jq |
| **workspace** | Multi-session project tracking — organized folders, sessions, archives | setup-projects, create-project, create-session, archive-project |

## Process

### Step 1: Determine Agent Directory

Check if we're in an agent directory (has CLAUDE.md) or if user specified a path.

```bash
# Check current directory
if [ -f "CLAUDE.md" ]; then
  AGENT_DIR="$(pwd)"
else
  # Ask user for agent path
fi
```

If no CLAUDE.md found, ask:
- **Question:** "What agent should I add memory to?"
- **Hint:** "Enter the path to the agent directory (should contain CLAUDE.md)"

### Step 2: Check Argument or Ask Memory Type

If user provided an argument (e.g., `/agent-dev:add-memory brain`), use that.

Otherwise, use AskUserQuestion:
- **Question:** "What kind of memory does this agent need?"
- **Header:** "Add Memory"
- **Options:**

  1. **File awareness (file-index)** — "I need the agent aware of workspace files"
     - Creates a searchable index of files in the workspace
     - Good for: agents that need to find and reference files
     
  2. **Knowledge graph (brain)** — "I need connected notes, evolving knowledge"
     - Zettelkasten-style atomic notes with connections
     - Good for: research agents, knowledge management, idea linking
     
  3. **Structured state (json-state)** — "I need counters, config, structured data"
     - JSON-based state with efficient jq updates
     - Good for: tracking metrics, configuration, action logs
     
  4. **Multi-session workspace (workspace)** — "I need organized projects and sessions"
     - Project folders with session tracking and archiving
     - Good for: long-running work, multiple parallel projects

### Step 3: Copy Memory Skills

Memory templates are stored in this plugin at:
```
agent-dev/memory-templates/
  file-index/     # setup-index/, refresh-index/, search-files/
  brain/          # setup-brain/, create-note/, search-brain/, find-connections/
  json-state/     # setup-memory/, load-memory/, update-memory/, memory-jq/
  workspace/      # setup-projects/, create-project/, create-session/, archive-project/
```

Copy the selected memory type's skills into the agent:

```bash
# Get the plugin directory (where this skill lives)
PLUGIN_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
TEMPLATES_DIR="$PLUGIN_DIR/memory-templates"

# Copy skills to agent
cp -r "$TEMPLATES_DIR/[selected-type]/"* "$AGENT_DIR/.claude/skills/"
```

### Step 4: Update Agent CLAUDE.md

Add a section documenting the new memory capabilities:

```markdown
## Memory: [Type Name]

This agent has [type] memory installed. Available skills:
- `/[skill-1]` — description
- `/[skill-2]` — description
...

Run `/[setup-skill]` to initialize.
```

### Step 5: Confirm and Guide

Output:

```markdown
## Memory Added

Installed **[type]** memory to `[agent-name]`.

### New Skills
- `/[skill-1]` — description
- `/[skill-2]` — description

### Next Step
Run `/[setup-skill]` to initialize the memory system.
```

## Notes

- Skills are COPIED, not linked — agent becomes self-contained
- Multiple memory types can be installed in the same agent
- If skills already exist (duplicate names), warn and ask before overwriting
- The setup skill initializes the memory system (creates directories, indexes, etc.)
