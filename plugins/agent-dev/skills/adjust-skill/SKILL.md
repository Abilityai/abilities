---
name: adjust-playbook
description: Modify an existing playbook based on conversation context or explicit instructions. Use when user wants to update, fix, extend, or refine a playbook they already have.
disable-model-invocation: false
user-invocable: true
argument-hint: "[playbook-name] [what to change] [--archive]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.2"
  created: 2025-02-10
  updated: 2026-04-14
  author: Ability.ai
  changelog:
    - "1.2: Add autonomous validation — cannot add gates to autonomous or change to autonomous with gates"
    - "1.1: Added --archive flag and versioning workflow for breaking changes"
    - "1.0: Initial version"
---

# Adjust Playbook

Modify existing playbooks while preserving their core structure and functionality.

## When to Use

- User says "update the X playbook"
- User says "add Y to the playbook"
- User says "fix the Z step"
- User says "change the schedule"
- After running a playbook and finding issues

---

## Workflow

### Step 1: Locate the Playbook

If `$0` (playbook name) provided:
```bash
# Check project skills
ls .claude/skills/$0/SKILL.md 2>/dev/null

# Check personal skills
ls ~/.claude/skills/$0/SKILL.md 2>/dev/null
```

If not provided or not found, list available playbooks:
```bash
echo "=== Project Playbooks ==="
for d in .claude/skills/*/; do
  [ -f "$d/SKILL.md" ] && grep -l "automation:" "$d/SKILL.md" 2>/dev/null && basename "$d"
done

echo "=== Personal Playbooks ==="
for d in ~/.claude/skills/*/; do
  [ -f "$d/SKILL.md" ] && grep -l "automation:" "$d/SKILL.md" 2>/dev/null && basename "$d"
done
```

Ask user to select if multiple options.

### Step 2: Read Current Playbook

Read the full SKILL.md:
```bash
cat [path]/SKILL.md
```

Parse and display structure:
```
## Current Playbook: [name]

**Automation**: [level]
**Schedule**: [cron or none]
**Location**: [path]

**State Dependencies**:
[table or "none defined"]

**Process Steps**: [count]
1. [step name]
2. [step name]
...

**Approval Gates**: [count]
**Checklist Items**: [count]
```

### Step 3: Determine What to Change

From `$ARGUMENTS` or conversation context, identify:

| Change Type | Examples |
|-------------|----------|
| **Add step** | "add a validation step", "include backup" |
| **Remove step** | "remove the notification", "skip review" |
| **Modify step** | "change step 3 to...", "update the API call" |
| **Change automation** | "make it autonomous", "add approval gate" |
| **Change schedule** | "run daily at 9am", "change to weekly" |
| **Add state** | "also track X", "read from Y" |
| **Update checklist** | "add verification for Z" |
| **Fix issue** | "it's failing because...", "handle the edge case" |

If unclear, ask:
```
What would you like to change in [playbook-name]?

1. Add/modify process steps
2. Change automation level or schedule
3. Update state dependencies
4. Fix an issue
5. Other (describe)
```

### Step 4: Propose Changes

Show exactly what will change:

```
## Proposed Changes to [name]

### Changes

1. **[Section]**: [what changes]

   Before:
   ```
   [current content]
   ```

   After:
   ```
   [new content]
   ```

2. **[Section]**: [what changes]
   ...

### Unchanged

Everything else remains the same:
- [list preserved sections]

### Impact

- Functionality: [same / enhanced / modified]
- State dependencies: [same / new reads / new writes]
- Automation: [same / changed]
- Breaking: [yes/no] - if yes, recommend archiving
```

**If change is breaking** (output format changes, steps removed, args changed):
```
⚠️  This is a breaking change.

Other playbooks calling /[skill-name] may break.
Recommend: Archive current version before modifying.

Archive as [skill-name]-v[N]? [Y/n]
```

### Step 5: Confirm

Ask for approval before making changes.

Options:
- Approve all changes
- Approve some, reject others
- Modify proposal
- Cancel

### Step 6: Apply Changes

Use Edit tool to apply approved changes.

For each change:
1. Find the exact text to replace
2. Apply the edit
3. Verify the edit succeeded

### Step 7: Verify

Read the updated playbook and confirm:
- Changes applied correctly
- Structure still valid
- No content lost

```
## Updated: [name]

Changes applied:
- [x] [change 1]
- [x] [change 2]

Verify the playbook works:
/[playbook-name] --dry-run (if supported)
```

---

## Common Adjustments

### Add a Step

```markdown
### Before Step N: [New Step Name]

[Instructions for new step]
```

Insert in the Process section at appropriate position.

### Add Approval Gate

**⚠️ First, check if playbook is autonomous:**

```bash
grep "automation:" [path]/SKILL.md
```

If `automation: autonomous`, **STOP** — cannot add approval gates:

```
⚠️  Cannot add approval gate — playbook is autonomous.

Autonomous playbooks run unattended and would hang waiting for approval 
that never comes.

Options:
1. Change to `automation: gated` (then add the gate)
2. Cancel — keep autonomous without this gate

Which would you prefer?
```

**If gated or manual, proceed:**

```markdown
[APPROVAL GATE] - [Description of what needs approval]

Present to user:
- [what to show]

Wait for approval before proceeding.
```

### Change Automation Level

