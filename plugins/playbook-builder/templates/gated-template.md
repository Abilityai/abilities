# Gated Playbook Template

Use this template for playbooks that need human approval at specific checkpoints.

**Characteristics:**
- Can run on schedule or be triggered
- Pauses at `[APPROVAL GATE]` markers for human decision
- Human reviews output before proceeding
- Combines automation with oversight

---

```yaml
---
name: ${PLAYBOOK_NAME}
description: ${DESCRIPTION}
automation: gated
schedule: "${CRON_EXPRESSION}"      # Optional - omit for trigger-only
allowed-tools: ${TOOLS}
metadata:
  version: "1.0"
  created: ${DATE}
  author: ${AUTHOR}
---

# ${PLAYBOOK_TITLE}

## Purpose
${PURPOSE_ONE_SENTENCE}

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| ${SOURCE_1} | ${PATH_1} | ✓ | | ${DESC_1} |
| ${SOURCE_2} | ${PATH_2} | ✓ | ✓ | ${DESC_2} |
| ${SOURCE_3} | ${PATH_3} | | ✓ | ${DESC_3} |

## Prerequisites
- ${PREREQ_1}
- ${PREREQ_2}

## Inputs
- `$0`: ${ARGUMENT_1_DESC}
- `$1`: ${ARGUMENT_2_DESC} (optional)

---

## Process

### Step 1: Read Current State

Read fresh copies of all state dependencies:

1. Read `${PATH_1}`:
   - Parse contents
   - Verify: ${VALIDATION_1}

2. Read `${PATH_2}`:
   - Parse contents
   - Verify: ${VALIDATION_2}

Present current state summary to user.

### Step 2: ${ANALYSIS_STEP_NAME}

${ANALYSIS_INSTRUCTIONS}

Produce:
- ${ANALYSIS_OUTPUT_1}
- ${ANALYSIS_OUTPUT_2}

### Step 3: ${GENERATION_STEP_NAME}

${GENERATION_INSTRUCTIONS}

Output:
- ${GENERATED_ARTIFACT}

### Step 4: Review Generated Output

[APPROVAL GATE] - Review ${ARTIFACT_TYPE} before proceeding

**Present to user:**
${WHAT_TO_SHOW}

**User options:**
1. **Approve** - Continue to next step
2. **Request changes** - Specify modifications
3. **Abort** - Cancel playbook execution

If changes requested:
- Apply modifications
- Return to this gate for re-review

### Step 5: ${ACTION_STEP_NAME}

${ACTION_INSTRUCTIONS}

This step ${CONSEQUENCE_DESCRIPTION}.

### Step 6: Confirm Action

[APPROVAL GATE] - Confirm before ${IRREVERSIBLE_ACTION}

**Summary of pending action:**
${ACTION_SUMMARY}

**This will:**
- ${EFFECT_1}
- ${EFFECT_2}

**Cannot be undone:** ${YES_OR_NO}

### Step 7: Execute Action

After approval:
${EXECUTION_INSTRUCTIONS}

### Step 8: Write Updated State

Save all changes:

1. Update `${PATH_2}`:
   - ${CHANGE_1}
   - ${CHANGE_2}

2. Create/update `${PATH_3}`:
   - ${WHAT_CREATED}

3. Commit changes:
   ```bash
   git add ${PATHS}
   git commit -m "${COMMIT_MESSAGE}"
   ```

---

## Outputs
- ${OUTPUT_1}
- ${OUTPUT_2}

## State Changes Summary
- `${PATH_2}`: ${CHANGE_SUMMARY_1}
- `${PATH_3}`: ${CHANGE_SUMMARY_2}

## Error Recovery

If this playbook fails mid-execution:

**Before any approval gate:**
- No state changes made
- Safe to re-run from beginning

**After Step 6 approval, before Step 8:**
- Action may be partially complete
- Check: ${HOW_TO_CHECK}
- Recovery: ${HOW_TO_RECOVER}

**After Step 8:**
- Changes committed
- Rollback: `git revert HEAD`

## Completion Checklist
- [ ] All state dependencies read fresh
- [ ] ${TASK_CHECK_1}
- [ ] All approval gates passed
- [ ] ${TASK_CHECK_2}
- [ ] All state updates written
- [ ] Changes committed

## Related Playbooks
- [/${RELATED_1}](${PATH}) - ${RELATIONSHIP_1}
- [/${RELATED_2}](${PATH}) - ${RELATIONSHIP_2}
```

