---
name: onboard
description: Onboard this agent to Trinity platform. Creates required files, sets up git, deploys to Trinity, and installs Trinity skills for ongoing management.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__trinity__list_agents, mcp__trinity__create_agent, mcp__trinity__get_agent, mcp__trinity__start_agent
metadata:
  version: "1.0"
  author: Ability.ai
---

# Trinity Onboarding

Zero-friction onboarding to deploy any Claude Code agent to the Trinity platform.

## What This Skill Does

1. **Discovery** - Identify agent name, check existing Trinity files
2. **Compatibility Analysis** - Generate report of current state vs requirements
3. **User Confirmation** - Present report, ask to proceed
4. **Create Required Files** - template.yaml, .gitignore, .env.example, .mcp.json.template
5. **Git Setup** - Initialize git if needed, commit, push
6. **Deploy to Trinity** - Call MCP tool to deploy agent
7. **Completion Report** - Show what was done, next steps

---

## Phase 1: Discovery

Gather information about the current agent:

```bash
# Get agent name from template.yaml or directory
AGENT_NAME=$(grep "^name:" template.yaml 2>/dev/null | cut -d: -f2 | tr -d ' ' || basename "$(pwd)")
echo "Agent name: $AGENT_NAME"

# Check what already exists
ls -la template.yaml .mcp.json.template .env.example .gitignore 2>/dev/null
ls -la .claude/skills/ 2>/dev/null
ls -la CLAUDE.md 2>/dev/null

# Check git status
git status 2>/dev/null || echo "Not a git repository"
git remote -v 2>/dev/null
```

---

## Phase 2: Compatibility Analysis

Check current state against Trinity requirements:

### Required Files Checklist

| File | Purpose | Status |
|------|---------|--------|
| `template.yaml` | Agent metadata for Trinity | Check exists |
| `CLAUDE.md` | Agent instructions | Check exists |
| `.mcp.json.template` | MCP config with placeholders | Check exists |
| `.env.example` | Document required env vars | Check exists |
| `.gitignore` | Security exclusions | Check has required entries |

### Required .gitignore Entries

```
.mcp.json
.env
*.pem
*.key
.claude/projects/
.claude/statsig/
.claude/todos/
.claude/debug/
content/
session-files/
```

### Security Check

- No `.mcp.json` committed (should use `.mcp.json.template`)
- No `.env` committed
- No hardcoded API keys in tracked files

---

## Phase 3: User Confirmation

Present findings and ask to proceed:

```
## Trinity Onboarding Analysis

### Agent: [agent-name]
### Directory: [current path]

### Current State
| Item | Status |
|------|--------|
| template.yaml | [EXISTS/MISSING] |
| CLAUDE.md | [EXISTS/MISSING] |
| .mcp.json.template | [EXISTS/MISSING] |
| .env.example | [EXISTS/MISSING] |
| .gitignore | [COMPLETE/INCOMPLETE/MISSING] |
| Git repository | [INITIALIZED/NOT INITIALIZED] |
| Remote origin | [SET/NOT SET] |

### Actions Required
1. [List of files to create/update]
2. [Git operations needed]
3. [Deployment steps]

### Ready to proceed?
This will:
- Create/update configuration files
- Initialize git if needed
- Deploy agent to Trinity

Proceed? [Y/n]
```

---

## Phase 4: Create Required Files

### 4a. Create template.yaml (if missing)

```yaml
name: [agent-name-lowercase]
display_name: [Agent Display Name]
description: |
  [Description from CLAUDE.md or directory purpose]
resources:
  cpu: "2"
  memory: "4g"
credentials:
  mcp_servers: {}
  env_file: []
```

### 4b. Create/Update .gitignore

Ensure all required exclusions are present. Add missing entries:

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

### 4c. Create .env.example (if missing)

```
# Environment variables for [agent-name]
# Copy to .env and fill in values
# NEVER commit .env to version control!

# Trinity API Key (get from Trinity dashboard)
TRINITY_API_KEY=your-trinity-api-key

# Add other required credentials below
```

### 4d. Create .mcp.json.template (if missing)

If `.mcp.json` exists, convert it:
1. Read `.mcp.json`
2. Replace credential values with `${VAR_NAME}` placeholders
3. Write to `.mcp.json.template`
4. Add variables to `.env.example`

If no `.mcp.json`, create minimal template:

```json
{
  "mcpServers": {
    "trinity": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://trinity.abilityai.dev/mcp"],
      "env": {
        "TRINITY_API_KEY": "${TRINITY_API_KEY}"
      }
    }
  }
}
```

---

## Phase 5: Git Setup

### 5a. Initialize Git (if needed)

```bash
if [ ! -d .git ]; then
  git init
  echo "Git repository initialized"
fi
```

### 5b. Create Initial Commit

```bash
# Stage Trinity configuration files
git add template.yaml .gitignore .env.example

# Stage .mcp.json.template if exists
[ -f .mcp.json.template ] && git add .mcp.json.template

# Stage CLAUDE.md and skills
git add CLAUDE.md .claude/skills/ .claude/agents/ 2>/dev/null

# Commit
git commit -m "Trinity onboarding: Configure agent for Trinity platform"
```

### 5c. Set Up Remote (if not set)

If no remote origin, inform user:

```
Git remote not configured. To complete deployment:

1. Create a GitHub repository for this agent
2. Add the remote:
   git remote add origin https://github.com/YOUR-ORG/[agent-name].git
3. Push:
   git push -u origin main
4. Re-run /onboard to complete deployment
```

### 5d. Push Changes

```bash
git push origin $(git branch --show-current)
```

---

## Phase 6: Deploy to Trinity

Use Trinity MCP tools to deploy the agent:

### 6a. Check if Agent Exists

```
mcp__trinity__list_agents()
```

Look for agent with matching name.

### 6b. Create or Update Agent

If agent doesn't exist:
```
mcp__trinity__create_agent(
  name: "[agent-name]",
  template: "github:[org]/[repo]"
)
```

### 6c. Start Agent

```
mcp__trinity__start_agent(name: "[agent-name]")
```

### 6d. Verify Deployment

```
mcp__trinity__get_agent(name: "[agent-name]")
```

Confirm status is "running".

---

## Phase 7: Completion Report

```
## Trinity Onboarding Complete!

### Agent Deployed
- **Name**: [agent-name]
- **Platform**: Trinity (https://trinity.abilityai.dev)
- **Status**: Running

### Files Created/Updated
- [x] template.yaml
- [x] .gitignore
- [x] .env.example
- [x] .mcp.json.template

### Next Steps

1. **Configure credentials** in Trinity dashboard
   Visit: https://trinity.abilityai.dev/agents/[agent-name]/credentials

2. **Test remote execution**
   Use Trinity MCP tools to interact with your agent

3. **Check agent status**
   Visit: https://trinity.abilityai.dev/agents/[agent-name]
```

---

## Error Handling

| Error | Resolution |
|-------|------------|
| No CLAUDE.md | Create minimal CLAUDE.md with agent description |
| Git push failed | Check remote permissions, resolve conflicts |
| Agent creation failed | Verify Trinity API key, check agent name uniqueness |
| MCP tools not available | Ensure Trinity MCP server is connected |

---

## Idempotency

This skill is safe to run multiple times:
- Existing files are only updated if needed
- Git commits are skipped if no changes
- Agent deployment updates existing agent
