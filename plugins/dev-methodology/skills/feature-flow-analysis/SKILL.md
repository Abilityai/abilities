---
name: feature-flow-analysis
description: Create or update a feature flow document for end-to-end understanding of a feature.
allowed-tools: Read, Write, Edit, Grep, Glob
user-invocable: true
argument-hint: "<feature-name>"
automation: manual
---

# Feature Flow Analysis

Create or update a feature flow document for end-to-end understanding.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Feature Flows Index | `docs/memory/feature-flows.md` | ✅ | ✅ | Flow index (keep minimal!) |
| Feature Flow Doc | `docs/memory/feature-flows/{name}.md` | ✅ | ✅ | Flow document |
| Frontend Code | `src/frontend/` | ✅ | | UI components |
| Backend Code | `src/backend/` | ✅ | | API endpoints |

## Arguments

- `$ARGUMENTS` - Feature name (e.g., "user-login", "payment-processing")

## Process

### Step 1: Identify Feature

If no feature name provided, ask for one.

### Step 2: Trace Execution Path

**Frontend (UI -> State -> API)**
- Find UI entry point (component, button/action)
- Trace to state management (store/context)
- Document API call made

**Backend (Endpoint -> Logic -> Data)**
- Find API endpoint handler
- Trace business logic
- Document database operations

**Side Effects (if applicable)**
- Background jobs, notifications, external integrations

### Step 3: Document Side Effects

- Event broadcasts
- Log events
- State changes

### Step 4: Document Error Handling

- What can fail?
- HTTP status codes
- Error messages

### Step 5: Add Testing Section

Include step-by-step testing instructions:
```markdown
## Testing
### Prerequisites
- Services running

### Test Steps
1. **Action**: Do X
   **Expected**: Y happens
   **Verify**: Check Z
```

### Step 6: Save Flow Document

Write to: `docs/memory/feature-flows/{feature-name}.md`

### Step 7: Update Index (MINIMAL!)

**CRITICAL**: The index is for navigation, not documentation.

**For NEW flows**, add:
1. ONE row to "Recent Updates" table
2. ONE row to the appropriate category table

**For UPDATED flows**:
- Only update the flow document itself
- Do NOT add entries to Recent Updates
- Only update the index row if name/description changed

## Output Template

```markdown
# Feature: {Feature Name}

## Overview
Brief description.

## Entry Points
- **UI**: `path/to/Component:line` - Action trigger
- **API**: `METHOD /api/endpoint`

## Frontend Layer
### Components
- `Component:line` - handler()

### State Management
- `stores/store` - actionName

## Backend Layer
### Endpoints
- `src/backend/routes/file:line` - handler()

### Business Logic
1. Step one
2. Step two

## Data Layer
- Query: description
- Update: description

## Side Effects
- Events: `{type, data}`
- Logs: event logged

## Error Handling
- Case -> HTTP status

## Testing
### Prerequisites
- Services running

### Test Steps
1. **Action**: X
   **Expected**: Y
   **Verify**: Z

## Related Flows
- [related-flow.md](feature-flows/related-flow.md)
```

## Principle

Information density over completeness. Think debugging notes, not comprehensive docs.

## Completion Checklist

- [ ] Feature identified
- [ ] Frontend traced
- [ ] Backend traced
- [ ] Side effects listed
- [ ] Testing section added
- [ ] Flow document saved
- [ ] Index updated (ONE LINE only)
