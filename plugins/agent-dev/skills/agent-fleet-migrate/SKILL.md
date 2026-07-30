---
name: agent-fleet-migrate
description: Build a verified Claude Code fleet from an agent-fleet-analysis work order — non-destructive migration of mixed fleets (Claude Code, n8n exports, LangChain/CrewAI/AutoGen apps, freeform-coded loops). Sources are never mutated; each agent is copied or scaffolded into fleet-migrated/, its logic extracted per paradigm, every fix delegated to a named marketplace skill, every copy verified through the review gate, and the run ends with a before/after maturity report plus a gated deploy offer.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion
user-invocable: true
argument-hint: "[report.md | report.json | fleet-path ...] [--target dir]"
metadata:
  version: "1.0"
  created: 2026-07-30
  updated: 2026-07-30
  author: Ability.ai
  changelog:
    - "1.0: Initial version — execute the agent-fleet-analysis work order: non-destructive copies, per-paradigm logic extraction (n8n / framework / freeform), composed marketplace fixes, per-agent review gate + maturity re-score, capability coverage matrix, gated deploy handoff"
---

# Agent Fleet Migrate

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `agent-fleet-migrate vX.Y — recent: <summary>`. Then proceed.

Execute the work order that `/agent-dev:agent-fleet-analysis` produces. The analysis is the *diagnose* half; this skill is the *execute* half — the same relationship as `create-agent:review` → `create-agent:adjust`, one level up.

**Three properties are non-negotiable:**

1. **Non-destructive.** Source agents are never mutated — not even "safe" fixes. All writes land in the target workspace; a run is reversible by deleting a folder. The run proves this at the end (Step 7).
2. **Composition, not duplication.** This skill owns exactly three things: copy semantics, per-paradigm logic extraction, and the fleet-level before/after report. Every other stage is a named skill invocation (see the composition table). This file must contain **no inline restatement of any composed skill's checks or templates** — a restated rubric line is future drift. Gaps found in a composed skill get fixed *in that skill*.
3. **Honest gates.** An agent is reported "migrated" only after the review gate passes and the re-score clears the bar (Step 4d). Failures are reported as failures with named findings — never rounded up. A gate FAIL is a blocker, not an advisory.

## Composition table

| Stage | Invoke |
|-------|--------|
| Work order (missing or stale) | `/agent-dev:agent-fleet-analysis` |
| Scaffold target shape (non-Claude-Code paradigms) | `/create-agent:custom` |
| Extracted capabilities → skills | `/agent-dev:create-playbook` |
| Gap fixes on the copies | `/create-agent:adjust` (composes the review itself) |
| Memory / hub / canon wiring | `/agent-dev:add-memory` · `/agent-dev:add-orchestrator` · `/agent-dev:add-canon` — driven by the work order's `upgrade_paths`, which already names the skill per agent |
| **Verification gate** | `/create-agent:review` per migrated copy |
| Numeric before/after | `/agent-dev:agent-fleet-analysis` re-run on the target workspace |
| Deploy handoff (gated) | `/trinity:onboard` per agent, or `mcp__trinity__deploy_system` for the fleet |

Execution is **sequential in the main loop** — one agent at a time, in manifest order. Slower than fan-out, but every composed skill resolves exactly as it does when the user runs it directly.

## Usage

```
/agent-fleet-migrate [report.md | report.json | fleet-path ...] [--target dir]
```

- **Report path** (`.md` or `.json` from a previous analysis run): execute it.
- **Fleet path(s)** (directories of agents): run `/agent-dev:agent-fleet-analysis` on them first, then execute the fresh report.
- **Nothing**: find the newest `agent-fleet-analysis-*.json` in the conventional output locations — `./session-files/*_agent_fleet_analysis/`, `./fleet-analysis/`, `/home/developer/public/` — and confirm it at the plan gate.
- `--target dir`: target workspace (default `./fleet-migrated/`). Never inside any source agent directory.

---

## Step 1: Resolve the Work Order

Parse the arguments per Usage. Whenever a markdown report is given or found, prefer its JSON twin (`agent-fleet-analysis-<date>.json`, written alongside) — the structured form carries `agents[]`, `upgrade_paths`, `fleet_topology`, and the roadmap without re-parsing prose. If only the markdown exists, work from it.

**Staleness check:** if any source agent directory listed in the report contains files newer than the report file itself, the diagnosis may no longer match reality. Say which directories changed and offer to refresh via `/agent-dev:agent-fleet-analysis` before executing. Proceeding on a stale report is the operator's call, made at the plan gate — never silent.

