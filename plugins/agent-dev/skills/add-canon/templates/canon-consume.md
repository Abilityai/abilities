---
name: canon-consume
description: "Read published canonical data from the fleet's shared canon repo — another agent's folder or a protocol — always fresh (pull first) and always cited at canon@<short-sha>, with staleness flagged from the verified: stamps. Read-only."
allowed-tools: Read, Bash, Glob, Grep
user-invocable: true
argument-hint: "<agent-or-protocol> [path]"
metadata:
  version: "1.0"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version — fresh read (pull --ff-only, degrade to last-known ref offline), fuzzy target resolution across agents/ and protocols/, citation at canon@<short-sha>, staleness flags from verified: stamps against the CONVENTIONS.md bound; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Consume

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-consume vX.Y — recent: <summary>`. Then proceed.

Read what another agent (or the fleet) has **published** — the canonical record, not a chat answer. This skill is strictly **read-only**: it never writes to the canon repo, not even a stamp.

**Argument:** `<agent-or-protocol> [path]` — e.g. `/canon-consume researcher`, `/canon-consume researcher accounts.md`, `/canon-consume handoff-protocol`.

## Process

### Step 1: Load config + freshen

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` default `canon/`). No `x-canon:` block → stop, point at `/add-canon`. Clone missing at `clone_path` (fresh deploy — the path is gitignored) → **self-heal**: re-clone from `x-canon.repo` (`gh repo clone` / `git clone`, same resolution as `/canon-publish`) and note it in the report. Then:

```bash
git -C canon pull --ff-only 2>/dev/null || echo "OFFLINE_OR_DIVERGED"
```

On failure, continue with the local copy but **say so** — the citation then reads `canon@<sha> (local copy — pull failed, may be stale)`.

### Step 2: Resolve the target

1. `agents/<arg>/` exists → that folder (optionally narrowed to `[path]`).
2. Else `protocols/<arg>*` matches → that protocol file.
3. Else fuzzy: case-insensitive substring match over `agents/*/` names and `protocols/*` filenames. One hit → use it, noting the resolution. Multiple → list them and ask. Zero → list what *is* published (`ls agents/ protocols/`) and stop — **don't guess, and don't fall back to private sources silently**; if the data isn't in canon, say it isn't published and suggest asking the owning agent (or `/orchestrate` in orchestrator fleets).

### Step 3: Read and cite

Read the resolved files. Every answer built from canon carries a citation:

```
canon@<short-sha> (<commit date>) · agents/<owner>/<file> · updated: <stamp> · verified: <stamp>
```

`git -C canon rev-parse --short HEAD` supplies the sha.

### Step 4: Flag staleness — trust accordingly

Read the staleness bound from `canon/CONVENTIONS.md` (default **30 days**). Any consumed file whose `verified:` stamp is older gets a visible flag:

```
⚠️ stale: verified <date> (> <bound> days ago) — treat with caution; the owner's /canon-reconcile should refresh it
```

Never present stale canon as current fact without the flag.

### Step 5: Report

Answer the actual question from the consumed data, citations inline, stale flags where they apply, and a one-line footer: `source: canon@<sha> · <n> file(s) from agents/<owner>/ (and protocols/ if used)`.

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | Stop → `/add-canon` |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo`; stop only if the clone itself fails |
| Pull fails (offline / diverged) | Read local copy, mark the citation as possibly stale |
| Target not found | List published agents/protocols; suggest the owning agent — never guess |
| File lacks front-matter stamps | Consume it, but flag `unstamped — freshness unknown` |
| Asked to write/fix canon data | Refuse — that's `/canon-publish` (own folder) or a PR (someone else's) |
