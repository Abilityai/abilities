---
name: trinity-compatibility
description: Analyze current agent for Trinity platform compatibility. Use when checking if an agent meets Trinity requirements, preparing for deployment, or auditing agent structure.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Bash(ls *), Bash(cat *)
---

# Trinity Compatibility Analysis

Analyze the current agent directory against Trinity Compatible Agent requirements and produce a detailed compatibility report with actionable remediation steps.

## Trinity Requirements Reference

### Required Files (5 Essential)

1. **template.yaml** - Agent metadata with: name, display_name, description, resources.cpu, resources.memory, credentials
2. **CLAUDE.md** - Domain-specific instructions (the agent's "brain")
3. **.mcp.json.template** - MCP server config using `${VAR}` placeholder syntax (if using MCP servers)
4. **.env.example** - Documentation of required environment variables (no actual values)
5. **.gitignore** - Security-critical exclusions

### Required Directory Structure

```
agent/
├── .git/
├── .gitignore
├── CLAUDE.md
├── README.md
├── template.yaml
├── .claude/
│   ├── agents/
│   ├── commands/
│   ├── skills/
│   ├── skills-library/
│   └── settings.local.json
├── .mcp.json.template
├── .env.example
├── docs/
├── outputs/           # COMMITTED - smaller deliverables
├── content/           # NOT COMMITTED - large generated assets
├── scripts/
└── resources/
```

### .gitignore Must Exclude

**Never commit (credentials/secrets):**
- `.mcp.json`
- `.env`
- `*.pem`, `*.key`
- Credential files

**Never commit (generated/large):**
- `content/` directory
- `.claude/projects/`
- `.claude/statsig/`
- `.claude/todos/`
- `.claude/debug/`

**Always commit:**
- `.claude/commands/`
- `.claude/skills/`
- `.claude/agents/`
- `settings.local.json`
- `outputs/` directory

### template.yaml Required Fields

```yaml
name: lowercase-with-hyphens
display_name: Human Readable Name
description: |
  Multi-line purpose statement
resources:
  cpu: "2"
  memory: "4g"
credentials:
  mcp_servers:
    server_name:
      - VAR_NAME
  env_file:
    - VAR_NAME
```

### Security Requirements

- No hardcoded credentials in any file
- All secrets excluded via .gitignore
- Placeholder syntax `${VAR_NAME}` in .mcp.json.template
- Never push secrets to GitHub

## Analysis Task

1. **Read current agent files:**
   - Check for existence of all 5 required files
   - Read template.yaml and verify required fields
   - Read .gitignore and check for required exclusions
   - Check .mcp.json for hardcoded credentials vs .mcp.json.template with placeholders
   - Scan for any .env files that shouldn't exist

2. **Verify directory structure:**
   - List top-level directories
   - Check for required directories (outputs/, content/, .claude/)
   - Verify .claude/ subdirectories

3. **Security audit:**
   - Grep for potential hardcoded credentials (API keys, tokens, passwords)
   - Check if .mcp.json exists (should only be .mcp.json.template)
   - Verify .env.example exists but .env does not (or is gitignored)

4. **Generate compatibility report:**

```
## Trinity Compatibility Report

### Status: [COMPATIBLE / NEEDS WORK]

### Required Files
| File | Status | Notes |
|------|--------|-------|
| template.yaml | [X] / [ ] | ... |
| CLAUDE.md | [X] / [ ] | ... |
| .mcp.json.template | [X] / [ ] | ... |
| .env.example | [X] / [ ] | ... |
| .gitignore | [X] / [ ] | ... |

### Directory Structure
| Directory | Status | Notes |
|-----------|--------|-------|
| .claude/ | [X] / [ ] | ... |
| outputs/ | [X] / [ ] | ... |
| content/ | [X] / [ ] | ... |
| scripts/ | [X] / [ ] | ... |

### Security Check
| Item | Status | Notes |
|------|--------|-------|
| No hardcoded credentials | [X] / [ ] | ... |
| .mcp.json excluded | [X] / [ ] | ... |
| .env excluded | [X] / [ ] | ... |
| Proper .gitignore | [X] / [ ] | ... |

### Required Actions
1. [Action item with specific file and change needed]
2. [Another action item]
...

### Optional Improvements
- [Nice-to-have improvements]
```

5. **Wait for user approval** before making any changes

Present the report and ask: "Would you like me to implement these changes to make this agent Trinity-compatible?"
