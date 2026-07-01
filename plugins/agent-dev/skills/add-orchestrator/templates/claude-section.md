## Orchestration

This agent is a **system-aware orchestrator**. It maintains a picture of the other agents in its world — deployed on Trinity *or* living only as GitHub repos — and can route work to them, batch across them, or roll one out ephemerally, use it, and spin it down.

**Artifacts (under `fleet/`):**

| File | Role | Written by |
|---|---|---|
| `fleet/sources.yaml` | the repo list you curate (local paths + `github:Org/repo`) | you |
| `fleet/system-map.yaml` | descriptive registry — who exists, what they do, where/when they run | `/discover-agents` |
| `fleet/system.yaml` | prescriptive Trinity `SystemManifest` — deploy-ready | `/compose-system` |

**Two modes** (don't assume a linear pipeline):
- **Describe & route over an existing fleet** (read-only — the common case): `/discover-agents` → `/orchestrate <task>`. The `system-map.yaml` *is* the read surface; **skip `/compose-system`**.
- **Provision a new system** (create agents that are only catalog repos today): `/discover-agents` → `/compose-system` (map → Trinity `SystemManifest` → `deploy_system`) → `/orchestrate`.

Deployed agents are called by their live `deployed_name` from the map (matched repo-first, so a name that differs from the template name resolves correctly). Agents self-describe via an optional `x-capabilities:` block in `template.yaml` (coexists with Trinity's native flat `capabilities:` list).

**Invariant — orchestration is agent-owned.** Trinity provides the substrate (agent-to-agent messaging, shared folders, permissions, cron) but runs no central DAG engine. The roll-out → work → tear-down lifecycle lives inside `/orchestrate`, stitched from Trinity MCP calls (`deploy_system`/`deploy_local_agent` → `chat_with_agent` → `stop_agent`/`delete_agent`). The multi-agent *definition* is Trinity's `SystemManifest` — this agent does not invent a parallel format.

**Skills:**

| Skill | Purpose |
|---|---|
| `/discover-agents` | Scan `fleet/sources.yaml` for `template.yaml`/`system.yaml`, cross-reference live Trinity agents, write `fleet/system-map.yaml` |
| `/compose-system` | Map the registry onto a Trinity `SystemManifest`, validate (dry-run), and `deploy_system` |
| `/orchestrate` | Read the map + live Trinity MCP to route a task to the best-fit agent, `fan_out` across many, or run an ephemeral agent |
