---
name: agent-fleet-analysis
description: Scan one or more directories of agents in ANY paradigm — Claude Code, n8n workflow exports, framework apps (LangChain/CrewAI/AutoGen), or freeform-coded agents — assess quality (fleet maturity for Claude Code, migration readiness for the rest), design the right fleet architecture (hierarchy, knowledge brain, memory, canon layer), map every improvement to an installable skill from the abilities plugin marketplace, and generate a PDF report plus a markdown twin that agents can execute as a work order. Value-first — useful whether or not you ever deploy to Trinity.
allowed-tools: Read, Bash, Write, Glob, Grep, mcp__trinity__share_file
user-invocable: true
metadata:
  version: "2.3.3"
  created: 2026-07-30
  updated: 2026-08-07
  author: Ability.ai
  changelog:
    - "2.3.3: New gap `freeform delegation` — prose schedule messages or prose inter-agent briefs instead of one-line playbook calls (fleet convention protocols/playbook-call.md); mapped to agent-dev:adjust-playbook in the marketplace table"
    - "2.3.2: The .gitignore audit list matches Trinity's current birth-state set — adds .env.*, credentials.json, *.pem, *.key, .claude/plugins/ and .claude/settings.json (container-only config that bricks outside clones, trinity#2036), and notes the platform enforces this on every Push"
    - "2.3.1: Upgrade-path table now names `agent-dev:add-project-management` — the skill moved into the agent-dev plugin, and this was the one row emitting an un-namespaced command into generated work orders"
    - "2.3: Marketplace integration — published into the agent-dev plugin (abilities marketplace); frontmatter normalized to marketplace conventions (comma-separated allowed-tools)"
    - "2.2: Universal agent discovery — classify n8n / framework (LangChain, CrewAI, AutoGen) / freeform-coded agents as first-class inventory entries (paradigm field), scan depth 2 -> 3; Migration Readiness score (0-100) for non-Claude-Code agents; marketplace upgrade paths — every recommendation maps to an installable abilities-marketplace skill (add-orchestrator, add-memory, kb-agent, add-canon, create-agent:custom, trinity:onboard); new 'Making your agents useful' report section; JSON schema + report script additions (paradigm column, upgrade_paths)"
    - "2.1: Markdown report twin (agent-executable work order) alongside the PDF; roadmap reframed to agent-speed (hours, not weeks); multiple scan paths per invocation; empty CLAUDE.md scores 0 for identity; local-run output path fallback; schema field name fix (maturity_score)"
    - "2.0: Reframe — fleet quality + architecture first, Trinity as natural landing in phase 4 only; score renamed Fleet Maturity Score; roadmap phases 1-3 platform-agnostic"
    - "1.0: Initial version — agent scan, Trinity compatibility scoring, fleet architecture recommendation, ASCII topology, 4-phase migration roadmap, ReportLab PDF"
---

# Agent Fleet Analysis

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `agent-fleet-analysis vX.Y — recent: <summary>`. Then proceed.

Scan a collection of agents — Claude Code agents AND agents built any other way (n8n workflows, LangChain/CrewAI/AutoGen apps, freeform-coded LLM loops) — produce a strategic fleet design recommendation (hierarchy, knowledge brain, memory, canon layer) with every improvement mapped to an installable skill from the abilities plugin marketplace, and generate two artifacts:

1. **A4 PDF report** — for humans, with a shareable download URL when running on Trinity.
2. **Markdown report** — the machine-readable twin, written alongside the PDF. This is the agent-executable version: every gap, quick win, and roadmap item is a checkbox an agent can work through. Hand it to a Claude Code session (or the fleet hub) as the work order for fixing the fleet.

The report is useful **regardless of deployment platform**. It tells you how well your agents are designed, how they should be organized, and what's missing. If you want to run the fleet autonomously in the cloud, the last section shows how Trinity handles that — but the organizational work comes first and stands on its own.

**Timescale framing (important):** everything the report recommends is agent-executable work. A single Claude Code session can fix the gaps across every agent, create Trinity-compatible copies, and deploy them — in a couple of hours, not weeks. The roadmap phases are a **sequence** (do 1 before 2), never a calendar. Write the report accordingly: no "this week / next month" language anywhere.

## Usage

