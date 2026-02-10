---
name: create-playbook
description: Create a new playbook from conversation context or requirements. Use when user wants to capture a workflow, create a repeatable process, or build an automatable skill. Playbooks are skills with transactional state management.
disable-model-invocation: false
user-invocable: true
argument-hint: "[playbook-name]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Create Playbook

Create structured, transactional playbooks that can run autonomously, with approval gates, or manually.

## What is a Playbook?

A **playbook** is a skill that follows a disciplined pattern:

1. **Declares its state dependencies** - what data it reads and writes
2. **Reads fresh state** - never relies on stale context
3. **Executes its process** - step by step with optional approval gates
4. **Writes updated state** - all changes explicitly saved
5. **Confirms completion** - checklist verification

**Playbook = Skill** (same thing, different perspective)
- *Playbook*: business term - "run the weekly content playbook"
- *Skill*: Claude Code term - the SKILL.md file that implements it

---

## Playbook Automation Levels

| Level | Keyword | Runs When | Human Role | Use For |
|-------|---------|-----------|------------|---------|
| **Autonomous** | `autonomous` | On schedule, no intervention | None | Metrics, backups, monitoring |
| **Gated** | `gated` | Schedule or trigger, pauses at gates | Approve at checkpoints | Content creation, deployments |
| **Manual** | `manual` | Only when explicitly invoked | Full control | Dangerous ops, one-offs |

### Choosing the Right Level

```
Is this safe to run without any human oversight?
├─ YES → autonomous
└─ NO → Does it need human decisions at specific points?
         ├─ YES → gated (add [APPROVAL GATE] markers)
         └─ NO → manual (human starts and monitors entire thing)
```

---

## State Management: The Transactional Pattern

