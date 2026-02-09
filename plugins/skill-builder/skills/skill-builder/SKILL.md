---
name: skill-builder
description: Expert guide for creating Claude Code skills. Use when user wants to create a new skill, build a skill, design a slash command, or needs help with SKILL.md files, frontmatter, or skill structure. Also use when reviewing or improving existing skills.
---

# Skill Builder - Expert Guide

You are an expert at creating Claude Code skills. Follow this guide precisely when helping users create, review, or improve skills.

## What is a Skill?

A skill is a folder containing instructions that teach Claude how to handle specific tasks or workflows. Skills enable:
- Repeatable workflows with consistent methodology
- Domain expertise embedded in every interaction
- Automated multi-step processes
- Integration with MCP servers

## Skill Structure

```
skill-name/
├── SKILL.md           # Required - main instructions with YAML frontmatter
├── scripts/           # Optional - executable code (Python, Bash, etc.)
├── references/        # Optional - detailed documentation loaded on demand
└── assets/            # Optional - templates, fonts, icons for output
```

**CRITICAL RULES:**
- `SKILL.md` must be exactly this spelling (case-sensitive)
- Folder name must be `kebab-case` (lowercase with hyphens)
- NO `README.md` inside the skill folder
- NO spaces, underscores, or capitals in folder names

## YAML Frontmatter

### Required Format

```yaml
---
name: skill-name
description: What it does. Use when [specific trigger phrases].
---
```

### All Available Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | kebab-case, max 64 chars, must match folder name |
| `description` | Yes | What + When + Capabilities, max 1024 chars |
| `argument-hint` | No | Hint for autocomplete, e.g., `[filename] [format]` |
| `disable-model-invocation` | No | `true` = only user can invoke via `/name` |
| `user-invocable` | No | `false` = hidden from `/` menu, Claude only |
| `allowed-tools` | No | Tools Claude can use without permission prompts |
| `model` | No | Model to use when skill is active |
| `context` | No | `fork` to run in isolated subagent |
| `agent` | No | Subagent type when `context: fork` (Explore, Plan, etc.) |
| `hooks` | No | Lifecycle hooks for this skill |
| `license` | No | For open-source: MIT, Apache-2.0, etc. |
| `compatibility` | No | Environment requirements (max 500 chars) |
| `metadata` | No | Custom key-value pairs (author, version, etc.) |

### Security Restrictions

**FORBIDDEN in frontmatter:**
- XML angle brackets (`<` or `>`)
- Names containing "claude" or "anthropic" (reserved)

## Writing the Description Field

The description is the MOST IMPORTANT part - it determines when Claude loads the skill.

**Structure:** `[What it does] + [When to use it] + [Key capabilities]`

### Good Descriptions

```yaml
# Specific and actionable
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# Includes trigger phrases
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".

# Clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles account creation, payment setup, and subscription management. Use when user says "onboard new customer", "set up subscription", or "create PayFlow account".
```

### Bad Descriptions

```yaml
# Too vague
description: Helps with projects.

# Missing triggers
description: Creates sophisticated multi-page documentation systems.

# Too technical, no user triggers
description: Implements the Project entity model with hierarchical relationships.
```

## String Substitutions

Use these variables in skill content:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` or `$N` | Specific argument by index (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |

**Example:**
```markdown
Fix GitHub issue $ARGUMENTS following our coding standards.
```
Running `/fix-issue 123` gives Claude: "Fix GitHub issue 123 following our coding standards."

## Dynamic Context Injection

The exclamation-backtick syntax (`!` followed by a backtick-wrapped command) runs shell commands before sending to Claude:

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
---

## Pull request context
- PR diff: !`gh pr diff`
- Changed files: !`gh pr diff --name-only`

## Your task
Summarize this pull request...
```

## Invocation Control

| Frontmatter | User can invoke | Claude can invoke | When loaded |
|-------------|-----------------|-------------------|-------------|
| (default) | Yes | Yes | Description always, full skill when invoked |
| `disable-model-invocation: true` | Yes | No | Only when user invokes |
| `user-invocable: false` | No | Yes | Description always, full skill when invoked |

