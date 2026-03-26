---
name: batch-claude-loop
description: Orchestrate batch headless Claude Code calls - loop over inputs with clean context per iteration, collect structured results
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
argument-hint: "[description of what to process]"
---

# Batch Claude Loop

## Purpose

Orchestrate multiple headless Claude Code invocations in a loop — each with clean context, different input, and structured output collection. This skill builds and executes the batch script; individual worker calls run independently via `claude -p`.

## Process

### Step 1: Clarify the Batch Job

Determine from the user:

1. **What to iterate over** — file list, array of prompts, lines from a file, API results, etc.
2. **What each worker should do** — the prompt template with a `{{ITEM}}` placeholder
3. **Which tools workers need** — for `--allowedTools` (e.g., `Read,Bash,Edit`)
4. **Worker directory** — which directory should workers run in (default: current directory)
5. **Parallelism** — serial (default) or parallel (with max concurrency)
6. **Output format** — text, json, or stream-json

### Step 2: Configure Worker Flags

Select flags for each headless invocation:

```bash
# Required flags
claude -p "${PROMPT}"              # Headless mode

# Recommended flags
--output-format json               # Structured output (parse with jq)
--allowedTools "Read,Bash"         # Pre-approve tools (no permission prompts)
--max-turns 5                      # Prevent runaway execution

# Optional flags based on needs
--bare                             # Skip all auto-discovery (fastest, most isolated)
                                   # Omit if workers need skills/MCP/CLAUDE.md
--max-budget-usd 1.00              # Cost ceiling per worker
--no-session-persistence           # Don't save session history
--append-system-prompt "..."       # Inject extra instructions
```

**Decision: `--bare` vs normal mode**
- Use `--bare` when workers are self-contained (just a prompt + tools)
- Omit `--bare` when workers need project context (CLAUDE.md, skills, MCP servers)

### Step 3: Generate the Batch Script

Create an output directory for this batch run:

```bash
BATCH_DIR="batch_$(date +%Y-%m-%d_%H%M%S)"
mkdir -p "$BATCH_DIR"
```

**Serial execution template:**

```bash
#!/bin/bash
set -euo pipefail

OUTPUT_DIR="{{BATCH_DIR}}"
RESULTS_FILE="$OUTPUT_DIR/results.jsonl"
LOG_FILE="$OUTPUT_DIR/batch.log"

# Input items - adapt to source
ITEMS=({{ITEMS_ARRAY}})

echo "Starting batch: ${#ITEMS[@]} items" | tee "$LOG_FILE"

for i in "${!ITEMS[@]}"; do
  item="${ITEMS[$i]}"
  echo "[$((i+1))/${#ITEMS[@]}] Processing: $item" | tee -a "$LOG_FILE"

  result=$(claude {{BARE_FLAG}} -p "{{PROMPT_TEMPLATE}}" \
    --output-format json \
    --allowedTools "{{TOOLS}}" \
    --max-turns {{MAX_TURNS}} \
    2>>"$LOG_FILE") || {
      echo "FAILED: $item" | tee -a "$LOG_FILE"
      echo "{\"item\":\"$item\",\"error\":true}" >> "$RESULTS_FILE"
      continue
    }

  echo "$result" >> "$RESULTS_FILE"
  echo "  Done." | tee -a "$LOG_FILE"
done

echo "Batch complete. Results: $RESULTS_FILE" | tee -a "$LOG_FILE"
```

**Parallel execution template (with concurrency limit):**

```bash
#!/bin/bash
set -euo pipefail

OUTPUT_DIR="{{BATCH_DIR}}"
MAX_PARALLEL={{MAX_PARALLEL:-3}}

mkdir -p "$OUTPUT_DIR/parts"

process_item() {
  local idx=$1 item=$2
  claude {{BARE_FLAG}} -p "{{PROMPT_TEMPLATE}}" \
    --output-format json \
    --allowedTools "{{TOOLS}}" \
    --max-turns {{MAX_TURNS}} \
    > "$OUTPUT_DIR/parts/result_${idx}.json" 2>"$OUTPUT_DIR/parts/log_${idx}.txt" || true
}

ITEMS=({{ITEMS_ARRAY}})

running=0
for i in "${!ITEMS[@]}"; do
  process_item "$i" "${ITEMS[$i]}" &
  running=$((running + 1))
  if [ "$running" -ge "$MAX_PARALLEL" ]; then
    wait -n
    running=$((running - 1))
  fi
done
wait

# Merge results
cat "$OUTPUT_DIR/parts/result_*.json" > "$OUTPUT_DIR/results.jsonl"
echo "Batch complete. Results: $OUTPUT_DIR/results.jsonl"
```

### Step 4: Execute and Monitor

1. Make script executable and run it:
   ```bash
   chmod +x "$OUTPUT_DIR/batch_run.sh"
   bash "$OUTPUT_DIR/batch_run.sh"
   ```

2. For long-running batches, use `run_in_background` and notify on completion.

3. After completion, parse results:
   ```bash
   # Count successes/failures
   jq -s '[.[] | select(.error != true)] | length' "$OUTPUT_DIR/results.jsonl"

   # Extract result text from each
   jq -r '.result' "$OUTPUT_DIR/results.jsonl"
   ```

### Step 5: Deliver Results

1. Summarize outcomes (success/fail counts, highlights)
2. Provide path to results file
3. Open output folder:
   ```bash
   open "$OUTPUT_DIR"
   ```

## Outputs

- `batch_run.sh` — Generated and executed script
- `results.jsonl` — One JSON result per line
- `batch.log` — Execution log
- Summary of outcomes presented to user

## Quick Reference: Common Patterns

**Process files in a directory:**
```bash
ITEMS=($(ls src/**/*.py))
PROMPT="Review this file for bugs: $item"
TOOLS="Read"
```

**Run prompts from a file (one per line):**
```bash
mapfile -t ITEMS < prompts.txt
```

**Process with different working directory:**
```bash
cd /path/to/project && claude -p "..." --allowedTools "..."
```

**Resume a failed batch (skip completed):**
```bash
# Check which items already have results, process remaining
```
