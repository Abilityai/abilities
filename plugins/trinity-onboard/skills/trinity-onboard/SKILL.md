---
name: trinity-onboard
description: Convert any Claude Code agent to Trinity-compatible format. Use for initial setup, structure analysis, and methodology adoption.
argument-hint: "[analyze|adopt]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
metadata:
  version: "3.0"
  created: 2025-02-05
  author: eugene
  changelog:
    - "3.0: Focused scope - adoption only. Remote ops moved to /trinity-remote"
    - "2.0: Added remote execution, deploy-run, and notification features"
    - "1.0: Initial version"
---

# Trinity Methodology Adoption

Convert any Claude Code agent to Trinity-compatible format following best practices.

```
ADOPT → DEVELOP → DEPLOY → RUN → MONITOR
(THIS    (Local)   (Sync)   (Remote)  (Notify)
SKILL)
```

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity-compatibility` | Read-only audit of current state |
| `/trinity-onboard` | **This skill** - Implement changes to become Trinity-compatible |
| `/trinity-sync` | Git-based synchronization with remote |
| `/trinity-remote` | Remote agent operations (execute, deploy-run) |
| `/trinity-schedules` | Scheduled task management |

## Command Modes

Parse `$ARGUMENTS` to determine mode:

| Command | Mode | Description |
|---------|------|-------------|
| `/trinity-onboard` | adopt | Full adoption workflow (default) |
| `/trinity-onboard analyze` | analyze | Analysis only, no changes |

---

## What is Trinity Methodology?

A maturity model for business agent development:

```
EXPLORE → ADOPT → CODIFY → SCHEDULE → AUTONOMOUS
(Manual)   (You    (Build    (Trinity   (Monitored
           are     policies/  runs it)   execution)
           here)   procedures)
```

**Key principle:** Skills, policies, and procedures ARE the agent. Everything else is runtime state.

---

## Mode: Analyze Only (`analyze`)

Run analysis without making changes. Equivalent to `/trinity-compatibility`.

### Workflow

1. **Check current state**
2. **Generate compatibility report**
3. **List required changes** (but don't implement)

---

## Mode: Full Adoption (`adopt` - default)

Convert the current agent to Trinity-compatible format.

### Step 1: Current State Analysis

```bash
ls -la
ls .claude/ 2>/dev/null
ls .claude/skills/ 2>/dev/null
ls -d .claude/skills/policy-* .claude/skills/procedure-* 2>/dev/null
```

### Step 2: Present Adoption Report

```
## Trinity Adoption Analysis

### Current State
- Agent directory: [path]
- CLAUDE.md: [exists/missing]
- .claude/skills/: [count] skills
- Existing policies: [list or none]
- Existing procedures: [list or none]

### Required for Adoption
| Component | Status | Action Needed |
|-----------|--------|---------------|
| CLAUDE.md | [X]/[ ] | [action] |
| template.yaml | [X]/[ ] | [action] |
| .mcp.json.template | [X]/[ ] | [action] |
| .env.example | [X]/[ ] | [action] |
| .gitignore | [X]/[ ] | [action] |
| outputs/ | [X]/[ ] | [action] |
| scripts/ | [X]/[ ] | [action] |
```

### Step 3: Confirm Adoption

Ask user: "Ready to adopt Trinity methodology? This will:
1. Create missing required files
2. Set up directory structure
3. Create initial policy: policy-agent-purpose

Proceed? [Y/n]"

### Step 4: Execute Adoption

**4a. Create Required Directories**
```bash
mkdir -p outputs scripts .claude/skills .claude/agents memory
```

**4b. Create template.yaml (if missing)**

First, detect the agent name:
```bash
# Try to get from existing template.yaml
grep "^name:" template.yaml 2>/dev/null | cut -d: -f2 | tr -d ' '
# Or use directory name
basename "$(pwd)"
```

```yaml
name: [agent-name-from-directory]
display_name: [Agent Display Name]
description: |
  [To be filled - describe this agent's purpose]
resources:
  cpu: "2"
  memory: "4g"
credentials:
  mcp_servers: {}
  env_file: []
```

**4c. Create .env.example (if missing)**
```
# Environment variables for [agent-name]
# Copy to .env and fill in values
```

**4d. Create/Update .gitignore**

Ensure these exclusions exist:

```gitignore
# Credentials - never commit
.mcp.json
.env
*.pem
*.key

# Claude Code internals
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/

# Runtime/generated
content/
session-files/
```

**4e. Create .mcp.json.template (if .mcp.json exists)**

Convert `.mcp.json` to `.mcp.json.template` with `${VAR_NAME}` placeholders:

1. Read `.mcp.json`
2. Identify credential values (API keys, tokens, paths with user-specific content)
3. Replace with `${VAR_NAME}` placeholders
4. Write to `.mcp.json.template`
5. Document variables in `.env.example`

### Step 5: Create Initial Policy

Create `.claude/skills/policy-agent-purpose/SKILL.md`:

```markdown
---
name: policy-agent-purpose
description: Defines this agent's core purpose, scope, and boundaries.
user-invocable: false
metadata:
  version: "1.0"
  created: [today]
---

# Agent Purpose Policy

## Identity
- **Name**: [agent-name]
- **Owner**: [user-name]
- **Domain**: [business domain]

## Purpose
[What this agent does]

## Scope
- **In scope**: [what this agent handles]
- **Out of scope**: [what this agent should NOT do]

## Boundaries
- Never access systems outside defined integrations
- Always confirm destructive operations
- Escalate to human when uncertain
```

### Step 6: Confirm Completion

```
## Trinity Adoption Complete

### Created/Updated
- [x] template.yaml
- [x] .env.example
- [x] .gitignore
- [x] policy-agent-purpose

### Directory Structure
- [x] outputs/
- [x] scripts/
- [x] .claude/skills/
- [x] .claude/agents/
- [x] memory/

### Next Steps
1. Edit policy-agent-purpose to define this agent's purpose
2. Review and customize template.yaml
3. Run `/trinity-sync push` to deploy to remote
4. Configure notifications with `/trinity-remote notify`
```

---

## Trinity Requirements Reference

### Required Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Agent's main instructions (the "brain") |
| `template.yaml` | Trinity deployment metadata |
| `.mcp.json.template` | MCP config with `${VAR}` placeholders |
| `.env.example` | Documents required environment variables |
| `.gitignore` | Security-critical exclusions |

### Required Directories

| Directory | Purpose | Commit? |
|-----------|---------|---------|
| `.claude/skills/` | Agent capabilities | YES |
| `.claude/agents/` | Sub-agent definitions | YES |
| `memory/` | Persistent state, schedules | YES |
| `scripts/` | Automation scripts | YES |
| `outputs/` | Smaller deliverables | YES |
| `content/` | Large generated content | NO |
| `session-files/` | Session-specific work | NO |

### .gitignore Must Exclude

**Credentials (never commit):**
- `.mcp.json`
- `.env`
- `*.pem`, `*.key`

**Runtime state (discard):**
- `.claude/projects/`
- `.claude/statsig/`
- `.claude/todos/`
- `.claude/debug/`
- `content/`
- `session-files/`

---

## Error Handling

| Error | Resolution |
|-------|------------|
| No CLAUDE.md | Create minimal CLAUDE.md from template.yaml description |
| .mcp.json has secrets | Extract to .mcp.json.template with placeholders |
| Directory not a git repo | Run `git init` first |

---

## See Also

- `/trinity-compatibility` - Read-only audit
- `/trinity-sync` - Git synchronization
- `/trinity-remote` - Remote operations
- `/trinity-schedules` - Scheduled tasks