## Skill Categories

### Category 1: Document & Asset Creation
For consistent, high-quality output (documents, presentations, code, designs).

**Key techniques:**
- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing

### Category 2: Workflow Automation
For multi-step processes with consistent methodology.

**Key techniques:**
- Step-by-step workflow with validation gates
- Templates for common structures
- Iterative refinement loops

### Category 3: MCP Enhancement
For workflow guidance enhancing MCP server tool access.

**Key techniques:**
- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Error handling for common MCP issues

## SKILL.md Content Structure

```markdown
---
name: your-skill
description: [What + When + Capabilities]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

Example:
\`\`\`bash
python scripts/fetch_data.py --project-id PROJECT_ID
\`\`\`
Expected output: [describe what success looks like]

### Step 2: [Next Step]
...

## Examples

### Example 1: [Common scenario]
User says: "Set up a new marketing campaign"
Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters
Result: Campaign created with confirmation link

## Troubleshooting

### Error: [Common error message]
**Cause:** [Why it happens]
**Solution:** [How to fix]
```

## Best Practices for Instructions

### Be Specific and Actionable

**Good:**
```markdown
Run `python scripts/validate.py --input {filename}` to check data format.
If validation fails, common issues include:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)
```

**Bad:**
```markdown
Validate the data before proceeding.
```

### Include Error Handling

```markdown
## Common Issues

### MCP Connection Failed
If you see "Connection refused":
1. Verify MCP server is running
2. Confirm API key is valid
3. Try reconnecting
```

### Use Progressive Disclosure

- Keep SKILL.md focused (under 500 lines / 5,000 words)
- Move detailed reference to `references/` folder
- Link to references: "For API details, see [reference.md](references/api-guide.md)"

## Running Skills in Subagents

Add `context: fork` for isolated execution:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---

Research $ARGUMENTS thoroughly:
1. Find relevant files using Glob and Grep
2. Read and analyze the code
3. Summarize findings with specific file references
```

## Pre-Creation Checklist

Before creating a skill, gather:
- [ ] 2-3 concrete use cases
- [ ] Tools needed (built-in or MCP)
- [ ] Trigger phrases users would say
- [ ] Step-by-step workflow
- [ ] Error scenarios and handling

## Validation Checklist

Before finalizing:
- [ ] Folder named in kebab-case
- [ ] SKILL.md exists (exact spelling)
- [ ] YAML frontmatter has `---` delimiters
- [ ] `name` field: kebab-case, no spaces/capitals
- [ ] `description` includes WHAT and WHEN
- [ ] No XML tags (`<` `>`) anywhere
- [ ] Instructions are clear and actionable
- [ ] Error handling included
- [ ] Examples provided

## Troubleshooting Guide

### Skill doesn't trigger
- Description too vague - add specific trigger phrases
- Missing keywords - include terms users would say
- Test: Ask Claude "When would you use the [skill] skill?"

### Skill triggers too often
- Add negative triggers: "Do NOT use for..."
- Be more specific about scope
- Clarify with service/context names

### Instructions not followed
- Instructions too verbose - use bullet points
- Critical instructions buried - put at top with `## Important`
- Ambiguous language - be explicit with validation criteria

### Large context issues
- SKILL.md too large - move docs to `references/`
- Too many skills enabled - consider skill "packs"

## Creating the Skill

When user wants to create a skill:

1. **Gather requirements** - Ask about use cases, triggers, tools needed
2. **Design the structure** - Determine if subagent, MCP, or standalone
3. **Write frontmatter** - Focus on excellent description
4. **Write instructions** - Clear, actionable, with examples
5. **Add error handling** - Common issues and solutions
6. **Validate** - Run through checklist
7. **Create files** - Use proper directory structure

For detailed patterns and examples, see [references/patterns.md](references/patterns.md).
