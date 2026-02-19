# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Abilities Plugin Marketplace** - a curated collection of Claude Code plugins from Ability.ai. The project is **documentation-driven**: plugins are defined through YAML frontmatter and procedural markdown instructions, not traditional code.

## Repository Structure

```
.claude-plugin/marketplace.json  # Central registry of all plugins
plugins/
  ├── trinity-onboard/          # Trinity platform deployment
  └── playbook-builder/         # Structured playbook creation
```

Each plugin follows this structure:
```
plugins/[name]/
  ├── .claude-plugin/plugin.json  # Plugin metadata
  ├── README.md                   # User documentation
  ├── skills/[skill-name]/        # Skill-based plugins
  │   ├── SKILL.md               # Skill definition with YAML frontmatter
  │   └── reference.md           # Technical reference
  └── commands/[cmd].md          # Command-based plugins
```

## Plugin Installation

```bash
# Add marketplace (one-time)
/plugin marketplace add abilityai/abilities

# Install plugins
/plugin install trinity-onboard@abilityai
/plugin install playbook-builder@abilityai

# Manual installation from local
/plugin add ./plugins/trinity-onboard
```

## Skill Definition Format

Skills use YAML frontmatter to declare metadata and permissions:

```yaml
---
name: skill-name
description: What the skill does
allowed-tools:
  - Read
  - Write
  - Bash(command:*)
disable-model-invocation: true|false
user-invocable: true|false
argument-hint: "[optional args]"
---
# Procedural instructions follow in markdown
```

Key frontmatter fields:
- `allowed-tools`: Tools the skill can invoke (supports glob patterns like `Bash(python*:*)`)
- `disable-model-invocation`: If true, Claude executes steps without additional reasoning
- `argument-hint`: Shows users expected arguments

## Adding a New Plugin

1. Create directory: `plugins/[plugin-name]/`
2. Add `.claude-plugin/plugin.json`:
   ```json
   {
     "name": "plugin-name",
     "description": "...",
     "version": "1.0.0",
     "author": { "name": "Ability.ai", "email": "support@ability.ai" },
     "license": "MIT"
   }
   ```
3. Add skills in `skills/[skill-name]/SKILL.md` or commands in `commands/[cmd].md`
4. Add `README.md` with usage documentation
5. Register in `marketplace.json` under the `plugins` array with explicit `skills` array (required for skill discovery)

## Marketplace Registration (Critical)

**Skills must be explicitly declared in `marketplace.json`.** Claude Code does NOT auto-discover skills from the `skills/` directory - they must be listed in a `skills` array for each plugin entry:

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin",
  "strict": false,
  "skills": [
    "./skills/skill-one",
    "./skills/skill-two"
  ]
}
```

**When adding a new skill:**
1. Create the skill in `plugins/[name]/skills/[skill-name]/SKILL.md`
2. Add the skill path to the `skills` array in `marketplace.json`
3. Bump the plugin version in `plugin.json`

## Plugin Conventions

- **Report before action**: Generate audit/analysis first, then request approval for changes
- **Archive over delete**: Move files to `archive/` preserving structure instead of deleting
- **Safe artifacts are automatic**: `__pycache__`, `.pyc`, `.DS_Store` can be cleaned without approval
- **Templates use placeholders**: Files ending in `.example` or `.template` use `${VAR_NAME}` syntax
- **Always bump version on changes**: When modifying any plugin file (skills, commands, etc.), increment the patch version in `.claude-plugin/plugin.json`. This ensures client installations detect and sync the update.

## Version Bumping (Required)

**Every change to a plugin requires a version bump.** Without this, client installations won't receive updates when running `/plugin marketplace update`.

```bash
# Before: "version": "2.0.0"
# After:  "version": "2.0.1"
```

**Why:** Claude Code caches plugins locally at `~/.claude/plugins/cache/`. It uses the version number to detect changes. Same version = no update, even if files changed.

**Workflow:**
1. Make your changes to skills/commands/etc.
2. Bump the patch version in `plugins/[name]/.claude-plugin/plugin.json`
3. Commit both changes together

## Skill Versioning

When making breaking changes to a skill, archive the current version before modifying:

```
skills/
  my-skill/       # Current version (always latest)
  my-skill-v1/    # Archived version (frozen)
  my-skill-v2/    # Archived version (frozen)
```

**Rules:**
- **Unversioned = latest**: `/my-skill` runs the current version
- **Versioned = frozen**: `/my-skill-v1` runs that exact version, never changes
- **Archive before breaking changes**: Copy skill directory with version suffix before incompatible changes

**Workflow:**
```bash
# Archive current version before breaking changes
cp -r skills/my-skill skills/my-skill-v2

# Then modify skills/my-skill with new changes
```

Agents can pin to specific versions in their playbooks by calling `/skill-name-vN` explicitly.
