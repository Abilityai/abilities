# Process Miner

Analyze Claude Code execution logs to discover workflow patterns and generate process definitions.

## Installation

```bash
/plugin marketplace add abilityai/abilities
/plugin install process-miner@abilityai
```

## Usage

```bash
/process-miner
```

The skill will:
1. Locate your Claude Code transcripts
2. Analyze tool usage patterns
3. Classify user intents
4. Generate a report with discovered workflows
5. Produce YAML process definitions for proven patterns

## What It Analyzes

### Level 1: Tool Sequences
- N-gram analysis of tool calls (e.g., "Read -> Edit -> Read")
- Tool frequency counts
- MCP integration usage

### Level 2: Session Themes
- Files and directories worked on
- Domain analysis
- Read-to-write ratios

### Level 3: User Intent Patterns
- Recurring business workflows
- Common "jobs to be done"
- Trigger phrase patterns

## Output

### Analysis Report
```markdown
# Agent Process Mining Report

## Executive Summary
- Primary use case: DOCUMENT_CREATION (45% of sessions)
- Secondary use case: RESEARCH (30% of sessions)
- Agent profile: Content creation assistant

## Proven Workflows

### 1. Document Creation
- Occurrences: 12 sessions
- Trigger Examples:
  - "Create a report about..."
  - "Write a summary of..."
- Common Tools: [Read, WebSearch, Write]
```

### Process YAML
```yaml
name: document-creation
version: "1.0"
description: |
  Creates documents based on research.

steps:
  - id: research
    name: Gather Information
    type: agent_task
    agent: claude-code
    message: Research the topic

  - id: write
    name: Create Document
    type: agent_task
    agent: claude-code
    message: Write the document
    depends_on: [research]
```

## Files

- `skills/process-miner/SKILL.md` - Main skill definition
- `skills/process-miner/reference.md` - Technical reference

## License

MIT
