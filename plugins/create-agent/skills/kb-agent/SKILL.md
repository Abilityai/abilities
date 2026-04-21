---
name: install-kb-agent
description: Create a knowledge-base agent — asks a structured 6-question interview about the domain's ontology, then scaffolds a Cornelius-shaped Trinity-compatible KB agent with a typed graph, 7-layer vault, subagents, and scheduled coherence jobs
argument-hint: "[destination-path]"
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
metadata:
  version: "1.3"
  created: 2026-04-13
  updated: 2026-04-21
  author: Ability.ai
---

# Install KB Agent

Create a **Cornelius-shaped knowledge-base agent** powered by Claude Code, customized to a specific domain (community management, CS research, clinical research, legal analysis, personal KB, or custom), and compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and orchestration.

**What you'll get:**

- A Brain Dependency Graph ontology (`<agent>-graph.yaml`) tuned to the domain
- A 7-layer vault scaffold (signals → impressions → insights → frameworks → lenses → syntheses → indices)
- The cornelius local-brain-search Python machinery cloned in — FAISS vector search, spreading activation, coherence engine
- Domain-appropriate subagents (vault-manager + extractors + discovery + synthesis)
- KB-core scheduled skills: `/coherence-sweep`, `/compute-lifecycle`, `/detect-tensions`, `/refresh-index`, `/propagate-change`
- Domain-specific skills tailored to the preset (or blank if custom)
- Onboarding tracker, Trinity dashboard, and all standard agent files

