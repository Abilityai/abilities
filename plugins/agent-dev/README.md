# agent-dev

Develop and extend existing Claude Code agents with skills, memory systems, a full GitHub Issues development workflow, and planning tools.

## Installation

```
/plugin install agent-dev@abilityai
```

## Usage

### Adding Capabilities

```
/agent-dev:create-playbook    # Create a new skill/playbook for the agent
/agent-dev:adjust-playbook    # Modify an existing skill/playbook
/agent-dev:add-memory         # Add a memory system (file-index, brain, json-state, workspace)
/agent-dev:add-backlog        # Install the full GitHub Issues development workflow
/agent-dev:add-git-sync       # Install auto-commit hooks for durable state
/agent-dev:add-orchestrator   # Make the agent a system-aware orchestrator of other agents
/agent-dev:add-pipeline       # Add a long-running multi-stage pipeline (+ instance/stage/validate helpers)
```

### Development Workflow

Once backlog is installed, the full cycle looks like:

```
/agent-dev:groom              # Tag issues with skill:* labels, set priorities
/agent-dev:roadmap            # View issues grouped by affected skill
/agent-dev:claim              # Claim the next issue, mark in-progress
/agent-dev:autoplan           # Analyze the issue against the current SKILL.md
# → /agent-dev:adjust-playbook or /agent-dev:create-playbook
/agent-dev:commit             # Stage skill files, write commit, close issue
```

Or run the full guided cycle in one command:

```
/agent-dev:sprint             # roadmap → claim → autoplan → implement → commit
```

For autonomous processing of project-level issues:

```
/agent-dev:work-loop          # Autonomous loop — skill issues are deferred to /sprint
```

### Planning

```
/agent-dev:plan               # Plan multi-session work
/agent-dev:backlog            # Priority-ordered view of open issues
```

## Skills

### Capability Building

| Skill | Description |
|-------|-------------|
| **create-playbook** | Scaffold a new skill/playbook (guided wizard) |
| **adjust-playbook** | Modify an existing skill — steps, logic, triggers, interface |
| **add-memory** | Copy a memory system into the agent |
| **add-backlog** | Install the full GitHub Issues development workflow |
| **add-git-sync** | Install auto-commit hooks for durable cross-session state |
| **add-orchestrator** | Make the agent a system-aware orchestrator — installs `/discover-agents` (scan a repo list for Trinity specs into `fleet/system-map.yaml`), `/compose-system` (map → Trinity `SystemManifest` → `deploy_system`), and `/orchestrate` (route / fan out / run ephemeral agents). Aligns with Trinity's `SystemManifest`; orchestration stays agent-owned. |
| **add-pipeline** | Install a long-running, multi-stage pipeline (heartbeat + status/recover/pause/resume runtime skills). Extend with `add-pipeline-instance` and `add-pipeline-stage`; lint with `validate-pipeline` |

### Development Workflow

Installed into the agent by `/add-backlog`. The units of work are skills; issues track what needs changing and why.

| Skill | Description |
|-------|-------------|
| **backlog** | Priority-ordered view of open issues |
| **roadmap** | Issues grouped by `skill:*` label — shows which skills have the most open work |
| **groom** | Tag untagged issues with `skill:*` labels, set missing priorities, flag stale in-progress |
| **claim** | Claim the next issue — surfaces the affected skill file to open |
| **autoplan** | Read the affected SKILL.md and produce a targeted change plan before touching files |
| **close** | Close an issue without a git commit (for project-level tasks) |
| **commit** | Stage changed skill files, write `[skill-name]: ... (closes #N)` commit, close issue |
| **sprint** | Human-supervised full cycle: roadmap → claim → autoplan → implement → commit |
| **work-loop** | Autonomous loop — processes project-level issues, defers `skill:*` issues to sprint |

**Label scheme:**
- `status:todo` / `status:in-progress` / `status:blocked` / `status:done`
- `priority:p0` (do now) / `priority:p1` (do soon) / `priority:p2` (do eventually)
- `skill:<name>` — which skill this issue affects (created dynamically by `/groom`)

### Planning

| Skill | Description |
|-------|-------------|
| **plan** | Plan large multi-session projects with scope analysis and approval gates |

### Memory Systems

The `/add-memory` skill copies memory skills directly into the agent (no plugin dependency). Choose from:

| Type | Use Case | Skills Installed |
|------|----------|------------------|
| **file-index** | Agent needs awareness of workspace files | setup-index, refresh-index, search-files |
| **brain** | Connected notes, knowledge graph | setup-brain, create-note, search-brain, find-connections |
| **json-state** | Structured state, counters, config | setup-memory, load-memory, update-memory, memory-jq |
| **workspace** | Multi-session project tracking | setup-projects, create-project, create-session, archive-project |

### System Orchestration

`/add-orchestrator` makes an agent **system-aware** — able to discover other agents (deployed *or* just sitting in a GitHub repo), describe what each can do, and put them to work. It installs six fleet skills (plus an opt-in project-management pair) into the agent and a `fleet/` workspace:

