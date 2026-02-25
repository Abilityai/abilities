---
name: create-fork-skill
description: Generate an agent-specific skill that forks this agent into a clean client repository. Analyzes credentials, sensitive files, and agent structure to create a tailored fork-to-client skill with onboarding checklist.
disable-model-invocation: false
user-invocable: true
argument-hint: "[client-repo-prefix]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---

# Create Fork Skill

Generate an agent-specific `fork-to-client` skill that creates clean client derivative repositories from this agent. The generated skill knows exactly what to strip, what to template, and produces a client onboarding checklist.

## What This Creates

A new skill in `.claude/skills/fork-to-client/SKILL.md` that:

- Creates a new GitHub repository for the client
- Copies agent files, excluding sensitive/agent-specific content
- Replaces hardcoded values with client placeholders or actual values
- Generates `CLIENT_ONBOARDING.md` - setup checklist for the client instance
- Creates `.env.example` showing required credentials
- Commits clean baseline ready for client-specific customization

---

## STEP 1: Gather Agent Context

Analyze the current agent to understand its structure, credentials, and sensitive data.

### 1.1 Read Agent Identity

```
Read CLAUDE.md (or README.md if no CLAUDE.md exists)
Read template.yaml (if exists - Trinity agent)
```

Extract:
- Agent name and purpose
- GitHub repository URL (from git remote)
- Primary capabilities and responsibilities

### 1.2 Identify Credential Files

```
Check for existence of:
- .env
- .env.local
- .mcp.json
- .credentials.enc
- credentials.json
- config/secrets.*
- *.pem, *.key files
```

For each that exists, note:
- File path
- Type of credentials (API keys, tokens, certificates)
- Which services they connect to

### 1.3 Analyze .env Structure (if exists)

```
Read .env
```

Extract variable names (NOT values) to create `.env.example`:
- `API_KEY=` → needs client's API key
- `DATABASE_URL=` → needs client's database
- `WEBHOOK_SECRET=` → needs client's webhook secret

### 1.4 Analyze .mcp.json Structure (if exists)

```
Read .mcp.json
```

Identify:
- MCP servers configured
- Which require credentials (API keys in env vars)
- Which are generic (filesystem, etc.)

### 1.5 Identify Agent-Specific Patterns

Search for hardcoded values that should be templated:

```
Grep for:
- Current repo name/org in configs
- Hardcoded domain names
- Agent-specific identifiers
- Personal names/emails in non-git-config files
```

### 1.6 Discover Data Files to Exclude

```
Glob for state/data files that shouldn't transfer:
- memory/, data/, logs/, state/ directories
- *.log files
- *_state.json, *_history.json
- conversation_*.md
- Any agent-specific runtime artifacts
```

### 1.7 Check Existing .gitignore

```
Read .gitignore
```

These patterns are already excluded from git - they'll naturally be excluded from fork.

---

## STEP 2: Propose Fork Configuration

**CRITICAL: Present findings and get explicit approval before generating the skill.**

Use AskUserQuestion to present the fork configuration:

```
## Fork Configuration for {Agent Name}

Based on my analysis, here's what the fork-to-client skill will do:

### Files to EXCLUDE (never copied to client repo)

**Credential Files:**
- .env (contains secrets)
- .credentials.enc (encrypted creds)
- {other credential files found}

**Runtime State:**
- {state files found}
- {log files found}
- {memory directories found}

**Already Gitignored:**
- (these are automatically excluded)

### Values to TEMPLATE (replaced with ${PLACEHOLDER})

| Current Value | Placeholder | Description |
|---------------|-------------|-------------|
| {repo-name} | ${CLIENT_REPO} | Repository name |
| {org-name} | ${CLIENT_ORG} | GitHub organization |
| {agent-name} | ${CLIENT_AGENT_NAME} | Agent identifier |
| {custom patterns found} | ${...} | ... |

### Files Generated for Client

**CLIENT_ONBOARDING.md** - Setup checklist including:
- [ ] Create GitHub repository
- [ ] Configure credentials: {list from .env}
- [ ] Set up MCP servers: {list from .mcp.json}
- [ ] {other setup steps}

**.env.example** - Template with:
```
{VAR_NAME}=  # Description
{VAR_NAME2}=  # Description
```

### Naming Convention

New repos will be named: `{agent-base-name}-{client-name}`
Example: /fork-to-client acme → creates `{agent}-acme`

---

Would you like to:
1. Approve this configuration
2. Add more files to exclude
3. Add more values to template
4. Modify the onboarding checklist
```

