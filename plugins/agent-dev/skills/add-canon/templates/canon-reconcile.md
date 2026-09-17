---
name: canon-reconcile
description: "Scheduled freshness pass over this agent's own folder in the shared canon repo — run the deterministic linter first (its staleness findings are the worklist), verify each facts.yaml entry and doc against its declared source, update what changed, push review_by: forward on what verified, and flag what could not be verified in NEEDS-REVIEW.md. Shared-project charters (projects/<slug>/project.md) verify against their registry epic; decision ledgers are append-only and never re-stamped. The external-truth half of the division of labor: the linter proves internal consistency, this pass proves the facts still match reality. Headless-safe — never asks mid-run, never touches other folders."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__trinity__report
user-invocable: true
metadata:
  version: "1.4"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.4: Shared projects (ruling R21, CONVENTIONS.md § Projects) — projects/<slug>/project.md is treated like a doc for staleness: the linter's project-envelope + staleness findings feed the worklist, and a charter on it is verified against its registry epic (`epic:` in the envelope — open/closed and the status:* label, via gh when available): epic agrees → re-stamp review_by; epic moved (closed, or a different status:* label) → `changed` (mirror the status, updated: today, review_by forward); epic unreachable → NEEDS-REVIEW row; paused/done charters are never on the worklist. decisions.md is append-only and is NEVER re-stamped by this pass — a ledger envelope failure is a NEEDS-REVIEW row, not a repair; the workspace files beside the charter are never read"
    - "1.3: Relation docs (docs/relations/*.md, CONVENTIONS.md § Relations) reconcile mechanically — they are self-sourced (the owner's log IS the record; no external source to re-verify): enforce the 10-event cap (fold overflow into Earlier:), flag any Open-threads item older than 30 days as a NEEDS-REVIEW row — the dropped-thread alarm the convention exists for — and treat a rel doc past review_by: with no new events as dormant, not wrong (push review_by: forward, content untouched); report gains a relations line when threads have aged"
    - "1.2: Two-zone schema + linter-first — new Step 1b runs the canon repo's deterministic linter scoped to this folder (tools/canon-lint, seeded by /add-canon-lint): its staleness findings become the verification worklist (never re-derive what it already proved) and its other FAILs are repaired mechanically where safe (envelope stamps, ownership) or flagged; Step 2 walks facts.yaml entries as the primary verification units (each entry's source) plus canonical docs, with three outcomes per item — verified (push review_by +30d), changed (update value/content + updated: today + review_by forward), unverifiable (NEEDS-REVIEW.md row); drafts and superseded items are skipped by design; v1-contract folders (verified: stamps, no facts.yaml) still reconcile the old way with a migration note in the report"
    - "1.1: Deploy-ready auth — self-heal clone inherits /canon-publish v1.1's auth-aware resolution (gh → GH_TOKEN/GITHUB_TOKEN credential helper → plain https); git-identity fallback before commit; auth-failure reports name the headless fix (GH_TOKEN via .env + inject_credentials) and /canon-doctor — never an interactive gh auth login a scheduled run can't execute"
    - "1.0: Initial version — walks the own folder, verifies each file against its source: front-matter (workspace path, API, doc), three outcomes (verified → bump verified:, changed → edit + bump both stamps, unverifiable → NEEDS-REVIEW.md row, never a guess), own-folder-only commit + push, guarded Trinity report; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-reconcile vX.Y — recent: <summary>`. Then proceed.

The duty that makes the canon trustworthy: **is my published folder still true?** This runs on a schedule (or manually), verifies every fact in `agents/<name>/` against its declared source, and repairs or flags — it never guesses and never asks. Scope is hard: this skill reads and writes **only this agent's own folder**. It is autonomous-safe: no `AskUserQuestion`, no gates, single task, well under the 45-minute budget.

## Process

