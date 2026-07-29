---
name: add-canon-lint
description: Install deterministic consistency linting into a fleet's shared canon repo — seeds tools/canon-lint/ (stdlib-only Python, no LLM), lint/rules.yaml (severity config), a GitHub Actions workflow that lints every push/PR, and the "Lintable structure" section of CONVENTIONS.md defining the two-zone folder schema (facts.yaml = purely lintable claims, docs/ = prose with a linted envelope). Runs the first lint, offers migration seeding for pre-schema folders, and optionally makes the lint a required PR status check. Targets the canon repo itself, not an agent — run once per fleet; the per-agent gate ships with add-canon ≥1.4 runtime skills (/canon-publish lints before pushing, /canon-doctor verifies the linter).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-07-29
  author: Ability.ai
  changelog:
    - "1.0: Initial version — deterministic canon linter (9 rules: envelope, fact-schema, key-grammar, one-home-per-key, ownership, staleness, source-resolution, reachability, layout warn) seeded into the canon repo as tools/canon-lint/canon_lint.py + lint/rules.yaml + .github/workflows/canon-lint.yml + CONVENTIONS.md two-zone schema section; strict vs migration (report-only) presets; first-run report; sanctioned migration seeding for pre-schema folders; optional required-status-check branch protection; delivery via direct push or PR"
---

# Add Canon Lint

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `add-canon-lint vX.Y — recent: <summary>`. Then proceed.

Make the fleet's canon repo **mechanically self-consistent**: a deterministic linter — plain Python, zero dependencies, zero LLM — that runs on every push and enforces the two-zone folder schema (`facts.yaml` structured claims + enveloped prose in `docs/`), catches cross-folder fact conflicts, stale canon, ownership violations, and unreachable docs *before* they become drift disputes.

**Division of labor (the design):** the linter on every push = **internal consistency** — grammar, ownership, one-home-per-key, staleness bounds. Each agent's scheduled `/canon-reconcile` = **external truth** — does the fact still match reality? The linter deliberately never judges content; reconcile deliberately never re-derives what the linter already proved.

**Where the gates sit** (own-folder writes are *direct pushes*, so CI alone cannot block them):

| Gate | When | Blocks? |
|---|---|---|
| `/canon-publish` local lint (add-canon ≥1.4 runtime skills) | before every push | yes — the real gate for agent writes |
| `.github/workflows/canon-lint.yml` | every push + PR | red X; backstop for human edits and drift |
| Required status check (optional, Step 6) | PRs to protected branches | yes — for `protocols/` + cross-folder PRs |

This skill targets the **canon repo**, not an agent — run it once per fleet, from the orchestrator, any enrolled agent, or inside the canon repo itself. `/add-canon` installs the layer; this installs its law.

---

## Process

### Step 1: Preflight — locate the canon repo

Resolve the target, first match wins:

1. **Run from an enrolled agent** — `template.yaml` has `x-canon:` → target is the clone at `clone_path` (default `canon/`); if the clone is missing, self-heal it exactly as `/canon-publish` Step 1 does (auth-aware).
2. **Run inside the canon repo** — `agents/` directory and `CONVENTIONS.md` present → target is the current directory.
3. **Neither** — ask for the canon repo ref (`github:Org/repo` → clone to a temp dir, or a local path).

```bash
command -v git     >/dev/null 2>&1 || { echo "git is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required — the linter and the local publish gate run on it"; exit 1; }
command -v gh      >/dev/null 2>&1 || warn "gh not installed — PR delivery and branch protection (Step 6) will be unavailable"
```

Confirm the target is healthy: `git -C <canon> pull --ff-only` (divergence → stop, same rule as every canon skill). Record the default branch.

### Step 2: Confirm scope

Use `AskUserQuestion`:

**Q1 — Enforcement preset?**
- `Strict` (Recommended for new/small canons) — every rule `fail` (layout stays `warn`); the first CI run goes red until the repo conforms.
- `Migration (report-only)` — every rule `warn`; CI reports everything, blocks nothing. Flip rules to `fail` later by editing `lint/rules.yaml` (one line per rule, via PR).

**Q2 — Delivery?**
- `Branch + PR` (Recommended for adopted/shared canons) — the linting infrastructure lands via review, like any root-file change.
- `Direct push to <default branch>` — fine for a fresh canon or when you own the repo outright.

**Q3 — Branch protection: require the lint check on PRs?** *(only if `gh` is authed and the repo is `github:`)*
- `Yes` — `canon-lint / lint` becomes a required status check on the default branch (needs admin on the repo).
- `Not now` — the workflow still runs and reports; nothing is blocked at merge time.

### Step 3: Seed the linting artifacts (guarded — never clobber)

```bash
SKILL_DIR="<this add-canon-lint skill's own directory>"
cd <canon>

# The linter — one file, stdlib only
if [ ! -f tools/canon-lint/canon_lint.py ]; then
  mkdir -p tools/canon-lint
  cp "$SKILL_DIR/templates/canon_lint.py" tools/canon-lint/canon_lint.py
fi

# Severity config — {{SEVERITY}} = fail (strict) or warn (migration), per Q1
if [ ! -f lint/rules.yaml ]; then
  mkdir -p lint
  sed "s/{{SEVERITY}}/$SEVERITY/g" "$SKILL_DIR/templates/rules.yaml.template" > lint/rules.yaml
fi

# CI workflow
if [ ! -f .github/workflows/canon-lint.yml ]; then
  mkdir -p .github/workflows
  cp "$SKILL_DIR/templates/canon-lint.yml.template" .github/workflows/canon-lint.yml
fi

# CONVENTIONS.md — append the schema/grammar section once
grep -q '^## Lintable structure' CONVENTIONS.md 2>/dev/null || \
  { printf '\n' >> CONVENTIONS.md; cat "$SKILL_DIR/templates/conventions-lint-section.md.template" >> CONVENTIONS.md; }
```

