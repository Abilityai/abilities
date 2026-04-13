# install-kb-agent

Create a **Cornelius-shaped knowledge-base agent** for any domain — community manager, CS researcher, clinical research, legal analyst, personal KB, or custom. A guided wizard conducts a structured 6-axis ontology interview and scaffolds a Trinity-compatible agent with a typed graph, 7-layer vault, subagents, and scheduled coherence jobs.

## Usage

```
/install-kb-agent
/install-kb-agent ~/my-agents
```

## What It Does

1. **Domain preset** — pick from Personal KB, Community Manager, CS Researcher, Clinical Research, Legal Analyst, or Custom. Seeds defaults for all six ontology axes.
2. **Structured interview** — six progressive questions derive the ontology:
   - Atomic unit (the smallest indivisible thing the agent captures)
   - Entity types + mode model (generative vs reflective per type)
   - Edge types (cornerstones + domain-specific, with direction and decay)
   - Trigger topology (edit-driven / event-driven / hybrid)
   - Lifecycle signals (what promotes entities from reflective to generative)
3. **Clones cornelius brain-graph** — the Python coherence engine (classification, lifecycle scoring, staleness propagation, tension detection) is pulled from [github.com/Abilityai/cornelius](https://github.com/Abilityai/cornelius) into the new agent.
4. **Generates the full scaffold** — CLAUDE.md, `<agent>-graph.yaml` (load-bearing ontology), subagents, KB-core skills, domain skills, 7-layer vault, Trinity files, onboarding tracker.
5. **Initializes git** and optionally creates a GitHub repo.
6. **Hands off to `/onboarding`** — a resumable checklist walks the user through setup → first run → Trinity deployment → scheduled jobs.

## What Gets Created

Every agent this wizard produces includes:

| Artifact | Purpose |
|----------|---------|
| `CLAUDE.md` | Agent identity, BDG architecture rules, seven-layer ontology |
| `<agent>-graph.yaml` | Load-bearing ontology: entity types, edge types, propagation rules, lifecycle thresholds |
| `resources/brain-graph/` | Cornelius coherence engine (Python) — cloned, not re-implemented |
| `.claude/agents/` | Subagents: vault-manager, connection-finder, auto-discovery + one extractor per entity type |
| `.claude/skills/` | KB-core skills: `/coherence-sweep`, `/compute-lifecycle`, `/detect-tensions`, `/refresh-index`, `/propagate-change`, `/recall`, `/find-connections` + domain skills |
| 7-layer vault | `00-Inbox/` (impressions) → `01-Sources/` (signals) → `02-Permanent/` (insights + frameworks) → `03-MOCs/` (lenses) → `04-Output/` (syntheses) → `05-Meta/` (indices) |
| Scheduled jobs | `/refresh-index` daily; `/coherence-sweep`, `/compute-lifecycle`, `/detect-tensions` weekly |
| Trinity files | `template.yaml`, `dashboard.yaml`, `onboarding.json`, `/onboarding` skill, `/update-dashboard` skill |

## Domain Skills by Preset

| Preset | Domain skills generated |
|--------|------------------------|
| **Personal KB** | `/extract-insights`, `/graduate-insights`, `/create-article`, `/advise` |
| **Community Manager** | `/recap-community`, `/who-to-introduce`, `/reach-out-list`, `/flag-tensions` |
| **CS Researcher** | `/lit-review`, `/track-sota`, `/contradiction-map` |
| **Clinical Research** | `/evidence-summary`, `/replication-status`, `/subgroup-analysis` |
| **Legal Analyst** | `/obligation-map`, `/find-supersessions`, `/conflict-scan` |
| **Custom** | None — build with `/create-playbook` after onboarding |

## Why This Wizard Exists

Every KB agent shares the same skeleton. What differs across domains is how six slots get filled. If you elicit the right things in the right order, the rest cascades deterministically — storage schema, subagents, retrieval behavior, skills, and scheduled jobs all fall out of the ontology and trigger model.

Cornelius is the reference implementation of this pattern for the insight-harvester domain. `install-kb-agent` is the productization: the same architecture, parameterized by the six-axis interview, available as a wizard for arbitrary domains.

See `resources/universal-kb-agent-wizard.md` in the cornelius repo for the full design rationale.

## Installation

**One-liner (if you already have the abilityai marketplace):**
```bash
claude plugin install install-kb-agent@abilityai
```

**First time with abilityai marketplace:**
```bash
claude plugin add abilityai/abilities && claude plugin install install-kb-agent@abilityai
```

Or from inside a Claude Code session:
```
/plugin marketplace add abilityai/abilities
/plugin install install-kb-agent@abilityai
```

## About

Built by [Ability.ai](https://ability.ai) — the agent orchestration platform. Agents created by this wizard are specializations of [Cornelius](https://github.com/Abilityai/cornelius), the reference insight-harvester KB agent, and are compatible with [Trinity](https://ability.ai) for remote deployment, scheduling, and multi-agent coordination.