**Dead ends get a next action, never silence:**

| Situation | Action |
|-----------|--------|
| No report found anywhere | Print: `No fleet-analysis report found. Run /agent-dev:agent-fleet-analysis <fleet-path> first, or pass the fleet path directly to this skill.` Stop. |
| Report references source dirs that no longer exist | List them; migrate the ones that do exist; record the missing ones as `failed — source directory gone`. |
| Report has zero agents | Print the analysis skill's own no-agents guidance and stop. |
| Report predates schema v2.2 (no `paradigm` field) | Re-run `/agent-dev:agent-fleet-analysis` on the source paths — do not guess paradigms. |

## Step 2: Migration Manifest — the Plan Gate

Build the manifest from the work order and present it for **one approval before any write**. Every row is editable at the gate (skip an agent, rename a target, change the hub):

```
## Migration manifest — approve before any write

Work order: <report path> (generated <date>, <fresh | STALE — details above>)
Target:     <target dir>   Sources: never mutated

| # | Agent | Paradigm | Score | Action | Target |
|---|-------|----------|-------|--------|--------|
| 1 | <name> | claude-code | 45% maturity | uplift (copy + fix gaps) | <target>/<name>/ |
| 2 | <name> | n8n | 70% readiness | convert (scaffold + extract) | <target>/<name>/ |
| 3 | <name> | freeform-coded | 20% readiness | skip — operator call | — |

Hub designation: <name>  (from fleet_topology.hub)
Fleet wiring after per-agent work: <upgrade_paths entries, mechanical vs. handoff — see Step 5>
Skipped: <list with reasons — low readiness, non-agent, operator exclusion>
```

Actions are: **uplift** (`claude-code` — the copy is the migration; fixes close the gap list), **convert** (`n8n` / `framework` / `freeform-coded` — scaffold + extraction), **skip** (recorded with reason). Default: migrate everything the report inventoried as an agent; suggest skipping only agents the report scored under 40 readiness with no discoverable purpose.

If every agent ends up skipped, print what was skipped and why, plus the one action that would unblock the most agents (usually "state the purpose of X — its readiness score is limited by purpose discoverability"). Stop — an empty manifest is not a run.

The **deploy offer is a second, separate gate** (Step 8). Approving the manifest never implies deployment.

## Step 3: Prepare the Target Workspace

```bash
TARGET="${TARGET_DIR:-./fleet-migrated}"
mkdir -p "$TARGET"
STAMP="$TARGET/.pre-migration-stamp"
touch "$STAMP"   # mtime marker — Step 7 proves no source file is newer than this
```

**Re-run semantics (additive, never destructive):** if `<target>/<name>/` already exists from a previous run, do **not** re-copy, delete, or overwrite it — treat it as a resume: skip Step 4a for that agent and run Steps 4b–4d against the existing copy. Hand-edits the user made to a migrated copy are preserved; the git history inside each copy (initialized in 4a) shows exactly what each run changed. To start over instead, the user deletes the folder or passes a fresh `--target`.

## Step 4: Per-Agent Migration Loop

Process manifest agents sequentially. **One agent's failure never aborts the fleet run** — record the failure with its named reason and continue with the next agent.

### 4a: Copy or scaffold — the non-destructive workspace

**`claude-code` (uplift):** copy the source into the target, excluding volatile and secret-bearing paths, then initialize git so every later change is diffable:

```bash
SRC="<source agent dir>"; DEST="$TARGET/<name>"
mkdir -p "$DEST"
rsync -a \
  --exclude ".git" --exclude "node_modules" --exclude ".venv" --exclude "venv" \
  --exclude "__pycache__" --exclude ".env" --exclude ".env.*" --exclude ".mcp.json" \
  --include ".env.example" \
  "$SRC/" "$DEST/"
git -C "$DEST" init -q
git -C "$DEST" add -A && git -C "$DEST" commit -qm "pre-migration copy of $SRC"
```

Real `.env` / `.mcp.json` files are deliberately left behind — the migrated copy documents credentials via `.env.example` only; the user re-supplies real values when running the copy.

