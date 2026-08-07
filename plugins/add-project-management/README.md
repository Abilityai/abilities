# add-project-management

Install a battle-tested cross-actor project management standard into any Claude Code agent. GitHub Issues become the single source of truth for all project and task state; humans and agents interact with it through a shared vocabulary of labels, task anatomy, and an approval-ready completion lattice.

## Install

```bash
/plugin marketplace add abilityai/abilities   # add the marketplace (one-time)
/plugin install add-project-management@abilityai
```

Then run the installer:

```
/add-project-management
```

The installer asks four questions and wires up everything else.

## What gets installed

| Artifact | Purpose |
|---|---|
| `PROJECT_STANDARD.md` | Convention doc — the deployer's config surface. Skills read this at runtime; edit it to change behavior without touching skills. |
| `/project-init` | Create or adopt a project: GitHub epic issue + idempotent label creation + workspace stub |
| `/project-task` | Create task issues interactively. **The sanctioned interactive task-creation path** — enforces full anatomy including the Validation section. Supports `--headless` for cron/compose use. |
| `/project-intake` | **New in v1.1.** Headless intake primitive: route actionable items from any source (meetings, email, Slack, issue trackers) into the registry. Dedupes by meaning, creates task issues or posts state-news comments, returns the issue number. Called by domain skills and crons — never interactive. |
| `/project-steward` | Autonomous sweep: verify pending-verification claims, dispatch to owner agents, escalate stalls, age your open loops with drafted (never sent) follow-ups, classify quarantine, write a digest that opens by closing the loop with you |
| `/project-reconcile` | Projection sync: push registry state into personal task views; process gestures (check/date-push/delete) back per the typed-reversibility contract. Includes Google Tasks adapter v1. |

## Design

**One registry, write-authoritative.** GitHub Issues is the sole record of portfolio state. No other system (personal task views, external tools) writes state back. Projections are read-only views.

**Intake contract.** Work items enter the registry only through `/project-intake`. Projection surfaces are written only by `/project-reconcile`. Domain skills write workspace files freely. The roles are explicit and exclusive — no accidental cross-writes.

**Approval-ready completion lattice from day one.** Every task moves: `open → pending-verification → done`. Human completion writes done directly. Agent completion triggers verification against the Definition of Done before closing. The `## Validation` section in every task body is the approval chain — enabling multi-step chains later = adding more rows, not a schema change.

**Priority is human-only.** Priority changes only by explicit human speech act, logged with a reason. Observed behavior (staleness, projection gestures) surfaces as evidence for the human to act on — never a silent write.

**Owner ≠ executor.** `owner:<actor>` is the accountable party (can be a human or agent); `agent:<name>` is who is executing right now. This distinction enables proper escalation and approval routing.

**No loop closes by silence.** Tracked work still dies of silence, so the standard closes loops in both directions. *Toward you:* every run ends by saying what is now true, what is waiting on you, and what happens next without you; work you asked for is reported back to you personally, not just filed on an issue; a question you never answered gets louder with age instead of expiring. *Toward everyone else:* work parked on a client, vendor, colleague, or another fleet's agent is labeled `waiting-on:<actor>`, aged in every digest under **Your open loops**, and comes with a follow-up message drafted at 3 days (then weekly) that you can send as-is — at 14 days it forces a call: chase, drop, or route around. The agent drafts; **you send**. It never contacts a third party on your behalf.

**Workspace visibility is deployment config.** `project_files/<slug>/` may be local-only or git-synced to the agent's container — either way the standard works. The quarantine pass is idempotent wherever workspaces are visible.

**Altitude above single-agent dev loops.** This plugin governs cross-actor work (humans + multiple agents collaborating on projects). For a single agent's own task backlog, see `agent-dev`'s `/add-backlog`.

## Label taxonomy

| Label | Meaning |
|---|---|
| `project` | Epic issue (one per project) |
| `task` | Task issue belonging to a project |
| `project:<slug>` | Project membership |
| `owner:<actor>` | Accountable party (human or agent name) |
| `agent:<name>` | Currently executing agent |
| `waiting-on:<actor>` | Open loop — someone outside the registry owes a response; only you can close it |
| `status:active` | Being worked |
| `status:blocked` | External dependency blocking progress |
| `status:needs-decision` | Blocked on a named owner's decision |
| `status:paused` | Deliberately on hold |
| `status:pending-verification` | Agent claimed done; awaiting DoD verification |
| `status:unclassified` | Auto-stubbed workspace folder not yet classified |
| `priority:p1` | High |
| `priority:p2` | Normal |
| `priority:p3` | Low |

## Google Tasks adapter

The `/project-reconcile` skill ships with a Google Tasks adapter v1. To use it:

1. Set `GOOGLE_TASKS_TOKEN` in your agent's `.env` (a valid OAuth2 access token with `tasks` scope).
2. Set `GOOGLE_TASKS_LIST_ID` or let the reconciler prompt you to select one.
3. Add `[#NN]` to each Google Task's title to key it to the GitHub issue number. Items without a key are treated as personal reminders and skipped (no alerts).

Gesture semantics:
- **Check/complete** → completion endorsement (closes done or sets pending-verification)
- **Date-push** → defer signal (no registry write; logged as evidence)
- **Delete** → soft-skip proposal (registry item survives; confirmed at next review)

## Adapter contract

Other projection adapters (Fibery, Notion, etc.) are per-deployment extensions. See `PROJECT_STANDARD.md §11` for the adapter contract every extension must implement.
