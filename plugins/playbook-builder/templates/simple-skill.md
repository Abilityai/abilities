# Simple Skill Template (Tier 1)

Use this template for stateless, one-shot tasks that don't read or write persistent state.

**Characteristics:**
- No file or API state management needed
- Runs when invoked, produces output, done
- No scheduling, no automation level
- Minimal structure

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

## Process

${STEP_BY_STEP_INSTRUCTIONS}

## Outputs

- ${OUTPUT_1}
- ${OUTPUT_2}
```

---

## Example: Generate Commit Message

```yaml
---
name: generate-commit-message
description: Generate a commit message from staged changes
allowed-tools: Bash
user-invocable: true
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Generate Commit Message

## Purpose

Analyze staged git changes and generate a conventional commit message.

## Process

1. Check for staged changes:
   ```bash
   git diff --cached --stat
   ```

2. If no staged changes, inform user and exit.

3. Analyze the diff:
   ```bash
   git diff --cached
   ```

4. Generate commit message following conventional commits format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for refactoring
   - `test:` for tests

5. Present the suggested message to user.

## Outputs

- Suggested commit message in conventional format
- Summary of changes covered
```

---

## Example: Explain Code

```yaml
---
name: explain-code
description: Explain what a code file or function does
allowed-tools: Read
user-invocable: true
argument-hint: "[file-path] [function-name?]"
metadata:
  version: "1.0"
  created: 2025-02-10
  author: Ability.ai
---

# Explain Code

## Purpose

Read and explain what a piece of code does in plain language.

## Process

1. Read the specified file: `$0`

2. If function name provided (`$1`), locate that function.

3. Analyze the code:
   - What does it do?
   - What are the inputs/outputs?
   - What are the key logic paths?
   - Any notable patterns or techniques?

4. Explain in clear, non-technical language where possible.

## Outputs

- Plain-language explanation of the code
- Key concepts identified
- Potential gotchas or edge cases noted
```

---

## When to Use This Template

Use simple skills when:
- The task is stateless (no files to track, no data to persist)
- It runs once and produces immediate output
- There's no need for scheduling or automation
- Error recovery is "just run it again"

**Examples:**
- Generate text (commit messages, summaries, explanations)
- Transform input to output (format conversion, calculations)
- Answer questions about code or data
- One-time analysis or reports