Every playbook should behave like a database transaction:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTIONAL EXECUTION                       │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  READ STATE  │───▶│   PROCESS    │───▶│ WRITE STATE  │      │
│  │              │    │              │    │              │      │
│  │ Fresh reads  │    │ Execute      │    │ Atomic       │      │
│  │ of all deps  │    │ steps        │    │ updates      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
│  If failure at any point:                                       │
│  - State may be partially modified                              │
│  - Playbook documents recovery steps                            │
│  - Re-run from beginning after fixing issue                     │
└─────────────────────────────────────────────────────────────────┘
```

### Why Transactional?

1. **Portability**: Same playbook works locally and remotely (Trinity)
2. **Reliability**: Doesn't depend on stale conversation context
3. **Traceability**: All state changes are explicit and logged
4. **Recoverability**: Clear what to check if something fails

### State Dependency Types

| Type | Examples | Read Pattern | Write Pattern |
|------|----------|--------------|---------------|
| **Files** | YAML, JSON, MD | Read file contents | Write/Edit file |
| **APIs** | REST, GraphQL | Fetch current data | POST/PUT updates |
| **Databases** | SQL, NoSQL | Query records | Insert/Update |
| **External** | Email, Slack | Check status | Send message |
| **Git** | Repo state | git status, log | git commit, push |

---

## Playbook Structure

```yaml
---
name: playbook-name
description: When to use this playbook (triggers Claude's auto-loading)
automation: gated                    # autonomous | gated | manual
schedule: "0 9 * * 1"                # cron (optional, for scheduled runs)
allowed-tools: [tools needed]
metadata:
  version: "1.0"
  created: YYYY-MM-DD
  author: name
---

# Playbook Name

## Purpose
[One sentence: what this playbook accomplishes]

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| [name] | [path]   | ✓/   | ✓/   | [what it is] |

## Prerequisites
- [What must be true before running]
- [Required tools, access, files]

## Inputs
- [What the playbook needs to start]
- [Arguments: $ARGUMENTS or $0, $1, etc.]

---

## Process

### Step 1: Read Current State

**Always read fresh state, even if read earlier in session.**

[List each state dependency to read]
[How to verify state is valid]

### Step 2: [Action Name]

[Detailed instructions]
[Expected outcomes]

### Step 3: [Action Name]

[APPROVAL GATE] - [What needs human approval and why]

[Instructions for after approval]

### Step N: Write Updated State

**Explicitly save all state changes.**

[List each state update to make]
[How to verify updates succeeded]

---

## Outputs
- [What the playbook produces]
- [Where outputs are saved]

## State Changes Summary
- [File]: [what changed]
- [API]: [what was updated]

## Error Recovery

If this playbook fails:
1. [How to check what happened]
2. [How to fix partial state]
3. [Whether to re-run or continue]

## Completion Checklist
- [ ] All state dependencies read fresh
- [ ] [Task-specific verification]
- [ ] All state updates written
- [ ] Outputs confirmed
- [ ] Changes committed (if applicable)

## Related Playbooks
- [/playbook-name](path) - [relationship]
```

---

## Workflow: Creating a New Playbook

### Step 1: Check for Existing Playbooks

```bash
# List existing playbooks in project
ls -d .claude/skills/*/ 2>/dev/null | head -20

# List playbooks in personal skills
ls -d ~/.claude/skills/*/ 2>/dev/null | head -20
```

If a similar playbook exists, ask: update it, create variant, or proceed with new?

### Step 2: Gather Requirements

Ask or extract from context:

1. **Name**: What should this playbook be called?
   - Use lowercase-with-hyphens
   - Be descriptive: `weekly-content-cycle` not `content`

2. **Purpose**: What does it accomplish in one sentence?

3. **Automation level**:
   - Autonomous (safe to run unattended)?
   - Gated (needs approvals at checkpoints)?
   - Manual (human controls entire execution)?

4. **Schedule** (if autonomous or gated):
   - When should it run?
   - Provide cron expression

5. **State dependencies**:
   - What files/data does it read?
   - What files/data does it modify?

6. **Process steps**:
   - What are the main steps?
   - Where are approval gates needed (if gated)?

7. **Inputs/Outputs**:
   - What arguments does it accept?
   - What does it produce?

### Step 3: Determine Location

| Scope | Location | Use When |
|-------|----------|----------|
| Personal | `~/.claude/skills/[name]/` | Only you use it |
| Project | `.claude/skills/[name]/` | Team shares it |
| Plugin | `plugins/[plugin]/skills/[name]/` | Distribute widely |

### Step 4: Generate Playbook

Use the template based on automation level:

- **Autonomous**: [autonomous-template.md](../templates/autonomous-template.md)
- **Gated**: [gated-template.md](../templates/gated-template.md)
- **Manual**: [manual-template.md](../templates/manual-template.md)

Fill in all sections, especially:
- State Dependencies table (critical!)
- Read State step (must be Step 1)
- Write State step (must be final step)
- Completion Checklist

### Step 5: Confirm and Create

Present summary:

```
## New Playbook: [name]

**Automation**: [level]
**Schedule**: [cron or "manual only"]
**Location**: [path]

**State Dependencies**:
- Reads: [list]
- Writes: [list]

**Process** ([N] steps):
1. [step]
2. [step]
...

**Approval Gates**: [count] gates at steps [list]

Create this playbook?
```

After confirmation, create the skill directory and SKILL.md.

### Step 6: Validate

After creation:

```bash
# Verify file exists
cat [path]/SKILL.md | head -30

# Check skill is recognized (restart Claude Code if needed)
# Test with: /playbook-name --help or just /playbook-name
```

---

## Approval Gates

Use `[APPROVAL GATE]` markers in gated playbooks:

```markdown
### Step 3: Review Generated Content

[APPROVAL GATE] - Review the generated article before proceeding

Present to user:
- Article title
- Key points
- Estimated reading time

Wait for user to:
- Approve and continue
- Request changes
- Abort playbook
```

**Gate placement guidelines:**
- Before irreversible actions (publish, send, delete)
- After generation, before use (review AI output)
- At major phase transitions (research → creation → publishing)

---

## Best Practices

### 1. State is King

```markdown
## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Content DB | `content_library.yaml` | ✓ | ✓ | All content metadata |
| Drafts | `Articles/drafts/` | | ✓ | New article files |
| Schedule | `schedule.json` | ✓ | ✓ | Publishing calendar |
```

**Every playbook must have this table.** No exceptions.

### 2. Fresh Reads, Always

```markdown
### Step 1: Read Current State

Read fresh copies of all state dependencies. Do not rely on earlier reads.

1. Read `content_library.yaml`:
   - Parse current entries
   - Note last_updated timestamp

2. Read `schedule.json`:
   - Parse scheduled items
   - Identify available slots
```

Even if you read `content_library.yaml` 5 minutes ago in the same conversation, read it again at playbook start.

### 3. Explicit Writes

```markdown
### Step 5: Write Updated State

1. Update `content_library.yaml`:
   - Add new article entry
   - Update status fields
   - Set last_updated to now

2. Update `schedule.json`:
   - Add scheduled post
   - Confirm no conflicts

3. Commit changes:
   ```bash
   git add content_library.yaml schedule.json
   git commit -m "Add article [title] to library and schedule"
   ```
```

List every file/resource being updated and what changes.

### 4. Composable Playbooks

Playbooks can call other playbooks:

```markdown
### Step 2: Generate Article

Run the article generation playbook:
/create-article $TOPIC

This playbook will:
- Research the topic
- Generate draft
- Apply tone of voice
- Return article path
```

The called playbook handles its own state management.

### 5. Defensive Checks

```markdown
### Step 1: Read Current State

1. Read `content_library.yaml`
   - If file missing: create from template
   - If parse error: abort with error message

2. Verify prerequisites:
   - API key set: `echo $CONTENT_API_KEY | head -c 5`
   - Git clean: `git status --porcelain`
```

### 6. Recovery Documentation

```markdown
## Error Recovery

If this playbook fails mid-execution:

**Check state consistency:**
```bash
# Verify content library is valid YAML
python -c "import yaml; yaml.safe_load(open('content_library.yaml'))"

# Check for partial drafts
ls -la Articles/drafts/
```

**Common issues:**
- API timeout: Re-run from Step 3
- Git conflict: Resolve manually, then re-run
- Invalid state: Restore from git and re-run entirely
```

---

## Examples

### Minimal Autonomous Playbook

```yaml
---
name: daily-backup
description: Backup critical files daily
automation: autonomous
schedule: "0 2 * * *"
allowed-tools: Bash
---

# Daily Backup

## Purpose
Create timestamped backup of critical configuration files.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Config | `.env`, `config/` | ✓ | |
| Backups | `backups/` | | ✓ |

## Process

### Step 1: Read Current State
```bash
ls -la .env config/
ls -la backups/ | tail -5
```

### Step 2: Create Backup
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
tar -czf backups/config-$TIMESTAMP.tar.gz .env config/
```

### Step 3: Write State (Cleanup Old)
```bash
# Keep only last 7 backups
ls -t backups/config-*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null
ls -la backups/
```

## Completion Checklist
- [ ] Backup file created
- [ ] Old backups cleaned up
```

### Gated Playbook with Approval

```yaml
---
name: publish-article
description: Publish article to blog platform
automation: gated
allowed-tools: Read, Write, Bash, WebFetch
---

# Publish Article

## Purpose
Review and publish a draft article to the blog.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Draft | `Articles/drafts/$0/` | ✓ | |
| Library | `content_library.yaml` | ✓ | ✓ |
| Published | `Articles/published/` | | ✓ |
| Blog API | `api.blog.com` | | ✓ |

## Process

### Step 1: Read Current State
- Read draft article from `Articles/drafts/$0/article.md`
- Read `content_library.yaml` entry for this article
- Verify article status is "ready"

### Step 2: Preview Article

[APPROVAL GATE] - Review article before publishing

Display:
- Title and metadata
- Full article content
- Target publication date

Wait for approval to proceed.

### Step 3: Publish to Platform
- Call blog API to create post
- Capture published URL

### Step 4: Write Updated State
- Move draft to `Articles/published/`
- Update `content_library.yaml`:
  - status: "published"
  - published_url: [url]
  - published_at: [timestamp]
- Commit changes

## Completion Checklist
- [ ] Article published to blog
- [ ] Draft moved to published folder
- [ ] content_library.yaml updated
- [ ] Changes committed
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [skill-builder](../../skill-builder/) | Lower-level skill creation (non-playbook) |
| [trinity-schedules](../../trinity-onboard/skills/trinity-schedules/) | Schedule playbooks on Trinity |

---

## Quick Reference

**Create a playbook:**
```
/create-playbook [name]
```

**Playbook must have:**
1. `automation:` field (autonomous/gated/manual)
2. `## State Dependencies` table
3. `### Step 1: Read Current State`
4. `### Step N: Write Updated State`
5. `## Completion Checklist`

**State is transactional:**
- Read fresh at start
- Write explicitly at end
- Document recovery for failures
