# Skill Patterns Reference

## Pattern 1: Sequential Workflow Orchestration

Use when users need multi-step processes in a specific order.

```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

**Key techniques:**
- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

---

## Pattern 2: Multi-MCP Coordination

Use when workflows span multiple services.

```markdown
# Design-to-Development Handoff

### Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

### Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

### Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

### Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

**Key techniques:**
- Clear phase separation
- Data passing between MCPs
- Validation before moving to next phase
- Centralized error handling

---

## Pattern 3: Iterative Refinement

Use when output quality improves with iteration.

```markdown
## Iterative Report Creation

### Initial Draft
1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key techniques:**
- Explicit quality criteria
- Iterative improvement
- Validation scripts
- Know when to stop iterating

---

## Pattern 4: Context-Aware Tool Selection

Use when same outcome requires different tools depending on context.

```markdown
## Smart File Storage

### Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

### Execute Storage
Based on decision:
- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

### Provide Context to User
Explain why that storage was chosen
```

**Key techniques:**
- Clear decision criteria
- Fallback options
- Transparency about choices

---

## Pattern 5: Domain-Specific Intelligence

Use when skill adds specialized knowledge beyond tool access.

```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Call payment processing MCP tool
  - Apply appropriate fraud checks
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key techniques:**
- Domain expertise embedded in logic
- Compliance before action
- Comprehensive documentation
- Clear governance

---

## Complete Skill Examples

### Example: Read-Only Research Skill

```yaml
---
name: safe-reader
description: Read files without making changes. Use when user wants to explore code safely or review without risk of modification.
allowed-tools: Read, Grep, Glob
---

# Safe Reader

You are in read-only mode. Explore the codebase without making any modifications.

## Available Actions
- Search for files with Glob
- Search content with Grep
- Read files with Read

## Restrictions
- Do NOT use Edit, Write, or Bash
- Do NOT suggest modifications
- Focus on understanding and explanation
```

### Example: GitHub Issue Fixer

```yaml
---
name: fix-issue
description: Fix a GitHub issue following coding standards. Use when user says "fix issue", "resolve bug", or provides a GitHub issue number.
disable-model-invocation: true
argument-hint: [issue-number]
---

# Fix GitHub Issue

Fix GitHub issue $ARGUMENTS following our coding standards.

## Workflow

### Step 1: Understand the Issue
\`\`\`bash
gh issue view $0 --json title,body,labels
\`\`\`

### Step 2: Analyze Requirements
- Read the issue description
- Identify affected files
- Understand expected behavior

### Step 3: Implement Fix
- Make minimal, focused changes
- Follow existing code patterns
- Add tests if applicable

### Step 4: Create Commit
- Write descriptive commit message
- Reference issue number: "Fixes #$0"

### Step 5: Verify
- Run tests
- Check for regressions
```

### Example: Subagent Research Skill

```yaml
---
name: deep-research
description: Thoroughly research a topic in the codebase. Use when user asks "how does X work", "find all uses of", or needs comprehensive analysis.
context: fork
agent: Explore
---

# Deep Research

Research "$ARGUMENTS" thoroughly in this codebase.

## Research Process

1. **Find Entry Points**
   - Search for files matching the topic
   - Identify key classes/functions

2. **Trace Dependencies**
   - Follow imports and exports
   - Map the call graph

3. **Document Findings**
   - Summarize purpose and behavior
   - Note important patterns
   - List relevant file paths with line numbers

## Output Format

Provide a structured summary:
- Overview (2-3 sentences)
- Key files and their roles
- How components interact
- Potential gotchas or edge cases
```

---

## Testing Your Skill

### Triggering Tests

**Should trigger:**
- Direct requests matching description
- Paraphrased requests
- Requests using trigger phrases

**Should NOT trigger:**
- Unrelated topics
- Overlapping skills (ensure specificity)

### Functional Tests

Run the skill through its complete workflow:
1. Valid inputs produce expected outputs
2. Error conditions are handled gracefully
3. Edge cases don't break the workflow

### Performance Comparison

Compare with and without skill:
- Number of user interactions needed
- Consistency of output
- Error rate
- Token consumption

---

## Common Mistakes to Avoid

1. **Vague descriptions** - Always include specific trigger phrases
2. **Missing error handling** - Users will encounter edge cases
3. **Overly complex SKILL.md** - Use references/ for detailed docs
4. **No examples** - Show concrete usage scenarios
5. **Assuming context** - Skills should work independently
6. **README.md in skill folder** - This breaks skill loading
7. **Wrong case for SKILL.md** - Must be exact spelling
8. **Spaces in folder names** - Use kebab-case only
