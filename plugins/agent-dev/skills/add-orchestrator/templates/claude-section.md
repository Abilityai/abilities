## Orchestration

This agent is a **system-aware orchestrator**. It maintains a picture of the other agents in its world — deployed on Trinity *or* living only as GitHub repos — and can route work to them, batch across them, or roll one out ephemerally, use it, and spin it down.

**Artifacts (under `fleet/`):**

| File | Role | Written by |
|---|---|---|
| `fleet/sources.yaml` | the repo list you curate (local paths + `github:Org/repo`) — optional when discovering from live Trinity | you |
| `fleet/system-map.yaml` | descriptive FACTS — who exists, what they do, where/when they run (nodes) | `/discover-agents` |
| `fleet/orchestration.md` | design NARRATIVE — edges, permission intent, patterns; loaded at session start | you + tools |
| `fleet/system.yaml` | prescriptive Trinity `SystemManifest` — deploy-ready | `/compose-system` |

`system-map.yaml` is the *nodes*; `orchestration.md` is the *edges and the intent* — the design narrative the orchestrator reads before routing.

**Two modes** (don't assume a linear pipeline):
- **Describe & route over an existing fleet** (read-only — the common case): `/discover-agents` → `/orchestrate <task>`. The `system-map.yaml` *is* the read surface; **skip `/compose-system`**.
- **Provision a new system** (create agents that are only catalog repos today): `/discover-agents` → `/compose-system` (map → Trinity `SystemManifest` → `deploy_system`) → `/orchestrate`.

Deployed agents are called by their live `deployed_name` from the map (matched repo-first, so a name that differs from the template name resolves correctly). Agents self-describe via an optional `x-capabilities:` block in `template.yaml` (coexists with Trinity's native flat `capabilities:` list).

**Invariant — orchestration is agent-owned.** Trinity provides the substrate (agent-to-agent messaging, shared folders, permissions, cron) but runs no central DAG engine. The roll-out → work → tear-down lifecycle lives inside `/orchestrate`, stitched from Trinity MCP calls (`deploy_system`/`deploy_local_agent` → `chat_with_agent` → `stop_agent`/`delete_agent`). The multi-agent *definition* is Trinity's `SystemManifest` — this agent does not invent a parallel format.

**Skills:**

| Skill | Purpose |
|---|---|
| `/discover-agents` | Discover the fleet — from live Trinity (`list_agents`; the default when connected), the `fleet/sources.yaml` repo scan, or both — cross-reference repo-first, write `fleet/system-map.yaml` |
| `/compose-system` | Map the registry onto a Trinity `SystemManifest`, validate (dry-run), and `deploy_system` |
| `/orchestrate` | Read the map + orchestration.md + live Trinity MCP to route a task to the best-fit agent, `fan_out` across many, or run an ephemeral agent |
| `/sync-fleet-to-head` | Non-destructively bring in-scope agents to their GitHub HEAD (pull-only ladder, conflict gates) — fleet git hygiene |
| `/profile-fleet` | Interview + introspect agents, reconcile reality vs the narrative, and correct this file's prose behind a gate |
| `/fleet-reconcile` | Fold already-verified deltas (session fixes, audit queues) into the doc surfaces — narrative, dossiers, CLAUDE.md, memory — behind one gate; generates no new evidence |
| `/project-init` (opt-in layer) | Create or adopt a managed project — epic issue + workspace — per `fleet/project-standard.md` |
| `/project-steward` (opt-in layer) | Autonomous sweep of managed projects: reconcile dispatches, dispatch next work to explicitly-labeled owners, escalate stalls, daily digest — never asks mid-run |

**Loaded at session start (design narrative):**
@fleet/orchestration.md