```
/agent-fleet-analysis [path ...]
```

- `path` (optional, one or more): directories to scan. Defaults to `.` (current directory). Multiple paths (space- or newline-separated) are scanned in one run and merged into a single report.

The skill is fully autonomous — it runs through all steps and prints the report locations (and a shareable URL when on Trinity) at the end.

---

## Step 1: Resolve the Scan Paths

Parse `$ARGS` into a list of paths (whitespace/newline separated; ignore any leading free-text note the user included). If no paths given, use the current directory.

For each path: if it doesn't exist, report it and continue with the remaining paths. If NO valid paths remain, print an error and stop.

## Step 2: Discover Agents (any paradigm)

Discovery runs in two passes over each scan path, up to **3 levels deep** (agents often live one level down inside an `agents/` or `workflows/` folder). Every discovered agent becomes a first-class inventory entry with a `paradigm` field — nothing is demoted to a footnote.

### Pass 1 — Claude Code agents (`paradigm: claude-code`)

An agent directory is any directory containing at least one of `CLAUDE.md`, `template.yaml`, or a `.claude/` subdirectory:

```bash
# Find candidate directories (run per scan path)
find "$SCAN_PATH" -maxdepth 3 \( -name "CLAUDE.md" -o -name "template.yaml" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" \
  | xargs -I{} dirname {} | sort -u
find "$SCAN_PATH" -maxdepth 3 -type d -name ".claude" \
  -not -path "*/node_modules/*" | xargs -I{} dirname {} | sort -u
```

Deduplicate (same directory found via multiple markers). Nested agent directories are allowed (a sub-agent inside a parent repo) — record both, and note the nesting in the report.

### Pass 2 — other agent paradigms

For directories NOT already claimed by Pass 1, classify by evidence (first match wins):

| Paradigm | Evidence |
|----------|----------|
| `n8n` | `workflow.json`, or any `*.json` whose top level has both `"nodes"` and `"connections"` keys — each workflow (or a folder of them) is one agent entry |
| `framework` | Source files importing `langchain`, `crewai`, `autogen`, `openai` Assistants API, or similar agent frameworks (grep `*.py`/`*.js`/`*.ts`, excluding venv/node_modules) |
| `freeform-coded` | LLM API usage (anthropic/openai/gemini SDK or direct REST calls) PLUS prompt assets (a `prompts/` dir, `*_prompt*` files, `system_prompt*`) or an evident agentic loop — an agent written in plain code with no framework |
| `non-agent` | None of the above — list the path once under "Scanned, not agents" in the report and move on |

```bash
# n8n detection example
find "$SCAN_PATH" -maxdepth 3 -name "*.json" -not -path "*/node_modules/*" \
  | head -50 | xargs grep -l '"nodes"' 2>/dev/null | xargs grep -l '"connections"' 2>/dev/null
# framework / LLM-SDK detection example
grep -rlE "from langchain|import crewai|import autogen|from anthropic|import anthropic|from openai|import openai" \
  "$SCAN_PATH" --include="*.py" --include="*.js" --include="*.ts" \
  --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv 2>/dev/null | head -5
```

Use judgment on granularity: an n8n export folder with one orchestrator + several sub-workflows can be inventoried as one fleet-let with named members, or as individual agents if they are clearly independent.

If zero agents are found across ALL paths (all paradigms), print:
```
No agents found in <paths>. Try a directory containing CLAUDE.md files,
n8n workflow exports, or agent code (LangChain/CrewAI/LLM API loops).
```
and stop.

**Build the initial agent list** — for each discovered agent, record:
- `dir`: absolute path
- `name`: directory basename (or `name:` field from template.yaml / n8n workflow `name` if present)
- `paradigm`: `claude-code` | `n8n` | `framework` | `freeform-coded`

## Step 3: Per-Agent Inventory and Fleet Maturity Score

For each **`claude-code`** agent directory, run 3a–3f. Agents of other paradigms skip to **3g (Migration Readiness)** — their record uses `migration_readiness` instead of `maturity_score`. Build a structured record per agent either way.

### 3a: Read Core Files

