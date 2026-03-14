---
name: init
description: Initialize the dev-methodology in the current project. Scaffolds CLAUDE.md, memory files, workflow docs, and testing templates. Run once per project.
allowed-tools: Read, Write, Edit, Bash, Glob
user-invocable: true
argument-hint: "[project-name]"
automation: manual
---

# Initialize Dev Methodology

Scaffold the documentation-driven development methodology into the current project.

## Process

### Step 1: Check Existing Setup

Check if the methodology is already initialized:

```bash
ls docs/memory/requirements.md 2>/dev/null && echo "EXISTS" || echo "NOT_FOUND"
ls CLAUDE.md 2>/dev/null && echo "EXISTS" || echo "NOT_FOUND"
```

If files already exist, ask the user if they want to overwrite or skip existing files.

### Step 2: Gather Project Information

If `$ARGUMENTS` is provided, use it as the project name.

Otherwise, ask the user for:
- **Project name** (e.g., "My App")
- **Project description** (one-line)
- **Repository URL** (e.g., `https://github.com/org/repo`)
- **Backend URL** (default: `http://localhost:8000`)
- **Frontend URL** (default: `http://localhost:3000`)

### Step 3: Create Directory Structure

```bash
mkdir -p docs/memory/feature-flows
mkdir -p docs/reports
mkdir -p docs/security-reports
mkdir -p testing/phases
```

### Step 4: Scaffold CLAUDE.md

Read the CLAUDE.md template from the plugin:
```
${CLAUDE_PLUGIN_ROOT}/reference/templates/CLAUDE.md.template
```

Replace all placeholders with the user's values:
- `{{PROJECT_NAME}}` -> project name
- `{{PROJECT_DESCRIPTION}}` -> description
- `{{REPO_URL}}` -> repository URL
- `{{BACKEND_URL}}` -> backend URL
- `{{FRONTEND_URL}}` -> frontend URL

Write to `CLAUDE.md` in the project root.

### Step 5: Scaffold Memory Files

Copy each template from the plugin, removing the `.template` extension:

| Source (in plugin) | Destination |
|-------------------|-------------|
| `reference/templates/requirements.md.template` | `docs/memory/requirements.md` |
| `reference/templates/architecture.md.template` | `docs/memory/architecture.md` |
| `reference/templates/roadmap.md.template` | `docs/memory/roadmap.md` |
| `reference/templates/changelog.md.template` | `docs/memory/changelog.md` |
| `reference/templates/feature-flows.md.template` | `docs/memory/feature-flows.md` |
| `reference/templates/feature-flows/_example-feature.md` | `docs/memory/feature-flows/_example-feature.md` |

Read each template from `${CLAUDE_PLUGIN_ROOT}/reference/templates/` and write to the destination.

### Step 6: Scaffold Workflow Docs

| Source (in plugin) | Destination |
|-------------------|-------------|
| `reference/DEVELOPMENT_WORKFLOW.md` | `docs/DEVELOPMENT_WORKFLOW.md` |
| `reference/TESTING_GUIDE.md` | `docs/TESTING_GUIDE.md` |
| `reference/testing/INDEX.md.template` | `testing/phases/INDEX.md` |
| `reference/testing/_PHASE_TEMPLATE.md` | `testing/phases/_PHASE_TEMPLATE.md` |

Read each source from `${CLAUDE_PLUGIN_ROOT}/reference/` and write to the destination.

### Step 7: Scaffold Local Config Example

Copy `reference/templates/CLAUDE.local.md.example` to `CLAUDE.local.md.example` in the project root.

### Step 8: Update .gitignore

Check if `.gitignore` exists and add these entries if not already present:

```
# Claude Code local config
CLAUDE.local.md
.claude/settings.local.json
```

### Step 9: Create Initial Changelog Entry

Update `docs/memory/changelog.md` to replace the placeholder date with the current timestamp:

```bash
date '+%Y-%m-%d %H:%M:%S'
```

Replace `YYYY-MM-DD HH:MM:SS` in the changelog with the actual timestamp.

### Step 10: Setup GitHub Labels (Optional)

Ask the user if they want to set up GitHub labels for roadmap integration.

If yes, run:
```bash
# Priority labels
gh label create "priority-p0" --color "B60205" --description "Blocking/Urgent" --force
gh label create "priority-p1" --color "D93F0B" --description "Critical path" --force
gh label create "priority-p2" --color "FBCA04" --description "Important" --force
gh label create "priority-p3" --color "0E8A16" --description "Nice to have" --force

# Type labels
gh label create "type-feature" --color "0075CA" --description "New feature" --force
gh label create "type-bug" --color "D73A4A" --description "Bug fix" --force
gh label create "type-refactor" --color "CFD3D7" --description "Code refactoring" --force
gh label create "type-docs" --color "0075CA" --description "Documentation" --force

# Status labels
gh label create "status-ready" --color "0E8A16" --description "Ready to work on" --force
gh label create "status-in-progress" --color "FBCA04" --description "Being worked on" --force
gh label create "status-review" --color "D93F0B" --description "In review" --force
gh label create "status-blocked" --color "B60205" --description "Blocked" --force
```

### Step 11: Report Completion

```
## Dev Methodology Initialized

### Files Created
- `CLAUDE.md` - Project instructions
- `docs/memory/requirements.md` - Feature requirements
- `docs/memory/architecture.md` - System design
- `docs/memory/roadmap.md` - Task queue
- `docs/memory/changelog.md` - Change history
- `docs/memory/feature-flows.md` - Flow index
- `docs/memory/feature-flows/_example-feature.md` - Example flow
- `docs/DEVELOPMENT_WORKFLOW.md` - Workflow guide
- `docs/TESTING_GUIDE.md` - Testing guide
- `testing/phases/INDEX.md` - Test phases index
- `testing/phases/_PHASE_TEMPLATE.md` - Phase template

### Next Steps
1. Edit `CLAUDE.md` to customize project structure and commands
2. Edit `docs/memory/requirements.md` to add your features
3. Edit `docs/memory/architecture.md` to document your stack
4. Run `/read-docs` to verify setup
5. Create your first feature flow: `/feature-flow-analysis <feature-name>`
```

## Completion Checklist

- [ ] Existing setup checked
- [ ] Project information gathered
- [ ] Directory structure created
- [ ] CLAUDE.md scaffolded with project values
- [ ] Memory files created
- [ ] Workflow docs created
- [ ] .gitignore updated
- [ ] Initial changelog entry timestamped
- [ ] GitHub labels created (optional)
- [ ] Completion report generated
