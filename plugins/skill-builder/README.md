# Skill Builder Plugin

Expert guidance for creating Claude Code skills and following agentic best practices.

## Installation

```bash
/plugin install skill-builder@abilityai
```

## Skills

### `/skill-builder` - Create New Skills

Expert guide for designing, creating, and validating Claude Code skills.

```
/skill-builder                    # Start skill creation wizard
/skill-builder review             # Review existing skills
```

**Covers:**
- YAML frontmatter format and all available fields
- Skill structure and folder conventions
- Description writing (the most important part)
- Invocation control (user-only, Claude-only, both)
- Dynamic context injection with `!`backticks``
- String substitutions (`$ARGUMENTS`, `$0`, `$1`, etc.)
- Testing and validation checklists

### `/agentic-best-practices` - Work Thoughtfully

Guidance for complex multi-step tasks.

```
/agentic-best-practices           # Apply best practices to current work
```

**Core Principles:**
1. **Understand before acting** - Read before writing, explore the codebase
2. **Plan incrementally** - Break down tasks, work in iterations
3. **Verify continuously** - Test after each change, validate assumptions
4. **Communicate clearly** - State what you're doing, ask when uncertain

## Skill Structure Reference

```
skill-name/
├── SKILL.md           # Required - main instructions
├── scripts/           # Optional - executable code
├── references/        # Optional - detailed documentation
└── assets/            # Optional - templates, fonts, icons
```

**Critical rules:**
- `SKILL.md` must be exactly this spelling (case-sensitive)
- Folder name must be `kebab-case`
- NO `README.md` inside skill folders
- NO spaces, underscores, or capitals in folder names

## Frontmatter Quick Reference

```yaml
---
name: skill-name                    # kebab-case, max 64 chars
description: What + When to use     # max 1024 chars

# Optional - Invocation Control
disable-model-invocation: true      # Only user can invoke
user-invocable: false               # Only Claude can invoke
argument-hint: "[arg1] [arg2]"      # Autocomplete hint

# Optional - Execution
allowed-tools: Read, Grep, Glob     # Restrict available tools
context: fork                       # Run in subagent
agent: Explore                      # Subagent type
---
```

## License

MIT
