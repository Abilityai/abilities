---
name: canon-publish
description: "Publish this agent's canonical data — freshen the shared canon repo clone, review working changes, enforce the own-folder-only write rule (cross-folder changes split to a branch + PR), stamp the two-zone schema (facts.yaml entries + doc envelopes), run the deterministic canon linter as the pre-push gate, commit and push."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.4"
  created: 2026-07-28
  author: Ability.ai
  changelog:
    - "1.4: Relation docs (docs/relations/<counterpart>.md, CONVENTIONS.md § Relations) — sanctioned home for relational events (asks, commitments, handoffs, outcomes with refs): Step 4's process-state exclusion does not bar them, tick-by-tick status still stays out; on publish the cap is enforced (more than 10 events → fold the oldest into the Earlier: rolling summary) and the doc must be linked from profile.md under ## Relations before the commit — an unlinked canonical doc is exactly what the reachability lint rejects"
    - "1.3: Publish test as the first review gate (Step 4) — before stamping, each new/changed claim must pass 'would another agent decide something differently knowing this?'; self-describing registry data (agent version, schedule counts, internal cadences) is working state and stays out of the publish, reported rather than silently committed; process state (active runs, pending requests) never publishes — it belongs in messages/events, not a durable repo"
    - "1.2: Two-zone schema + local lint gate — stamping follows the new contract (docs: owner/status/updated/review_by/tldr envelope; facts.yaml entries: key/value/status/updated/review_by/source; updated: today on content change, review_by: pushed +30 days when it's missing or past); new Step 4b runs the canon repo's deterministic linter (tools/canon-lint, seeded by /add-canon-lint) scoped to this folder before any push — lint FAILs stop the publish (this local gate is what CI cannot be for direct own-folder pushes); linter absent → note /add-canon-lint once and continue; v1-contract folders (verified:/source:, no facts.yaml) still publish, with a one-line migration nudge"
    - "1.1: Deploy-ready auth — the self-heal clone is credential-aware (gh when logged in, else a GH_TOKEN/GITHUB_TOKEN credential helper wired at clone time that reads the env var at use — the token never lands on disk, else plain https for public repos); git-identity fallback before commit; clone/push remediation is context-aware (workstation gh auth login vs deployed GH_TOKEN via .env + inject_credentials) and points at /canon-doctor"
    - "1.0: Initial version — own-folder direct commits with updated: stamping and rebase-on-reject push retry; anything outside the folder (other agents' folders, protocols/, root files) goes out as a branch + PR via gh, never a direct push; self-heals a missing clone from x-canon.repo (fresh deploys)"
---

# Canon Publish

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `canon-publish vX.Y — recent: <summary>`. Then proceed.

Move this agent's canonical data from *edited* to *published*: review what changed in the canon clone, stamp it, commit it, push it. The write rule is structural, not etiquette: **direct commits only inside this agent's own folder**; every other path goes out as a branch + PR so the owner (via CODEOWNERS) reviews it.

## Process

### Step 1: Load the layer config

Read `template.yaml` → `x-canon:` (`repo`, `clone_path` — default `canon/` — and `folder`). Use `yq -r '.["x-canon"].folder // ""' template.yaml`, with a grep fallback when `yq` is absent. No `x-canon:` block → stop: "Canon layer not installed — run `/add-canon` first."

**Self-heal a missing clone** (fresh deploy — `clone_path` is gitignored, so a re-cloned agent arrives without it): if `x-canon.repo` is declared but there's no repo at `clone_path`, re-clone it instead of stopping:

```bash
[ -d canon/.git ] || case "$CANON_REPO" in
  github:*)
    SLUG="${CANON_REPO#github:}"
    if gh auth status >/dev/null 2>&1; then
      gh repo clone "$SLUG" canon
    elif [ -n "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]; then
      # headless/deployed — credential helper reads the env token at use time; nothing secret lands on disk
      git clone -c credential.helper='!f(){ echo username=x-access-token; echo "password=${GH_TOKEN:-$GITHUB_TOKEN}"; };f' \
        "https://github.com/$SLUG" canon
    else
      git clone "https://github.com/$SLUG" canon   # public read works; pushes will need gh or GH_TOKEN
    fi ;;
  *) git clone "$CANON_REPO" canon ;;
esac
```

