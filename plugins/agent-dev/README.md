# agent-dev

Develop and extend existing Claude Code agents with skills, memory systems, a full GitHub Issues development workflow, planning tools, and fleet-level analysis.

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
/agent-dev:add-canon          # Join the fleet's shared canonical-data repo (publish/consume/reconcile/doctor)
/agent-dev:add-canon-lint     # Install deterministic linting into the canon repo (two-zone schema, CI on every push)
/agent-dev:add-pipeline       # Add a long-running multi-stage pipeline (+ instance/stage/validate helpers)
/agent-dev:add-project-management  # Install the cross-actor project-management standard (GitHub Issues as the registry)
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

### Fleet Analysis & Migration

```
/agent-dev:agent-fleet-analysis [path ...]   # Scan directories of agents (any paradigm), score them, get an architecture + roadmap report
/agent-dev:agent-fleet-migrate [report|path] # Execute that report as a work order — non-destructive migration into verified Claude Code copies
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
| **add-canon** | Give the agent a shared canonical-data layer — a fleet **canon repo** (`agents/<name>/` owned folders in the two-zone schema + `protocols/`) with `/canon-publish`, `/canon-consume`, `/canon-reconcile`, `/canon-doctor` runtime skills. Own-folder-only writes, cross-folder via PR |
| **add-canon-lint** | Install deterministic consistency linting into the canon repo — stdlib-Python linter + CI on every push (schema, key grammar, one-home-per-key, ownership, staleness, reachability), `lint/rules.yaml` severities, optional required PR check. Run once per fleet |
| **add-pipeline** | Install a long-running, multi-stage pipeline (heartbeat + status/recover/pause/resume runtime skills). Extend with `add-pipeline-instance` and `add-pipeline-stage`; lint with `validate-pipeline` |
| **add-project-management** | Install the cross-actor project-management standard — GitHub Issues as the single write-authoritative registry, uniform task anatomy, the `open → pending-verification → done` completion lattice, loop closure in both directions, and projection sync (Google Tasks adapter v1). Writes `PROJECT_STANDARD.md` + five runtime skills (`/project-init`, `/project-task`, `/project-intake`, `/project-steward`, `/project-reconcile`). **Altitude:** governs humans + multiple agents on shared projects; for one agent's own dev-loop backlog use `add-backlog`. Moved here from its own plugin in 1.12.0 |
| **agent-fleet-analysis** | Scan one or more directories of agents in **any paradigm** — Claude Code, n8n exports, framework apps (LangChain/CrewAI/AutoGen), freeform-coded LLM loops — score each (Fleet Maturity for Claude Code, Migration Readiness for the rest), recommend a fleet architecture (hub, knowledge brain, memory, canon layer) with every gap mapped to an installable marketplace skill, and emit an A4 PDF report + an agent-executable markdown work order |
| **agent-fleet-migrate** | Execute the fleet-analysis work order — the *execute* half of the pair. Non-destructive: each agent is copied (or scaffolded, for non-Claude-Code paradigms) into `fleet-migrated/`, its logic extracted per paradigm (n8n node graphs, framework code, freeform prompts), every fix delegated to a named marketplace skill, every copy verified through `/create-agent:review`, ending with a before/after maturity report, capability coverage matrix, and a **gated** Trinity deploy offer. Sources are never mutated |

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
| **project-steward** *(opt-in)* | Autonomous scheduled project driver — sweep, dispatch to labeled owners, escalate, age the operator's open loops, digest |

**Nothing ends in silence (standard §12).** The bundle treats an unclosed loop as a defect in both directions. Inbound: `/orchestrate` isn't finished until the person who asked has actually been told the outcome — successes *and* failures — and every report ends with *your open loops / waiting on you / next without you*; the steward's digest opens the same way. Outbound: work parked on somebody the fleet can't dispatch to (a client, a vendor, a colleague, an agent in another fleet) is labeled `waiting-on:<actor>`, aged in every digest, and handed over with a follow-up drafted at 3 days and weekly after — **the agent drafts it, the human sends it.** Nothing in the bundle contacts a third party on the operator's behalf.

**Two modes, not one pipeline:** to *describe and route over a fleet that already exists on Trinity*, run `/discover-agents` then `/orchestrate` — the map is the read surface, **skip `/compose-system`**. To *provision a new system* from catalog repos, go `/discover-agents` → `/compose-system` → `deploy_system` → `/orchestrate`.

The multi-agent *definition* aligns with Trinity's `SystemManifest` — no parallel format. Orchestration stays **agent-owned**: Trinity brokers the calls and the lifecycle but runs no central DAG engine. Agents self-describe via an optional `x-capabilities:` block in `template.yaml` — an extension key that coexists with Trinity's native flat `capabilities:` keyword list; the scanner reads both and degrades to `description` + `tags` when neither is present. Deployed agents are matched **repo-first** and called by their live `deployed_name` (which may differ from the template name). A fourth artifact — **`fleet/orchestration.md`** — holds the design *narrative* (who-calls-whom edges, permission intent, collaboration patterns) as human prose plus tool-refreshed roster/topology blocks; it's imported into the agent's `CLAUDE.md` (`@fleet/orchestration.md`) so it loads at session start, and `/compose-system` derives `agent_permissions` from its Permissions section — closing the loop from narrative intent to enforced permissions. It also carries an **ownership matrix** (§3b, RACI-lite): one fleet-wide informational table (domain → responsible / consulted / informed) that `/orchestrate`, `/project-init`, and `/project-steward` read as routing and consult/notify defaults — etiquette the orchestrator follows, never gates.

### Canonical Data Layer

`/add-canon` gives an agent a **published data layer**: a separately-versioned git repo — the fleet's **canon** — where each agent owns `agents/<name>/` (the canonical business facts humans and other agents rely on) and `protocols/` holds inter-agent contracts. Humans and agents co-edit under one rule: **own-folder-only direct writes; everything else via branch + PR** (CODEOWNERS routes review). Every folder follows the **two-zone schema**: `facts.yaml` — the purely lintable zone, structured claims (`key` = lowercase dotted `subject.relation` with **one home per key fleet-wide**, plus `value`/`status`/`updated`/`review_by`/`source`) — beside free prose in `docs/` under a linted front-matter envelope, indexed from `profile.md`. Statuses (`canonical`/`draft`/`superseded`) separate conviction levels so ideas can't dress as canon. Each agent carries the duty to keep its folder true — `/canon-reconcile` runs on a schedule, verifies facts against their declared sources, re-stamps `review_by:`, and flags what it can't verify instead of guessing.

| Skill Installed | Purpose |
|------|----------|
| **canon-publish** | Review + commit changes to the agent's own canon folder — lints before pushing; cross-folder changes go out as a branch + PR |
| **canon-consume** | Read another agent's published data or a protocol — facts.yaml first, fresh, cited at `canon@<sha>`, staleness flagged |
| **canon-reconcile** | Scheduled external-truth pass — lint first, verify facts and docs against their sources, re-stamp, push |
| **canon-doctor** | Verify the layer end-to-end (credentials, clone, push probe, lint) — PASS/WARN/FAIL with the exact fix; dispatchable fleet-wide |

**`/add-canon-lint`** (run once per fleet, against the canon repo itself) installs the layer's *law*: a deterministic linter — stdlib Python, no LLM — plus a GitHub Actions workflow that checks every push and PR for schema validity, key grammar, cross-folder key conflicts, ownership violations, staleness, dead sources, and unreachable docs; severities live in `lint/rules.yaml` (strict or report-only migration preset), with an optional required status check on PRs. **Division of labor:** the linter on every push = internal consistency; each agent's scheduled `/canon-reconcile` = external truth — the LLM residual the linter deliberately leaves out.

The layer is **convention + skills on plain git** — no platform primitive. It's declared via `x-canon:` in `template.yaml` (the same `x-` extension pattern as `x-capabilities:`), which is how the orchestration layer sees it: `/discover-agents` scans it into a `canon:` field per map node (and reports **canon coverage** — N/M mapped agents enrolled), and `/orchestrate` serves reads of published facts from the canon repo instead of spending a chat turn — writes still route to the owning agent.

**Fleet enrollment:** on an orchestrator (`fleet/system-map.yaml` present), `/add-canon` doesn't stop at the agent it runs in — it offers to enroll **all mapped agents or a subset** into the same canon: each target repo gets the runtime skills, its `x-canon:` declaration, the CLAUDE.md section, and the reconcile schedule (local repos → direct commit; repo-only → branch + PR, or authorized direct push), and each `agents/<name>/` folder is seeded in the canon (the one sanctioned cross-folder write — enrollment seeding). Targets need no clone up front: their canon skills self-heal it on first use. Idempotent — already-enrolled agents are counted and untouched, so re-running aligns only the remainder.

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

**Long-running tasks, in one line:** a **headless/scheduled run is one agent turn** and cannot host a job past the **~10-min synchronous Bash ceiling** — past it the harness auto-backgrounds the job and the turn ending reaps it (fires `killed`, not `completed`; streaming output changes nothing — the separate no-output watchdog watches `mcp__*` tools only, 1800s default — and the monitor/re-invoke model is interactive-only). So anything longer (index rebuild, bulk embedding, big migration) runs as an **OS-level cron/systemd/sidecar** writing a done-marker, and the run only triggers it and **verifies the artifact moved** (mtime + count, never an exit code / `business_status`). `/create-playbook` carries the rule as a Design Constraint; `/add-pipeline` keeps heavy compute out of the heartbeat turn.

## Source

This plugin consolidates:
- playbook-builder (create-playbook, adjust-playbook)
- file-indexing, brain-memory, json-memory, workspace-kit (memory templates)
- github-backlog (backlog workflow)
- project-planner (plan)
