---
name: save-playbook
description: Capture a workflow from the current conversation and save it as a reusable playbook. Use after completing a task that should be repeatable.
disable-model-invocation: false
user-invocable: true
argument-hint: "[playbook-name]"
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Save Playbook

Capture what was just done in this conversation and save it as a reusable playbook.

Use this after completing a workflow that should be repeatable. The skill analyzes the conversation history to extract the steps, state changes, and patterns, then generates a properly structured playbook.

---

## When to Use

- After completing a multi-step task you'll need to repeat
- When you realize "I should save this as a procedure"
- To document a workflow while the context is fresh
- To convert ad-hoc work into structured automation

---

## Workflow

### Step 1: Analyze Conversation History

Review the current conversation to identify:

1. **What was the goal?** - The user's original request or intent
2. **What steps were taken?** - The sequence of actions performed
3. **What was read?** - Files, APIs, or state that was consulted
4. **What was written?** - Files, APIs, or state that was modified
5. **What tools were used?** - Which Claude Code tools were invoked
6. **Were there decision points?** - Places where human judgment was needed
7. **What was the outcome?** - The final result or deliverable

### Step 2: Determine Playbook Name

If name provided as argument (`$0`), use it.

Otherwise, derive from the goal:
- Use lowercase-with-hyphens
- Be descriptive: `deploy-to-staging` not `deploy`
- Prefix with verb: `generate-`, `sync-`, `update-`, `create-`

### Step 3: Classify Complexity Tier

Based on conversation analysis:

**Tier 1 - Simple Skill** (no state management):
- Task was stateless (no files read/written)
- One-shot execution, immediate output
- No side effects to track

**Tier 2 - Stateful Skill** (has state dependencies):
- Read or wrote files/APIs
- But was a one-time manual execution
- No scheduling or automation needed

**Tier 3 - Full Playbook** (needs reliability):
- Should run on a schedule
- Needs approval gates (had decision points)
- Failure recovery matters
- Will run unattended

If unclear, ask user which tier fits best.

### Step 4: Determine Automation Level (Tier 3 only)

If Tier 3, classify:

| If the workflow... | Automation = |
|-------------------|--------------|
| Could run completely unattended | `autonomous` |
| Had decision points needing human judgment | `gated` |
| Required human oversight throughout | `manual` |

### Step 5: Extract State Dependencies (Tier 2-3)

From the conversation, identify:

```
| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
```

Look for:
- Files that were `cat`, `Read`, or opened
- Files that were `Write`, `Edit`, or created
- APIs that were called (GET = read, POST/PUT = write)
- Git operations (status = read, commit/push = write)
- Databases queried or updated

### Step 6: Extract Process Steps

Distill the conversation into clear, numbered steps:

1. Strip out false starts, debugging, and errors
2. Keep the successful path
3. Generalize specific values to parameters (`$0`, `$1`, etc.)
4. Note where approval was needed (mark with `[APPROVAL GATE]`)
5. Identify the final "write state" actions

### Step 7: Determine Location

| Scope | Location | Choose When |
|-------|----------|-------------|
| Personal | `~/.claude/skills/[name]/` | Only you will use it |
| Project | `.claude/skills/[name]/` | Team should share it |

Default to project scope.

### Step 8: Generate Playbook

Use the appropriate template structure:

**Tier 1:**
```yaml
---
name: [name]
description: [derived from goal]
allowed-tools: [tools used in conversation]
user-invocable: true
---
# [Title]
## Purpose
## Process
## Outputs
```

**Tier 2:**
```yaml
---
name: [name]
description: [derived from goal]
allowed-tools: [tools used]
user-invocable: true
---
# [Title]
## Purpose
## State Dependencies
[table]
## Process
## Outputs
```

**Tier 3:**
```yaml
---
name: [name]
description: [derived from goal]
automation: [level]
allowed-tools: [tools used]
user-invocable: true
---
# [Title]
## Purpose
## State Dependencies
## Prerequisites
## Process
### Step 1: Read Current State
### Step N: [extracted steps]
### Final Step: Write Updated State
## Completion Checklist
## Error Recovery
```

### Step 9: Present and Confirm

Show the generated playbook:

```
## Captured Playbook: [name]

**Based on:** [summary of what was done]
**Tier:** [1/2/3]
**Automation:** [level or n/a]
**Location:** [path]

**State Dependencies:**
[list or "none"]

**Process:** [N] steps
1. [step summary]
2. [step summary]
...

---

[Full SKILL.md content preview]

---

Save this playbook?
```

### Step 10: Create Playbook

After confirmation:

```bash
mkdir -p [location]
```

Write SKILL.md to the location.

Verify:
```bash
cat [location]/SKILL.md | head -20
```

Inform user they may need to restart Claude Code.

---

## Extraction Patterns

### Identifying Steps from Conversation

Look for:
- Tool calls (Bash, Read, Write, Edit, etc.)
- "Let me...", "Now I'll...", "Next..."
- Sequential actions toward the goal
- User confirmations or approvals

### Generalizing Values

Replace specific values with parameters:

| Specific | Generalized |
|----------|-------------|
| `src/components/Button.tsx` | `$0` (first argument) |
| `2025-02-10` | `$(date +%Y-%m-%d)` |
| `fix: update button styling` | `$1` (second argument) |
| Hardcoded API key | `$API_KEY` (env variable) |

### Handling Errors and Retries

If the conversation included errors:
- Extract the successful path only
- Optionally add error handling based on what failed
- Note common failure modes in Error Recovery section

---

## Examples

### Example 1: Capturing a Deploy Workflow

After deploying an app:

```
User: /save-playbook deploy-to-staging

Conversation analysis:
- Goal: Deploy app to staging environment
- Steps: Build → Test → Deploy → Verify
- State: Read package.json, wrote dist/, called deploy API
- Decision point: Confirmed deployment after seeing diff

Generated: Tier 3 gated playbook with approval before deploy
```

### Example 2: Capturing a Simple Transform

After converting a file format:

```
User: /save-playbook convert-csv-to-json

Conversation analysis:
- Goal: Convert CSV file to JSON
- Steps: Read CSV, transform, output JSON
- State: Read input file, wrote output file
- No scheduling needed

Generated: Tier 2 stateful skill
```

### Example 3: Capturing a Code Explanation

After explaining code:

```
User: /save-playbook explain-function

Conversation analysis:
- Goal: Explain what a function does
- Steps: Read file, analyze, explain
- State: Read-only, no writes
- Pure analysis

Generated: Tier 1 simple skill
```

---

## Tips

- **Save early**: Capture while context is fresh
- **Review before saving**: Edit the generated playbook if needed
- **Name clearly**: Future you should understand what it does
- **Consider audience**: Personal skill or team skill?

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [create-playbook](../create-playbook/) | Create from scratch (no conversation to capture) |
| [adjust-playbook](../adjust-playbook/) | Modify an existing playbook |
| [playbook-architect](../playbook-architect/) | Audit and improve existing skills |