(`git clone -c` also persists the helper into the new clone's config, so later pulls/pushes authenticate the same way.) Note the re-clone in the report. Clone fails (auth, no access) → stop with the exact remote and the context-appropriate fix: on a workstation, `gh auth login`; on a deployed instance, `GH_TOKEN` (fine-grained PAT — canon repo only, Contents: Read and write) into `.env` via `inject_credentials` (`/trinity:onboard` Step 5e). `/canon-doctor` runs the full diagnostic ladder.

### Step 2: Freshen the clone

```bash
git -C canon pull --ff-only
```

If the pull fails (diverged history): **stop and report** — never force, never rebase silently. Divergence means something committed to this folder outside this skill; show `git -C canon status` + the divergent commits and let the operator resolve.

### Step 3: Inventory and classify the changes

```bash
git -C canon status --porcelain
```

Split changed paths into:
- **IN** — inside `x-canon.folder` (e.g. `agents/<name>/…`) → publishable directly.
- **OUT** — everything else: another agent's folder, `protocols/`, root files → PR-only.

Nothing changed → say so and stop.

### Step 4: Stamp the IN files (two-zone contract — see `canon/CONVENTIONS.md` § Lintable structure)

- **The publish test comes first — content, then stamps.** For each new or changed claim: *would another agent (or a human) decide something differently knowing this?* If it only describes this agent — its version, schedule counts, internal cadences — it is working state, not canon: leave it out of the publish and say so in the report (see `canon/CONVENTIONS.md` § What belongs here, where present). Process state (active runs, pending requests) never publishes — that traffic belongs in messages/events. (`profile.md`, `docs/*.md`): set `updated:` to today (UTC); if `review_by:` is missing or already past, push it to today + 30 days; ensure `owner:` matches this agent's folder and `status:` is one of `canonical | draft | superseded`. New docs get the full envelope — `owner`, `status`, `updated`, `review_by`, `tldr` (one line, quoted).
- **Changed `facts.yaml` entries**: same stamping (`updated:` today, `review_by:` forward when missing/past); every entry needs `key` (lowercase dotted `subject.relation`), `value`, `status`, `source`. A claim other agents will rely on that only exists in prose → offer to mirror it as a fact entry now.
- **Relation docs** (`docs/relations/<counterpart>.md` — CONVENTIONS.md § Relations): the sanctioned home for *relational* events — asks, commitments, handoffs, deliveries, outcomes, one line each with refs. The process-state exclusion above does not bar them; tick-by-tick status still stays out. On publish, enforce the cap — more than 10 events → fold the oldest into the `Earlier:` rolling summary — and make sure the doc is linked from `profile.md` under `## Relations` (add the link in the same commit; an unlinked canonical doc is exactly what the reachability lint rejects).
- **Draft discipline:** a doc you're linking from `profile.md` must be `status: canonical` — publishing a draft into the index is exactly what the linter rejects.
- **v1-contract folder** (old `verified:` stamps, no `facts.yaml`): stamp the old way, publish, and add one line to the report — "folder predates the two-zone schema; migrate via /add-canon-lint's seeding or CONVENTIONS.md § Migration note."

### Step 4b: Lint — the local gate CI cannot be

Own-folder writes are direct pushes, so the repo's CI can only report them after the fact; **this** is the gate:

```bash
[ -f canon/tools/canon-lint/canon_lint.py ] && \
  python3 canon/tools/canon-lint/canon_lint.py --repo canon --scope "agents/<name>" || true
```

- Linter present + **FAIL** findings in scope → **stop before committing**: show the findings, fix (or downgrade the item to `status: draft` and unlink it), re-run. Never push a red own folder — cross-folder `one-home-per-key` conflicts surfacing here are a dispute to settle with the other owner via PR, not to push past.
- Linter present + warnings only → publish, include the warnings in the report.
- Linter absent → continue (fleets without linting still publish); note once: "no deterministic linter in this canon — seed it with /add-canon-lint."

### Step 5: Publish IN — direct commit + push

Show a diffstat first (`git -C canon diff --stat` scoped to the folder). Then commit — with an identity fallback so a bare deployed container never fails the commit itself:

```bash
git -C canon config user.email >/dev/null || { git -C canon config user.name "<name>"; git -C canon config user.email "<name>@agents.local"; }
git -C canon add "agents/<name>/"
git -C canon commit -m "canon(<name>): <one-line summary of what changed and why>"
git -C canon push || { git -C canon pull --rebase --autostash && git -C canon push; }
```

One rebase-on-reject retry; if it still fails, report the exact error — never leave the operator guessing whether the publish landed. Own-folder publishes need no approval gate: the folder is this agent's to keep true, and git history is the audit trail.

### Step 6: Route OUT via branch + PR (never direct)

If OUT paths exist:

```bash
BRANCH="canon/<name>/<short-slug>"
git -C canon checkout -b "$BRANCH"
git -C canon add <OUT paths only>
git -C canon commit -m "canon(<name>): propose — <what and why>"
git -C canon push -u origin "$BRANCH"
gh pr create --repo <Org/repo> --head "$BRANCH" \
  --title "canon(<name>): <what>" \
  --body  "Proposed by <name>. Touches: <paths>. Why: <reason>. Owner review per CODEOWNERS."
git -C canon checkout <default-branch>
```

Report the PR URL. `gh` absent or no remote → commit on the branch, stay on the default branch, and print the manual PR instructions. **Never** fold OUT paths into the Step 5 direct push — not even trivial ones.

### Step 7: Report

```
Published: <n> file(s) in agents/<name>/ → canon@<short-sha>
Proposed:  <PR URL | none> (<paths>)
Skipped:   <anything left unstaged, and why>
```

## Error handling

| Situation | Action |
|---|---|
| No `x-canon:` | Stop → `/add-canon` |
| Clone missing at `clone_path` (fresh deploy) | Self-heal: re-clone from `x-canon.repo` (auth-aware — gh / env-token helper / plain https); stop only if the clone itself fails |
| Clone or push denied (auth) | Context-aware fix: workstation → `gh auth login`; deployed → `GH_TOKEN` via `.env` + `inject_credentials`; `/canon-doctor` diagnoses the full ladder |
| `pull --ff-only` fails (diverged) | Stop, show status + divergent commits — operator resolves |
| Push rejected twice | Report the error verbatim; the commit is local — say so |
| OUT change with no remote/`gh` | Branch committed locally; print manual PR steps |
| File without front-matter | Add the envelope per CONVENTIONS.md § Lintable structure before committing |
| Lint FAIL in own folder (Step 4b) | Stop before commit — fix, or downgrade to `status: draft` and unlink; never push red |
| Lint FAIL is a cross-folder key conflict | A drift dispute, not a push blocker to bypass — settle with the other owner via PR |
| Linter missing in the canon repo | Publish normally; note `/add-canon-lint` once |
| Secrets spotted in the diff (keys, tokens, credentials) | Refuse to publish that file; canon is public-safe by convention |
