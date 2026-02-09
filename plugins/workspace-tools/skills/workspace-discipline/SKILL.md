---
name: workspace-discipline
description: Enforce workspace organization rules when creating files, writing documents, or generating assets. Use when about to create any file, write output, save reports, or generate artifacts. Ensures files are placed in proper locations - never in root directory.
allowed-tools:
  - Write
  - Bash
  - Edit
---

# Workspace Organization Discipline

**NEVER create files in the agent's root directory.** Before creating ANY file or asset, determine the proper location.

## Location Decision Tree

Before using Write or Bash to create files, follow this decision tree:

### 1. Is this persistent project work?
**YES** -> `docs/` or project-specific folder (git-tracked)
- Documentation
- Strategies and plans
- Process documentation
- Project deliverables

### 2. Is this a generated asset?
**YES** -> Within relevant subfolder structure
- Diagrams -> `assets/visuals/`
- Analysis -> `assets/analysis/`
- Reports -> `assets/reports/`

### 3. Is this session-specific temporary work?
**YES** -> `session-files/YYYY-MM-DD_activity/`
- Drafts before sending
- One-off artifacts
- Temporary outputs
- Meeting prep materials

### 4. Is this a script or utility?
**YES** -> `scripts/[functional-area]/`
- Code files
- Automation scripts
- Integration utilities

### 5. Is this a multi-session project initiative?
**YES** -> `projects/[project-name]/`
- Ongoing initiatives
- Multi-session work
- Project-specific materials

## File Naming Convention

**Always use snake_case**: `lowercase_with_underscores.ext`

Examples:
- `meeting_notes_2025_01_25.md`
- `sales_analysis_q4.json`
- `contact_enrichment_report.txt`

## Session Files Structure

```
session-files/
  YYYY-MM-DD_activity_name/
    drafts/
    outputs/
    notes.md
```

Create dated activity folders: `2025-01-25_client_outreach`

## Before Write/Bash Operations - CHECKLIST

1. **Identify context**: Project-related, session-specific, or script/utility?
2. **Check existing structure**: Does appropriate subfolder exist?
3. **Place in proper location**: Never root directory
4. **When in doubt**: ASK before creating in root

## What Goes Where - Quick Reference

| File Type | Location |
|-----------|----------|
| Email drafts | `session-files/YYYY-MM-DD_activity/drafts/` |
| Reports | `session-files/YYYY-MM-DD_activity/outputs/` or `assets/reports/` |
| Scripts | `scripts/[functional-area]/` |
| Documentation | `docs/[area]/` |
| Project materials | `projects/[project-name]/` |
| Meeting prep | `session-files/YYYY-MM-DD_meeting-prep/` |

## Delivering Generated Files

When creating files by user request, after saving:
1. Provide the full path to the output folder
2. Open it in Finder (macOS): `open /path/to/folder`

## Root Directory - NEVER Place Here

These should NEVER be in root:
- Generated reports
- Draft documents
- Analysis outputs
- Temporary files
- Session artifacts

**Root directory discipline is non-negotiable.**

## Error Handling

| Situation | Response |
|-----------|----------|
| User requests file in root | Explain policy, suggest appropriate location, ask for confirmation |
| Unsure about file category | Ask user for clarification before creating |
| Required folder doesn't exist | Create the folder structure first, then write file |
| File already exists at location | Ask user: overwrite, rename, or choose new location |
| Path contains invalid characters | Sanitize filename using snake_case convention |

## Customization

Edit this skill to match your workspace structure. Replace folder names with your preferred organization:

```
your-agent/
  docs/           # Persistent documentation
  scripts/        # Utility scripts
  assets/         # Generated assets (reports, visuals)
  projects/       # Multi-session project work
  session-files/  # Temporary session outputs
```