| Skill Installed | Purpose |
|------|----------|
| **discover-agents** | Scan a repo list (local paths + `github:Org/repo`) for Trinity specs (`template.yaml`/`system.yaml`) into a descriptive `fleet/system-map.yaml`; refresh the roster/topology blocks in `fleet/orchestration.md` |
| **compose-system** | Turn the map into a Trinity `SystemManifest` (`fleet/system.yaml`) and `deploy_system` |
| **orchestrate** | Route a task to the best-fit agent, fan out across many, or roll a catalog agent out ephemerally (deploy → chat → tear down) |
| **sync-fleet-to-head** | Non-destructively bring in-scope agents to their GitHub HEAD (pull-only ladder, conflict gates) — fleet git hygiene |
| **profile-fleet** | Interview + introspect the agents, reconcile reality vs declared config, and correct the `orchestration.md` narrative behind a gate |
| **fleet-reconcile** | Fold already-verified deltas (session fixes, audit corrections) into every doc surface behind one gate — no new evidence |
| **project-init** *(opt-in)* | Create/adopt a managed project (GitHub epic + workspace) per `fleet/project-standard.md` |
| **project-steward** *(opt-in)* | Autonomous scheduled project driver — sweep, dispatch to labeled owners, escalate, digest |

**Two modes, not one pipeline:** to *describe and route over a fleet that already exists on Trinity*, run `/discover-agents` then `/orchestrate` — the map is the read surface, **skip `/compose-system`**. To *provision a new system* from catalog repos, go `/discover-agents` → `/compose-system` → `deploy_system` → `/orchestrate`.

The multi-agent *definition* aligns with Trinity's `SystemManifest` — no parallel format. Orchestration stays **agent-owned**: Trinity brokers the calls and the lifecycle but runs no central DAG engine. Agents self-describe via an optional `x-capabilities:` block in `template.yaml` — an extension key that coexists with Trinity's native flat `capabilities:` keyword list; the scanner reads both and degrades to `description` + `tags` when neither is present. Deployed agents are matched **repo-first** and called by their live `deployed_name` (which may differ from the template name). A fourth artifact — **`fleet/orchestration.md`** — holds the design *narrative* (who-calls-whom edges, permission intent, collaboration patterns) as human prose plus tool-refreshed roster/topology blocks; it's imported into the agent's `CLAUDE.md` (`@fleet/orchestration.md`) so it loads at session start, and `/compose-system` derives `agent_permissions` from its Permissions section — closing the loop from narrative intent to enforced permissions. It also carries an **ownership matrix** (§3b, RACI-lite): one fleet-wide informational table (domain → responsible / consulted / informed) that `/orchestrate`, `/project-init`, and `/project-steward` read as routing and consult/notify defaults — etiquette the orchestrator follows, never gates.

## Composing skills (hierarchical playbooks)

**Compose, don't copy.** When a skill needs work another skill already does, it *invokes that skill by name* — it never inlines the other skill's steps, calls its internal `scripts/`/`reference.md`/templates directly, or paraphrases what it does. The child is the single source of truth for its own behavior; the parent owns only the *orchestration* (which children, in what order, with what inputs). A fix to the child then propagates to every parent automatically, with no edits to the parents. This is what `/sprint` does — it invokes `/claim`, `/autoplan`, `/commit` rather than reimplementing them.

**How:** add `Skill` to the parent's `allowed-tools`; in the body write ``Invoke `/child-skill` `` (leading slash = the entry point). Cross-plugin, namespace it: ``Invoke `/create-agent:custom` ``. Pass inputs the way a user would: ``Invoke `/child-skill <args>` ``.

**Latest vs. pinned.** Call the **unversioned** name (`/child`) to ride the latest version — this is the default and what gives automatic propagation. Pin `/child-vN` *only* when a parent must be insulated from a child's breaking changes.

**Never reach inside a child.** Go through the skill entry point so the child's own setup and guardrails run. Reaching past it (calling its scripts/files directly) reintroduces the drift you were avoiding.

**Composition is a DAG.** No cycles (A→B→A), keep it shallow — the harness won't re-enter a skill that's already running, and every nested skill spends the same context window / 45-minute budget.

**Autonomy is transitive.** An autonomous parent may only compose children that are themselves gate-free. The No-Gates, 45-Minute, and Single-Task rules apply to the *union* of parent + all invoked children, because they all run in one context window — validate the whole tree, not just the parent.

**Compose ≠ install (the two non-violations).** The rule governs *runtime* reuse, and two look-alike patterns are explicitly fine, not copies to refactor: **(1) Install/scaffold** — an `add-*` skill that `cp`s skill files into a *target* agent (`add-pipeline`, `add-memory`, `add-backlog`…) is installing deliverables that must physically live and run in that agent (often a remote with no access to the installer); copying is correct there. **(2) Example ≠ invocation** — an `` Invoke `/x` `` inside a code fence, in a skill whose job is to *generate* skill text (`create-playbook`, `adjust-playbook`), is documentation, not a call, and needs no `Skill` tool. A real violation is a skill that *executes* `` Invoke `/x` `` — only those must carry `Skill` in `allowed-tools`.

## How It Works

**Skill development is the unit of work.** When you create an issue like "improve claim flow to show skill file path", `/groom` tags it `skill:claim`. `/roadmap` surfaces it alongside all other `skill:claim` work. `/autoplan` reads `.claude/skills/claim/SKILL.md`, identifies what changes, and flags risks. `/commit` writes `[claim]: show skill file path on claim (closes #N)`.

`/work-loop` is the autonomous sprint — but it skips `skill:*` issues since modifying SKILL.md files requires the interactive wizard tools. Those stay in `/sprint`.

**Trinity scheduling, in one line:** a schedule should call a single playbook and nothing else — business logic belongs in the playbook, so the cron prompt stays a bare skill invocation and behavior changes are edits to the playbook, never the schedule.

## Source

This plugin consolidates:
- playbook-builder (create-playbook, adjust-playbook)
- file-indexing, brain-memory, json-memory, workspace-kit (memory templates)
- github-backlog (backlog workflow)
- project-planner (plan)