If an artifact already exists but differs from the template (e.g. an older linter), show the diff and ask: update / keep. An update to `canon_lint.py` is safe — behavior is config-driven; `lint/rules.yaml` is **live fleet configuration** and is never overwritten.

### Step 4: First lint — the state of the canon, measured

```bash
python3 tools/canon-lint/canon_lint.py --repo .
```

Show the report verbatim. Then interpret it honestly:

- **Clean** → say so; the fleet starts green.
- **Failures in pre-schema folders** (v1 front matter, no `facts.yaml`) → offer **migration seeding** — a sanctioned cross-folder write, same class as enrollment seeding (documented in the CONVENTIONS section): for each folder, scaffold `facts.yaml` with `facts: []`, and port existing front matter mechanically (`status: canonical`, `review_by:` = `verified:` + 30 days, `tldr:` from the first heading; `owner`/`updated` kept). **Never invent fact entries** — mirroring claims into `facts.yaml` is the owner's judgment; leave a one-line note in each seeded folder's report row telling the owner to run `/canon-publish` after declaring facts.
- **Real conflicts** (`one-home-per-key` across folders) → these are the drift disputes the linter exists for; list them and leave resolution to the owners (cross-folder = PR territory). Migration preset keeps CI green meanwhile; strict preset means CI stays red until they're settled — say which applies.

Re-run after any seeding and show the delta.

### Step 5: Deliver

One commit for the whole install: `canon: install deterministic linting (canon-lint) — <strict|migration> preset`.

- **Direct push** (Q2): `git push` from the default branch.
- **Branch + PR**: push `canon/add-lint` and `gh pr create` with the first-run report in the body — reviewers see exactly what goes red.

If this ran from an agent's `canon/` clone, note that the clone is now ahead-of/at HEAD — nothing else to sync.

### Step 6: Branch protection (only if Q3 = Yes)

```bash
SLUG="<Org/repo>"; BRANCH="<default-branch>"
gh api -X PUT "repos/$SLUG/branches/$BRANCH/protection/required_status_checks" \
  -f strict=true -f 'contexts[]=canon-lint / lint' 2>/dev/null || \
gh api -X PUT "repos/$SLUG/branches/$BRANCH/protection" \
  --input - <<'JSON'
{"required_status_checks":{"strict":true,"contexts":["canon-lint / lint"]},
 "enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null}
JSON
```

(The first form updates an existing protection rule; the fallback creates one with only the status check set — it does **not** add review requirements the fleet didn't ask for.) Failure (no admin, API shape) → WARN with the manual path: repo Settings → Branches → require `canon-lint / lint`. Be explicit about the limit: protection gates **PRs**; agents' direct own-folder pushes are gated locally by `/canon-publish` — that's by design, not a hole.

### Step 7: Summary

```
## Canon linting installed → <repo ref> (<strict | migration> preset)

### Seeded
- tools/canon-lint/canon_lint.py        (deterministic, stdlib-only — 9 rules)
- lint/rules.yaml                       (severities — live config, change via PR)
- .github/workflows/canon-lint.yml      (lints every push + PR)
- CONVENTIONS.md § Lintable structure   (two-zone schema + restricted grammar + rule table)

### First run
<folders>/<facts>/<docs> scanned — <n> failures, <n> warnings
<one line per finding class, or "clean">
migration seeding: <n folders scaffolded | none needed | declined>

### Gates
- CI:        <pushed | PR <url>>
- Protection: <required check installed | manual: Settings → Branches | skipped>
- Local:     /canon-publish ≥1.2 lints before every push — fleets on older runtime
             skills get it by re-running /add-canon (or its Step 9 enrollment)

### Next steps
1. Owners of seeded folders: declare your facts — mirror the claims others rely on
   into facts.yaml, then /canon-publish.
2. Resolve any one-home-per-key conflicts via PR between the owning agents.
3. <migration preset only> When the report is quiet, flip lint/rules.yaml to fail (via PR).
4. /canon-doctor ≥1.1 verifies the linter end-to-end from any agent — dispatch it fleet-wide.
```

---

## Error handling

| Situation | Action |
|---|---|
| No canon repo found (no `x-canon:`, not in one, no ref given) | Stop → run `/add-canon` first; this skill installs the law, not the layer |
| `python3` missing | Stop — the linter and the publish gate both need it |
| `pull --ff-only` fails (diverged clone) | Stop, show status — never force; same rule as every canon skill |
| Artifact exists but differs from template | Show diff, ask update/keep; `lint/rules.yaml` is never overwritten |
| First lint finds cross-folder conflicts | Report as the product working, not an install failure; owners resolve via PR |
| Migration seeding on a folder with unparseable files | Skip that folder, name it in the report — never guess a port |
| Push/PR fails (auth) | Context-aware fix (workstation `gh auth login` · deployed `GH_TOKEN` per add-canon Step 6b); commit stays local, say so |
| Branch protection API fails (no admin) | WARN + manual path; everything else stands |
| Canon repo has no `agents/` dir | Exit-2 from the linter — wrong repo; re-check the target |

## Idempotency

Re-running is safe: every artifact is seeded only when absent; `canon_lint.py` updates are diff-shown and asked; `lint/rules.yaml` and CONVENTIONS.md sections are grep-guarded and never overwritten; migration seeding skips folders that already conform; branch protection PUT is idempotent. Re-run after adding folders, after add-canon enrollments, or to roll out a newer linter.