Update frontmatter:
```yaml
automation: gated  # was: manual
```

**⚠️ If changing TO autonomous:**

Autonomous playbooks run unattended — there is no human to approve gates. Before changing to autonomous, verify using the Autonomous Validation Checklist:

- [ ] **No approval gates** — grep for `[APPROVAL GATE]` — must return zero matches
- [ ] **No human decision points** — no "ask user", "wait for confirmation", "present options"
- [ ] **Complete error handling** — all failure paths handled without human intervention
- [ ] **Notifications on failure** — errors must alert via Slack, email, or logging
- [ ] **Under 45 minutes** — execution time within agent reliability window
- [ ] **Idempotent or safe to retry** — can re-run without causing duplicate effects

If existing playbook has approval gates, you MUST either:
1. Remove all `[APPROVAL GATE]` sections (and their associated user interaction steps)
2. OR keep the playbook as `gated`/`manual`

```bash
# Check for approval gates
grep -c "\[APPROVAL GATE\]" [path]/SKILL.md
# Must return 0 to proceed with autonomous
```

If gates exist, warn:
```
⚠️  Cannot change to autonomous — playbook contains [N] approval gate(s).

Autonomous playbooks cannot have approval gates — they run unattended and would 
hang waiting for approval that never comes.

Options:
1. Remove the approval gates (will skip those review steps)
2. Keep as gated (human reviews at scheduled time)
3. Cancel change

Which would you prefer?
```

### Change Schedule

Update frontmatter:
```yaml
schedule: "0 9 * * 1-5"  # Weekdays at 9am
```

Provide cron reference if user needs it.

### Add State Dependency

Add row to State Dependencies table:
```markdown
| [Source] | [Location] | ✓ | ✓ | [Description] |
```

Add corresponding read in Step 1 and write in final step.

### Update Checklist

Add item to Completion Checklist:
```markdown
- [ ] [New verification item]
```

### Fix an Issue

1. Understand the failure from user description
2. Identify the problematic section
3. Propose specific fix
4. Optionally add error handling

---

## Version Tracking

When making significant changes, update metadata:

```yaml
metadata:
  version: "1.1"  # increment
  updated: 2025-02-10
  changelog:
    - "1.1: [what changed]"
    - "1.0: Initial version"
```

### Breaking Changes: Archive First

When changes are **breaking** (incompatible with existing workflows), archive the current version before modifying:

```bash
# Archive current version
cp -r [skill-path] [skill-path]-v[N]
```

Example:
```
skills/
  data-export/       # Current (will become v3)
  data-export-v1/    # Frozen
  data-export-v2/    # Frozen
```

**When to archive:**
- Changing output format
- Removing/renaming steps that other playbooks depend on
- Changing required arguments
- Modifying state dependencies in incompatible ways

**When NOT to archive (just increment version):**
- Adding new optional features
- Bug fixes
- Improving error messages
- Adding steps that don't affect existing behavior

If user passes `--archive` or change is breaking:
```bash
# Determine current version from metadata or count existing versions
CURRENT_VERSION=$(ls -d [skill-name]-v* 2>/dev/null | wc -l | tr -d ' ')
NEXT_VERSION=$((CURRENT_VERSION + 1))

# Archive
cp -r [skill-path] [skill-path]-v${NEXT_VERSION}

echo "Archived as [skill-name]-v${NEXT_VERSION}"
```

Then proceed with modifications to the main (unversioned) skill directory.

---

## Safety

### Before Editing

- Always read the full current content
- Show exact before/after for each change
- Get explicit approval

### Preserve Structure

- Don't remove required sections (State Dependencies, Read State, Write State, Checklist)
- If user asks to remove required section, warn about playbook compliance

### Backup Option

For major changes:
```bash
cp [path]/SKILL.md [path]/SKILL.md.backup
```

User can restore if needed.

---

## Examples

### Example 1: Add a Step

User: "add email notification to weekly-report"

```
## Proposed Changes to weekly-report

### Changes

1. **Process**: Add Step 5 before Write State

   Adding:
   ```markdown
   ### Step 5: Send Notification

   Send email summary to stakeholders:
   - To: $NOTIFY_EMAIL
   - Subject: Weekly Report - [date]
   - Body: Summary of report highlights
   ```

2. **State Dependencies**: Add email service

   Adding row:
   | Email | SMTP/$NOTIFY_EMAIL | | ✓ | Send notifications |

3. **Checklist**: Add verification

   Adding:
   - [ ] Notification email sent

### Unchanged
- Steps 1-4: same
- Automation level: same
- Schedule: same
```

### Example 2: Change Schedule

User: "run daily-backup twice a day"

```
## Proposed Changes to daily-backup

### Changes

1. **Frontmatter**: Update schedule

   Before:
   ```yaml
   schedule: "0 2 * * *"
   ```

   After:
   ```yaml
   schedule: "0 2,14 * * *"  # 2am and 2pm
   ```

2. **Name**: Consider renaming

   Current name "daily-backup" implies once daily.
   Options:
   a) Keep name (still daily, just twice)
   b) Rename to "scheduled-backup"

   Recommend: (a) keep name

### Unchanged
- All process steps
- State dependencies
- Checklist
```

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| [/create-playbook](../create-playbook/) | Create new playbook |
| [/playbook-architect](../playbook-architect/) | Audit and bulk adoption |