**`n8n` / `framework` / `freeform-coded` (convert):** copy the source material to `<target>/_sources/<name>/` (same exclusions; reference only, never git-inited) — the extraction in 4b reads from this copy, not from the original. Then scaffold the target agent: **Invoke `/create-agent:custom`** for `<target>/<name>/` with the purpose extracted by the analysis (the report's `purpose` field) as the agent's stated purpose. Port the 4b extraction results into the scaffold.

### 4b: Per-paradigm logic extraction (convert actions only)

The one piece of new IP this skill owns. Extraction turns source artifacts into four kinds of ported material: **identity** (→ CLAUDE.md), **skill candidates** (→ `/agent-dev:create-playbook`, one per capability), **credential references** (→ `.env.example` entries, names + placeholders only, never values), and a **memory-kind recommendation** (→ `/agent-dev:add-memory`, using the analysis skill's four kinds vocabulary: file awareness / knowledge graph / structured state / multi-session tracking).

**`n8n`** — read each workflow JSON (`name`, `nodes[]`, `connections`):

- *Identity:* system prompts embedded in AI/LLM/Agent nodes (`systemMessage`, `prompt`, `text` parameters) + the workflow name and any sticky-note documentation → the CLAUDE.md identity section.
- *Skill candidates:* one per trigger-to-sink path through the connection graph, and one per `Execute Workflow` sub-workflow target. Intermediate nodes (HTTP Request, transform, DB) become **steps inside** that skill, not separate skills.
- *Triggers:* Cron/Schedule Trigger nodes → a `schedules:` recommendation in the copy's template.yaml; Webhook triggers → the skill's documented input contract.
- *Credentials:* every node-level `credentials` reference → one `.env.example` entry named after the service.
- *State:* data-store / DB / spreadsheet nodes → memory kind (usually structured state).

**`framework` (LangChain / CrewAI / AutoGen)** — read entry points and agent definitions:

- *Identity:* system prompts, prompt templates, CrewAI `role`/`goal`/`backstory`, AutoGen agent descriptions → CLAUDE.md.
- *Skill candidates:* each `@tool`/Tool definition, chain, or crew task → one skill candidate; agent-to-agent edges → delegation notes in CLAUDE.md.
- *Credentials:* `os.environ` / `getenv` / dotenv keys actually read by the code → `.env.example`.
- *State:* vector stores and retrievers → file awareness; entity/relationship stores → knowledge graph; queues, checkpointers, run ledgers → structured state.

**`freeform-coded`** — read the prompt assets and the agentic loop:

- *Identity:* `prompts/` dir, `*_prompt*` files, inline system-prompt strings → CLAUDE.md.
- *Skill candidates:* discrete functions or CLI subcommands the loop dispatches to → one each.
- *Credentials:* env-var reads → `.env.example`.
- *State:* state files, JSON ledgers, SQLite schemas → the matching memory kind.

**Named validation errors:** when a source artifact resists extraction, record an error naming the artifact and the reason — e.g. `n8n node "HTTP Request 3" (workflow "enricher") has no discoverable purpose — needs operator input` — in the analysis skill's error-table style. The capability goes into the coverage matrix as an **explicit omission**; the agent's migration continues with what did extract.

**Capability coverage matrix** — built per converted agent, from the union of the report's I/O contracts, gap list, and everything 4b discovered:

```
| Source capability | Evidence | Target skill | Status |
|-------------------|----------|--------------|--------|
| Enrich new leads via Clearbit | n8n path: Webhook → HTTP → Sheets | /enrich-lead | ported |
| Nightly digest email | Cron node "Daily 7am" | /send-digest + schedule rec | ported |
| <unclear node> | node "HTTP Request 3" | — | OMITTED: no discoverable purpose |
```

Every source capability maps to a named target skill or a listed omission — semantic fidelity, not file presence. **No silent capability loss.**

### 4c: Compose the fixes

Work through the copy's items from the work order — its gap list, quick wins, and the `upgrade_paths` entries targeting this agent:

- Structure and content gaps → **Invoke `/create-agent:adjust`** on the copy (it runs the review first and applies findings — do not pre-empt it with manual fixes it would make anyway).
- Each extracted skill candidate (4b) → **Invoke `/agent-dev:create-playbook`** in the copy.
- `upgrade_paths` entries naming this agent → invoke the named skill (`/agent-dev:add-memory` with the recommended kind, etc.).

### 4d: Verify — the review gate and re-score

**Invoke `/create-agent:review`** on the copy. Read its scorecard and findings:

- Any **MISSING** or **BROKEN** area, or any **High-severity** finding → **Invoke `/create-agent:adjust`** to apply the findings, then re-review. Maximum **3** adjust→review rounds; if findings persist after that, stop looping — the remaining findings are named in the report and the agent is **not** counted as migrated.
- Review clean → the agent's migration gate is met pending the fleet re-score (Step 6).

**Per-agent status vocabulary** (the report uses exactly these):

| Status | Meaning |
|--------|---------|
| `migrated` | Review gate passed AND re-scored maturity ≥ 60 (Functional). Copies also reaching ≥ 80 carry the Well-designed label. |
| `incomplete` | Gate not met after 3 rounds, or re-score < 60 — remaining findings named. |
| `failed` | Copy/scaffold/extraction failed — reason named (e.g. source gone, extraction needs operator input on the load-bearing artifact). |
| `skipped` | Operator call at the plan gate — reason recorded. |

The ≥ 60 bar is deliberate: thin source material (readiness < 40) often cannot honestly reach Well-designed in one pass, and looping until it fakes 80 would violate the honesty property. The report shows every score; raising the copy from Functional to Well-designed is a listed next action, not a silent loop.

## Step 5: Fleet-Level Wiring

After the per-agent loop, execute the fleet-scoped `upgrade_paths` entries **that are mechanical**:

- Hub designation → **Invoke `/agent-dev:add-orchestrator`** on the migrated hub copy.
- Canon layer (when the work order recommends it) → **Invoke `/agent-dev:add-canon`**.

Entries that require an interactive interview (e.g. `create-agent:kb-agent` for a missing knowledge brain) are **not run autonomously** — they land in the report's next-actions list with the exact command, so the operator runs them with the interview they deserve.

## Step 6: Re-Score

**Invoke `/agent-dev:agent-fleet-analysis`** on the target workspace (exclude `_sources/`; a `--target` that is inside the current directory is fine — the analysis writes its report outside the scanned tree). Read the fresh JSON: its `maturity_score` per agent is the **after** number; the original work order holds the **before** (maturity or readiness). No scoring logic lives in this file — the delta comes from two runs of the same scorer.

## Step 7: Before/After Report + Non-Destructive Proof

Prove the sources untouched, then write the report:

```bash
for SRC in <each source dir from the manifest>; do
  find "$SRC" -newer "$STAMP" -type f | head -5
done
# Empty output for every source = proof. Any hit = report it loudly as a bug in the run.
```

Write `<target>/migration-report-<date>.md`:

```
# Fleet Migration Report — <date>

Work order: <report path> · Target: <target dir>
Sources verified untouched: <yes / VIOLATION — files listed>

## Before / after

| Agent | Paradigm | Before | After | Status |
|-------|----------|--------|-------|--------|
| <name> | claude-code | 45% maturity | 85% maturity | migrated (Well-designed) |
| <name> | n8n | 70% readiness | 65% maturity | migrated |
| <name> | freeform-coded | 20% readiness | — | failed: <named reason> |

Fleet average: <before>% → <after>%

## Capability coverage (converted agents)
<per-agent matrix from 4b — ported rows + every omission>

## Incomplete / failed — what remains
<named findings per agent, verbatim from the last review>

## Next actions
- <interactive upgrade_paths handoffs, exact commands>
- <raise Functional copies to Well-designed — exact gaps>
- Deploy (gated): see below
```

Print the report path and the before/after table inline.

## Step 8: Deploy — the Second Gate

Deployment never runs inside the migration loop. Offer, don't do:

- **Trinity MCP available:** offer `/trinity:onboard` per migrated agent, or `mcp__trinity__deploy_system` for the whole fleet. Only on explicit approval, and only for agents with status `migrated`.
- **No Trinity connection:** print the local handoff instead — each migrated copy is a complete local agent: `cd <target>/<name> && claude`, credentials via its `.env.example`. Trinity is the upgrade, never the gate.

---

## Error Handling Reference

| Situation | Action |
|-----------|--------|
| No report + no paths given, none found | Named next action (Step 1 table), stop |
| Stale report (sources newer) | Offer refresh; operator decides at the plan gate |
| Source dir listed in report no longer exists | `failed — source directory gone`, continue with the rest |
| Composed skill not installed (e.g. create-agent plugin missing) | Print the exact `/plugin install <name>@abilityai` command, mark affected agents `incomplete`, continue where possible |
| Extraction hits an unreadable/opaque artifact | Named validation error (4b), capability → explicit omission, continue |
| Review gate still failing after 3 rounds | Status `incomplete` with named findings — never loop further, never round up |
| One agent fails mid-loop | Record, continue with the next agent |
| Target dir exists from a prior run | Resume semantics (Step 3) — update in place, never delete |
| Non-destructive proof finds a newer file in a source | Report loudly as a run bug at the top of the report — this is a defect, not a footnote |
| No Trinity connection at deploy time | Local handoff instructions (Step 8) — not a dead end |