> Built by [Ability.ai](https://ability.ai). The agent this wizard generates is a specialization of [Cornelius](https://github.com/Abilityai/cornelius) — the reference insight-harvester KB agent.

---

## Background: Why a Structured Interview

Every KB agent shares the same skeleton. What differs across domains is how six slots get filled:

1. **Atomic unit** — the smallest indivisible thing the agent captures
2. **Entity types** — the taxonomy of first-class nouns beyond the atomic unit
3. **Edge types** — how entities connect, with direction, mode, and decay
4. **Mode model** — which entities are generative (prescriptive) vs reflective (descriptive)
5. **Trigger topology** — edit-driven vs event-driven vs hybrid
6. **Lifecycle signals** — observed behaviors that promote/demote entities

If you elicit these correctly, storage schema, subagents, propagation rules, skills, and scheduled jobs all fall out mechanically. This wizard runs that interview and generates the cascade.

The reference implementation is Cornelius — see `resources/local-brain-search/BRAIN-DEPENDENCY-GRAPH-ARCHITECTURE.md` in the cornelius repo for the full architecture spec, and `resources/universal-kb-agent-wizard.md` for the design rationale behind this wizard.

---

## STEP 1: Determine Destination

If the user passed a path as argument, use it. Otherwise:

Use AskUserQuestion:
- **Question:** "Where should the KB agent be created?"
- **Header:** "Location"
- **Options:**
  1. `~/[agent-name]` — home directory (recommended; resolved after Q3 agent name)
  2. `./[agent-name]` — current directory
  3. Custom path

Note: the final agent name is chosen in STEP 3. For now, capture the *container*: home directory, current directory, or a custom parent path.

Expand `~` to `$HOME`. Do not create the directory yet — the name isn't known.

---

## STEP 2: Domain Preset

Use AskUserQuestion:
- **Question:** "Which domain preset best fits the agent you're building? The preset seeds defaults for all six ontology axes. You can override any of them in the next questions."
- **Header:** "Domain"
- **Options:**
  1. **Personal KB (Cornelius-flavor)** — insight harvesting from your own writing + external reading. Atomic unit: atomic insight. Edit-driven.
  2. **Community Manager** — tracking people, events, norms, conflicts in a community. Atomic unit: member profile. Hybrid (events + user notes).
  3. **CS Researcher** — tracking papers, methods, benchmarks, claims, replications. Atomic unit: verifiable claim with provenance. Hybrid.
  4. **Clinical Research** — tracking studies, populations, interventions, outcomes. Atomic unit: study finding. Hybrid.
  5. **Legal Analyst** — tracking obligations, parties, triggers, consequences across contracts and cases. Atomic unit: contractual obligation. Edit-driven.
  6. **Custom** — define from scratch; each subsequent question starts blank.

Store the choice as `$preset`. Load the preset's defaults into memory (the six axes are tabulated at the bottom of this skill under **Preset Defaults**) and use them to pre-fill subsequent questions. If preset is "Custom", subsequent questions have no defaults — the user must answer cold.

---

## STEP 3: Agent Name

Use AskUserQuestion:
- **Question:** "What should the agent be called? This becomes the directory name, the install command suffix, and the graph config filename."
- **Header:** "Agent Name"
- **Options:**
  1. Preset-suggested name (e.g., `tribune` for community manager, `scholar` for CS researcher, `clinician` for clinical, `counselor` for legal, `cornelius-n` for personal KB, or blank for custom)
  2. Custom

Rules:
- Lowercase, short, memorable. Kebab-case allowed.
- Directory becomes `[destination]/[agent-name]`. Validate no collision. If exists, offer: overwrite / pick different name / cancel.
- Store as `$agent_name`. Also capture `$display_name` (title-case) and `$graph_file` = `${agent_name}-graph.yaml`.

Expand the destination path now: `$destination = [container]/${agent_name}`.

---

## STEP 4: Atomic Unit (Axis 1)

Use AskUserQuestion:
- **Question:** "What is the smallest indivisible thing this agent captures and connects? The preset suggests `[preset.atomic_unit]` — accept or edit."
- **Header:** "Atomic Unit"
- **Options:**
  1. Accept the preset suggestion: **[preset.atomic_unit_label]** ([preset.atomic_unit_description])
  2. Edit — provide an alternative

For "Custom" preset, there is no accept option — user must describe their atomic unit in free text, specifying: (a) the noun, (b) what fields every instance must have, (c) what makes two instances the same vs different (duplicate-detection rule).

Store the result as `$atomic_unit` with sub-fields: `name`, `description`, `required_fields` (list), `identity_rule`.

This determines the frontmatter schema for every insight-layer note in the generated vault.

---

## STEP 5: Entity Types and Mode Model (Axes 2 + 4)

Use AskUserQuestion:
- **Question:** "Beyond the atomic unit, which other first-class entity types does this agent track? Pre-selected options come from the `[preset]` preset — adjust freely."
- **Header:** "Entity Types"
- **multiSelect:** true
- **Options:** the preset's entity types, each labeled with its default mode. For example, for Community Manager:
  1. `people` (reflective — observed behavior)
  2. `events` (reflective — event log)
  3. `groups` (reflective)
  4. `norms` (generative — user-authored)
  5. `topics` (reflective)
  6. `conflicts` (reflective — observed sentiment)
  7. `initiatives` (generative)

For "Custom" preset, show a canonical palette of entity types (source, note, concept, person, claim, artifact) and let user select + add.

After the multiselect, for each *selected* entity type ask a follow-up:
- Is this entity type **generative** (prescriptive — what should be true; e.g., frameworks, proposed methods, norms) or **reflective** (descriptive — what is true; e.g., observed events, source material)? Default from preset.

Store as `$entity_types`, a list of `{name, mode: generative|reflective|mixed, description}`. This determines: (a) folder structure, (b) which subagents get generated (one extractor per entity type with a distinct ingestion path), (c) mode-model propagation rules.

Also confirm the 7-layer vault mapping. The cornelius convention is:

| Layer | Folder | Default contents |
|-------|--------|------------------|
| 1 Signal | `01-Sources/` | External source material |
| 2 Impression | `00-Inbox/` | Fleeting captures |
| 3 Insight | `02-Permanent/` + domain-specific | Atomic units (selected in Q4) |
| 4 Framework | `02-Permanent/` (subset) | Generative entities |
| 5 Lens | `03-MOCs/` | Maps / indices |
| 6 Synthesis | `04-Output/` | Composed output |
| 7 Index | `05-Meta/` | Meta-structural |

If the user's entity types don't map cleanly, extend `vault_paths` in the graph config. Do NOT rename layers — the cornelius local-brain-search code expects layer 1-7.

---

## STEP 6: Trigger Topology (Axis 5)

Use AskUserQuestion:
- **Question:** "What kicks the agent into motion?"
- **Header:** "Trigger"
- **Options:**
  1. **Edit-driven** — agent responds to user authorship. File watcher + weekly coherence sweep. Suited to reflective corpora (personal KB, research vault, legal contracts). Cornelius is pure edit-driven.
  2. **Event-driven** — agent responds to external streams (webhooks/polling). Near-real-time response. Suited to live domains (community, monitoring, sales CRM).
  3. **Hybrid (recommended for most real-world agents)** — both. Clear ownership per entity type: events for live entities, edits for user-curated ones.

Store as `$trigger_topology`. This determines:
- Ingestion infrastructure (file watcher only, webhook/polling subagents, or both)
- Schedule cadence for `/refresh-index` and event ingestion jobs
- Whether to generate an `event-ingester` subagent

If Hybrid, ask a follow-up multiselect: which entity types are event-driven vs edit-driven? (e.g., in Community Manager: events are event-driven; norms are edit-driven.)

---

## STEP 7: Edge Types (Axis 3)

Use AskUserQuestion:
- **Question:** "Which edge types should the graph support? The six cornerstone edges (derives-from, instantiates, references, associates, tension, supersedes) are always included. Select additional domain-specific edges — these are the preset's suggestions."
- **Header:** "Edges"
- **multiSelect:** true
- **Options:** preset-specific domain edges. For example:
  - Community Manager: `introduced-by`, `conflicts-with`, `co-attends`, `champions`, `violates`
  - CS Researcher: `cites`, `extends`, `refutes`, `reproduces`, `evaluates-on`
  - Clinical: `studies`, `contradicts`, `replicates`, `subgroup-of`
  - Legal: `supersedes-clause`, `cross-references`, `triggers`, `exempts`
  - Personal KB: (cornerstone edges only; no additional)
  - Custom: show cornerstones + blank; user specifies

For each selected domain edge, ask (can be batched as a single follow-up with multiSelect=false per edge, or a table):
- **Direction:** source→target or bidirectional
- **Decay (0.0-1.0):** when source changes, how much does target get flagged? (Decays: 0.0=no propagation, 0.2=weak, 0.5=moderate, 0.8=strong, 1.0=full)
- **Mode:** does source carry generative authority, or is source derived from target?

Use preset defaults. Store as `$edge_types` — a list of `{name, direction, decay, authority_side, tension: bool, description}`.

**Critical:** always include the 6 cornerstones with cornelius' exact decay values (derives-from=0.8, instantiates=0.7, references=0.2, associates=0.05, tension=0.0, supersedes=1.0). These are the structural backbone; the domain edges sit on top.

---

## STEP 8: Lifecycle Signals (Axis 6)

Use AskUserQuestion:
- **Question:** "Which observed signals should drive lifecycle transitions (reflective → crystallizing → generative)?"
- **Header:** "Signals"
- **multiSelect:** true
- **Options:** preset-specific. For example:
  - Personal KB (cornelius default): citation_frequency, generative_ratio, cross_domain_reach, temporal_acceleration
  - Community Manager: interaction_recency, reciprocity_ratio, co_attendance_diversity, sentiment_trajectory
  - CS Researcher: replication_count, supersession_velocity, contradiction_density, citation_frequency
  - Clinical: replication_count, effect_stability, sample_size_growth
  - Legal: citation_by_cases, supersession_velocity, cross_reference_count
  - Custom: cornelius defaults + blank

For each selected signal, ask:
- **Weight (0.0-1.0):** contribution to lifecycle score. Weights across selected signals must sum to 1.0 — the skill normalizes if they don't.
- **Crystallizing threshold:** the minimum value that flips the signal to "crystallizing"
- **Generative threshold:** the minimum value that flips the signal to "generative"

Preset defaults provided. Store as `$signals`.

This determines: (a) scheduled jobs that compute signals, (b) lifecycle promotion/demotion rules, (c) what `/compute-lifecycle` outputs.

---

## STEP 9: Plugin Selection

Always-included plugins for KB agents:
- `agent-dev` — create new skills, memory infrastructure
- `trinity` — deploy remotely

The github-backlog skills (`/backlog`, `/pick-work`, `/close-work`, `/work-loop`) are generated directly into the agent's `.claude/skills/` directory during wizard execution — no external plugin install required. This gives the KB agent a complete task management workflow out of the box.

Use AskUserQuestion to confirm + add any of:
- `utilities` (ops/incident skills; rarely needed for KB)

Store as `$plugins`.

---

## STEP 10: Review

Summarize the full design to the user before generating files:

```
## Review: $agent_name

**Preset:** $preset
**Location:** $destination
**Trigger:** $trigger_topology

### Atomic unit
$atomic_unit.name — $atomic_unit.description

### Entity types ($N)
- entity_1 (mode)
- entity_2 (mode)
...

### Edge types ($M total: 6 cornerstones + $K domain)
| Edge | Direction | Decay | Mode |
|------|-----------|-------|------|
| derives-from | S→T | 0.8 | varies |
| ...

### Lifecycle signals
| Signal | Weight | Crystallizing | Generative |
|--------|--------|---------------|------------|
...

### Files to be created
- CLAUDE.md
- ${agent_name}-graph.yaml
- template.yaml, dashboard.yaml, onboarding.json
- .claude/agents/: vault-manager, connection-finder, auto-discovery, [N extractors]
- .claude/skills/: coherence-sweep, compute-lifecycle, detect-tensions, refresh-index,
  propagate-change, recall, find-connections, onboarding, update-dashboard, [domain skills]
- .claude/skills/: backlog, pick-work, close-work, work-loop (GitHub backlog workflow)
- resources/local-brain-search/ (cloned from cornelius)
- 7-layer vault (00-Inbox through 05-Meta)
- .env.example, .gitignore, .mcp.json.template
```

Use AskUserQuestion:
- **Question:** "Looks good? Or adjust something?"
- **Header:** "Confirm"
- **Options:** Generate / Edit an axis (re-enter any of steps 4-8) / Cancel

Only proceed to STEP 11 on Generate.

---

## STEP 11: Create Directory Structure

```bash
mkdir -p "$destination"
mkdir -p "$destination/.claude/agents"
mkdir -p "$destination/.claude/skills"
mkdir -p "$destination/resources/local-brain-search/data"
mkdir -p "$destination/00-Inbox"
mkdir -p "$destination/01-Sources"
mkdir -p "$destination/02-Permanent"
mkdir -p "$destination/03-MOCs"
mkdir -p "$destination/04-Output"
mkdir -p "$destination/05-Meta/Changelogs"
```

For each entity type whose vault paths extend beyond the default 7 layers (from STEP 5), add its folders here.

Additionally create a skill directory per KB-core skill and per domain skill (see STEP 15 and STEP 16).

---

## STEP 12: Clone Local-Brain-Search Machinery from Cornelius

The local vector search system (FAISS + sentence-transformers + NetworkX) lives in cornelius' `resources/local-brain-search/` Python package. **Fully local — no cloud API needed.** Clone it in:

```bash
# Option A: sparse checkout from public cornelius repo
TMPDIR=$(mktemp -d)
git clone --depth 1 --filter=blob:none --sparse https://github.com/Abilityai/cornelius "$TMPDIR/cornelius"
cd "$TMPDIR/cornelius" && git sparse-checkout set resources/local-brain-search && cd -
cp -r "$TMPDIR/cornelius/resources/local-brain-search/"* "$destination/resources/local-brain-search/"
rm -rf "$TMPDIR"
```

If the public cornelius repo does not include `resources/local-brain-search/` (check first with `git ls-remote`), fall back to:

```bash
# Option B: copy from local cornelius directory
if [ -d "$HOME/Dropbox/Agents/cornelius/resources/local-brain-search" ]; then
  cp -r "$HOME/Dropbox/Agents/cornelius/resources/local-brain-search/"* \
        "$destination/resources/local-brain-search/"
else
  echo "WARNING: local-brain-search source not found. Scaffolding stubs only."
  # Create stub README pointing at cornelius repo for manual install
fi
```

After the copy, clean up cornelius-specific artifacts:

```bash
# Remove cornelius-specific reports (we'll generate fresh ones)
rm -rf "$destination/resources/local-brain-search/reports/"

# Remove Python cache
rm -rf "$destination/resources/local-brain-search/__pycache__/"

# Clear data directory of cornelius enrichments (keep directory structure)
rm -f "$destination/resources/local-brain-search/data/"*.json 2>/dev/null
rm -f "$destination/resources/local-brain-search/data/"*.faiss 2>/dev/null
rm -f "$destination/resources/local-brain-search/data/"*.npy 2>/dev/null
```

Then **overwrite** `resources/local-brain-search/memory_config.py` with the domain-customized version generated in STEP 13 (or create a separate `agent_config.yaml` that the memory_config.py imports).

Record which path was used (A, B, or stub) in the completion summary.

---

## STEP 13: Generate `<agent>-graph.yaml`

This is the **load-bearing ontology file**. Write it as `$destination/${agent_name}-graph.yaml`. The local-brain-search machinery reads from `memory_config.py` — ensure the BRAIN_PATH and other settings align with this agent's vault structure.

Template structure (fill from wizard answers):

```yaml
# ${display_name} Dependency Graph Configuration
# Central schema defining artifact types, default edges, and propagation rules.
# This file is the structural rulebook for the coherence engine.
# Generated by install-kb-agent wizard on ${today}.

agent:
  name: ${agent_name}
  domain: ${preset}
  atomic_unit:
    name: ${atomic_unit.name}
    description: ${atomic_unit.description}
    required_fields: ${atomic_unit.required_fields}
    identity_rule: ${atomic_unit.identity_rule}
  trigger_topology: ${trigger_topology}

artifact_types:
  signal:
    layer: 1
    default_mode: reflective
    vault_paths: ["01-Sources/"]
    description: "Raw inputs - external source material"

  impression:
    layer: 2
    default_mode: reflective
    vault_paths: ["00-Inbox/"]
    description: "First-pass captures, fleeting notes"

  insight:
    layer: 3
    default_mode: mixed  # determined by lifecycle score
    vault_paths: ["02-Permanent/"]  # plus any additional from entity types
    description: "Atomic permanent notes - instances of the atomic unit"

  framework:
    layer: 4
    default_mode: generative
    vault_paths: ["02-Permanent/"]  # subset, detected by heuristics
    description: "Generative entities - authored, prescriptive"

  lens:
    layer: 5
    default_mode: reflective
    vault_paths: ["03-MOCs/"]
    description: "Maps of content, navigational indices"

  synthesis:
    layer: 6
    default_mode: reflective
    vault_paths: ["04-Output/"]
    description: "Articles, essays, composed output"

  index:
    layer: 7
    default_mode: reflective
    vault_paths: ["05-Meta/", "Changelogs/"]
    description: "Structural meta - analysis, changelogs"

# Domain-specific entity types (extend layer 3-4 with domain semantics)
domain_entity_types:
  # For each entity type the user selected in STEP 5:
  ${entity.name}:
    base_layer: ${entity.base_layer}  # usually 3 or 4
    mode: ${entity.mode}
    vault_paths: ${entity.vault_paths}
    description: ${entity.description}

# Default edge types between layers (cornelius cornerstones)
default_edges:
  # Layer 1 -> 2
  - {from_type: signal, to_type: impression, edge_type: derives-from, authority: source}
  # Layer 1 -> 3
  - {from_type: signal, to_type: insight, edge_type: derives-from, authority: source}
  # Layer 2 -> 3
  - {from_type: impression, to_type: insight, edge_type: derives-from, authority: target}
  # Layer 3 -> 4 (emergence)
  - {from_type: insight, to_type: framework, edge_type: derives-from, authority: target}
  # Layer 4 -> 3 (generation)
  - {from_type: framework, to_type: insight, edge_type: instantiates, authority: source}
  # Layer 3 -> 5
  - {from_type: insight, to_type: lens, edge_type: derives-from, authority: source}
  # Layer 4 -> 5
  - {from_type: framework, to_type: lens, edge_type: derives-from, authority: source}
  # Layer 4 -> 6
  - {from_type: framework, to_type: synthesis, edge_type: instantiates, authority: source}
  # Layer 3 -> 6
  - {from_type: insight, to_type: synthesis, edge_type: derives-from, authority: source}
  # Layer 5 -> 6
  - {from_type: lens, to_type: synthesis, edge_type: references, authority: source}
  # Layer 6 -> 7
  - {from_type: synthesis, to_type: index, edge_type: derives-from, authority: source}

same_layer_defaults:
  insight: {edge_type: references, authority: null}
  framework: {edge_type: references, authority: null}
  signal: {edge_type: associates, authority: null}

# Cornerstone edges + domain-specific edges from STEP 7
edge_types:
  # Cornerstones (always present, cornelius defaults)
  derives-from: {direction: directed, decay: 0.8}
  instantiates: {direction: directed, decay: 0.7}
  references: {direction: directed, decay: 0.2}
  associates: {direction: bidirectional, decay: 0.05}
  tension: {direction: bidirectional, decay: 0.0, immune_to_propagation: true}
  supersedes: {direction: directed, decay: 1.0}
  # Domain edges - one entry per user-selected edge from STEP 7
  ${domain_edge.name}:
    direction: ${domain_edge.direction}
    decay: ${domain_edge.decay}
    authority_side: ${domain_edge.authority_side}
    description: ${domain_edge.description}

propagation:
  edge_decay:
    derives-from: 0.8
    instantiates: 0.7
    references: 0.2
    associates: 0.05
    tension: 0.0
    supersedes: 1.0
    # ...plus domain edges
  distance_decay: [1.0, 0.5, 0.1, 0.0]
  hub_threshold: 50
  staleness_threshold: 0.3
  max_propagation_depth: 3

lifecycle:
  detection_window_days: 30
  crystallizing_threshold: 0.3
  generative_threshold: 0.6
  signals:
    # One entry per signal selected in STEP 8
    ${signal.name}:
      weight: ${signal.weight}
      crystallizing_min: ${signal.crystallizing_min}
      generative_min: ${signal.generative_min}

framework_detection:
  type_indicators: ${preset.framework_type_indicators}  # default to cornelius'
  title_patterns: ${preset.framework_title_patterns}
  graph_thresholds:
    min_in_degree: 20
    min_out_degree: 10
    min_betweenness: 0.02
```

**Validation:** after writing, verify:
- All 6 cornerstone edges are present in both `default_edges` and `edge_types`
- Lifecycle signal weights sum to 1.0 (normalize if needed)
- All entity types from STEP 5 appear under `domain_entity_types`
- All domain edges from STEP 7 appear under `edge_types`

---

## STEP 14: Generate CLAUDE.md

The generated CLAUDE.md is modeled on cornelius' CLAUDE.md but customized to the domain. Structure:

```markdown
# CLAUDE.md

## Identity

You are **${display_name}** — ${preset.identity_statement}.

${preset.persona_paragraph}

**Your atomic unit:** ${atomic_unit.name}. Every time you capture something new, it should reduce to one or more ${atomic_unit.name} instances. Never create junk-drawer notes; if something doesn't fit the atomic unit, it is either supporting material (put it in 01-Sources) or it belongs in another agent.

## Core Architecture: Brain Dependency Graph

This agent runs on the Brain Dependency Graph (BDG) — a typed, mode-aware, direction-aware graph that functions as a coherence engine rather than a retrieval engine. See `resources/local-brain-search/BRAIN-DEPENDENCY-GRAPH-ARCHITECTURE.md` for the full spec.

**Key concepts you must internalize:**

1. **Authority is edge-local, not node-global.** The same entity can be authoritative on one edge and subordinate on another. Do not build node-level authority hierarchies.

2. **Detect, don't declare.** Lifecycle and tension emerge from behavioral signals. Manual tagging is a fallback, not the primary mechanism. The `/compute-lifecycle` skill does the detection.

3. **Contradictions are assets.** Tension edges are immune to propagation and surfaced as synthesis opportunities. Never auto-resolve.

4. **Staleness propagates with attenuation.** When a source changes, targets get flagged via `/propagate-change`. Decay is by edge type (see `${agent_name}-graph.yaml`), distance, and hub dampening.

5. **The graph is the agent's operating context.** `${agent_name}-graph.yaml` is part of the loaded context alongside this prompt. Derive behavior from graph structure, not ad-hoc rules.

6. **You are a gardener, not an engineer.** You prune, suggest, surface patterns. You do not decide creative matters on the user's behalf.

7. **Automate measurement and maintenance. Never automate creation or judgment.**

## The Seven-Layer Ontology

| Layer | Folder | Entity Types | Mode |
|-------|--------|-------------|------|
| 1 Signal | `01-Sources/` | External source material | Reflective |
| 2 Impression | `00-Inbox/` | Fleeting captures | Reflective |
| 3 Insight | `02-Permanent/` | ${insight_entities} | Mixed |
| 4 Framework | `02-Permanent/` (subset) | ${framework_entities} | Generative |
| 5 Lens | `03-MOCs/` | MOCs, navigational indices | Reflective |
| 6 Synthesis | `04-Output/` | Articles, composed output | Reflective |
| 7 Index | `05-Meta/` | Meta-structural | Reflective |

${domain_entity_types_table}

## Edge Types

Cornerstone edges (always present):
- `derives-from` (directed, decay 0.8) — target synthesized from source
- `instantiates` (directed, decay 0.7) — target is specific case of source framework
- `references` (directed, decay 0.2) — weak mention
- `associates` (bidirectional, decay 0.05) — thematic neighborhood
- `tension` (bidirectional, decay 0.0, immune) — productive contradiction
- `supersedes` (directed, decay 1.0) — replacement

Domain edges:
${domain_edges_list}

## Core Capabilities

| Skill | Purpose | Schedulable |
|-------|---------|-------------|
| `/coherence-sweep` | Full graph coherence analysis — staleness, lifecycle transitions, structural health | Weekly |
| `/compute-lifecycle` | Recompute lifecycle scores from behavioral signals | Weekly |
| `/detect-tensions` | Find productive contradictions | Weekly |
| `/refresh-index` | Rebuild FAISS vector index | Daily |
| `/propagate-change` | Propagate staleness after a substantive edit | On-demand |
| `/recall <query>` | 3-layer semantic search with spreading activation | On-demand |
| `/find-connections <note>` | Discover hidden edges around a specific note | On-demand |
${domain_skills_table}

## Task Management

This agent manages its work via GitHub Issues in this repository.

**Workflow:**
1. Create issues with clear requirements and priority labels
2. Agent picks highest priority `status:todo` issue
3. Moves to `status:in-progress` while working
4. Closes with summary when complete
5. Repeats until backlog is empty

**Skills:**
| Skill | Purpose |
|-------|---------|
| `/backlog` | View current workload by priority |
| `/pick-work` | Grab next task, mark in-progress |
| `/close-work "summary"` | Complete current task |
| `/work-loop` | Autonomous processing (schedulable) |

**Labels:**
- `status:todo` / `status:in-progress` / `status:blocked` / `status:done`
- `priority:p0` (do now) / `priority:p1` (do soon) / `priority:p2` (do eventually)

**Creating Issues for this Agent:**
- Clear title describing the task
- Body with requirements/acceptance criteria
- Add appropriate priority label
- Leave as `status:todo` (or no status — defaults to todo)

**Autonomous Mode (Trinity):**
Schedule `/work-loop` to run periodically. The agent will process its backlog automatically:
```bash
trinity schedules create work-loop --cron "0 */4 * * *"
```

## Subagents

${subagents_table}

**Decision guide:**
${subagent_decision_guide}

## Trigger Topology

This agent is **${trigger_topology}**.

${trigger_specifics}

## Development Workflow

Build this agent iteratively:

1. **Start with /onboarding** — get credentials configured, plugins installed, and your first skill run done
2. **Add skills with /create-playbook** — each new capability becomes a slash command
3. **Refine skills with /adjust-playbook** — improve based on real usage
4. **Refine the ontology** — after 2-3 weeks of real use, revisit `${agent_name}-graph.yaml`. Ontologies are hypotheses; they get revised.
5. **Deploy when ready** — `trinity deploy .` to go live remotely

## Deploying to Trinity

```bash
pip install trinity-cli
trinity init
trinity deploy .
```

After deploying:
- `trinity chat ${agent_name} "message"` — talk to remote agent
- `trinity logs ${agent_name}` — view logs
- `trinity schedules list ${agent_name}` — check scheduled jobs (coherence-sweep, compute-lifecycle, detect-tensions, refresh-index)

## Onboarding

This agent tracks your setup progress in `onboarding.json`. Run `/onboarding` to see
your checklist and continue where you left off.

On conversation start, if `onboarding.json` exists and has incomplete steps in the
current phase, briefly remind the user:
"You have [N] setup steps remaining. Run `/onboarding` to continue."

Do not nag — mention once per session.

## Installed Plugins

These plugins are installed during onboarding (`/onboarding` handles automatically):

- `/plugin install agent-dev@abilityai` — create new skills
- `/plugin install trinity@abilityai` — deploy to Trinity
${extra_plugin_installs}

**Built-in (no install needed):**
- GitHub Backlog — task management via GitHub Issues (`/backlog`, `/pick-work`, `/close-work`, `/work-loop`)

## Project Structure

\`\`\`
${agent_name}/
  CLAUDE.md                  # This file
  ${agent_name}-graph.yaml   # Ontology — load-bearing
  template.yaml              # Trinity metadata
  dashboard.yaml             # Trinity dashboard
  onboarding.json            # Setup tracker
  .env.example               # Credential template
  .gitignore                 # Git exclusions
  .mcp.json.template         # MCP config template
  .claude/
    agents/                  # Subagents (${num_subagents} total)
    skills/                  # Skills (${num_skills} total)
  resources/
    local-brain-search/      # Cloned from cornelius — FAISS + sentence-transformers
      memory_config.py         # Config for embeddings, graph, spreading activation
      *.py                   # Python machinery
      data/                  # Graph enrichments (populated at runtime)
  00-Inbox/                  # Layer 2
  01-Sources/                # Layer 1
  02-Permanent/              # Layer 3 + 4
  03-MOCs/                   # Layer 5
  04-Output/                 # Layer 6
  05-Meta/                   # Layer 7
    Changelogs/              # Session changelogs (mandatory)
\`\`\`

## Artifact Dependency Graph

\`\`\`yaml
artifacts:
  CLAUDE.md:
    mode: prescriptive
    direction: source
    description: "Agent identity and behavior"

  ${agent_name}-graph.yaml:
    mode: prescriptive
    direction: source
    description: "Ontology — load-bearing. All skills and subagents derive behavior from this."

  resources/local-brain-search/memory_config.py:
    mode: descriptive
    direction: target
    sources: [${agent_name}-graph.yaml]
    description: "Python-facing copy of the ontology. Must stay in sync."

  resources/local-brain-search/data/graph_enrichments.json:
    mode: descriptive
    direction: target
    sources: [vault notes, compute-lifecycle skill]
    description: "Node/edge metadata sidecar. Lifecycle scores, staleness flags."

  onboarding.json:
    mode: descriptive
    direction: target
    sources: [onboarding/SKILL.md]
    description: "Persistent onboarding state"

  dashboard.yaml:
    mode: descriptive
    direction: target
    sources: [update-dashboard/SKILL.md]
    description: "Trinity dashboard"
\`\`\`

## Recommended Schedules

| Skill | Schedule | Purpose |
|-------|----------|---------|
| `/refresh-index` | `0 5 * * *` | Rebuild FAISS vector index (daily 5am) |
| `/coherence-sweep` | `0 6 * * 1` | Weekly graph coherence analysis (Monday 6am) |
| `/compute-lifecycle` | `0 7 * * 1` | Weekly lifecycle score recompute (Monday 7am) |
| `/detect-tensions` | `0 8 * * 1` | Weekly tension detection (Monday 8am) |
| `/update-dashboard` | `0 */4 * * *` | Dashboard metrics refresh (every 4 hours) |
| `/work-loop` | `0 */4 * * *` | Process GitHub Issues backlog (every 4 hours) |
${event_schedules_if_hybrid_or_event_driven}

## Guidelines

- **Every new note instantiates the atomic unit.** If it doesn't, redirect the user.
- **Never edit someone else's voice.** When extracting insights, preserve the user's phrasing.
- **Contradictions get flagged, not resolved.** Surface tensions; let the user decide.
- **Sidecar, not frontmatter.** Never write lifecycle scores or staleness flags into note frontmatter. They live in `resources/local-brain-search/data/graph_enrichments.json`.
- **Changelogs are mandatory.** Every subagent session ends with a dated changelog in `05-Meta/Changelogs/`.
- **Refine ontology after 2-3 weeks.** Schedule a review to revisit ${agent_name}-graph.yaml once you have real usage data.
```

Customize each `${...}` variable from the wizard answers. For preset-specific content (`persona_paragraph`, `identity_statement`, `trigger_specifics`, `subagent_decision_guide`), see the **Preset Defaults** section at the bottom of this skill.

---

## STEP 15: Generate Subagents

Write one subagent file per distinct ingestion/processing path. Standard set for every KB agent:

### 15a. `.claude/agents/vault-manager.md`

CRUD operations on vault notes. Modeled on cornelius' vault-manager. Must enforce the mandatory frontmatter template. Always gets full Read/Write/Edit tool access to the vault.

### 15b. `.claude/agents/connection-finder.md`

Discover hidden connections around a specific note. Reads graph enrichments, invokes FAISS semantic search via `resources/local-brain-search/`, surfaces high-strength-low-distance candidates.

### 15c. `.claude/agents/auto-discovery.md`

Autonomous cross-domain connection hunting. Runs periodically, looks for **low similarity + high conceptual strength** pairs (the cornelius heuristic for non-obvious bridges). Emits candidate tension edges for user review.

### 15d. One extractor per entity type

For each entity type from STEP 5 with a distinct ingestion path, generate `.claude/agents/${entity}-extractor.md`. Example for Community Manager:

- `.claude/agents/message-extractor.md` — ingests chat messages (Slack/Discord), extracts people + events + conflicts
- `.claude/agents/event-extractor.md` — ingests calendar events/RSVPs

### 15e. `.claude/agents/event-ingester.md` (if trigger_topology ∈ {event, hybrid})

Webhook/polling listener. Translates incoming events into vault impressions for downstream extractors.

**Subagent file template:**

```yaml
---
name: ${subagent-name}
description: ${one-line purpose}
allowed-tools: ${tools}
---
```

```markdown
# ${Subagent Title}

## Purpose

${Purpose paragraph — tied to entity types or ingestion path from wizard}

## Responsibilities

- ${responsibility 1}
- ${responsibility 2}
- ${responsibility 3}

## Process

### Step 1: ${action}
${instructions}

### Step 2: ${action}
${instructions}

## Output Conventions

- Notes go to: ${vault_path based on layer}
- Frontmatter: include the mandatory cornelius fields (created, updated, created_by, updated_by, agent_version) plus entity-type-specific fields
- Changelog: create/append `05-Meta/Changelogs/${YYYY-MM-DD}-${subagent-name}.md` with what was processed

## Constraints

- Never edit notes authored by the user — only extract into new notes with provenance
- Never auto-resolve tensions — flag them, let /detect-tensions surface to user
- Respect the atomic unit: ${atomic_unit.name}
```

---

## STEP 16: Generate KB-Core Skills

Every KB agent gets these seven skills. They are templated to the agent's ontology (graph.yaml). Each references the cloned local-brain-search Python package in `resources/local-brain-search/`.

### 16a. `/coherence-sweep`

Runs full graph coherence analysis. Invokes `resources/local-brain-search/coherence.py`. Reports: staleness flags, lifecycle transitions detected, structural health metrics (hubs, orphans, cluster sizes), tension candidates.

Output: `05-Meta/Coherence-Reports/${YYYY-MM-DD}.md`.

Scheduled: `0 6 * * 1` (weekly Monday 6am).

### 16b. `/compute-lifecycle`

Recomputes lifecycle scores for all insights and frameworks based on the signals from STEP 8. Invokes `resources/local-brain-search/lifecycle.py`. Updates `resources/local-brain-search/data/graph_enrichments.json`.

Scheduled: `0 7 * * 1` (weekly Monday 7am).

### 16c. `/detect-tensions`

Finds productive contradictions: pairs of notes with high semantic similarity but opposing conclusions. Invokes `resources/local-brain-search/tension.py`. Emits candidate tension edges for user review.

Scheduled: `0 8 * * 1` (weekly Monday 8am).

### 16d. `/refresh-index`

Rebuilds the FAISS vector index over all vault notes. Invokes `resources/local-brain-search/` (specific path varies — check cornelius' cli.py for the command).

Scheduled: `0 5 * * *` (daily 5am).

### 16e. `/propagate-change`

Given a note path + change magnitude, propagates staleness along typed edges according to decay rules. Invokes `resources/local-brain-search/propagation.py`. Typically invoked on-demand after substantive edits (or by a file watcher in edit-driven mode).

### 16f. `/recall <query>`

3-layer semantic search with spreading activation: FAISS similarity → graph neighbors (1-hop + 2-hop with distance decay) → cluster expansion via MOCs. Returns ranked results grouped by layer.

### 16g. `/find-connections <note-path>`

Connection discovery around a single note. Combines low-similarity-high-strength heuristic (auto-discovery style) with typed-edge traversal to surface non-obvious neighbors.

### 16h-16k. GitHub Backlog Skills (Task Management)

Every KB agent gets the GitHub backlog workflow for task and project management. These skills let the agent manage work via GitHub Issues — pick tasks, track progress, close with summaries, and run autonomous work loops.

Generate these 4 skills directly (adapted from the `install-github-backlog` wizard pattern):

**16h. `/backlog`**

View current workload from GitHub Issues by priority and status. Shows in-progress work, next up (P0 todos), and queued (P1/P2).

```yaml
---
name: backlog
description: Show current GitHub Issues backlog — what's in progress, what's next, priorities
argument-hint: "[all|in-progress|blocked]"
allowed-tools: Bash, Read
user-invocable: true
---
```

Process:
1. Parse argument (default: overview, or `all`/`in-progress`/`blocked`)
2. Verify `gh auth status`
3. Query issues with status/priority labels
4. Format output as priority-grouped table

**16i. `/pick-work`**

Select the next task and mark it in-progress.

```yaml
---
name: pick-work
description: Pick the next task from the backlog — selects highest priority todo, moves to in-progress
argument-hint: "[issue-number]"
allowed-tools: Bash, Read
user-invocable: true
---
```

Process:
1. Check if any issue is already in-progress
2. If argument provided, use that issue; otherwise find highest priority todo (P0→P1→P2)
3. Move to in-progress: `gh issue edit $N --remove-label "status:todo" --add-label "status:in-progress"`
4. Add start comment and display the issue for work

**16j. `/close-work`**

Complete current work with summary.

```yaml
---
name: close-work
description: Mark current work done — adds summary comment, updates labels, closes issue
argument-hint: "\"summary of what was done\""
allowed-tools: Bash, Read
user-invocable: true
---
```

Process:
1. Find in-progress issue
2. Validate summary argument (require if empty)
3. Add completion comment with summary
4. Update labels and close: `gh issue edit $N --remove-label "status:in-progress" --add-label "status:done" && gh issue close $N`

**16k. `/work-loop`**

Autonomous work processing — schedulable on Trinity.

```yaml
---
name: work-loop
description: Autonomous work loop — process backlog issues until empty or time limit reached
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent, Skill
automation: autonomous
schedule: "0 */4 * * *"
user-invocable: true
---
```

Process:
1. Initialize, record start time (40-minute limit for reliability)
2. Check for in-progress work; if found, continue it
3. If none, pick highest priority todo
4. Execute task based on issue content (invoke skills, direct execution, or spawn Agent)
5. Close with summary when complete
6. Loop back to step 2 if under 40 minutes

**GitHub Labels Setup:**

The `/backlog` skill creates these labels on first run if missing:
- `status:todo`, `status:in-progress`, `status:blocked`, `status:done`
- `priority:p0` (do now), `priority:p1` (do soon), `priority:p2` (do eventually)

**Skill file template for each:**

```yaml
---
name: ${skill-name}
description: ${one-line}
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: ${today}
  author: ${agent_name}
---
```

```markdown
# ${Skill Title}

## Purpose
${purpose}

## Process

### Step 1: Load ontology
Read `${agent_name}-graph.yaml` to get current ontology: entity types, edge types, propagation rules, lifecycle thresholds.

### Step 2: ${action}
Invoke the corresponding module in `resources/local-brain-search/`:
\`\`\`bash
cd resources/local-brain-search && python search.py ${args}
\`\`\`
(Exact command depends on cornelius' CLI — see `resources/local-brain-search/cli.py`.)

### Step 3: Interpret and report
${reporting pattern — how to present results to user}

## Output
${output location and format}
```

For each of the 7 skills, flesh out the Step 2 + Step 3 content based on what that skill does. Use cornelius' `resources/local-brain-search/cli.py` as the canonical reference for invocation syntax — it's in the cloned package.

---

## STEP 17: Generate Domain Skills

Based on `$preset`, generate 2-3 domain-specific skills. Preset defaults:

- **Personal KB (cornelius-flavor):** `/extract-insights`, `/graduate-insights`, `/create-article`, `/advise`
- **Community Manager:** `/recap-community`, `/who-to-introduce`, `/reach-out-list`, `/flag-tensions`
- **CS Researcher:** `/lit-review`, `/track-sota`, `/contradiction-map`
- **Clinical Research:** `/evidence-summary`, `/replication-status`, `/subgroup-analysis`
- **Legal Analyst:** `/obligation-map`, `/find-supersessions`, `/conflict-scan`
- **Custom:** none — user will create with `/create-playbook` after onboarding

Each skill file follows the standard skill template (see 16's template). Each must:
- Reference the ontology (graph.yaml) in Step 1
- Use domain-specific logic in Step 2
- Produce a concrete artifact in a well-defined location

For **Personal KB**, prefer copying the exact skill prose from cornelius' `.claude/skills/` where possible (these are battle-tested). Note the copy source in a comment at the top of each copied skill: `# Copied from cornelius on ${today}; customize as needed.`

---

## STEP 18: Generate Onboarding

### 18a. `onboarding.json`

```json
{
  "phase": "local",
  "started": "${today}",
  "steps": {
    "local": {
      "env_configured": { "done": false, "label": "Configure environment variables (.env)" },
      "local_brain_search_ready": { "done": false, "label": "Verify local-brain-search (cd resources/local-brain-search && python index_brain.py --help)" },
      "first_extraction": { "done": false, "label": "Run your first extraction (/${primary-domain-skill})" },
      "first_coherence_sweep": { "done": false, "label": "Run /coherence-sweep to see the graph" },
      "plugins_installed": { "done": false, "label": "Install plugins (${plugin_list})" }
    },
    "trinity": {
      "onboarded": { "done": false, "label": "Deploy to Trinity (/trinity:onboard)" },
      "first_remote_run": { "done": false, "label": "Run a skill remotely via mcp__trinity__chat_with_agent" }
    },
    "schedules": {
      "coherence_scheduled": { "done": false, "label": "Schedule /coherence-sweep, /compute-lifecycle, /detect-tensions, /refresh-index" },
      "first_scheduled_run": { "done": false, "label": "Verify first scheduled execution completed" },
      "ontology_review_scheduled": { "done": false, "label": "Calendar a 2-week ontology review (revisit graph.yaml)" }
    }
  }
}
```

### 18b. `.claude/skills/onboarding/SKILL.md`

Standard onboarding skill — same as install-ghostwriter's, with labels updated for KB agent's steps. Include phase-transition messages and the guidance text for each step. The domain-specific local steps (`first_extraction`, `first_coherence_sweep`) should tell the user exactly which command to run.

Copy the onboarding pattern from install-ghostwriter's Section 8 — the structure is unchanged, only the step labels differ.

---

## STEP 19: Generate Dashboard

### 19a. `dashboard.yaml`

KB-specific dashboard with sections:

```yaml
title: "${display_name}"
refresh: 300
updated: "${today}"

sections:
  - title: "Graph Health"
    layout: grid
    columns: 3
    widgets:
      - {type: metric, label: "Total Notes", value: "0"}
      - {type: metric, label: "Edges", value: "0"}
      - {type: metric, label: "Clusters", value: "0"}
      - {type: status, label: "Last Coherence Sweep", value: "—", color: gray}
      - {type: metric, label: "Staleness Flags", value: "0"}
      - {type: metric, label: "Tension Candidates", value: "0"}

  - title: "Lifecycle Distribution"
    layout: grid
    columns: 3
    widgets:
      - {type: metric, label: "Reflective", value: "0"}
      - {type: metric, label: "Crystallizing", value: "0"}
      - {type: metric, label: "Generative", value: "0"}

  - title: "By Layer"
    layout: list
    widgets:
      - {type: list, title: "Notes per layer", items: [], max_items: 7}

  - title: "Recent Activity"
    layout: list
    widgets:
      - {type: list, title: "Changelogs", items: [], max_items: 5}

  - title: "Quick Links"
    layout: list
    widgets:
      - {type: link, label: "Trinity Dashboard", url: "https://ability.ai", external: true}
      - {type: link, label: "Ontology", url: "./${agent_name}-graph.yaml", external: false}
```

### 19b. `.claude/skills/update-dashboard/SKILL.md`

Standard update-dashboard, with metrics gathering adapted to read `resources/local-brain-search/data/graph_enrichments.json` for edge/node counts, lifecycle distribution, staleness flags. Enumerate `05-Meta/Changelogs/` for recent activity.

---

## STEP 20: Generate Supporting Files

### `.env.example`

```
# Core
AGENT_NAME=${agent_name}

# Local brain search (fully local — no cloud API needed)
# BRAIN_PATH is auto-detected; override if vault lives elsewhere
# BRAIN_PATH=

# Trinity (optional until deployment)
TRINITY_API_KEY=
TRINITY_ORG=
${preset_specific_env_vars}
```

### `.gitignore`

```
.env
.mcp.json
.claude/temp/
resources/local-brain-search/__pycache__/
resources/local-brain-search/data/*.faiss
resources/local-brain-search/data/*.npy
node_modules/
```

Note: `graph_enrichments.json` **is** committed (it's the graph sidecar and travels with the vault). The FAISS `.faiss` and `.npy` files are rebuilt by `/refresh-index` and can be reproduced, so ignore.

### `.mcp.json.template`

Start with an empty template. If any selected plugin provides an MCP server, add the placeholder entry here.

### `template.yaml`

```yaml
name: ${agent_name}
display_name: ${display_name}
description: |
  ${preset.one_paragraph_description}
avatar_prompt: ${preset.avatar_prompt}
resources:
  cpu: "2"
  memory: "4g"
```

Preset-specific avatar prompts live in the **Preset Defaults** section.

---

## STEP 21: Initialize Git

```bash
cd "$destination" && git init && git add -A && git commit -m "Initial ${agent_name} scaffold: KB agent via install-kb-agent wizard"
```

---

## STEP 22: Offer GitHub Repo Creation

Use AskUserQuestion:
- **Question:** "Create a GitHub repo for this agent?"
- **Header:** "GitHub"
- **Options:**
  1. Private repo
  2. Public repo
  3. Skip

If private or public, use `gh repo create "${agent_name}" --${public|private} --source=. --push`. If `gh` is unavailable, show manual instructions.

---

## STEP 23: Completion

Display:

```
## ${display_name} Installed

### What Was Created

| Item | Path |
|------|------|
| Agent identity | CLAUDE.md |
| Ontology (load-bearing) | ${agent_name}-graph.yaml |
| Coherence engine | resources/local-brain-search/ (${source}) |
| Subagents (${N}) | .claude/agents/ |
| KB-core skills (7) | .claude/skills/ |
| Task management (4) | .claude/skills/backlog, pick-work, close-work, work-loop |
| Domain skills (${M}) | .claude/skills/ |
| 7-layer vault | 00-Inbox/ through 05-Meta/ |
| Trinity files | template.yaml, dashboard.yaml, onboarding.json |
| Setup tracker | .claude/skills/onboarding/ |

### Get Started

1. Open your new agent:
   \`\`\`
   cd ${destination} && claude
   \`\`\`

2. Run the setup wizard:
   \`\`\`
   /onboarding
   \`\`\`

   This walks you through: configuring env vars, verifying the local-brain-search
   machinery, your first extraction, your first coherence sweep, and — when
   you're ready — deploying to Trinity with scheduled jobs.

3. Add cross-session durability: run \`/agent-dev:add-git-sync\` (auto-commits on session end, rebases on start — essential for scheduled Trinity runs).

### Remember

Your ontology (\`${agent_name}-graph.yaml\`) is a hypothesis, not a specification.
Schedule a 2-week review to revisit it once you have real usage data.
```

Do not list manual steps beyond `/onboarding`. The onboarding skill handles the rest in a tracked, resumable flow.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Destination exists | Warn; offer overwrite / new name / cancel |
| `git clone` for cornelius fails | Fall back to local `cornelius-internal` copy; if that also fails, scaffold stub skill files with TODO comments pointing at the cornelius repo and warn in completion summary |
| Signal weights don't sum to 1.0 | Normalize silently; report the normalization in completion summary |
| User selects 0 entity types | Block; require ≥1 |
| User selects 0 signals | Block; require ≥1 — without signals, /compute-lifecycle has nothing to do |
| User selects Custom preset and leaves atomic unit vague | Push back with follow-up questions: what fields? what's the identity rule? Refuse to generate until concrete |
| gh CLI not available | Show manual GitHub instructions |
| User wants more than 5 domain skills | Generate top 5, note the rest as "planned" in README |

---

## Preset Defaults

Used to pre-fill questions and generate customized content. Values below inform the answers that flow into steps 4-8 and the preset-specific prose in STEP 14 (identity, persona, avatar).

### Personal KB (cornelius-flavor)

- **atomic_unit:** `{name: "atomic insight", description: "one claim in the user's voice, tagged with provenance", required_fields: [claim, voice, provenance], identity_rule: "text-similarity above 0.92"}`
- **entity_types:** insights (mixed), frameworks (generative), sources (reflective), lenses (reflective), syntheses (reflective), indices (reflective)
- **domain_edges:** (none — cornerstones only)
- **trigger_topology:** edit-driven
- **signals:** citation_frequency (0.3), generative_ratio (0.3), cross_domain_reach (0.25), temporal_acceleration (0.15)
- **identity_statement:** "an insight harvester and second-brain partner that preserves the user's authentic voice while surfacing emergent frameworks from their own writing"
- **persona_paragraph:** "You are an insight scout, perspective preservationist, and wisdom curator. You do not write on the user's behalf. You surface what they already think, cluster it, and notice when contradictions become productive."
- **avatar_prompt:** "A thoughtful archivist in a dimly lit study, surrounded by floating threads of light connecting hundreds of open notebooks. Warm lamp glow, concentrated expression, wire-rim glasses, linen shirt. Conveys care and patient attention."
- **domain_skills:** `/extract-insights`, `/graduate-insights`, `/create-article`, `/advise`

### Community Manager

- **atomic_unit:** `{name: "member profile", description: "a person with observed behavior record", required_fields: [handle, joined, last_seen, groups, traits], identity_rule: "handle + platform"}`
- **entity_types:** people (reflective), events (reflective), groups (reflective), norms (generative), topics (reflective), conflicts (reflective), initiatives (generative)
- **domain_edges:** introduced-by (directed, decay 0.4), conflicts-with (bidirectional, decay 0.0, tension), co-attends (bidirectional, decay 0.1), champions (directed, decay 0.7), violates (directed, decay 0.8)
- **trigger_topology:** hybrid
- **signals:** interaction_recency (0.3), reciprocity_ratio (0.25), co_attendance_diversity (0.2), sentiment_trajectory (0.25)
- **identity_statement:** "a community steward that watches interactions, surfaces who's at-risk, who to connect, and which conflicts deserve facilitation"
- **persona_paragraph:** "You are a gardener of community health. You notice quiet people going quieter, connections that haven't happened but should, and tensions that want to be facilitated rather than resolved."
- **avatar_prompt:** "A warm, attentive community organizer at a large table spread with name cards and colored threads connecting them. Soft daylight, welcoming expression, hand-knitted sweater. Conveys social intelligence and care."
- **domain_skills:** `/recap-community`, `/who-to-introduce`, `/reach-out-list`, `/flag-tensions`

### CS Researcher

- **atomic_unit:** `{name: "verifiable claim", description: "a claim with paper + section + result + conditions", required_fields: [claim_text, paper, section, conditions, support_type], identity_rule: "claim_text canonicalized + paper_id"}`
- **entity_types:** papers (reflective), authors (reflective), methods (mixed), datasets (reflective), benchmarks (reflective), claims (reflective), replication_attempts (reflective)
- **domain_edges:** cites (directed, decay 0.2), extends (directed, decay 0.6), refutes (directed, decay 1.0, tension-adjacent), reproduces (directed, decay 0.3), evaluates-on (directed, decay 0.5)
- **trigger_topology:** hybrid
- **signals:** replication_count (0.3), supersession_velocity (0.25), contradiction_density (0.2), citation_frequency (0.25)
- **identity_statement:** "a research librarian and coherence engine for a specific CS subfield — tracks claims, replications, and supersessions across the literature"
- **persona_paragraph:** "You are methodical, evidence-grounded, and suspicious of hype. Every claim gets a provenance. Every method gets benchmarks. Every contradiction gets flagged, not papered over."
- **avatar_prompt:** "A scholar in a university library corner, multiple papers arranged on a desk with hand-annotated margins. Soft fluorescent light, focused but welcoming expression, round glasses, cardigan over oxford shirt. Conveys rigor."
- **domain_skills:** `/lit-review`, `/track-sota`, `/contradiction-map`

### Clinical Research

- **atomic_unit:** `{name: "study finding", description: "a finding with population + intervention + outcome + effect size", required_fields: [population, intervention, outcome, effect_size, ci, sample_size], identity_rule: "study_id + outcome_id"}`
- **entity_types:** studies (reflective), populations (reflective), interventions (mixed), outcomes (reflective), findings (reflective), subgroups (reflective)
- **domain_edges:** studies (directed), contradicts (directed, decay 1.0), replicates (directed, decay 0.3), subgroup-of (directed, decay 0.4)
- **trigger_topology:** hybrid
- **signals:** replication_count (0.35), effect_stability (0.3), sample_size_growth (0.2), citation_frequency (0.15)
- **identity_statement:** "a clinical evidence synthesizer that tracks findings, replications, and effect stability across a specific clinical domain"
- **persona_paragraph:** "You are evidence-hierarchy-aware. You distinguish RCTs from observational, large N from small N, replicated from one-off. You never conflate association with causation."
- **avatar_prompt:** "A clinical researcher in a hospital library, holding a tablet with forest plots visible. White coat over scrubs, calm analytical expression, grey-streaked hair. Conveys clinical rigor and empathy."
- **domain_skills:** `/evidence-summary`, `/replication-status`, `/subgroup-analysis`

### Legal Analyst

- **atomic_unit:** `{name: "contractual obligation", description: "a duty with party + trigger + consequence + source clause", required_fields: [party, trigger, consequence, source_clause, contract_id], identity_rule: "contract_id + clause_id"}`
- **entity_types:** contracts (reflective), parties (reflective), clauses (reflective), obligations (reflective), triggers (reflective), consequences (mixed), cases (reflective)
- **domain_edges:** supersedes-clause (directed, decay 1.0), cross-references (directed, decay 0.3), triggers (directed, decay 0.5), exempts (directed, decay 0.7)
- **trigger_topology:** edit-driven
- **signals:** citation_by_cases (0.4), supersession_velocity (0.3), cross_reference_count (0.3)
- **identity_statement:** "a contract and case analyst that tracks obligations, supersessions, and cross-references across a legal corpus"
- **persona_paragraph:** "You are precise and literal. Every obligation has a party, a trigger, a consequence, and a source. Ambiguity gets flagged, not smoothed over."
- **avatar_prompt:** "An attorney at a long oak desk with contracts and a tablet open to annotations. Charcoal suit, half-rim glasses, focused expression. Warm afternoon light through leaded glass. Conveys precision and gravitas."
- **domain_skills:** `/obligation-map`, `/find-supersessions`, `/conflict-scan`

### Custom

No defaults. Every question starts blank; user must specify explicitly. The wizard refuses to generate until the atomic unit is concrete (has required_fields and identity_rule defined).

---

## Best Practices the Generated Agent Must Inherit

These principles from the BDG architecture carry over unchanged to every agent this wizard produces:

1. **Authority is edge-local, not node-global.** Never build node-level authority hierarchies.
2. **Detect, don't declare.** Lifecycle emerges from signals, not manual tagging.
3. **Contradictions are assets.** Tension edges are immune to propagation.
4. **Staleness propagates with attenuation.** By edge type, distance, and hub dampening.
5. **The graph is the agent's operating context.** Loaded alongside the purpose prompt.
6. **The agent is a gardener, not an engineer.** Prune, suggest, surface — don't decide creative matters.
7. **Automate measurement and maintenance. Never automate creation or judgment.**

These must appear verbatim in every generated CLAUDE.md (STEP 14 already includes them).