**Wait for user confirmation before proceeding.**

If user wants changes:
- Iterate on the configuration
- Present updated version
- Get approval again

---

## STEP 3: Generate the Fork-to-Client Skill

Once approved, create `.claude/skills/fork-to-client/SKILL.md`:

The generated skill should be `disable-model-invocation: true` for consistent execution.

```markdown
---
name: fork-to-client
description: Fork {agent-name} into a clean client repository, stripping credentials and agent-specific data
disable-model-invocation: true
user-invocable: true
argument-hint: "<client-name> [--org github-org]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# Fork to Client

Create a clean derivative of {agent-name} for a new client.

## Arguments

- `<client-name>` - Client identifier (lowercase, hyphens ok)
- `--org <org>` - GitHub organization (default: {default-org})

## Output

- New GitHub repo: `{base-name}-{client-name}`
- Clean codebase with no credentials
- `CLIENT_ONBOARDING.md` - Setup checklist
- `.env.example` - Required credentials template

---

## STEP 1: Parse Arguments

Extract from arguments:
- `CLIENT_NAME` - the client identifier
- `GITHUB_ORG` - organization (use default if not specified)
- `NEW_REPO_NAME` - `{base-name}-${CLIENT_NAME}`

Validate:
- CLIENT_NAME is provided
- CLIENT_NAME is lowercase alphanumeric with hyphens
- No repo with NEW_REPO_NAME already exists

---

## STEP 2: Create GitHub Repository

```bash
gh repo create ${GITHUB_ORG}/${NEW_REPO_NAME} --private --description "Client implementation for ${CLIENT_NAME}"
```

Clone to temporary directory:

```bash
TEMP_DIR=$(mktemp -d)
cd ${TEMP_DIR}
git clone git@github.com:${GITHUB_ORG}/${NEW_REPO_NAME}.git
cd ${NEW_REPO_NAME}
```

---

## STEP 3: Copy Agent Files

Copy all files from source agent EXCEPT:

**Credential files (NEVER copy):**
{list of credential files from analysis}

**State/runtime files (NEVER copy):**
{list of state files from analysis}

**Git artifacts:**
- .git/ (new repo has its own)

Use rsync or cp with exclusions:

```bash
rsync -av --exclude='.git' \
  {exclusion flags for each file/pattern} \
  {source-agent-path}/ ./
```

---

## STEP 4: Template Agent-Specific Values

Replace hardcoded values with client values:

{For each templated value from analysis:}

```bash
# Replace {pattern} with client value
find . -type f -name "*.md" -o -name "*.yaml" -o -name "*.json" | \
  xargs sed -i '' 's/{old-value}/{new-value}/g'
```

Specific replacements:
| Find | Replace With |
|------|--------------|
| {source-repo-name} | ${NEW_REPO_NAME} |
| {source-agent-name} | ${CLIENT_NAME}-agent |
| {other patterns} | ${CLIENT_*} |

---

## STEP 5: Generate .env.example

Create `.env.example` with required credentials:

```
# {Agent Name} - Client: ${CLIENT_NAME}
# Copy this to .env and fill in values

{For each env var from analysis:}
{VAR_NAME}=  # {description of what this is for}
```

---

## STEP 6: Generate CLIENT_ONBOARDING.md

Create `CLIENT_ONBOARDING.md`:

```markdown
# Client Onboarding: ${CLIENT_NAME}

This repository was forked from {source-agent-name} on {date}.

## Setup Checklist

### 1. Repository Access
- [ ] Verify you have push access to this repo
- [ ] Add team members as collaborators

### 2. Credentials Setup

{For each credential type identified:}
- [ ] **{Service Name}**: {description}
  - Get from: {where to get it}
  - Set in `.env` as: `{VAR_NAME}`

### 3. MCP Server Configuration

{For each MCP server that needs setup:}
- [ ] **{Server Name}**: {description}
  - Configure in `.mcp.json`
  - Requires: {credentials needed}

### 4. Trinity Deployment (if applicable)
- [ ] Deploy to Trinity: `/trinity-onboard`
- [ ] Sync credentials: `/credential-sync push`
- [ ] Set up schedules: `/trinity-schedules`