```bash
AGENT_DIR="<agent_dir>"
test -f "$AGENT_DIR/CLAUDE.md"         && HAS_CLAUDE_MD=1    || HAS_CLAUDE_MD=0
test -f "$AGENT_DIR/template.yaml"     && HAS_TEMPLATE=1     || HAS_TEMPLATE=0
test -f "$AGENT_DIR/.mcp.json.template" && HAS_MCP_TEMPLATE=1 || HAS_MCP_TEMPLATE=0
test -f "$AGENT_DIR/.env.example"      && HAS_ENV_EXAMPLE=1  || HAS_ENV_EXAMPLE=0
test -f "$AGENT_DIR/.gitignore"        && HAS_GITIGNORE=1    || HAS_GITIGNORE=0
test -d "$AGENT_DIR/.claude"           && HAS_CLAUDE_DIR=1   || HAS_CLAUDE_DIR=0
test -d "$AGENT_DIR/.claude/skills"    && HAS_SKILLS=1       || HAS_SKILLS=0
test -d "$AGENT_DIR/.claude/memory"    && HAS_MEMORY=1       || HAS_MEMORY=0
test -f "$AGENT_DIR/fleet.yaml"        && HAS_FLEET=1        || HAS_FLEET=0
```

Read CLAUDE.md to extract: purpose (first non-empty paragraph), any explicit autonomy/role signals.

If template.yaml exists, read it for: `name`, `display_name`, `description`, `resources`, `credentials`, `schedules`.

