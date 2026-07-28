---
name: canon-reconcile
description: "Scheduled freshness pass over this agent's own folder in the shared canon repo — verify each published fact against its declared source, update what changed, bump the verified:/updated: stamps, push, and flag what could not be verified in NEEDS-REVIEW.md. Headless-safe — never asks mid-run, never touches other folders."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__trinity__report
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version — walks the own folder, verifies each file against its source: front-matter (workspace path, API, doc), three outcomes (verified → bump verified:, changed → edit + bump both stamps, unverifiable → NEEDS-REVIEW.md row, never a guess), own-folder-only commit + push, guarded Trinity report; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Reconcile

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-reconcile vX.Y — recent: <summary>`. Then proceed.

The duty that makes the canon trustworthy: **is my published folder still true?** This runs on a schedule (or manually), verifies every fact in `agents/<name>/` against its declared source, and repairs or flags — it never guesses and never asks. Scope is hard: this skill reads and writes **only this agent's own folder**. It is autonomous-safe: no `AskUserQuestion`, no gates, single task, well under the 45-minute budget.

## Process

### Step 1: Load config + freshen

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` default `canon/`, `folder`). No `x-canon:` block → stop with a one-line note (headless runs must fail loudly-but-cleanly, not hang). Clone missing at `clone_path` (fresh deploy — the path is gitignored) → **self-heal**: re-clone from `x-canon.repo` quietly and note it in the report; only a failed clone stops the run. Then `git -C canon pull --ff-only`; on divergence, **report and stop** — a reconcile must start from the shared truth, and force-anything is forbidden.

### Step 2: Walk the owned folder

For every canonical file in `agents/<name>/` (skip `NEEDS-REVIEW.md`):

1. Read its front-matter — `owner:`, `updated:`, `verified:`, `source:` (see `canon/CONVENTIONS.md`).
2. Resolve `source:`:
   - a workspace path (this agent's own repo) → re-read it and compare the facts
   - an API/tool this agent owns → re-query, compare
   - a doc/URL → re-fetch if cheap, else treat as manual
   - `manual` / absent → nothing to verify against mechanically
3. Three outcomes, exactly one per file:
   - **Verified unchanged** → bump `verified:` to today. Content untouched.
   - **Source changed** → edit the content to match reality, bump `updated:` **and** `verified:`.
   - **Unverifiable** (source unreachable, `manual`, ambiguous) → leave stamps alone; upsert one row into `agents/<name>/NEEDS-REVIEW.md` (`| file | why unverifiable | since |` — dedup on file, keep the earliest `since`). A verified-later file gets its row removed.

Never invent a fact to fill a gap, and never delete a published fact just because its source is unreachable today — that's what the flag is for.

### Step 3: Publish (own folder only)

Changes staged strictly under `agents/<name>/`:

```bash
git -C canon add "agents/<name>/"
git -C canon commit -m "canon(<name>): reconcile — <V> verified, <U> updated, <F> flagged"
git -C canon push || { git -C canon pull --rebase --autostash && git -C canon push; }
```

Nothing to commit (all verified, no stamp older than today) → fine, report and end. One rebase-on-reject retry on push, then report the error verbatim.

### Step 4: Report

```
Canon reconcile — agents/<name>/ @ canon@<short-sha>
  verified unchanged: <V>   updated: <U>   flagged unverifiable: <F>
  needs-review rows: <total open>   pushed: <yes | no — local only | error>
```

Then publish a guarded Trinity report: `mcp__trinity__report(report_type: "<agent>.canon_reconcile", display_hint: "table", payload: <the counts>)` — if the tool is absent **or** raises an auth/permission/scope error, swallow it and continue; the git push already succeeded.

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | One-line stop — run `/add-canon` (never hang a scheduled run) |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo`; only a failed clone stops the run |
| `pull --ff-only` fails (diverged) | Report and stop — no force, no rebase of shared history |
| Source unreachable | Flag in NEEDS-REVIEW.md; keep the published fact and its stamps |
| Push rejected twice | Report verbatim; commit stays local — next run retries |
| Change detected outside own folder | Do not stage it; note it in the report (someone edited the clone — `/canon-publish` classifies it properly) |
| Report tool absent / key out of scope | Swallow; the reconcile already succeeded |
