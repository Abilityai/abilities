# Stateful Skill Template (Tier 2)

Use this template for skills that read or write files, APIs, or other persistent state, but don't need the full playbook machinery (scheduling, automation levels, completion checklists).

**Characteristics:**
- Reads and/or writes state (files, APIs, databases)
- Runs when invoked by user
- No scheduling or automation level
- State Dependencies table required
- Lighter than full playbook

---

```yaml
---
name: ${NAME}
description: ${DESCRIPTION}
allowed-tools: ${TOOLS}
user-invocable: true
metadata:
  version: "1.0"
  created: ${DATE}
  author: ${AUTHOR}
---

# ${TITLE}

## Purpose

${ONE_SENTENCE_PURPOSE}

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| ${SOURCE_1} | ${PATH_1} | ✓ | | ${DESC_1} |
| ${SOURCE_2} | ${PATH_2} | ✓ | ✓ | ${DESC_2} |

## Process

${STEP_BY_STEP_INSTRUCTIONS}

## Outputs

- ${OUTPUT_1}
- ${OUTPUT_2}
```

---

## Example: Update Changelog

```yaml
---
name: update-changelog
description: Add an entry to CHANGELOG.md based on recent commits
allowed-tools: Read, Edit, Bash
user-invocable: true
argument-hint: "[version]"
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Update Changelog

## Purpose

Add a new version entry to CHANGELOG.md based on commits since the last tag.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Changelog | CHANGELOG.md | ✓ | ✓ | Version history |
| Git | .git/ | ✓ | | Commit history |

## Process

1. Read current CHANGELOG.md to understand format.

2. Get commits since last tag:
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --oneline
   ```

3. Categorize commits:
   - Features (feat:)
   - Fixes (fix:)
   - Other changes

4. Generate new version section with date.

5. Insert at top of changelog (after header).

## Outputs

- Updated CHANGELOG.md with new version entry
- Summary of changes included
```

---

## Example: Sync Config Files

```yaml
---
name: sync-config
description: Synchronize configuration between environments
allowed-tools: Read, Write, Bash
user-invocable: true
argument-hint: "[source-env] [target-env]"
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Sync Config

## Purpose

Copy configuration from one environment to another, preserving environment-specific values.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Source Config | config/${0}.yaml | ✓ | | Source environment config |
| Target Config | config/${1}.yaml | ✓ | ✓ | Target environment config |
| Preserve List | config/.preserve | ✓ | | Keys to not overwrite |

## Process

1. Read source config: `config/$0.yaml`

2. Read target config: `config/$1.yaml`

3. Read preserve list (keys that should not be overwritten):
   ```bash
   cat config/.preserve 2>/dev/null || echo ""
   ```

4. Merge configs:
   - Copy all keys from source to target
   - Preserve target values for keys in .preserve list
   - Flag any new keys added

5. Write updated target config.

6. Show diff of changes made.

## Outputs

- Updated target config file
- Diff showing what changed
- List of preserved keys
```

---

## When to Use This Template

Use stateful skills when:
- The task reads or writes files, APIs, or databases
- It's invoked manually (not scheduled)
- You need to track what state is affected
- But you don't need completion checklists, error recovery docs, or automation levels

**Upgrade to Tier 3 (Full Playbook) when:**
- The skill will run on a schedule
- It needs approval gates
- Failure recovery is complex
- It runs unattended and needs reliability guarantees

**Examples of Tier 2 skills:**
- Update configuration files
- Sync data between sources
- Generate reports from data files
- Modify project files based on analysis