If .gitignore exists, check it excludes: `.env`, `.env.*`, `.mcp.json`, `credentials.json`, `*.pem`, `*.key`, `content/`, `.claude/projects/`, `.claude/plugins/`, and `.claude/settings.json` (container-only config — a committed copy bricks clones made outside the container, trinity#2036). For a Trinity-deployed agent this list is enforced platform-side on every Push, so a gap is repaired rather than silently persisted — but it churns until the repo matches.

### 3b: Credential Security Scan

```bash
# Check for hardcoded credentials (never expose results in the report — just flag pass/fail)
grep -r --include="*.yaml" --include="*.yml" --include="*.json" --include="*.md" \
  --include="*.py" --include="*.sh" --include="*.js" --include="*.ts" --include="*.env" \
  -lE "(api_key|API_KEY|secret|password|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}" \
  "$AGENT_DIR" 2>/dev/null \
  | grep -vE "\.gitignore|\.env\.example|template\.yaml|node_modules|\.venv|__pycache__" \
  | wc -l
```

For each flagged file, classify the match as placeholder vs. real-looking WITHOUT printing values: if the matched value contains `your|example|placeholder|xxx|dummy|changeme|<|>` (case-insensitive) it's a placeholder — not an exposure. Only real-looking values count.

If any real-looking match remains: credential exposure risk = true (flag in report with file names only, do NOT print the values). Also check whether real `.env` files exist on disk and whether they are git-tracked (`git ls-files` inside the agent dir) — a tracked `.env` is an exposure even if the content scan found nothing.

### 3c: Fleet Maturity Score (0–100)

Score each agent on **agent quality** — not platform-specific files. These dimensions apply to any well-designed autonomous agent regardless of where it runs:

| Criterion | Points | Why it matters |
|-----------|--------|----------------|
| `CLAUDE.md` exists with clear identity and purpose — an empty or near-empty file (< 100 bytes of content) scores 0 | 20 | Without clear instructions, the agent's behavior is unpredictable |
| `.env.example` exists documenting required env vars | 15 | Portability — anyone can understand what credentials the agent needs |
| `.gitignore` exists excluding secrets (.env, .mcp.json) | 15 | Security — credentials stay out of version control |
| `.claude/skills/` directory present with ≥ 1 skill | 15 | Structured capability — the agent knows how to do something specific |
| `.claude/memory/` directory present | 10 | State persistence — the agent learns and remembers across sessions |
| No credential exposure detected in tracked files | 15 | Security hygiene — hardcoded secrets are a critical risk |
| `template.yaml` exists (deployment metadata) | 10 | Deployability — can run on any platform without manual setup |
| **Total** | **100** | |

Score label:
- 80–100 → **Well-designed** (green)
- 60–79 → **Functional** (amber)
- 40–59 → **Needs improvement** (amber)
- 0–39 → **Early stage** (red)

### 3d: Gap List

For each failed criterion, produce a gap entry with a plain-language action:
- `CLAUDE.md missing` → "Add CLAUDE.md: write a clear purpose statement and operating instructions for this agent. This is the single most important file."
- `.env.example missing` → "Add .env.example listing every environment variable the agent needs (with placeholder values, not real ones). Makes the agent portable and self-documenting."
- `.gitignore missing/incomplete` → "Add .gitignore excluding .env, .env.*, .mcp.json, credentials.json, *.pem, *.key, content/, .claude/projects/, .claude/plugins/, .claude/settings.json — prevents secrets reaching version control and keeps container-only config out of clones (trinity#2036)."
- `.claude/skills/ missing` → "Create .claude/skills/ and add at least one skill file — a markdown file describing a specific task the agent knows how to do. This gives the agent structured, reusable capabilities."
- `.claude/memory/ missing` → "Create .claude/memory/ with a memory_index.json file — lets the agent persist facts, decisions, and context across sessions instead of starting fresh every time."
- `credential exposure` → "URGENT: Remove credentials from tracked files before sharing or deploying this agent. Use .env.example to document what's needed; actual values go in .env (gitignored)."
- `template.yaml missing` → "Add template.yaml describing the agent's name, purpose, and resource needs — enables deployment on any platform (Trinity, Kubernetes, etc.) without manual setup."
- `freeform delegation` (Claude Code agents: a `template.yaml` schedule `message` that is prose rather than a one-line `/playbook [args]` call, or a skill/CLAUDE.md that instructs the agent to brief other agents in prose instead of calling their playbooks) → "Move the work into a named playbook and call it: schedules and inter-agent hand-offs should be one-line `/playbook [args]` calls (fleet convention `protocols/playbook-call.md`). Prose briefs are unversioned process — the platform cannot measure or guard them, and changing the process means editing every caller."

### 3e: Quick Wins vs. Structural Changes

The split is **mechanical vs. decision-gated**, not fast vs. slow — an agent executes both; structural items just need an operator decision first.

**Quick wins** (mechanical — an agent applies each in minutes, no decisions needed):
- Creating .env.example
- Adding .gitignore exclusions
- Adding template.yaml (if CLAUDE.md exists — the agent's identity is clear)
- Writing a missing/empty CLAUDE.md when the codebase makes the purpose obvious

**Structural changes** (need an operator design decision before an agent executes):
- Adding .claude/skills/ from scratch (which capabilities?)
- Refactoring agent to follow stateful-folder pattern
- Migrating from a non-Claude-Code framework (n8n, LangChain, etc.)
- Deciding whether a codebase should become an autonomous agent at all

### 3f: Autonomy Level

Infer from what's present:
- Has `schedules:` in template.yaml → `scheduled`
- Has `credentials.mcp_servers` in template.yaml → `mcp-connected`
- Has `.claude/memory/` → `memory-enabled`
- Has `.claude/skills/` with ≥ 3 skills → `skill-rich`
- None of the above → `basic`

Autonomy summary string: list applicable tags joined by `, ` or `basic` if none.

### 3g: Migration Readiness Score (0–100) — non-Claude-Code agents

For `n8n`, `framework`, and `freeform-coded` agents, score how ready the agent is to be converted into a well-designed Claude Code agent. First extract the **purpose**, trying sources in this order: embedded system prompt → README → workflow/node names (n8n) → code entry points and docstrings.

| Criterion | Points | What to look for |
|-----------|--------|------------------|
| Purpose discoverable | 25 | A system prompt, README, or self-evident workflow/node naming that states what the agent does |
| Logic extractability | 25 | Discrete nodes/steps/functions that map to skills; not one tangled script. n8n node graphs usually score high here |
| Credential hygiene | 20 | Run the same 3b scan: no real-looking hardcoded secrets in tracked files; env-var or credential-store patterns in use |
| State/memory articulated | 15 | A DB schema, state files, or memory structure you can point at (vs. implicit state buried in code) |
| I/O contracts clear | 15 | Triggers, webhooks, APIs, input/output shapes documented or evident |

Same labels as 3c (Well-designed / Functional / Needs improvement / Early stage) — but the report renders it as **"readiness XX%"**, never "maturity". Autonomy level: describe what exists (`cron-triggered`, `webhook-triggered`, `manual-run`) rather than the Claude Code tags.

**Gap list for these agents** describes what a conversion needs, not missing dotfiles — e.g. "system prompt embedded in n8n node — extract to CLAUDE.md", "credentials referenced via n8n credential store — map to .env.example", "5 sub-workflows map cleanly to 5 skills". The conversion itself is always a structural change (paradigm migration), executed via `create-agent:custom` (see Step 4b).

## Step 4: Fleet Architecture Recommendation

After all agents are scored, synthesize a fleet architecture across **all paradigms** — an n8n "Chief" orchestrator or a coded coordinator counts in role assignment just like a Claude Code hub (note its paradigm; making it the actual hub implies migrating it first). Read each agent's purpose field (from CLAUDE.md, or the 3g-extracted purpose) and apply these heuristics:

### Role Assignment

Assign each agent exactly one primary role:

**Hub / Orchestrator** — matches if CLAUDE.md purpose contains any of:
`orchestrat`, `chief`, `coordinator`, `chief of staff`, `manager`, `director`, `oversee`

**Knowledge Brain** — matches if purpose contains:
`knowledge`, `brain`, `research`, `memory`, `second brain`, `intel`, `information`

**Domain Manager** — matches if purpose contains domain-management signals without hub signals:
`product`, `engineer`, `marketing`, `sales`, `finance`, `hr`, `operations`, `devops`

**Specialist** — default role if no other role matched

If multiple agents match Hub: recommend the highest-scorer as Hub; note the others as Hub candidates. Recommend exactly **one** orchestrator.

If no Hub exists: recommend the highest-scoring `claude-code` agent as the candidate Hub (a non-Claude-Code orchestrator, if one exists, is noted as the design blueprint to migrate).

### Cornelius Pattern

If there is no Knowledge Brain agent: recommend creating one. Say explicitly:
> "Your fleet lacks a shared knowledge layer. Consider adding a Cornelius-style agent: a long-running agent with structured memory that all other agents can query for institutional knowledge, market context, and strategic guidance. The concrete path: `/create-agent:kb-agent` scaffolds one — a 6-question interview about your domain's ontology, then a Cornelius-shaped agent with a typed graph, layered vault, and scheduled coherence jobs."

If a Knowledge Brain exists: call out which agent fills this role and note which other agents should be wired to query it.

### Memory Recommendation (per agent)

For each agent that keeps no state (no `.claude/memory/`, no articulated state files), recommend a **specific memory kind** — installed via `/agent-dev:add-memory` — chosen from what the agent actually does:
- **file awareness** — the agent works over a corpus of documents/code it should know its way around
- **knowledge graph** — the agent accumulates entities and relationships (contacts, competitors, dependencies)
- **structured state** — the agent runs a repeatable process and must remember where things stand (queues, statuses, ledgers)
- **multi-session tracking** — the agent's work spans sessions and it must recall decisions and context

Never recommend generic "add memory" — always name the kind and the one-line reason.

### Canon Layer Recommendation

Identify which agents produce shared facts others might consume:
- Any agent with "report", "analysis", "research", "track", "monitor" in its purpose → canon publisher candidate
- Any agent with "orchestrat", "chief", "coordinator" → canon consumer candidate

Recommend: "Adopt the canon layer after Phase 2 — install via `/agent-dev:add-canon` — have [publishers] write to `canon/agents/<name>/facts.yaml` so [consumers] can query current facts without ad-hoc chat calls."

### ASCII Fleet Topology Diagram

Draw a simple ASCII diagram. Use this template, filling in actual agent names:

```
                    ┌─────────────────┐
                    │  [HUB AGENT]    │  ← Orchestrator
                    │  score: XX%     │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │ [DOMAIN MGR] │  │ [KNOWLEDGE]  │  │ [DOMAIN MGR] │
  │  score: XX%  │  │  score: XX%  │  │  score: XX%  │
  └──────┬───────┘  └──────────────┘  └──────┬───────┘
         │                                    │
    ┌────┴────┐                          ┌────┴────┐
    ▼         ▼                          ▼         ▼
[SPEC]     [SPEC]                     [SPEC]     [SPEC]
```

For fleets ≤ 3 agents, simplify to a two-level diagram. For fleets > 8 agents, group specialists by their domain manager.

Draw the diagram in plain ASCII (no Unicode box-drawing — use `+`, `-`, `|`, `>`, `<`, `v`, `^`). Ensure the diagram fits in 72 characters wide.

**Revised diagram using ASCII-safe characters:**
```
                  +-------------------+
                  |   [HUB AGENT]     |  <- Orchestrator
                  |   score: XX%      |
                  +--------+----------+
                           |
          +----------------+----------------+
          v                v                v
  +--------------+  +--------------+  +--------------+
  | [DOMAIN MGR] |  | [KNOWLEDGE]  |  | [DOMAIN MGR] |
  |  score: XX%  |  |  score: XX%  |  |  score: XX%  |
  +------+-------+  +--------------+  +------+-------+
         |                                   |
    +----+----+                         +----+----+
    v         v                         v         v
 [SPEC]    [SPEC]                    [SPEC]    [SPEC]
```

## Step 4b: Map Recommendations to Marketplace Skills

Every architecture recommendation must resolve to a **runnable install** from the abilities plugin marketplace (`Abilityai/abilities` — the plugin layer maintained by trinity-pm). This is what turns the report from advice into a work order:

| Fleet need | Marketplace skill | When to recommend |
|------------|-------------------|-------------------|
| Designate/create the orchestrator | `agent-dev:add-orchestrator` | Always — every fleet gets exactly one hub; installs /discover-agents, /orchestrate, /compose-system on it |
| Add memory (name the kind) | `agent-dev:add-memory` | Any agent with no persistent state; pick the kind per the Memory Recommendation heuristic in Step 4 |
| Knowledge brain (Cornelius pattern) | `create-agent:kb-agent` | No Knowledge Brain agent exists in the fleet |
| Migrate an n8n / framework / freeform agent | `create-agent:custom` (scaffold) + port the extracted logic | Every non-`claude-code` agent worth keeping |
| Shared facts layer | `agent-dev:add-canon` | ≥ 2 agents where one produces facts another consumes |
| Cross-actor project management | `agent-dev:add-project-management` | The hub coordinates work across humans + agents |
| Audit / refine an existing agent | `create-agent:review` + `create-agent:adjust` | Any Claude Code agent scoring 40–79 |
| Make a playbook callable by other agents / fix freeform delegation | `agent-dev:adjust-playbook` (Make Callable by Other Agents) | Any `freeform delegation` gap |
| Deploy autonomous, 24/7 | `trinity:onboard` | Phase 4, per agent |

Build an `upgrade_paths` list (see Step 7 JSON): each entry names the need, the marketplace skill, the target agent(s), and a one-line reason. These feed the report's **"Making your agents useful"** section and turn roadmap checkboxes into commands — e.g. `- [ ] Run /agent-dev:add-orchestrator on <hub>` instead of "wire the hub".

## Step 5: Fleet Improvement Roadmap

Always generate exactly 4 phases. Phases 1-3 are platform-agnostic — they improve the fleet regardless of where it runs. Phase 4 covers autonomous deployment.

**The phases are a sequence, not a calendar.** All of this is agent-executable work: a single Claude Code session working through the markdown report can complete phases 1-3 across every agent, create Trinity-compatible copies, and deploy them — the whole roadmap lands in a couple of hours. State this explicitly in the report's roadmap intro. Never use week/month language in phase titles or items.

**Phase 1 — Fix foundations (minutes per agent):**
Focus: fix the most important gaps and establish clear agent identity.
- Address any credential exposure issues first — highest priority (remove, rotate, gitignore)
- Add `.env.example` to every agent missing one
- Add `.gitignore` entries to every agent missing them
- Write or fix `CLAUDE.md` wherever it is missing, empty, or unclear
- Designate the Hub agent (name it): `<hub_agent_name>`

**Phase 2 — Build capabilities (same session):**
Focus: give each agent structured capabilities and make the fleet navigable.
- Add `.claude/skills/` to agents missing them — start with 2–3 core tasks per agent
- Add memory to agents that need to remember state across sessions — `/agent-dev:add-memory`, naming the kind per agent (file awareness / knowledge graph / structured state / multi-session)
- Add `template.yaml` deployment metadata to every agent
- Migrate non-Claude-Code agents worth keeping: `/create-agent:custom` scaffolds the target, then port the extracted logic (n8n nodes → skills, system prompts → CLAUDE.md)
- Document how agents relate to each other: which agent delegates to which

**Phase 3 — Connect the fleet (same session):**
Focus: connect the fleet into a coherent system.
- Make the Hub a real orchestrator: `/agent-dev:add-orchestrator` on `<hub_agent_name>` — installs fleet discovery, routing, and system composition
- Add or designate a Knowledge Brain agent — `/create-agent:kb-agent` scaffolds a Cornelius-style agent with structured memory that others query for shared context, decisions, and institutional knowledge
- Adopt the canon layer via `/agent-dev:add-canon`: agents that produce shared facts (reports, analysis, research) write them to `canon/agents/<name>/facts.md` so other agents can consume current facts without ad-hoc calls
- Dry-run the fleet as a coordinated unit — the Hub routes work, specialists execute, knowledge brain answers questions

**Phase 4 — Deploy to Trinity (same day):**
With phases 1-3 done, the fleet is deployable immediately:
- Create Trinity-compatible copies of each agent (template.yaml + .mcp.json.template from phase 2 make this mechanical) and onboard each via `/trinity:onboard`
- Deploy to Trinity (an open-source platform for running Claude Code agents in the cloud, 24/7)
- Wire autonomous schedules — each agent runs its own tasks without human prompts (remember the autonomy toggle: schedules only fire when agent autonomy is ON)
- Hub orchestrates the fleet via Trinity's agent-to-agent messaging
- The fleet runs on its own: schedules fire, agents report back, Hub coordinates

> **Note:** Trinity is free to self-host (Apache 2.0). The organizational work in phases 1–3 is what makes autonomous deployment actually work well — an autonomous fleet of poorly-organized agents is not better than a coordinated fleet of well-designed ones. But "well-organized" is hours of agent work away, not weeks.

## Step 6: Compile the Quick Wins List

Aggregate the top quick wins across all agents, deduplicated. Prioritize:
1. Security issues (credential exposure) — always #1
2. Missing .env.example (affects every agent missing it)
3. Missing .gitignore entries
4. Missing template.yaml (highest-scoring agents first)
5. Missing `.claude/skills/` structure

Cap the list at 12 items total.

## Step 7: Build the JSON Data File

Write all collected data to `/tmp/fleet_analysis_data.json`:

```json
{
  "generated_at": "YYYY-MM-DD",
  "scan_path": "<path>",
  "executive_summary": [
    "<N> agents found in <paths>",
    "Average fleet maturity: <avg>% — fleet status: <Well-designed|Functional|Needs improvement|Early stage>",
    "Recommended hub: <name> (<score>%)",
    "<N> improvements identified — all agent-executable; the full roadmap through Trinity deployment is a couple of hours of agent work"
  ],
  "agents": [
    {
      "name": "<name>",
      "dir": "<path>",
      "paradigm": "<claude-code|n8n|framework|freeform-coded>",
      "purpose": "<first paragraph of CLAUDE.md, or 3g-extracted purpose>",
      "role": "<hub|knowledge|domain-manager|specialist>",
      "autonomy_level": "<tags>",
      "maturity_score": <0-100, claude-code agents only — omit otherwise>,
      "migration_readiness": <0-100, non-claude-code agents only — omit otherwise>,
      "score_label": "<Well-designed|Functional|Needs improvement|Early stage>",
      "gaps": ["<gap1>", ...],
      "quick_wins": ["<win1>", ...],
      "structural_changes": ["<change1>", ...]
    }
  ],
  "upgrade_paths": [
    {
      "need": "<orchestrator|memory|knowledge-brain|migration|canon|project-management|audit|deploy>",
      "skill": "<marketplace skill, e.g. agent-dev:add-orchestrator>",
      "targets": ["<agent name>", ...],
      "note": "<one-line reason, incl. memory kind where relevant>"
    }
  ],
  "fleet_topology": {
    "hub": "<agent_name or null>",
    "knowledge_brain": "<agent_name or null>",
    "domain_managers": ["<name>", ...],
    "specialists": ["<name>", ...],
    "ascii_diagram": "<72-char-wide ASCII art, newlines as \\n>",
    "notes": [
      "<Cornelius pattern note if applicable>",
      "<Canon layer recommendation>"
    ]
  },
  "roadmap": {
    "phase1": {
      "title": "Phase 1 — Fix foundations (minutes per agent)",
      "items": ["<item1>", ...]
    },
    "phase2": {
      "title": "Phase 2 — Build capabilities (same session)",
      "items": ["<item1>", ...]
    },
    "phase3": {
      "title": "Phase 3 — Connect the fleet (same session)",
      "items": ["<item1>", ...]
    },
    "phase4": {
      "title": "Phase 4 — Deploy to Trinity (same day)",
      "items": ["<item1>", ...]
    }
  },
  "quick_wins": ["<win1>", "<win2>", ...]
}
```

Validate that every agent has exactly one of `maturity_score` / `migration_readiness`, each an integer 0–100, and a `paradigm`. Ensure `ascii_diagram` uses only printable ASCII (no Unicode box-drawing characters). Check no summary, note, or roadmap item uses week/month timescale language. Non-agent paths scanned go into a summary line ("Scanned, not agents: ..."), not into `agents`.

## Step 8: Generate the PDF + Markdown Reports

Resolve the output directory by environment:
- **Trinity container** (`/home/developer/public/` exists): `OUTPUT_DIR="/home/developer/public"`
- **Local run**: `OUTPUT_DIR="./session-files/$(date +%Y-%m-%d)_agent_fleet_analysis"` if the repo uses a `session-files/` convention; otherwise a `fleet-analysis/` folder in the working directory. Never write into the scanned repos.

```bash
DATE=$(date +%Y-%m-%d)
SCRIPT_DIR="<skill base directory>/scripts"

python3 "$SCRIPT_DIR/generate_report.py" \
  --data /tmp/fleet_analysis_data.json \
  --output   "$OUTPUT_DIR/agent-fleet-analysis-${DATE}.pdf" \
  --markdown "$OUTPUT_DIR/agent-fleet-analysis-${DATE}.md"
```

Also copy the data JSON next to the reports (`agent-fleet-analysis-${DATE}.json`) — agents consuming the report programmatically prefer the structured form.

If the script exits non-zero, print the error and stop.

## Step 9: Deliver the Files

**On Trinity:** call `mcp__trinity__share_file` for BOTH `agent-fleet-analysis-${DATE}.pdf` and `agent-fleet-analysis-${DATE}.md`. Print:
```
Agent Fleet Analysis report generated.
PDF (for humans):      <pdf_url>
Markdown (for agents): <md_url>
```

**Locally** (no Trinity, or the file isn't in the container): print all three paths and, on macOS, open the output folder (`open "$OUTPUT_DIR"`):
```
Report saved:
  PDF (for humans):      <OUTPUT_DIR>/agent-fleet-analysis-<date>.pdf
  Markdown (for agents): <OUTPUT_DIR>/agent-fleet-analysis-<date>.md
  Data JSON:             <OUTPUT_DIR>/agent-fleet-analysis-<date>.json
```

**Executing the report:** offer the natural next step — feed the markdown report back to an agent session ("work through the roadmap in <md file>") to actually apply the fixes, create Trinity-compatible copies, and deploy. The report is a work order, not just a document.

---

## Error Handling Reference

| Situation | Action |
|-----------|--------|
| A scan path doesn't exist | Report it, continue with remaining paths; stop only if none remain |
| No agents found in any path (all paradigms) | Print suggestion to check the paths, stop |
| Scanned path holds non-Claude-Code automation (n8n, framework, freeform code) | Classify per Step 2 Pass 2, score migration readiness (3g), include as first-class inventory entries |
| Directory has LLM code but classification is ambiguous | Prefer `freeform-coded` if prompts + an agentic loop are evident; otherwise `non-agent` — never guess an agent into existence |
| CLAUDE.md exists but is empty | Score identity criterion 0, list "write the empty CLAUDE.md" as a quick win |
| ReportLab not installed | Print `pip install reportlab`, stop |
| Output path not writable | Print path and permission error, stop |
| JSON data malformed | Print which field failed validation, stop |
| share_file unavailable / local run | Print local paths, open folder on macOS, continue (not a fatal error) |