### 5. Verification
- [ ] Run initial test: {test command}
- [ ] Verify all integrations work
- [ ] Remove this file or mark complete

## Source Agent

- **Origin**: {source-repo-url}
- **Forked**: {date}
- **Base version**: {git hash or tag}

## Support

{contact info if applicable}
```

---

## STEP 7: Commit and Push

```bash
git add -A
git commit -m "Initial fork from {source-agent-name} for ${CLIENT_NAME}

Forked from: {source-repo-url}
Base commit: {source-git-hash}

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin main
```

---

## STEP 8: Report Success

```
## Fork Complete

**New Repository:** https://github.com/${GITHUB_ORG}/${NEW_REPO_NAME}

### Files Created
- All agent source files (sanitized)
- `.env.example` - credential template
- `CLIENT_ONBOARDING.md` - setup checklist

### Files Excluded
{list of excluded files}

### Next Steps

1. Clone the new repo:
   ```
   git clone git@github.com:${GITHUB_ORG}/${NEW_REPO_NAME}.git
   ```

2. Follow `CLIENT_ONBOARDING.md` to set up credentials

3. Start Claude Code in the new repo to begin client customization
```
```

---

## STEP 4: Add .forkignore Support (Optional)

If the agent wants to maintain its own exclusion list, create `.forkignore`:

```
# Files/patterns to exclude when forking this agent to clients
# One pattern per line, uses gitignore syntax

# Credentials (required - never fork these)
.env
.env.*
.credentials.enc
*.pem
*.key

# State files
memory/
state/
logs/
*.log

# Agent-specific
{additional patterns from analysis}
```

Add to generated skill: "Read .forkignore if exists and add those patterns to exclusions"

---

## STEP 5: Write and Confirm

Write the generated skill to `.claude/skills/fork-to-client/SKILL.md`

Present completion summary:

```
## Fork Skill Created

**Skill:** /fork-to-client
**Location:** .claude/skills/fork-to-client/SKILL.md

### Configuration

**Excluded Files:**
{list}

**Templated Values:**
{list}

**Generated for Clients:**
- CLIENT_ONBOARDING.md (setup checklist)
- .env.example (credentials template)

### Usage

Fork for a new client:
```
/fork-to-client acme-corp
/fork-to-client acme-corp --org different-org
```

### Customization

Edit `.claude/skills/fork-to-client/SKILL.md` to:
- Add more exclusion patterns
- Add more value replacements
- Modify onboarding checklist
- Change naming convention

Optionally create `.forkignore` for pattern exclusions.
```

---

## Examples

### Example 1: Research Agent with API Keys

```
/create-fork-skill

Analysis:
- .env contains: OPENAI_API_KEY, TAVILY_API_KEY
- .mcp.json has: perplexity server (needs API key)
- memory/ directory has conversation history
- research_state.json has runtime state

Generated fork-to-client will:
- Exclude: .env, memory/, research_state.json
- Template: agent name in CLAUDE.md
- Generate: .env.example with OPENAI_API_KEY, TAVILY_API_KEY
- Generate: CLIENT_ONBOARDING.md with API setup steps
```

### Example 2: Business Assistant with Database

```
/create-fork-skill

Analysis:
- .env contains: DATABASE_URL, SLACK_WEBHOOK
- config/credentials.json has service accounts
- data/ has client-specific records
- logs/ has execution history

Generated fork-to-client will:
- Exclude: .env, config/credentials.json, data/, logs/
- Template: database schema references
- Generate: .env.example with DATABASE_URL, SLACK_WEBHOOK
- Generate: CLIENT_ONBOARDING.md with database setup, Slack integration
```

### Example 3: Trinity-Deployed Agent

```
/create-fork-skill

Analysis:
- template.yaml has Trinity config
- .credentials.enc has encrypted secrets
- .mcp.json has Trinity MCP server config
- dashboard.yaml has agent-specific metrics

Generated fork-to-client will:
- Exclude: .credentials.enc, dashboard.yaml (client generates own)
- Template: agent name in template.yaml
- Generate: CLIENT_ONBOARDING.md with Trinity deployment steps
- Include: /trinity-onboard in onboarding checklist
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `/trinity-onboard` | Deploy forked agent to Trinity |
| `/credential-sync` | Sync credentials after fork |
| `/create-dashboard-playbook` | Generate dashboard for forked agent |
