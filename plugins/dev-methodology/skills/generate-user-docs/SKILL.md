---
name: generate-user-docs
description: Generate and update user-facing documentation from code, feature flows, and recent changes into docs/user-docs/
automation: gated
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
user-invocable: true
---

# Generate User Docs

Generate and maintain `docs/user-docs/` — authoritative user documentation derived from code as the single source of truth.

## Purpose

Read source code, feature flows, and recent changes to produce clear, non-redundant, MECE documentation. Code is the source of truth — docs describe what the code does, not what it should do.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Source code | Project source directories | Yes | No |
| Feature flows | `docs/memory/feature-flows/*.md` | Yes | No |
| Feature flow index | `docs/memory/feature-flows.md` | Yes | No |
| Requirements | `docs/memory/requirements.md` | Yes | No |
| Architecture | `docs/memory/architecture.md` | Yes | No |
| Changelog | `docs/memory/changelog.md` (last 200 lines) | Yes | No |
| Existing user docs | `docs/user-docs/**/*.md` | Yes | Yes |
| Git history | `git log --since` | Yes | No |

## Prerequisites

- Repository checked out with source code available
- `docs/memory/` populated (optional but recommended — skill works from code alone if needed)

## Process

### Step 1: Discover Project Structure

Identify the project type and source layout:

```bash
# Find project markers
ls -la package.json pyproject.toml Cargo.toml go.mod Makefile 2>/dev/null
```

Build a map of:
- **Language/framework** — What tech stack is this?
- **Entry points** — API routers, CLI commands, UI views, exported modules
- **Public surface** — What do users interact with? (APIs, UI, CLI, SDK)

### Step 2: Inventory Current Docs

Read what already exists in `docs/user-docs/` and build a checklist of files needing creation or update.

```bash
find docs/user-docs -name "*.md" -type f 2>/dev/null | sort
```

### Step 3: Read Source Material

Read these sources to extract current feature state. Use parallel agents where possible.

**3a. Feature flows** — Read `docs/memory/feature-flows.md` (the index) if it exists, then read individual flows as needed per section.

**3b. Requirements** — Read `docs/memory/requirements.md` for the canonical feature list and acceptance criteria.

**3c. Architecture** — Read `docs/memory/architecture.md` for system design context, component relationships, and data flow.

**3d. Recent changes** — Read the last 200 lines of `docs/memory/changelog.md` and run:
```bash
git log --oneline --since="2 weeks ago" | head -30
```
This identifies what changed recently and which docs may need updating.

**3e. Source code** — Read source files relevant to each documentation section. Extract:
- Public API endpoints, methods, and paths
- CLI commands and flags
- UI screens, views, and workflows
- Configuration options
- Request/response patterns and data models

### Step 4: Plan Documentation Structure

Based on what the project exposes to users, propose a documentation structure. Organize by user task, not by code module.

Example structure (adapt to project):

```
docs/user-docs/
├── README.md                    # Index + navigation
├── getting-started/
│   ├── overview.md              # What is this, key concepts
│   ├── setup.md                 # Installation, first-time config
│   └── quick-start.md           # Hello-world in 5 minutes
├── [feature-area-1]/
│   ├── topic-a.md
│   └── topic-b.md
├── [feature-area-2]/
│   └── ...
├── configuration/
│   └── ...
├── api-reference/
│   └── ...
└── troubleshooting.md
```

**Present the proposed structure to the user and get approval before writing.**

### Step 5: Generate/Update Documentation

For each section, produce or update the markdown file following these rules:

#### Writing Rules

1. **MECE structure** — Each section covers a mutually exclusive, collectively exhaustive slice of functionality. No concept is explained in two places. If a concept spans sections, explain it once and cross-reference.

2. **Dual audience format** — Each doc follows this template:

```markdown
# [Feature Name]

[1-2 sentence summary of what this feature does and why it matters]

## Concepts

[Define key terms specific to this feature. Only terms not defined elsewhere.]

## How It Works

[Step-by-step explanation for users. Describe workflows with specific
UI locations, CLI commands, or API calls. Include what the user sees
or gets back at each step.]

## For Developers

[Programmatic usage. API endpoints, SDK methods, CLI flags.
Include example snippets only when the pattern is non-obvious.]

## Limitations

[Known constraints, edge cases, or things that don't work yet.
Only include if meaningful.]

## See Also

[Cross-references to related docs. Use relative links.]
```

3. **No redundancy** — Do not repeat information from other docs. Cross-reference instead. The `Concepts` section in `getting-started/overview.md` is the canonical glossary.

4. **Code-derived accuracy** — Every claim must trace to code or a feature flow. Do not invent features. If something is TODO or planned, note it as upcoming rather than documenting it as available.

5. **Clear, direct tone** — Active voice. Short sentences. No filler ("In order to", "It should be noted that"). Say what happens, not what "can" happen.

6. **Placeholder values** — Use `your-domain.com`, `your-api-key`, `user@example.com` in examples. Never include real credentials or internal URLs.

### Step 6: Generate README.md Index

Create `docs/user-docs/README.md` as the entry point:

```markdown
# [Project Name] User Documentation

> Auto-generated from source code. Run `/generate-user-docs` to update.

## Getting Started
- [Overview](getting-started/overview.md) — What is [Project Name]
- [Setup](getting-started/setup.md) — Installation and first-time config
- [Quick Start](getting-started/quick-start.md) — Your first [action]

## [Feature Area]
- [Topic](feature-area/topic.md) — Description
...
```

List every file with a one-line description. Group by section folder.

### Step 7: Diff Review (Approval Gate)

**STOP and present changes to the user before writing.**

Show:
- Files to create (new)
- Files to update (with summary of what changed)
- Files unchanged (skipped)

Ask: "Write these changes?" Only proceed after confirmation.

### Step 8: Write Files

Create directories and write all approved files using Write or Edit tools.

### Step 9: Verify

```bash
find docs/user-docs -name "*.md" -type f | wc -l
```

Confirm the expected number of files were created/updated. Report the final count.

## Completion Checklist

- [ ] All sections in target structure have corresponding files
- [ ] Every doc follows the dual-audience template
- [ ] No redundant explanations across docs (MECE verified)
- [ ] No real credentials, internal URLs, or PII in any doc
- [ ] README.md index is complete and links are valid
- [ ] Changes reviewed by user before writing

## Error Recovery

| Error | Recovery |
|-------|----------|
| No feature flows exist | Write docs entirely from source code |
| Source code has no docstrings | Read function bodies and signatures to infer behavior |
| Conflicting info between requirements and code | Trust code (source of truth); note discrepancy |
| Existing doc is manually edited | Preserve manual edits; append auto-generated sections below a separator |
| Feature has no corresponding code yet | Mark as "Planned" with brief description from requirements |