### Step 1: Load config + freshen

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` default `canon/`, `folder`). No `x-canon:` block → stop with a one-line note (headless runs must fail loudly-but-cleanly, not hang). Clone missing at `clone_path` (fresh deploy — the path is gitignored) → **self-heal**: re-clone from `x-canon.repo` quietly, using the same auth-aware resolution as `/canon-publish` Step 1 (gh when logged in → `GH_TOKEN`/`GITHUB_TOKEN` credential helper → plain https), and note it in the report; only a failed clone stops the run — and an auth failure must name the headless fix (`GH_TOKEN` into `.env` via `inject_credentials`; diagnose with `/canon-doctor`), never `gh auth login`, which a scheduled run cannot execute. Then `git -C canon pull --ff-only`; on divergence, **report and stop** — a reconcile must start from the shared truth, and force-anything is forbidden.

### Step 1b: Lint first — the worklist is deterministic

```bash
[ -f canon/tools/canon-lint/canon_lint.py ] && \
  python3 canon/tools/canon-lint/canon_lint.py --repo canon --scope "agents/<name>" --format json || true
```

The linter (seeded by `/add-canon-lint`) already computed what's past due — **never re-derive it**:

- `staleness` findings → the verification worklist for Step 2 (anything not flagged is not due; verify it anyway only if its `source` is trivially cheap to check).
- Mechanically-safe FAILs → repair in place: missing envelope keys (stamp them), `owner:` mismatch in own files (set to folder name), unquoted `": "` values (quote them). **Exception:** a `project-envelope` finding on `projects/<slug>/decisions.md` is never repaired here — the ledger is append-only (Step 2, Shared projects); flag it instead.
- Judgment FAILs (`one-home-per-key` conflicts, `reachability` decisions) → NEEDS-REVIEW.md rows; a headless run never resolves a dispute.
- Linter absent → treat every canonical item as the worklist (pre-lint behavior) and note `/add-canon-lint` in the report.

### Step 2: Verify the worklist against reality (two-zone contract)

**Primary units — `facts.yaml` entries** (skip `status: draft | superseded`): resolve each entry's `source:` —
   - a local `docs/`/`files/` path → re-read it, confirm the `value` still matches what the doc establishes
   - a workspace path (this agent's own repo) → re-read it and compare
   - an API/tool this agent owns → re-query, compare
   - a URL → re-fetch if cheap, else treat as manual
   - `manual` / absent → nothing to verify against mechanically

**Then canonical docs** (`profile.md`, `docs/*.md` with `status: canonical`) on the worklist: same source logic; also confirm the prose still agrees with the facts that cite it — a doc contradicting its own mirrored fact entry is a `changed` outcome, not a pass.

Three outcomes, exactly one per item:
   - **Verified unchanged** → push `review_by:` to today + 30 days. Content untouched.
   - **Changed** → edit the `value`/content to match reality, set `updated:` today **and** push `review_by:` forward.
   - **Unverifiable** (source unreachable, `manual`, ambiguous) → leave stamps alone; upsert one row into `agents/<name>/NEEDS-REVIEW.md` (`| item (fact key or file) | why unverifiable | since |` — dedup on item, keep the earliest `since`). A verified-later item gets its row removed.

**Relation docs** (`docs/relations/*.md` — CONVENTIONS.md § Relations) are **self-sourced**: the owner's log *is* the record, so there is no external source to re-verify. Reconcile them mechanically instead:
   - **Cap** — more than 10 events → fold the oldest into the `Earlier:` rolling summary.
   - **Open-thread aging** — any Open-threads item older than 30 days is the dropped-thread alarm this convention exists for: upsert a NEEDS-REVIEW.md row (`relation <counterpart>: thread open since <date> — <one-line ask>`) and count it as flagged. Never resolve or delete the thread itself — whether it's truly dead is the owner's call, made in conversation, not on a schedule.
   - **Dormancy** — a rel doc past `review_by:` with no new events is *dormant, not wrong*: push `review_by:` forward and leave content untouched; the event dates already say how current the relationship is.

**Shared projects** (`projects/<slug>/` — CONVENTIONS.md § Projects, ruling R21: managed exactly like an agent-level project; canon placement only decides who can read it). Two files, two rules:
   - **`project.md` — the charter — is a doc for staleness purposes.** It mirrors the registry epic named in its `epic:` (`owner/repo#N`), so the epic is its source. A charter on the worklist (linter `staleness` on it; `paused` / `done` charters are never on it): `gh issue view <N> --repo <owner/repo> --json state,labels` when `gh` is available — epic open and its `status:*` label equals the charter's `status:` → **verified** (push `review_by:` +30d); epic closed, or a different `status:*` label → **changed** (mirror the epic — `status:` to the label, `done` when closed — `updated:` today, `review_by:` forward; the epic is authoritative, the charter never argues with it); `gh` absent / epic unreachable → **unverifiable** (NEEDS-REVIEW row `project <slug>: epic <ref> unreachable`). A charter with a missing or malformed `epic:` is a judgment item → NEEDS-REVIEW row; a missing `project.md` under a slug folder is reported, never scaffolded (the charter's content is `/project-init`'s job).
   - **`decisions.md` — the ledger — is append-only and NEVER re-stamped by this pass.** Its `updated:` moves only when a decision is appended, by the owner in conversation; a ledger envelope failure (missing `status`/`tldr`) is a NEEDS-REVIEW row, not a repair. Everything else in the slug folder is the project's workspace — never read, never stamped.

Never invent a fact to fill a gap, and never delete a published fact just because its source is unreachable today — that's what the flag is for. **v1-contract folder** (old `verified:` stamps, no `facts.yaml`): reconcile the old way (bump `verified:`) and add one migration-nudge line to the report.

### Step 3: Publish (own folder only)

Changes staged strictly under `agents/<name>/` (identity fallback first, so a bare deployed container never fails the commit):

```bash
git -C canon config user.email >/dev/null || { git -C canon config user.name "<name>"; git -C canon config user.email "<name>@agents.local"; }
git -C canon add "agents/<name>/"
git -C canon commit -m "canon(<name>): reconcile — <V> verified, <U> updated, <F> flagged"
git -C canon push || { git -C canon pull --rebase --autostash && git -C canon push; }
```

Nothing to commit (all verified, no stamp older than today) → fine, report and end. One rebase-on-reject retry on push, then report the error verbatim.

### Step 4: Report

```
Canon reconcile — agents/<name>/ @ canon@<short-sha>
  lint: <clean | <n> findings — <m> repaired, <k> flagged | no linter (/add-canon-lint)>
  verified unchanged: <V>   updated: <U>   flagged unverifiable: <F>
  relations: <r> doc(s) · <t> open thread(s) aged >30d   (omit line when no relation docs)
  projects: <p> charter(s) · <v> verified · <c> re-mirrored from epic · <f> flagged   (omit line when no projects/)
  needs-review rows: <total open>   pushed: <yes | no — local only | error>
```

Then publish a guarded Trinity report: `mcp__trinity__report(report_type: "<agent>.canon_reconcile", display_hint: "table", payload: <the counts>)` — if the tool is absent **or** raises an auth/permission/scope error, swallow it and continue; the git push already succeeded.

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | One-line stop — run `/add-canon` (never hang a scheduled run) |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo` (auth-aware); only a failed clone stops the run |
| Clone/pull/push auth failure | Report names the headless fix — `GH_TOKEN` into `.env` via `inject_credentials` — and `/canon-doctor`; never an interactive `gh auth login` |
| `pull --ff-only` fails (diverged) | Report and stop — no force, no rebase of shared history |
| Source unreachable | Flag in NEEDS-REVIEW.md; keep the published fact and its stamps |
| Lint FAIL that needs judgment (key conflict, reachability) | NEEDS-REVIEW.md row — a headless run never resolves a dispute |
| Prose contradicts its own mirrored fact entry | `changed` outcome — reconcile them in the same commit |
| Project charter disagrees with its epic | `changed` — mirror the epic (status / done); the epic is the authoritative record |
| Project charter's epic unreachable / `gh` absent | NEEDS-REVIEW row; stamps untouched |
| `decisions.md` ledger fails its envelope | NEEDS-REVIEW row — never re-stamp or edit a ledger on a schedule |
| Push rejected twice | Report verbatim; commit stays local — next run retries |
| Change detected outside own folder | Do not stage it; note it in the report (someone edited the clone — `/canon-publish` classifies it properly) |
| Report tool absent / key out of scope | Swallow; the reconcile already succeeded |