---

## Example: Weekly Content Production

```yaml
---
name: weekly-content
description: Weekly content production cycle - create, review, and schedule articles
automation: gated
schedule: "0 9 * * 1"
allowed-tools: Read, Write, Edit, Bash, WebFetch
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Weekly Content Production

## Purpose
Produce and schedule one week of content with human review at key stages.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Library | `content_library.yaml` | ✓ | ✓ | Content inventory |
| Ideas | `content/ideas.md` | ✓ | ✓ | Idea backlog |
| Drafts | `content/drafts/` | | ✓ | New articles |
| Schedule | `schedule.json` | ✓ | ✓ | Publishing calendar |

## Prerequisites
- Content library initialized
- At least 5 ideas in backlog
- Publishing platform credentials set

## Inputs
- `$0`: Number of articles to produce (default: 3)

---

## Process

### Step 1: Read Current State

1. Read `content_library.yaml`:
   - Count articles by status
   - Identify content gaps by topic

2. Read `content/ideas.md`:
   - Parse idea list
   - Check viability scores

3. Read `schedule.json`:
   - Find empty slots this week
   - Note any conflicts

Present:
```
## Current State

**Content Library:** X articles (Y drafts, Z published)
**Content Gaps:** [topics needing coverage]
**Idea Backlog:** N ideas available
**Schedule Slots:** M slots open this week
```

### Step 2: Select Topics

Analyze:
- Content gaps vs available ideas
- Audience engagement data
- Seasonal relevance

Recommend top N topics for this week.

### Step 3: Review Topic Selection

[APPROVAL GATE] - Approve topics before content creation

**Recommended topics:**
1. [Topic A] - [rationale]
2. [Topic B] - [rationale]
3. [Topic C] - [rationale]

**Alternatives available:**
- [Topic D], [Topic E], [Topic F]

Select topics to proceed with.

### Step 4: Generate Drafts

For each approved topic:
1. Research key points
2. Generate article draft
3. Apply brand voice
4. Save to `content/drafts/[slug]/article.md`

### Step 5: Review Drafts

[APPROVAL GATE] - Review each draft before scheduling

For each draft, present:
- Title and hook
- Key points covered
- Estimated read time
- Suggested publish date

**Options per draft:**
- Approve for scheduling
- Request revisions
- Save as draft for later
- Discard

### Step 6: Schedule Approved Articles

Map approved articles to schedule slots:
```
Monday:    [Article A]
Wednesday: [Article B]
Friday:    [Article C]
```

### Step 7: Confirm Schedule

[APPROVAL GATE] - Confirm weekly schedule before saving

**This week's schedule:**
[Full schedule display]

Confirm to save schedule.

### Step 8: Write Updated State

1. Update `content_library.yaml`:
   - Add new article entries
   - Status: "scheduled"
   - Scheduled dates

2. Update `content/ideas.md`:
   - Mark used ideas
   - Add any new ideas surfaced

3. Update `schedule.json`:
   - Add scheduled posts
   - Confirm no conflicts

4. Commit:
   ```bash
   git add content_library.yaml content/ideas.md schedule.json content/drafts/
   git commit -m "Weekly content: [article titles]"
   ```

---

## Outputs
- N article drafts in `content/drafts/`
- Updated content library
- Week's publishing schedule

## Completion Checklist
- [ ] Content library read fresh
- [ ] Topics selected and approved
- [ ] All drafts created
- [ ] All drafts reviewed
- [ ] Schedule confirmed
- [ ] All state files updated
- [ ] Changes committed

## Related Playbooks
- [/publish-article](../publish-article/) - Publish individual article
- [/content-metrics](../content-metrics/) - Analyze content performance
```
