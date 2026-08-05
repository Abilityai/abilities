---
name: canon-consume
description: "Read published canonical data from the fleet's shared canon repo — another agent's folder or a protocol — always fresh (pull first) and always cited at canon@<short-sha>, answering from the owner's facts.yaml (the structured claims zone) before opening prose, with staleness flagged from review_by: dates. `<agent> relations` serves both sides of a collaboration record with divergence named. Read-only."
allowed-tools: Read, Bash, Glob, Grep
user-invocable: true
argument-hint: "<agent-or-protocol> [path]"
metadata:
  version: "1.3"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.3: Relations mode — `/canon-consume <agent> relations` serves both sides of a collaboration record (the counterpart's docs/relations/<self>.md and this agent's own docs/relations/<counterpart>.md) and notes divergence explicitly — open threads or events one side logged that the other didn't are the dropped-thread signal CONVENTIONS.md § Relations defines; plain agent reads gain a one-line footer when a relation pair exists"
    - "1.2: Two-zone fast path — resolve against the owner's facts.yaml first (key/value entries are the claims the fleet may rely on; cite the fact key in the citation) and open docs/ prose only when the question needs the explanation behind the claim; staleness now reads per-item review_by: dates (canonical + past due = flagged) instead of a blanket 30-day bound, with the verified:-stamp rule kept as fallback for v1-contract folders; status honored — draft and superseded items are never served as current fact"
    - "1.1: Self-heal clone inherits /canon-publish v1.1's auth-aware resolution (gh when logged in → GH_TOKEN/GITHUB_TOKEN credential helper → plain https for public repos), so a deployed instance can re-clone a private canon; clone failures point at /canon-doctor"
    - "1.0: Initial version — fresh read (pull --ff-only, degrade to last-known ref offline), fuzzy target resolution across agents/ and protocols/, citation at canon@<short-sha>, staleness flags from verified: stamps against the CONVENTIONS.md bound; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Consume

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-consume vX.Y — recent: <summary>`. Then proceed.

Read what another agent (or the fleet) has **published** — the canonical record, not a chat answer. This skill is strictly **read-only**: it never writes to the canon repo, not even a stamp.

**Argument:** `<agent-or-protocol> [path]` — e.g. `/canon-consume researcher`, `/canon-consume researcher accounts.md`, `/canon-consume handoff-protocol`.

## Process

### Step 1: Load config + freshen

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` default `canon/`). No `x-canon:` block → stop, point at `/add-canon`. Clone missing at `clone_path` (fresh deploy — the path is gitignored) → **self-heal**: re-clone from `x-canon.repo` using the same auth-aware resolution as `/canon-publish` Step 1 (gh when logged in → `GH_TOKEN` credential helper on a deployed instance → plain https for public repos) and note it in the report. Then:

```bash
git -C canon pull --ff-only 2>/dev/null || echo "OFFLINE_OR_DIVERGED"
```

On failure, continue with the local copy but **say so** — the citation then reads `canon@<sha> (local copy — pull failed, may be stale)`.

### Step 2: Resolve the target

1. `agents/<arg>/` exists → that folder (optionally narrowed to `[path]`).
2. Else `protocols/<arg>*` matches → that protocol file.
3. Else fuzzy: case-insensitive substring match over `agents/*/` names and `protocols/*` filenames. One hit → use it, noting the resolution. Multiple → list them and ask. Zero → list what *is* published (`ls agents/ protocols/`) and stop — **don't guess, and don't fall back to private sources silently**; if the data isn't in canon, say it isn't published and suggest asking the owning agent (or `/orchestrate` in orchestrator fleets).

**Relations mode** — `[path]` is the literal word `relations` (e.g. `/canon-consume dev relations`): serve **both sides** of the collaboration record (CONVENTIONS.md § Relations) — the counterpart's view of this agent, `agents/<arg>/docs/relations/<self>.md`, and this agent's own view, `agents/<self>/docs/relations/<arg>.md` (`<self>` from `x-canon.folder`). Then compare the pair and **name the divergence explicitly**: open threads or events one side logged that the other didn't — that asymmetry is the dropped-thread signal the convention exists to surface. One side missing → say which side has no record; both missing → "no relationship record on either side — starts on first real interaction." Reading the own view here is fine (still read-only); appending the current interaction to it is `/canon-publish`'s job, not this skill's.

### Step 3: Read and cite — facts first, prose second

**Fast path:** if the target folder has `facts.yaml`, check whether its entries answer the question — they are precisely the claims the owner published for the fleet to rely on. Serve from a matching entry (`status: canonical` only — never serve `draft` or `superseded` as current fact; note a `superseded` hit as history) and cite the key:

```
canon@<short-sha> (<commit date>) · agents/<owner>/facts.yaml · <key> · updated: <stamp> · review_by: <date>
```

Open `profile.md` / `docs/` prose only when the question needs the explanation *behind* the claim — then cite the file:

```
canon@<short-sha> (<commit date>) · agents/<owner>/<file> · updated: <stamp> · review_by: <date>
```

`git -C canon rev-parse --short HEAD` supplies the sha.

### Step 4: Flag staleness — trust accordingly

Per-item: anything `canonical` whose `review_by:` date is past gets a visible flag:

```
⚠️ stale: review_by <date> is past — treat with caution; the owner's /canon-reconcile should refresh it
```

**v1-contract fallback** (folder has old `verified:` stamps, no `review_by:`): use the CONVENTIONS.md bound (default **30 days**) against `verified:`, as before. Never present stale canon as current fact without the flag.

### Step 5: Report

Answer the actual question from the consumed data, citations inline, stale flags where they apply, and a one-line footer: `source: canon@<sha> · <n> file(s) from agents/<owner>/ (and protocols/ if used)`. On a plain agent read (not relations mode), if a relation pair exists between this agent and the target, add one footer line: `relations: collaboration record exists on <both sides | their side only | your side only> — /canon-consume <agent> relations`.

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | Stop → `/add-canon` |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo` (auth-aware); stop only if the clone itself fails — then point at `/canon-doctor` |
| Pull fails (offline / diverged) | Read local copy, mark the citation as possibly stale; repeated auth failures → `/canon-doctor` |
| Target not found | List published agents/protocols; suggest the owning agent — never guess |
| File lacks front-matter stamps | Consume it, but flag `unstamped — freshness unknown` |
| Asked to write/fix canon data | Refuse — that's `/canon-publish` (own folder) or a PR (someone else's) |
