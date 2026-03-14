---
name: update-docs
description: Update project documentation after making changes. Updates changelog, architecture, feature flows, and requirements as needed.
allowed-tools: Read, Write, Edit, Bash, Agent
user-invocable: true
automation: manual
---

# Update Project Documentation

Update project documentation after making changes.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Changelog | `docs/memory/changelog.md` | ✅ | ✅ | Change history |
| Architecture | `docs/memory/architecture.md` | ✅ | ✅ | System design |
| Feature Flows | `docs/memory/feature-flows/` | ✅ | ✅ | Flow docs |
| Requirements | `docs/memory/requirements.md` | ✅ | ✅ | Feature specs |
| GitHub Issues | GitHub repo | ✅ | ✅ | Task tracking |

## Process

### Step 1: Get Timestamp

```bash
date '+%Y-%m-%d %H:%M:%S'
```

### Step 2: Update Changelog

Update `docs/memory/changelog.md`:
- Add entry at the TOP of "Recent Changes" section
- Use appropriate emoji prefix:
  - 🎉 Major milestones
  - ✨ New features
  - 🔧 Bug fixes
  - 🔄 Refactoring
  - 📝 Documentation
  - 🔒 Security updates
  - 🚀 Performance improvements
  - 💾 Data/persistence changes
  - 🐳 Infrastructure/DevOps
- Include what changed and why

### Step 3: Update Architecture (if applicable)

If API/schema/integration changed:
- Update `docs/memory/architecture.md`
- Add new endpoints to API table
- Update database schema if changed
- Update architecture diagram if needed

### Step 4: Update Feature Flows (if applicable)

If feature behavior changed:
- Use the `feature-flow-analyzer` agent to update impacted feature flows
- The agent will automatically analyze and update relevant flow documents in `docs/memory/feature-flows/`

### Step 5: Update Requirements (if applicable)

If feature scope changed:
- Update `docs/memory/requirements.md`
- Mark requirements as completed if done
- Add new requirements if scope expanded

### Step 6: Update GitHub Issues (if applicable)

- Task completed -> close the issue
- New tasks discovered -> create issue with priority/type labels

## Format for Changelog Entry

```markdown
### YYYY-MM-DD HH:MM:SS
🔧 **Brief Title**
- What was changed
- Why it was changed
- Key files: `path/to/file.py`, `another/file.js`
```

## Principle

Make MINIMAL necessary documentation changes only. Don't add unnecessary detail.

## Completion Checklist

- [ ] Timestamp captured
- [ ] Changelog updated with emoji prefix
- [ ] Architecture updated (if API/schema changed)
- [ ] Feature flows updated (if behavior changed)
- [ ] Requirements updated (if scope changed)
- [ ] GitHub Issues updated (if applicable)
